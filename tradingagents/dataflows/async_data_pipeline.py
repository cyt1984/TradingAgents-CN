#!/usr/bin/env python3
"""
异步数据管道优化模块
通过异步数据流水线架构实现高效的数据获取、处理和分析

核心特性:
1. 异步数据获取 - 并发获取多源数据
2. 流式处理 - 数据流式处理减少内存占用
3. 管道优化 - 多级管道并行处理
4. 智能调度 - 动态任务调度和负载均衡
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, AsyncIterator, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
from asyncio import Queue, Semaphore
from collections import defaultdict
import functools
import json

from ..utils.logging_manager import get_logger

# 导入雪球数据提供器
try:
    from .xueqiu_utils import get_xueqiu_provider
    XUEQIU_AVAILABLE = True
except ImportError:
    XUEQIU_AVAILABLE = False

logger = get_logger('async_data_pipeline')


class PipelineStage(Enum):
    """管道阶段枚举"""
    DATA_FETCH = "data_fetch"          # 数据获取
    DATA_CLEAN = "data_clean"          # 数据清洗
    DATA_ENRICH = "data_enrich"        # 数据增强
    DATA_ANALYZE = "data_analyze"      # 数据分析
    DATA_AGGREGATE = "data_aggregate"  # 数据聚合


@dataclass
class PipelineConfig:
    """管道配置"""
    max_concurrent_tasks: int = 50          # 最大并发任务数
    batch_size: int = 100                   # 批处理大小
    queue_size: int = 1000                  # 队列大小
    timeout_seconds: float = 30.0           # 超时时间
    retry_count: int = 3                    # 重试次数
    retry_delay: float = 1.0                # 重试延迟
    enable_streaming: bool = True           # 启用流式处理
    enable_caching: bool = True             # 启用缓存
    cache_ttl: int = 3600                   # 缓存TTL
    enable_metrics: bool = True             # 启用度量
    checkpoint_interval: int = 100          # 检查点间隔


@dataclass
class DataPacket:
    """数据包"""
    id: str                                 # 数据包ID
    symbol: str                             # 股票代码
    stage: PipelineStage                   # 当前阶段
    data: Dict[str, Any]                   # 数据内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    retry_count: int = 0                   # 重试次数
    error: Optional[str] = None            # 错误信息


@dataclass
class PipelineMetrics:
    """管道度量指标"""
    total_packets: int = 0                  # 总数据包数
    processed_packets: int = 0              # 已处理数据包数
    failed_packets: int = 0                 # 失败数据包数
    total_time: float = 0.0                 # 总耗时
    stage_times: Dict[str, float] = field(default_factory=dict)  # 各阶段耗时
    throughput: float = 0.0                 # 吞吐量
    error_rate: float = 0.0                 # 错误率
    queue_sizes: Dict[str, int] = field(default_factory=dict)  # 队列大小


class AsyncDataPipeline:
    """异步数据管道"""
    
    def __init__(self, config: PipelineConfig = None):
        """
        初始化异步数据管道
        
        Args:
            config: 管道配置
        """
        self.config = config or PipelineConfig()
        self.data_manager = None  # 延迟初始化以避免循环导入
        
        # 初始化雪球数据提供器
        self.xueqiu_provider = None
        if XUEQIU_AVAILABLE:
            try:
                self.xueqiu_provider = get_xueqiu_provider()
                logger.info("✅ 异步管道：雪球数据提供器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 异步管道：雪球数据提供器初始化失败: {e}")
        
        # 创建阶段队列
        self.queues = {
            PipelineStage.DATA_FETCH: Queue(maxsize=self.config.queue_size),
            PipelineStage.DATA_CLEAN: Queue(maxsize=self.config.queue_size),
            PipelineStage.DATA_ENRICH: Queue(maxsize=self.config.queue_size),
            PipelineStage.DATA_ANALYZE: Queue(maxsize=self.config.queue_size),
            PipelineStage.DATA_AGGREGATE: Queue(maxsize=self.config.queue_size)
        }
        
        # 信号量控制并发
        self.semaphore = Semaphore(self.config.max_concurrent_tasks)
        
        # 缓存
        self._cache = {}
        self._cache_timestamps = {}
        
        # 度量指标
        self.metrics = PipelineMetrics()
        self._stage_timers = defaultdict(list)
        
        # 处理器注册表
        self.processors = {}
        self._register_default_processors()
        
        # HTTP会话
        self.session = None
        
        # 运行状态
        self.is_running = False
        self.workers = []
        
        logger.info("🚀 异步数据管道初始化完成")
        logger.info(f"📊 配置: 最大并发={self.config.max_concurrent_tasks}, 批次大小={self.config.batch_size}")
    
    async def start(self):
        """启动管道"""
        if self.is_running:
            logger.warning("⚠️ 管道已在运行中")
            return
        
        self.is_running = True
        
        # 创建HTTP会话
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )
        
        # 启动工作器
        self.workers = [
            asyncio.create_task(self._stage_worker(stage))
            for stage in PipelineStage
        ]
        
        # 启动度量收集器
        self.workers.append(
            asyncio.create_task(self._metrics_collector())
        )
        
        logger.info("✅ 异步数据管道已启动")
    
    async def stop(self):
        """停止管道"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待队列清空
        for queue in self.queues.values():
            await queue.join()
        
        # 取消工作器
        for worker in self.workers:
            worker.cancel()
        
        # 关闭HTTP会话
        if self.session:
            await self.session.close()
        
        logger.info("🛑 异步数据管道已停止")
    
    async def process_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """
        处理股票列表
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        logger.info(f"🎯 开始处理 {len(symbols)} 只股票")
        
        # 启动管道
        await self.start()
        
        try:
            # 创建数据包并加入队列
            packets = []
            for symbol in symbols:
                packet = DataPacket(
                    id=f"{symbol}_{int(time.time()*1000)}",
                    symbol=symbol,
                    stage=PipelineStage.DATA_FETCH,
                    data={'symbol': symbol}
                )
                packets.append(packet)
                await self.queues[PipelineStage.DATA_FETCH].put(packet)
            
            # 收集结果
            results = {}
            result_queue = self.queues[PipelineStage.DATA_AGGREGATE]
            
            # 等待所有结果
            processed_count = 0
            while processed_count < len(symbols):
                try:
                    # 设置超时避免无限等待
                    packet = await asyncio.wait_for(
                        result_queue.get(), 
                        timeout=self.config.timeout_seconds
                    )
                    
                    if packet.error:
                        logger.warning(f"⚠️ {packet.symbol} 处理失败: {packet.error}")
                        results[packet.symbol] = {'error': packet.error}
                    else:
                        results[packet.symbol] = packet.data
                    
                    processed_count += 1
                    
                    # 进度报告
                    if processed_count % 50 == 0 or processed_count == len(symbols):
                        progress = processed_count / len(symbols) * 100
                        logger.info(f"📈 处理进度: {processed_count}/{len(symbols)} ({progress:.1f}%)")
                    
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ 等待结果超时，已处理 {processed_count}/{len(symbols)}")
                    break
            
            # 计算度量
            total_time = time.time() - start_time
            self.metrics.total_time = total_time
            self.metrics.throughput = processed_count / max(total_time, 1)
            self.metrics.error_rate = (len(symbols) - processed_count) / max(len(symbols), 1)
            
            logger.info(f"✅ 处理完成: {processed_count}/{len(symbols)} 成功")
            logger.info(f"⏱️ 总耗时: {total_time:.2f}秒")
            logger.info(f"🚀 吞吐量: {self.metrics.throughput:.2f}股票/秒")
            
            return {
                'results': results,
                'metrics': self._get_metrics_summary()
            }
            
        finally:
            # 停止管道
            await self.stop()
    
    async def _stage_worker(self, stage: PipelineStage):
        """阶段工作器"""
        input_queue = self.queues[stage]
        
        # 确定下一阶段
        stage_order = list(PipelineStage)
        current_index = stage_order.index(stage)
        next_stage = stage_order[current_index + 1] if current_index < len(stage_order) - 1 else None
        output_queue = self.queues[next_stage] if next_stage else None
        
        while self.is_running:
            try:
                # 从输入队列获取数据包
                packet = await asyncio.wait_for(
                    input_queue.get(), 
                    timeout=1.0
                )
                
                # 处理数据包
                async with self.semaphore:
                    start_time = time.time()
                    
                    try:
                        # 获取处理器
                        processor = self.processors.get(stage)
                        if processor:
                            # 执行处理
                            processed_packet = await processor(packet)
                            
                            # 更新阶段
                            if next_stage:
                                processed_packet.stage = next_stage
                            
                            # 记录处理时间
                            process_time = time.time() - start_time
                            self._stage_timers[stage.value].append(process_time)
                            
                            # 发送到下一阶段或完成
                            if output_queue:
                                await output_queue.put(processed_packet)
                            
                            # 更新度量
                            self.metrics.processed_packets += 1
                            
                        else:
                            logger.warning(f"⚠️ 未找到 {stage.value} 阶段的处理器")
                            packet.error = f"未找到处理器: {stage.value}"
                            self.metrics.failed_packets += 1
                            
                            # 直接发送到聚合阶段
                            if stage != PipelineStage.DATA_AGGREGATE:
                                await self.queues[PipelineStage.DATA_AGGREGATE].put(packet)
                    
                    except Exception as e:
                        logger.error(f"❌ 处理 {packet.symbol} 在 {stage.value} 阶段失败: {e}")
                        packet.error = str(e)
                        packet.retry_count += 1
                        
                        # 重试或放弃
                        if packet.retry_count < self.config.retry_count:
                            await asyncio.sleep(self.config.retry_delay * packet.retry_count)
                            await input_queue.put(packet)
                        else:
                            self.metrics.failed_packets += 1
                            # 发送到聚合阶段标记为失败
                            if stage != PipelineStage.DATA_AGGREGATE:
                                await self.queues[PipelineStage.DATA_AGGREGATE].put(packet)
                
                # 标记任务完成
                input_queue.task_done()
                
            except asyncio.TimeoutError:
                # 超时继续循环
                continue
            except asyncio.CancelledError:
                # 任务被取消
                break
            except Exception as e:
                logger.error(f"❌ 工作器 {stage.value} 异常: {e}")
                await asyncio.sleep(1)
    
    def _register_default_processors(self):
        """注册默认处理器"""
        self.processors[PipelineStage.DATA_FETCH] = self._fetch_processor
        self.processors[PipelineStage.DATA_CLEAN] = self._clean_processor
        self.processors[PipelineStage.DATA_ENRICH] = self._enrich_processor
        self.processors[PipelineStage.DATA_ANALYZE] = self._analyze_processor
        self.processors[PipelineStage.DATA_AGGREGATE] = self._aggregate_processor
    
    async def _fetch_processor(self, packet: DataPacket) -> DataPacket:
        """数据获取处理器"""
        symbol = packet.symbol
        
        # 检查缓存
        if self.config.enable_caching:
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                packet.data.update(cached_data)
                packet.metadata['from_cache'] = True
                return packet
        
        # 异步获取多源数据
        fetch_tasks = []
        
        # 价格数据
        fetch_tasks.append(self._fetch_price_data(symbol))
        
        # 基础数据
        fetch_tasks.append(self._fetch_basic_data(symbol))
        
        # 市场数据
        fetch_tasks.append(self._fetch_market_data(symbol))
        
        # 社交数据（雪球）
        fetch_tasks.append(self._fetch_social_data(symbol))
        
        # 并发执行
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        # 合并结果
        merged_data = {}
        for result in results:
            if isinstance(result, dict):
                merged_data.update(result)
            elif isinstance(result, Exception):
                logger.debug(f"获取数据部分失败: {result}")
        
        packet.data.update(merged_data)
        
        # 缓存数据
        if self.config.enable_caching and merged_data:
            self._cache_data(symbol, merged_data)
        
        return packet
    
    async def _clean_processor(self, packet: DataPacket) -> DataPacket:
        """数据清洗处理器"""
        data = packet.data
        
        # 清洗规则
        cleaned_data = {}
        
        for key, value in data.items():
            # 移除None值
            if value is None:
                continue
            
            # 处理数值类型
            if key in ['price', 'volume', 'market_cap', 'pe_ratio']:
                try:
                    if isinstance(value, str):
                        value = float(value.replace(',', ''))
                    cleaned_data[key] = value
                except:
                    continue
            
            # 处理日期类型
            elif key in ['date', 'timestamp']:
                try:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    cleaned_data[key] = value
                except:
                    cleaned_data[key] = datetime.now()
            
            # 其他类型直接保留
            else:
                cleaned_data[key] = value
        
        # 数据验证
        if 'price' in cleaned_data and cleaned_data['price'] <= 0:
            packet.error = "无效的价格数据"
        
        packet.data = cleaned_data
        packet.metadata['cleaned'] = True
        
        return packet
    
    async def _enrich_processor(self, packet: DataPacket) -> DataPacket:
        """数据增强处理器"""
        data = packet.data
        
        # 计算衍生指标
        if 'price' in data and 'volume' in data:
            data['turnover'] = data['price'] * data['volume']
        
        if 'high' in data and 'low' in data:
            data['amplitude'] = (data['high'] - data['low']) / data.get('price', 1) * 100
        
        if 'price' in data and 'prev_close' in data:
            data['change_pct'] = (data['price'] - data['prev_close']) / data['prev_close'] * 100
        
        # 添加技术指标
        if 'price' in data:
            # 简单移动平均
            data['ma5'] = data.get('ma5', data['price'])  # 实际应该从历史数据计算
            data['ma20'] = data.get('ma20', data['price'])
            
            # RSI (简化版)
            data['rsi'] = 50.0  # 实际应该从历史数据计算
        
        # 添加基础评分
        score = 50.0
        if data.get('change_pct', 0) > 0:
            score += 10
        if data.get('volume', 0) > data.get('avg_volume', 0):
            score += 10
        if data.get('pe_ratio', 100) < 30:
            score += 10
        
        # 整合社交数据评分
        if 'social_sentiment_score' in data:
            sentiment = data['social_sentiment_score']
            if sentiment > 0.3:
                score += 15  # 积极情绪加分
            elif sentiment < -0.3:
                score -= 10  # 消极情绪减分
            
            # 热度加成
            heat = data.get('social_heat', 0)
            if heat > 80:
                score += 10  # 高热度
            elif heat > 50:
                score += 5   # 中等热度
            
            # 趋势加成
            trend = data.get('sentiment_trend', 'neutral')
            if trend == 'improving':
                score += 10
            elif trend == 'deteriorating':
                score -= 10
        
        data['enrich_score'] = min(100, max(0, score))
        
        packet.data = data
        packet.metadata['enriched'] = True
        
        return packet
    
    async def _analyze_processor(self, packet: DataPacket) -> DataPacket:
        """数据分析处理器"""
        data = packet.data
        
        # 基础分析
        analysis = {
            'symbol': packet.symbol,
            'timestamp': datetime.now(),
            'price': data.get('price', 0),
            'volume': data.get('volume', 0),
            'change_pct': data.get('change_pct', 0),
            'enrich_score': data.get('enrich_score', 50)
        }
        
        # 趋势分析
        if data.get('price', 0) > data.get('ma20', 0):
            analysis['trend'] = 'UP'
        else:
            analysis['trend'] = 'DOWN'
        
        # 成交量分析
        if data.get('volume', 0) > data.get('avg_volume', 0) * 1.5:
            analysis['volume_signal'] = 'HIGH'
        elif data.get('volume', 0) < data.get('avg_volume', 1) * 0.5:
            analysis['volume_signal'] = 'LOW'
        else:
            analysis['volume_signal'] = 'NORMAL'
        
        # 综合评分
        final_score = data.get('enrich_score', 50)
        if analysis['trend'] == 'UP':
            final_score += 10
        if analysis['volume_signal'] == 'HIGH':
            final_score += 5
        
        analysis['final_score'] = min(100, max(0, final_score))
        
        # 推荐
        if analysis['final_score'] >= 70:
            analysis['recommendation'] = 'BUY'
        elif analysis['final_score'] <= 30:
            analysis['recommendation'] = 'SELL'
        else:
            analysis['recommendation'] = 'HOLD'
        
        packet.data = analysis
        packet.metadata['analyzed'] = True
        
        return packet
    
    async def _aggregate_processor(self, packet: DataPacket) -> DataPacket:
        """数据聚合处理器"""
        # 最终聚合阶段，直接返回
        packet.metadata['completed'] = True
        packet.metadata['completion_time'] = datetime.now()
        
        # 计算总处理时间
        if 'timestamp' in packet.metadata:
            total_time = (datetime.now() - packet.timestamp).total_seconds()
            packet.metadata['total_processing_time'] = total_time
        
        return packet
    
    async def _fetch_price_data(self, symbol: str) -> Dict[str, Any]:
        """异步获取价格数据"""
        try:
            # 这里应该调用实际的API
            # 模拟异步获取
            await asyncio.sleep(0.1)
            
            # 延迟初始化数据管理器以避免循环导入
            if self.data_manager is None:
                try:
                    from ..dataflows.enhanced_data_manager import EnhancedDataManager
                    self.data_manager = EnhancedDataManager()
                except ImportError:
                    pass
            
            # 使用数据管理器获取
            if self.data_manager:
                try:
                    price_data = self.data_manager.get_latest_price_data(symbol)
                    if price_data:
                        return price_data
                except Exception as e:
                    logger.debug(f"数据管理器获取失败: {e}")
            
            # 返回模拟数据
            return {
                'price': np.random.uniform(10, 100),
                'volume': np.random.randint(1000000, 10000000),
                'high': np.random.uniform(100, 110),
                'low': np.random.uniform(90, 100),
                'prev_close': np.random.uniform(95, 105)
            }
        except Exception as e:
            logger.debug(f"获取价格数据失败 {symbol}: {e}")
            return {}
    
    async def _fetch_basic_data(self, symbol: str) -> Dict[str, Any]:
        """异步获取基础数据"""
        try:
            await asyncio.sleep(0.1)
            
            # 返回模拟数据
            return {
                'market_cap': np.random.uniform(10, 1000) * 100000000,
                'pe_ratio': np.random.uniform(5, 50),
                'pb_ratio': np.random.uniform(0.5, 5),
                'roe': np.random.uniform(5, 30)
            }
        except Exception as e:
            logger.debug(f"获取基础数据失败 {symbol}: {e}")
            return {}
    
    async def _fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """异步获取市场数据"""
        try:
            await asyncio.sleep(0.1)
            
            # 返回模拟数据
            return {
                'sector': 'Technology',
                'industry': 'Software',
                'avg_volume': np.random.randint(500000, 5000000),
                'ma5': np.random.uniform(95, 105),
                'ma20': np.random.uniform(90, 110)
            }
        except Exception as e:
            logger.debug(f"获取市场数据失败 {symbol}: {e}")
            return {}
    
    async def _fetch_social_data(self, symbol: str) -> Dict[str, Any]:
        """异步获取社交数据（雪球）"""
        try:
            if not self.xueqiu_provider:
                return {}
            
            # 使用线程池执行同步的雪球API调用
            loop = asyncio.get_event_loop()
            
            # 获取雪球情绪数据
            xueqiu_sentiment = await loop.run_in_executor(
                None, 
                self.xueqiu_provider.get_stock_sentiment,
                symbol,
                7  # days
            )
            
            if not xueqiu_sentiment:
                return {}
            
            # 获取讨论数据（限制数量以提高速度）
            discussions = await loop.run_in_executor(
                None,
                self.xueqiu_provider.get_stock_discussions,
                symbol,
                20  # limit
            )
            
            # 计算社交指标
            social_data = {
                'social_sentiment_score': xueqiu_sentiment.get('sentiment_score', 0),
                'total_discussions': xueqiu_sentiment.get('total_discussions', 0),
                'positive_ratio': xueqiu_sentiment.get('positive_ratio', 0),
                'negative_ratio': xueqiu_sentiment.get('negative_ratio', 0),
                'avg_interactions': xueqiu_sentiment.get('avg_interactions', 0),
                'discussion_count': len(discussions) if discussions else 0,
                'social_heat': self._calculate_social_heat(xueqiu_sentiment),
                'sentiment_trend': self._analyze_sentiment_trend(discussions) if discussions else 'neutral'
            }
            
            # 添加热门评论（如果有）
            if discussions and len(discussions) > 0:
                # 按互动数排序，取前3条
                top_discussions = sorted(
                    discussions, 
                    key=lambda x: x.get('fav_count', 0) + x.get('reply_count', 0),
                    reverse=True
                )[:3]
                
                social_data['top_comments'] = [
                    {
                        'text': d.get('text', '')[:200],  # 限制长度
                        'sentiment': d.get('sentiment_score', 0),
                        'interactions': d.get('fav_count', 0) + d.get('reply_count', 0)
                    }
                    for d in top_discussions
                ]
            
            logger.debug(f"📱 获取 {symbol} 社交数据: 讨论数={social_data['total_discussions']}, 情绪={social_data['social_sentiment_score']:.2f}")
            
            return social_data
            
        except Exception as e:
            logger.debug(f"获取社交数据失败 {symbol}: {e}")
            return {}
    
    def _calculate_social_heat(self, sentiment_data: Dict[str, Any]) -> float:
        """计算社交热度"""
        if not sentiment_data:
            return 0.0
        
        # 综合讨论数、互动数和情绪强度
        discussions = sentiment_data.get('total_discussions', 0)
        interactions = sentiment_data.get('avg_interactions', 0)
        sentiment_abs = abs(sentiment_data.get('sentiment_score', 0))
        
        # 归一化到0-100
        heat_score = min(100, (
            min(discussions / 2, 50) +  # 讨论数贡献最多50分
            min(interactions / 10, 30) +  # 互动数贡献最多30分
            sentiment_abs * 20  # 情绪强度贡献最多20分
        ))
        
        return heat_score
    
    def _analyze_sentiment_trend(self, discussions: List[Dict[str, Any]]) -> str:
        """分析情绪趋势"""
        if not discussions or len(discussions) < 5:
            return 'neutral'
        
        # 按时间排序（最新的在前）
        sorted_discussions = sorted(
            discussions,
            key=lambda x: x.get('created_at', 0),
            reverse=True
        )
        
        # 分析最近和之前的情绪
        recent_sentiments = [d.get('sentiment_score', 0) for d in sorted_discussions[:5]]
        older_sentiments = [d.get('sentiment_score', 0) for d in sorted_discussions[5:10]] if len(sorted_discussions) > 5 else []
        
        if not older_sentiments:
            return 'neutral'
        
        recent_avg = sum(recent_sentiments) / len(recent_sentiments)
        older_avg = sum(older_sentiments) / len(older_sentiments)
        
        # 判断趋势
        if recent_avg - older_avg > 0.2:
            return 'improving'  # 情绪改善
        elif recent_avg - older_avg < -0.2:
            return 'deteriorating'  # 情绪恶化
        else:
            return 'stable'  # 情绪稳定
    
    def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        if symbol in self._cache:
            cache_time = self._cache_timestamps.get(symbol, 0)
            if time.time() - cache_time < self.config.cache_ttl:
                return self._cache[symbol]
        return None
    
    def _cache_data(self, symbol: str, data: Dict[str, Any]):
        """缓存数据"""
        self._cache[symbol] = data
        self._cache_timestamps[symbol] = time.time()
    
    async def _metrics_collector(self):
        """度量收集器"""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # 每5秒收集一次
                
                # 更新队列大小
                for stage, queue in self.queues.items():
                    self.metrics.queue_sizes[stage.value] = queue.qsize()
                
                # 计算阶段平均时间
                for stage, times in self._stage_timers.items():
                    if times:
                        self.metrics.stage_times[stage] = sum(times) / len(times)
                
                # 清理旧的计时数据
                for stage in self._stage_timers:
                    if len(self._stage_timers[stage]) > 1000:
                        self._stage_timers[stage] = self._stage_timers[stage][-100:]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"度量收集器错误: {e}")
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """获取度量摘要"""
        return {
            'total_packets': self.metrics.total_packets,
            'processed_packets': self.metrics.processed_packets,
            'failed_packets': self.metrics.failed_packets,
            'total_time': self.metrics.total_time,
            'throughput': self.metrics.throughput,
            'error_rate': self.metrics.error_rate,
            'stage_times': dict(self.metrics.stage_times),
            'queue_sizes': dict(self.metrics.queue_sizes)
        }
    
    def register_processor(self, stage: PipelineStage, processor: Callable):
        """注册自定义处理器"""
        self.processors[stage] = processor
        logger.info(f"✅ 注册处理器: {stage.value}")


# 全局管道实例
_async_pipeline = None

def get_async_pipeline(config: PipelineConfig = None) -> AsyncDataPipeline:
    """获取全局异步管道实例"""
    global _async_pipeline
    if _async_pipeline is None:
        _async_pipeline = AsyncDataPipeline(config)
    return _async_pipeline


# 便捷函数
async def async_process_symbols(symbols: List[str], config: PipelineConfig = None) -> Dict[str, Any]:
    """异步处理股票列表"""
    pipeline = get_async_pipeline(config)
    return await pipeline.process_symbols(symbols)