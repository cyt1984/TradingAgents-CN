#!/usr/bin/env python3
"""
AI分析批次并行处理器
通过批量并行处理显著提升AI股票分析的速度和效率

核心功能:
1. 智能批次分组 - 根据系统资源动态调整批次大小
2. 并行处理管理 - 多线程/异步处理多个批次
3. 失败重试机制 - 自动重试失败的分析任务
4. 进度跟踪报告 - 实时反馈处理进度
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
import psutil
import gc
from functools import partial

from ..utils.logging_manager import get_logger

# 导入分析师类 - 如果不存在则创建模拟类
try:
    from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
except ImportError:
    class FundamentalsAnalyst:
        def analyze(self, symbol): return {'score': 50, 'recommendation': 'HOLD'}

try:
    from ..agents.analysts.technical_analyst import TechnicalAnalyst
except ImportError:
    class TechnicalAnalyst:
        def analyze(self, symbol): return {'score': 50, 'recommendation': 'HOLD'}

try:
    from ..agents.analysts.news_analyst import NewsAnalyst
except ImportError:
    class NewsAnalyst:
        def analyze(self, symbol): return {'score': 50, 'recommendation': 'HOLD'}

# 导入雪球数据提供器
try:
    from ..dataflows.xueqiu_utils import get_xueqiu_provider
    XUEQIU_AVAILABLE = True
except ImportError:
    XUEQIU_AVAILABLE = False
    logger = get_logger('batch_ai_processor')
    logger.warning("⚠️ 雪球数据提供器不可用，将跳过社交情绪分析")

logger = get_logger('batch_ai_processor')


class ProcessingStrategy(Enum):
    """处理策略枚举"""
    SEQUENTIAL = "sequential"          # 顺序处理
    THREADED = "threaded"             # 多线程处理
    ASYNC = "async"                   # 异步处理
    HYBRID = "hybrid"                 # 混合策略


@dataclass
class BatchConfig:
    """批处理配置"""
    batch_size: int = 20              # 每批次处理数量
    max_workers: int = 8              # 最大工作线程数
    strategy: ProcessingStrategy = ProcessingStrategy.HYBRID
    max_retries: int = 3              # 最大重试次数
    retry_delay: float = 1.0          # 重试延迟(秒)
    timeout_per_batch: int = 300      # 每批次超时时间(秒)
    memory_threshold: float = 0.85    # 内存使用阈值
    enable_progress_tracking: bool = True  # 启用进度跟踪
    enable_auto_scaling: bool = True  # 启用自动扩缩容
    cache_results: bool = True        # 缓存结果
    
    # 分析器配置
    enable_fundamentals: bool = True   # 启用基本面分析
    enable_technical: bool = True      # 启用技术面分析
    enable_news: bool = True          # 启用新闻分析
    enable_social: bool = True         # 启用社交情绪分析
    analysis_depth: str = "standard"  # 分析深度: light/standard/deep
    
    # 社交数据配置
    social_weight: float = 0.2        # 社交数据权重
    min_discussions: int = 10         # 最小讨论数量阈值
    sentiment_threshold: float = 0.3  # 情绪显著性阈值


@dataclass
class BatchResult:
    """批处理结果"""
    symbol: str                       # 股票代码
    analysis_result: Dict[str, Any]   # 分析结果
    processing_time: float            # 处理时间
    retry_count: int                  # 重试次数
    success: bool                     # 是否成功
    error_message: str = ""           # 错误信息
    analyst_results: Dict[str, Any] = field(default_factory=dict)  # 各分析师结果


@dataclass
class ProcessingReport:
    """处理报告"""
    total_stocks: int                 # 总股票数
    processed_stocks: int             # 已处理数量
    successful_stocks: int            # 成功处理数量
    failed_stocks: int               # 失败数量
    total_time: float                # 总耗时
    average_time_per_stock: float    # 平均每只股票耗时
    throughput: float                # 处理吞吐量(股票/秒)
    memory_peak: float               # 内存峰值使用率
    batch_stats: Dict[str, Any] = field(default_factory=dict)  # 批次统计


class BatchAIProcessor:
    """AI批次并行处理器"""
    
    def __init__(self, config: BatchConfig = None):
        """
        初始化批次处理器
        
        Args:
            config: 批处理配置
        """
        self.config = config or BatchConfig()
        self._results_cache = {}
        self._processing_queue = Queue()
        self._results_queue = Queue()
        self._progress_lock = threading.Lock()
        self._memory_monitor = threading.Thread(target=self._monitor_memory, daemon=True)
        self._stop_monitoring = False
        
        # 初始化分析师
        self.analysts = {}
        if self.config.enable_fundamentals:
            self.analysts['fundamentals'] = FundamentalsAnalyst()
        if self.config.enable_technical:
            self.analysts['technical'] = TechnicalAnalyst()
        if self.config.enable_news:
            self.analysts['news'] = NewsAnalyst()
        
        # 初始化雪球数据提供器
        self.xueqiu_provider = None
        if self.config.enable_social and XUEQIU_AVAILABLE:
            try:
                self.xueqiu_provider = get_xueqiu_provider()
                logger.info("✅ 雪球数据提供器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 雪球数据提供器初始化失败: {e}")
                self.config.enable_social = False
            
        # 启动内存监控
        self._memory_monitor.start()
        
        logger.info(f"🚀 AI批次并行处理器初始化完成")
        logger.info(f"📊 配置: 批次大小={self.config.batch_size}, 工作线程={self.config.max_workers}, 策略={self.config.strategy.value}")
    
    def process_stocks(self, stock_symbols: List[str], 
                      analysis_callback: Callable[[str], Dict[str, Any]] = None) -> ProcessingReport:
        """
        批量处理股票分析
        
        Args:
            stock_symbols: 股票代码列表
            analysis_callback: 自定义分析回调函数
            
        Returns:
            ProcessingReport: 处理报告
        """
        start_time = time.time()
        total_stocks = len(stock_symbols)
        
        logger.info(f"🎯 开始AI批量分析: {total_stocks}只股票")
        logger.info(f"🔄 处理策略: {self.config.strategy.value}")
        
        # 动态调整批次配置
        if self.config.enable_auto_scaling:
            self._adjust_batch_config(total_stocks)
        
        try:
            # 创建批次
            batches = self._create_batches(stock_symbols)
            logger.info(f"📦 创建批次: {len(batches)}个批次, 平均每批{self.config.batch_size}只股票")
            
            # 执行批量处理
            all_results = {}
            processing_stats = {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'batches_completed': 0,
                'start_time': start_time
            }
            
            if self.config.strategy == ProcessingStrategy.THREADED:
                all_results = self._process_batches_threaded(batches, analysis_callback, processing_stats)
            elif self.config.strategy == ProcessingStrategy.ASYNC:
                all_results = self._process_batches_async(batches, analysis_callback, processing_stats)
            elif self.config.strategy == ProcessingStrategy.HYBRID:
                all_results = self._process_batches_hybrid(batches, analysis_callback, processing_stats)
            else:
                all_results = self._process_batches_sequential(batches, analysis_callback, processing_stats)
            
            # 生成处理报告
            total_time = time.time() - start_time
            report = ProcessingReport(
                total_stocks=total_stocks,
                processed_stocks=processing_stats['processed'],
                successful_stocks=processing_stats['successful'],
                failed_stocks=processing_stats['failed'],
                total_time=total_time,
                average_time_per_stock=total_time / max(total_stocks, 1),
                throughput=processing_stats['successful'] / max(total_time, 1),
                memory_peak=self._get_memory_usage(),
                batch_stats={
                    'total_batches': len(batches),
                    'completed_batches': processing_stats['batches_completed'],
                    'avg_batch_time': total_time / max(len(batches), 1),
                    'results_cached': len(self._results_cache)
                }
            )
            
            logger.info(f"✅ AI批量分析完成!")
            logger.info(f"📈 处理结果: 总数:{total_stocks} 成功:{processing_stats['successful']} 失败:{processing_stats['failed']}")
            logger.info(f"⏱️  耗时: {total_time:.1f}秒, 吞吐量: {report.throughput:.1f}股票/秒")
            logger.info(f"💾 内存峰值: {report.memory_peak:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ AI批量分析失败: {e}")
            total_time = time.time() - start_time
            return ProcessingReport(
                total_stocks=total_stocks,
                processed_stocks=0,
                successful_stocks=0,
                failed_stocks=total_stocks,
                total_time=total_time,
                average_time_per_stock=0,
                throughput=0,
                memory_peak=self._get_memory_usage(),
                batch_stats={'error': str(e)}
            )
    
    def _create_batches(self, stock_symbols: List[str]) -> List[List[str]]:
        """创建处理批次"""
        batches = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(stock_symbols), batch_size):
            batch = stock_symbols[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def _process_batches_threaded(self, batches: List[List[str]], 
                                 analysis_callback: Callable,
                                 stats: Dict[str, Any]) -> Dict[str, BatchResult]:
        """多线程批次处理"""
        all_results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(self._process_single_batch, batch, analysis_callback): batch_idx
                for batch_idx, batch in enumerate(batches)
            }
            
            # 收集结果
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_results = future.result(timeout=self.config.timeout_per_batch)
                    all_results.update(batch_results)
                    
                    # 更新统计
                    with self._progress_lock:
                        stats['processed'] += len(batch_results)
                        stats['successful'] += sum(1 for r in batch_results.values() if r.success)
                        stats['failed'] += sum(1 for r in batch_results.values() if not r.success)
                        stats['batches_completed'] += 1
                        
                        if self.config.enable_progress_tracking:
                            self._log_progress(stats, len(batches))
                        
                        # 内存清理
                        if stats['batches_completed'] % 5 == 0:
                            gc.collect()
                    
                except Exception as e:
                    logger.error(f"❌ 批次 {batch_idx} 处理失败: {e}")
                    stats['failed'] += len(batches[batch_idx])
        
        return all_results
    
    def _process_batches_async(self, batches: List[List[str]], 
                              analysis_callback: Callable,
                              stats: Dict[str, Any]) -> Dict[str, BatchResult]:
        """异步批次处理"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                self._async_process_batches(batches, analysis_callback, stats)
            )
        finally:
            loop.close()
    
    async def _async_process_batches(self, batches: List[List[str]], 
                                   analysis_callback: Callable,
                                   stats: Dict[str, Any]) -> Dict[str, BatchResult]:
        """异步批次处理实现"""
        all_results = {}
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def process_batch_with_semaphore(batch):
            async with semaphore:
                return await self._async_process_single_batch(batch, analysis_callback)
        
        # 创建所有任务
        tasks = [process_batch_with_semaphore(batch) for batch in batches]
        
        # 执行任务
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                batch_results = await task
                all_results.update(batch_results)
                
                # 更新统计
                stats['processed'] += len(batch_results)
                stats['successful'] += sum(1 for r in batch_results.values() if r.success)
                stats['failed'] += sum(1 for r in batch_results.values() if not r.success)
                stats['batches_completed'] += 1
                
                if self.config.enable_progress_tracking:
                    self._log_progress(stats, len(batches))
                
            except Exception as e:
                logger.error(f"❌ 异步批次 {i} 处理失败: {e}")
                stats['failed'] += len(batches[i])
        
        return all_results
    
    def _process_batches_hybrid(self, batches: List[List[str]], 
                               analysis_callback: Callable,
                               stats: Dict[str, Any]) -> Dict[str, BatchResult]:
        """混合策略批次处理 - 结合线程池和异步"""
        logger.info("🎭 使用混合策略处理批次...")
        
        # 对于小批次使用线程池，大批次使用异步
        small_batches = [b for b in batches if len(b) <= 10]
        large_batches = [b for b in batches if len(b) > 10]
        
        all_results = {}
        
        # 处理小批次（线程池）
        if small_batches:
            logger.info(f"🔄 线程池处理 {len(small_batches)} 个小批次...")
            small_results = self._process_batches_threaded(small_batches, analysis_callback, stats)
            all_results.update(small_results)
        
        # 处理大批次（异步）
        if large_batches:
            logger.info(f"⚡ 异步处理 {len(large_batches)} 个大批次...")
            large_results = self._process_batches_async(large_batches, analysis_callback, stats)
            all_results.update(large_results)
        
        return all_results
    
    def _process_batches_sequential(self, batches: List[List[str]], 
                                   analysis_callback: Callable,
                                   stats: Dict[str, Any]) -> Dict[str, BatchResult]:
        """顺序批次处理"""
        all_results = {}
        
        for batch_idx, batch in enumerate(batches):
            try:
                batch_results = self._process_single_batch(batch, analysis_callback)
                all_results.update(batch_results)
                
                # 更新统计
                stats['processed'] += len(batch_results)
                stats['successful'] += sum(1 for r in batch_results.values() if r.success)
                stats['failed'] += sum(1 for r in batch_results.values() if not r.success)
                stats['batches_completed'] += 1
                
                if self.config.enable_progress_tracking:
                    self._log_progress(stats, len(batches))
                
            except Exception as e:
                logger.error(f"❌ 顺序批次 {batch_idx} 处理失败: {e}")
                stats['failed'] += len(batch)
        
        return all_results
    
    def _process_single_batch(self, batch: List[str], 
                             analysis_callback: Callable) -> Dict[str, BatchResult]:
        """处理单个批次"""
        batch_results = {}
        batch_start = time.time()
        
        logger.debug(f"🔄 处理批次: {len(batch)}只股票")
        
        for symbol in batch:
            result = self._analyze_single_stock(symbol, analysis_callback)
            batch_results[symbol] = result
        
        batch_time = time.time() - batch_start
        logger.debug(f"✅ 批次完成: {len(batch)}只股票, 耗时{batch_time:.1f}秒")
        
        return batch_results
    
    async def _async_process_single_batch(self, batch: List[str], 
                                        analysis_callback: Callable) -> Dict[str, BatchResult]:
        """异步处理单个批次"""
        batch_results = {}
        
        tasks = []
        for symbol in batch:
            task = asyncio.create_task(self._async_analyze_single_stock(symbol, analysis_callback))
            tasks.append((symbol, task))
        
        for symbol, task in tasks:
            try:
                result = await task
                batch_results[symbol] = result
            except Exception as e:
                logger.error(f"❌ 异步分析 {symbol} 失败: {e}")
                batch_results[symbol] = BatchResult(
                    symbol=symbol,
                    analysis_result={},
                    processing_time=0,
                    retry_count=0,
                    success=False,
                    error_message=str(e)
                )
        
        return batch_results
    
    def _analyze_single_stock(self, symbol: str, 
                             analysis_callback: Callable = None) -> BatchResult:
        """分析单只股票"""
        start_time = time.time()
        retry_count = 0
        
        # 检查缓存
        if self.config.cache_results and symbol in self._results_cache:
            cached_result = self._results_cache[symbol]
            logger.debug(f"📋 使用缓存结果: {symbol}")
            return cached_result
        
        while retry_count <= self.config.max_retries:
            try:
                if analysis_callback:
                    # 使用自定义分析回调
                    analysis_result = analysis_callback(symbol)
                else:
                    # 使用内置分析师
                    analysis_result = self._run_builtin_analysis(symbol)
                
                processing_time = time.time() - start_time
                result = BatchResult(
                    symbol=symbol,
                    analysis_result=analysis_result,
                    processing_time=processing_time,
                    retry_count=retry_count,
                    success=True,
                    analyst_results=analysis_result.get('analyst_results', {})
                )
                
                # 缓存结果
                if self.config.cache_results:
                    self._results_cache[symbol] = result
                
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= self.config.max_retries:
                    logger.warning(f"⚠️ {symbol} 分析失败，重试 {retry_count}/{self.config.max_retries}: {error_msg}")
                    time.sleep(self.config.retry_delay * retry_count)  # 指数退避
                else:
                    logger.error(f"❌ {symbol} 分析最终失败: {error_msg}")
                    
                    processing_time = time.time() - start_time
                    return BatchResult(
                        symbol=symbol,
                        analysis_result={},
                        processing_time=processing_time,
                        retry_count=retry_count - 1,
                        success=False,
                        error_message=error_msg
                    )
    
    async def _async_analyze_single_stock(self, symbol: str, 
                                        analysis_callback: Callable = None) -> BatchResult:
        """异步分析单只股票"""
        # 对于异步版本，使用线程池执行同步分析
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._analyze_single_stock, 
            symbol, 
            analysis_callback
        )
    
    def _run_builtin_analysis(self, symbol: str) -> Dict[str, Any]:
        """运行内置分析师分析"""
        analysis_result = {
            'symbol': symbol,
            'analysis_timestamp': datetime.now().isoformat(),
            'analyst_results': {},
            'combined_score': 0.0,
            'recommendation': 'HOLD',
            'social_signals': []  # 添加社交信号列表
        }
        
        scores = {}  # 使用字典存储各维度分数
        weights = {}  # 存储各维度权重
        
        # 基本面分析 (权重30%)
        if 'fundamentals' in self.analysts:
            try:
                fund_result = self.analysts['fundamentals'].analyze(symbol)
                analysis_result['analyst_results']['fundamentals'] = fund_result
                if fund_result and 'score' in fund_result:
                    scores['fundamentals'] = fund_result['score']
                    weights['fundamentals'] = 0.30
            except Exception as e:
                logger.debug(f"⚠️ {symbol} 基本面分析失败: {e}")
        
        # 技术面分析 (权重25%)
        if 'technical' in self.analysts:
            try:
                tech_result = self.analysts['technical'].analyze(symbol)
                analysis_result['analyst_results']['technical'] = tech_result
                if tech_result and 'score' in tech_result:
                    scores['technical'] = tech_result['score']
                    weights['technical'] = 0.25
            except Exception as e:
                logger.debug(f"⚠️ {symbol} 技术面分析失败: {e}")
        
        # 新闻分析 (权重20%)
        if 'news' in self.analysts:
            try:
                news_result = self.analysts['news'].analyze(symbol)
                analysis_result['analyst_results']['news'] = news_result
                if news_result and 'score' in news_result:
                    scores['news'] = news_result['score']
                    weights['news'] = 0.20
            except Exception as e:
                logger.debug(f"⚠️ {symbol} 新闻分析失败: {e}")
        
        # 雪球社交情绪分析 (权重20-25%)
        if self.config.enable_social and self.xueqiu_provider:
            try:
                # 获取雪球情绪数据
                xueqiu_sentiment = self.xueqiu_provider.get_stock_sentiment(symbol, days=7)
                
                if xueqiu_sentiment and xueqiu_sentiment.get('total_discussions', 0) >= self.config.min_discussions:
                    # 计算社交情绪分数
                    social_score = self._calculate_social_score(xueqiu_sentiment)
                    scores['social'] = social_score
                    weights['social'] = self.config.social_weight
                    
                    # 保存原始数据
                    analysis_result['analyst_results']['social'] = {
                        'xueqiu_sentiment': xueqiu_sentiment,
                        'social_score': social_score,
                        'data_source': 'xueqiu'
                    }
                    
                    # 生成社交信号
                    social_signals = self._generate_social_signals(xueqiu_sentiment)
                    analysis_result['social_signals'] = social_signals
                    
                    logger.debug(f"📱 {symbol} 社交情绪分析: 讨论数={xueqiu_sentiment.get('total_discussions')}, 情绪分={social_score:.2f}")
                else:
                    logger.debug(f"⚠️ {symbol} 讨论数量不足，跳过社交分析")
                    
            except Exception as e:
                logger.debug(f"⚠️ {symbol} 社交情绪分析失败: {e}")
        
        # 计算加权综合评分
        if scores:
            # 归一化权重
            total_weight = sum(weights.values())
            if total_weight > 0:
                weighted_score = sum(scores[k] * weights[k] for k in scores) / total_weight
                analysis_result['combined_score'] = weighted_score
            else:
                # 简单平均
                analysis_result['combined_score'] = sum(scores.values()) / len(scores) if scores else 50
            
            # 生成推荐
            if analysis_result['combined_score'] >= 70:
                analysis_result['recommendation'] = 'BUY'
            elif analysis_result['combined_score'] <= 30:
                analysis_result['recommendation'] = 'SELL'
            else:
                analysis_result['recommendation'] = 'HOLD'
            
            # 如果有强烈的社交信号，可能调整推荐
            if 'HIGH_HEAT_WARNING' in analysis_result['social_signals']:
                if analysis_result['recommendation'] == 'BUY':
                    analysis_result['recommendation'] = 'HOLD'  # 降级为持有
                    analysis_result['recommendation_note'] = '社交热度过高，建议谨慎'
            elif 'SENTIMENT_SURGE' in analysis_result['social_signals']:
                if analysis_result['recommendation'] == 'HOLD':
                    analysis_result['recommendation'] = 'BUY'  # 升级为买入
                    analysis_result['recommendation_note'] = '情绪积极转变，值得关注'
        
        return analysis_result
    
    def _calculate_social_score(self, sentiment_data: Dict[str, Any]) -> float:
        """计算社交情绪分数"""
        score = 50.0  # 基础分
        
        # 情绪倾向 (权重40%)
        sentiment_score = sentiment_data.get('sentiment_score', 0)
        if sentiment_score > self.config.sentiment_threshold:
            score += 20  # 积极情绪
        elif sentiment_score < -self.config.sentiment_threshold:
            score -= 20  # 消极情绪
        else:
            score += sentiment_score * 20  # 中性按比例
        
        # 讨论热度 (权重30%)
        discussions = sentiment_data.get('total_discussions', 0)
        if discussions > 100:
            score += 15  # 高热度
        elif discussions > 50:
            score += 10  # 中等热度
        elif discussions > 20:
            score += 5   # 一般热度
        
        # 互动程度 (权重20%)
        avg_interactions = sentiment_data.get('avg_interactions', 0)
        if avg_interactions > 50:
            score += 10
        elif avg_interactions > 20:
            score += 5
        
        # 积极比例 (权重10%)
        positive_ratio = sentiment_data.get('positive_ratio', 0)
        score += (positive_ratio - 0.5) * 20  # 偏离中性的程度
        
        return max(0, min(100, score))
    
    def _generate_social_signals(self, sentiment_data: Dict[str, Any]) -> List[str]:
        """生成社交信号"""
        signals = []
        
        # 热度信号
        discussions = sentiment_data.get('total_discussions', 0)
        if discussions > 200:
            signals.append('EXTREME_HEAT')
        elif discussions > 100:
            signals.append('HIGH_HEAT')
        
        # 情绪信号
        sentiment_score = sentiment_data.get('sentiment_score', 0)
        if sentiment_score > 0.5:
            signals.append('STRONG_BULLISH')
        elif sentiment_score > 0.3:
            signals.append('BULLISH')
        elif sentiment_score < -0.5:
            signals.append('STRONG_BEARISH')
        elif sentiment_score < -0.3:
            signals.append('BEARISH')
        
        # 互动信号
        avg_interactions = sentiment_data.get('avg_interactions', 0)
        if avg_interactions > 100:
            signals.append('HIGH_ENGAGEMENT')
        
        # 预警信号
        if discussions > 300 and sentiment_score > 0.7:
            signals.append('HIGH_HEAT_WARNING')  # 过热预警
        elif discussions > 50 and abs(sentiment_score) > 0.5:
            signals.append('SENTIMENT_SURGE')  # 情绪突变
        
        return signals
    
    def _adjust_batch_config(self, total_stocks: int):
        """根据股票数量和系统资源动态调整批次配置"""
        # 获取系统资源信息
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 基于系统资源调整工作线程数
        optimal_workers = min(
            cpu_count * 2,  # CPU核心数的2倍
            int(memory_gb),  # 每GB内存一个线程
            total_stocks // 10,  # 每10只股票一个线程
            32  # 最大限制
        )
        
        if optimal_workers != self.config.max_workers:
            logger.info(f"🔧 自动调整工作线程: {self.config.max_workers} -> {optimal_workers}")
            self.config.max_workers = max(1, optimal_workers)
        
        # 基于股票数量调整批次大小
        if total_stocks < 100:
            optimal_batch_size = 10
        elif total_stocks < 500:
            optimal_batch_size = 20
        elif total_stocks < 1000:
            optimal_batch_size = 30
        else:
            optimal_batch_size = 50
        
        if optimal_batch_size != self.config.batch_size:
            logger.info(f"🔧 自动调整批次大小: {self.config.batch_size} -> {optimal_batch_size}")
            self.config.batch_size = optimal_batch_size
    
    def _log_progress(self, stats: Dict[str, Any], total_batches: int):
        """记录处理进度"""
        elapsed_time = time.time() - stats['start_time']
        progress_pct = stats['batches_completed'] / total_batches * 100
        throughput = stats['successful'] / max(elapsed_time, 1)
        
        logger.info(f"📈 批次进度: {stats['batches_completed']}/{total_batches} ({progress_pct:.1f}%) "
                   f"成功:{stats['successful']} 失败:{stats['failed']} "
                   f"吞吐量:{throughput:.1f}股票/秒")
    
    def _monitor_memory(self):
        """监控内存使用情况"""
        while not self._stop_monitoring:
            try:
                memory_usage = self._get_memory_usage()
                if memory_usage > self.config.memory_threshold:
                    logger.warning(f"⚠️ 内存使用过高: {memory_usage:.1f}% > {self.config.memory_threshold*100}%")
                    gc.collect()  # 强制垃圾回收
                
                time.sleep(5)  # 每5秒检查一次
            except Exception as e:
                logger.error(f"❌ 内存监控失败: {e}")
                break
    
    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            return psutil.virtual_memory().percent / 100.0
        except:
            return 0.0
    
    def __del__(self):
        """析构函数"""
        self._stop_monitoring = True
        if hasattr(self, '_memory_monitor') and self._memory_monitor.is_alive():
            self._memory_monitor.join(timeout=1)


# 全局批处理器实例
_batch_processor = None

def get_batch_ai_processor(config: BatchConfig = None) -> BatchAIProcessor:
    """获取全局批处理器实例"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchAIProcessor(config)
    return _batch_processor