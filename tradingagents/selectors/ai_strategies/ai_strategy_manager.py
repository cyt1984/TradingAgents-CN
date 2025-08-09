#!/usr/bin/env python3
"""
AI策略管理器
统一管理和协调所有AI选股引擎，提供智能选股决策
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from tradingagents.utils.logging_manager import get_logger
from .expert_committee import AIExpertCommittee
from .adaptive_engine import AdaptiveEngine, MarketRegime, StrategyType
from .pattern_recognizer import PatternRecognizer, PatternType
from .similarity_engine import SimilarityEngine, SimilarityDimension

logger = get_logger('agents')


class AIMode(Enum):
    """AI选股模式"""
    BASIC = "basic"                     # 基础模式
    AI_ENHANCED = "ai_enhanced"         # AI增强模式
    EXPERT_COMMITTEE = "expert_committee"  # 专家委员会模式
    ADAPTIVE = "adaptive"               # 自适应模式
    PATTERN_BASED = "pattern_based"     # 模式驱动模式
    SIMILARITY_BASED = "similarity_based"  # 相似性驱动模式
    FULL_AI = "full_ai"                # 完整AI模式


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    symbol: str                         # 股票代码
    overall_score: float                # 综合AI评分 (0-100)
    confidence_level: float             # 置信度 (0-1)
    recommendation: str                 # AI建议
    risk_assessment: str                # 风险评估
    
    # 各引擎评分
    expert_committee_score: Optional[float] = None
    adaptive_strategy_score: Optional[float] = None  
    pattern_recognition_score: Optional[float] = None
    similarity_score: Optional[float] = None
    
    # 详细分析
    expert_analysis: Optional[Dict[str, Any]] = None
    market_regime: Optional[str] = None
    detected_patterns: Optional[List[str]] = None
    similar_stocks: Optional[List[str]] = None
    
    # 决策因素
    key_factors: List[str] = None
    risk_factors: List[str] = None
    opportunity_factors: List[str] = None
    
    # 元数据
    processing_time: float = 0.0
    timestamp: datetime = None


@dataclass
class AISelectionConfig:
    """AI选股配置"""
    ai_mode: AIMode = AIMode.AI_ENHANCED
    
    # 引擎权重
    expert_committee_weight: float = 0.4
    adaptive_strategy_weight: float = 0.3
    pattern_recognition_weight: float = 0.2
    similarity_weight: float = 0.1
    
    # 阈值配置
    min_ai_score: float = 70.0
    min_confidence: float = 0.6
    max_risk_level: str = "中等"
    
    # 性能配置
    enable_caching: bool = True
    parallel_processing: bool = True
    timeout_seconds: float = 30.0
    
    # 市场数据配置
    market_data_required: bool = True
    news_analysis_enabled: bool = True
    pattern_analysis_enabled: bool = True
    similarity_analysis_enabled: bool = True


class AIStrategyManager:
    """AI策略管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化AI策略管理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # AI引擎实例
        self.expert_committee: Optional[AIExpertCommittee] = None
        self.adaptive_engine: Optional[AdaptiveEngine] = None
        self.pattern_recognizer: Optional[PatternRecognizer] = None
        self.similarity_engine: Optional[SimilarityEngine] = None
        
        # 分析缓存
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 性能统计
        self.performance_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'average_processing_time': 0.0,
            'engine_performance': {}
        }
        
        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        logger.info("AI策略管理器初始化开始")
        self._initialize_ai_engines()
        logger.info("AI策略管理器初始化完成")
        
    def _initialize_ai_engines(self):
        """初始化AI引擎"""
        engines_status = {
            'expert_committee': False,
            'adaptive_engine': False,
            'pattern_recognizer': False,
            'similarity_engine': False
        }
        
        # 1. 初始化专家委员会
        try:
            logger.info("正在初始化AI专家委员会...")
            self.expert_committee = AIExpertCommittee(self.config)
            engines_status['expert_committee'] = True
            logger.info("✅ AI专家委员会初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ AI专家委员会初始化失败: {e}")
            logger.debug(f"专家委员会错误详情: {e}", exc_info=True)
            self.expert_committee = None
            
        # 2. 初始化自适应引擎
        try:
            logger.info("正在初始化自适应策略引擎...")
            self.adaptive_engine = AdaptiveEngine(self.config)
            engines_status['adaptive_engine'] = True
            logger.info("✅ 自适应策略引擎初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 自适应策略引擎初始化失败: {e}")
            logger.debug(f"自适应引擎错误详情: {e}", exc_info=True)
            self.adaptive_engine = None
            
        # 3. 初始化模式识别器
        try:
            logger.info("正在初始化模式识别引擎...")
            self.pattern_recognizer = PatternRecognizer(self.config)
            engines_status['pattern_recognizer'] = True
            logger.info("✅ 模式识别引擎初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 模式识别引擎初始化失败: {e}")
            logger.debug(f"模式识别错误详情: {e}", exc_info=True)
            self.pattern_recognizer = None
            
        # 4. 初始化相似性引擎
        try:
            logger.info("正在初始化相似股票推荐引擎...")
            self.similarity_engine = SimilarityEngine(self.config)
            engines_status['similarity_engine'] = True
            logger.info("✅ 相似股票推荐引擎初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 相似股票推荐引擎初始化失败: {e}")
            logger.debug(f"相似性引擎错误详情: {e}", exc_info=True)
            self.similarity_engine = None
            
        # 记录引擎状态
        successful_engines = [name for name, status in engines_status.items() if status]
        failed_engines = [name for name, status in engines_status.items() if not status]
        
        logger.info(f"🤖 AI引擎初始化完成:")
        logger.info(f"   ✅ 成功: {successful_engines}")
        if failed_engines:
            logger.warning(f"   ❌ 失败: {failed_engines}")
        
        # 存储状态用于监控
        self.performance_stats['engine_initialization'] = engines_status
        
        # 如果所有引擎都失败，给出警告
        if not any(engines_status.values()):
            logger.error("❌ 所有AI引擎初始化失败，将使用基础模式")
        elif len(successful_engines) < len(engines_status) / 2:
            logger.warning("⚠️ 部分AI引擎初始化失败，功能可能受限")
            
    def analyze_stock_with_ai(self, symbol: str, 
                            stock_data: Dict[str, Any],
                            market_data: Dict[str, Any] = None,
                            config: AISelectionConfig = None) -> AIAnalysisResult:
        """
        使用AI分析股票
        
        Args:
            symbol: 股票代码
            stock_data: 股票数据
            market_data: 市场数据
            config: AI配置
            
        Returns:
            AI分析结果
        """
        start_time = datetime.now()
        config = config or AISelectionConfig()
        
        try:
            logger.info(f"🤖 [AI策略管理器] 开始AI分析: {symbol} (模式: {config.ai_mode.value})")
            
            # 显示AI决策过程开始
            logger.info(f"🔍 [AI决策过程] 股票 {symbol} - 开始AI智能分析")
            logger.info(f"📊 [AI决策过程] 分析模式: {config.ai_mode.value}")
            logger.info(f"📋 [AI决策过程] 可用AI引擎: {[name for name, available in self.get_performance_summary()['ai_engines_status'].items() if available]}")
            
            # 检查缓存
            if config.enable_caching:
                cached_result = self._get_cached_analysis(symbol, stock_data)
                if cached_result:
                    self.performance_stats['cache_hits'] += 1
                    logger.info(f"🤖 [AI策略管理器] 使用缓存结果: {symbol}")
                    logger.info(f"⚡ [AI决策过程] 股票 {symbol} - 使用缓存结果，跳过重复分析")
                    return cached_result
            
            # 根据模式选择分析策略
            if config.ai_mode == AIMode.BASIC:
                logger.info(f"📝 [AI决策过程] 股票 {symbol} - 执行基础分析模式")
                result = self._basic_analysis(symbol, stock_data)
            elif config.ai_mode == AIMode.EXPERT_COMMITTEE:
                logger.info(f"👥 [AI决策过程] 股票 {symbol} - 启动专家委员会分析")
                result = self._expert_committee_analysis(symbol, stock_data, market_data)
            elif config.ai_mode == AIMode.ADAPTIVE:
                logger.info(f"🔄 [AI决策过程] 股票 {symbol} - 启动自适应策略分析")
                result = self._adaptive_analysis(symbol, stock_data, market_data)
            elif config.ai_mode == AIMode.PATTERN_BASED:
                logger.info(f"📈 [AI决策过程] 股票 {symbol} - 启动模式识别分析")
                result = self._pattern_based_analysis(symbol, stock_data)
            elif config.ai_mode == AIMode.SIMILARITY_BASED:
                logger.info(f"🔍 [AI决策过程] 股票 {symbol} - 启动相似性分析")
                result = self._similarity_based_analysis(symbol, stock_data)
            elif config.ai_mode == AIMode.FULL_AI:
                logger.info(f"🎆 [AI决策过程] 股票 {symbol} - 启动完整AI分析（全引擎）")
                result = self._full_ai_analysis(symbol, stock_data, market_data, config)
            else:  # AI_ENHANCED
                logger.info(f"⚡ [AI决策过程] 股票 {symbol} - 启动AI增强分析")
                result = self._ai_enhanced_analysis(symbol, stock_data, market_data, config)
            
            # 记录处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            result.timestamp = datetime.now()
            
            # 更新性能统计
            self._update_performance_stats(processing_time)
            
            # 缓存结果
            if config.enable_caching:
                self._cache_analysis(symbol, stock_data, result)
            
            # 显示AI决策过程结果
            logger.info(f"✅ [AI决策过程] 股票 {symbol} - AI分析完成")
            logger.info(f"🎯 [AI决策结果] 综合评分: {result.overall_score:.1f}")
            logger.info(f"💡 [AI决策结果] 投资建议: {result.recommendation}")
            logger.info(f"🔒 [AI决策结果] 风险评估: {result.risk_assessment}")
            logger.info(f"📊 [AI决策结果] 置信度: {result.confidence_level:.2f}")
            logger.info(f"⏱️ [AI决策结果] 分析耗时: {processing_time:.2f}秒")
            
            # 显示AI引擎贡献
            engine_contributions = []
            if result.expert_committee_score is not None:
                engine_contributions.append(f"专家委员会: {result.expert_committee_score:.1f}")
            if result.adaptive_strategy_score is not None:
                engine_contributions.append(f"自适应策略: {result.adaptive_strategy_score:.1f}")
            if result.pattern_recognition_score is not None:
                engine_contributions.append(f"模式识别: {result.pattern_recognition_score:.1f}")
            
            if engine_contributions:
                logger.info(f"🤖 [AI引擎贡献] {' | '.join(engine_contributions)}")
            
            # 显示关键决策因素
            if result.key_factors:
                logger.info(f"🔑 [AI决策因素] 关键因素: {' | '.join(result.key_factors[:3])}")
            
            logger.info(f"🤖 [AI策略管理器] AI分析完成: {symbol} - 评分: {result.overall_score:.1f} (耗时: {processing_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ [AI策略管理器] AI分析失败: {symbol} - {e}")
            logger.error(f"❌ [AI决策过程] 股票 {symbol} - AI分析失败: {e}")
            return self._create_error_result(symbol, str(e), start_time)
    
    def _full_ai_analysis(self, symbol: str, 
                         stock_data: Dict[str, Any],
                         market_data: Dict[str, Any] = None,
                         config: AISelectionConfig = None) -> AIAnalysisResult:
        """完整AI分析 - 使用所有AI引擎"""
        try:
            logger.debug(f"🔬 [完整AI分析] 开始: {symbol}")
            
            # 并行执行所有AI引擎分析
            future_tasks = []
            
            # 1. 专家委员会分析
            if self.expert_committee:
                future_tasks.append(
                    self.thread_pool.submit(
                        self.expert_committee.analyze_stock_committee,
                        symbol, stock_data, market_data.get('news_data', []) if market_data else []
                    )
                )
            
            # 2. 自适应策略分析
            if self.adaptive_engine and market_data:
                future_tasks.append(
                    self.thread_pool.submit(
                        self.adaptive_engine.get_adaptive_recommendations,
                        market_data, [{'symbol': symbol, **stock_data}]
                    )
                )
            
            # 3. 模式识别分析
            if self.pattern_recognizer and 'price_data' in stock_data:
                price_data = stock_data['price_data']
                volume_data = stock_data.get('volume_data', [])
                future_tasks.append(
                    self.thread_pool.submit(
                        self.pattern_recognizer.recognize_patterns,
                        symbol, price_data, volume_data
                    )
                )
            
            # 收集结果
            results = {
                'expert_result': None,
                'adaptive_result': None, 
                'pattern_result': None
            }
            
            # 等待所有任务完成 (带超时)
            timeout = config.timeout_seconds if config else 30.0
            for i, future in enumerate(as_completed(future_tasks, timeout=timeout)):
                try:
                    if i == 0:  # 专家委员会
                        results['expert_result'] = future.result()
                    elif i == 1:  # 自适应策略
                        results['adaptive_result'] = future.result()
                    elif i == 2:  # 模式识别
                        results['pattern_result'] = future.result()
                except Exception as e:
                    logger.warning(f"⚠️ AI引擎分析失败: {e}")
                    continue
            
            # 融合所有结果
            return self._fuse_analysis_results(symbol, results, config)
            
        except Exception as e:
            logger.error(f"❌ 完整AI分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _ai_enhanced_analysis(self, symbol: str, 
                            stock_data: Dict[str, Any],
                            market_data: Dict[str, Any] = None,
                            config: AISelectionConfig = None) -> AIAnalysisResult:
        """AI增强分析 - 平衡性能和智能度"""
        try:
            logger.debug(f"⚡ [AI增强分析] 开始: {symbol}")
            
            # 选择最重要的AI引擎进行分析
            results = {}
            
            # 1. 优先专家委员会分析 (权重最高)
            if self.expert_committee:
                try:
                    expert_result = self.expert_committee.analyze_stock_committee(
                        symbol, stock_data, 
                        market_data.get('news_data', []) if market_data else []
                    )
                    results['expert_result'] = expert_result
                except Exception as e:
                    logger.warning(f"⚠️ 专家委员会分析失败: {e}")
            
            # 2. 如果有市场数据，进行自适应分析
            if self.adaptive_engine and market_data:
                try:
                    adaptive_result = self.adaptive_engine.get_adaptive_recommendations(
                        market_data, [{'symbol': symbol, **stock_data}]
                    )
                    results['adaptive_result'] = adaptive_result
                except Exception as e:
                    logger.warning(f"⚠️ 自适应策略分析失败: {e}")
            
            # 3. 轻量级模式识别
            if self.pattern_recognizer and 'price_data' in stock_data:
                try:
                    pattern_result = self.pattern_recognizer.recognize_patterns(
                        symbol, stock_data['price_data'][-20:],  # 只分析最近20天
                        stock_data.get('volume_data', [])[-20:] if stock_data.get('volume_data') else None
                    )
                    results['pattern_result'] = pattern_result
                except Exception as e:
                    logger.warning(f"⚠️ 模式识别分析失败: {e}")
            
            return self._fuse_analysis_results(symbol, results, config)
            
        except Exception as e:
            logger.error(f"❌ AI增强分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _expert_committee_analysis(self, symbol: str, 
                                 stock_data: Dict[str, Any],
                                 market_data: Dict[str, Any] = None) -> AIAnalysisResult:
        """专家委员会分析模式"""
        try:
            if not self.expert_committee:
                logger.warning(f"⚠️ [专家委员会] 股票 {symbol} - 专家委员会未初始化")
                return self._create_error_result(symbol, "专家委员会未初始化")
            
            logger.info(f"👥 [专家委员会] 股票 {symbol} - 开始专家委员会分析")
            logger.info(f"🔍 [专家委员会] 股票 {symbol} - 启动6名AI专家分析师")
            
            expert_result = self.expert_committee.analyze_stock_committee(
                symbol, stock_data, 
                market_data.get('news_data', []) if market_data else []
            )
            
            # 转换为标准格式
            committee_decision = expert_result.get('committee_decision', {})
            
            # 显示专家委员会决策过程
            logger.info(f"📊 [专家委员会] 股票 {symbol} - 专家委员会决策完成")
            logger.info(f"🎯 [专家委员会] 股票 {symbol} - 委员会综合评分: {committee_decision.get('score', 50):.1f}")
            logger.info(f"💡 [专家委员会] 股票 {symbol} - 投资建议: {committee_decision.get('recommendation', '观望')}")
            logger.info(f"🤝 [专家委员会] 股票 {symbol} - 专家一致性: {committee_decision.get('consensus_level', '未知')}")
            logger.info(f"📊 [专家委员会] 股票 {symbol} - 置信度: {committee_decision.get('confidence', 0.5):.2f}")
            
            # 显示各专家意见
            expert_opinions = expert_result.get('expert_opinions', {})
            if expert_opinions:
                logger.info(f"👨‍💼 [专家意见] 股票 {symbol} - 各专家评分:")
                for expert_name, opinion in expert_opinions.items():
                    score = opinion.get('score', 0)
                    recommendation = opinion.get('recommendation', '观望')
                    confidence = opinion.get('confidence', 0)
                    logger.info(f"   • {expert_name}: {score:.1f}分 ({recommendation}, 置信度: {confidence:.2f})")
            
            # 显示决策因素
            decision_factors = committee_decision.get('decision_factors', [])
            if decision_factors:
                logger.info(f"🔑 [专家委员会] 股票 {symbol} - 关键决策因素: {' | '.join(decision_factors[:3])}")
            
            # 显示风险因素
            risk_factors = expert_result.get('final_recommendation', {}).get('risk_factors', [])
            if risk_factors:
                logger.info(f"⚠️ [专家委员会] 股票 {symbol} - 风险因素: {' | '.join(risk_factors[:2])}")
            
            # 显示机会因素
            opportunity_factors = expert_result.get('final_recommendation', {}).get('key_reasons', [])
            if opportunity_factors:
                logger.info(f"🌟 [专家委员会] 股票 {symbol} - 机会因素: {' | '.join(opportunity_factors[:2])}")
            
            result = AIAnalysisResult(
                symbol=symbol,
                overall_score=committee_decision.get('score', 50),
                confidence_level=committee_decision.get('confidence', 0.5),
                recommendation=committee_decision.get('recommendation', '观望'),
                risk_assessment=self._assess_risk_from_expert_analysis(expert_result),
                expert_committee_score=committee_decision.get('score', 50),
                expert_analysis=expert_result,
                key_factors=committee_decision.get('decision_factors', [])[:3],
                risk_factors=[f"专家一致性: {committee_decision.get('consensus_level', '未知')}"],
                opportunity_factors=expert_result.get('final_recommendation', {}).get('key_reasons', [])[:2]
            )
            
            logger.info(f"✅ [专家委员会] 股票 {symbol} - 专家委员会分析完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 专家委员会分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _adaptive_analysis(self, symbol: str, 
                         stock_data: Dict[str, Any],
                         market_data: Dict[str, Any] = None) -> AIAnalysisResult:
        """自适应策略分析模式"""
        try:
            if not self.adaptive_engine or not market_data:
                return self._create_error_result(symbol, "自适应引擎未初始化或缺少市场数据")
            
            adaptive_result = self.adaptive_engine.get_adaptive_recommendations(
                market_data, [{'symbol': symbol, **stock_data}]
            )
            
            # 从推荐结果中提取信息
            recommended_stocks = adaptive_result.get('recommended_stocks', [])
            target_stock = next((s for s in recommended_stocks if s.get('symbol') == symbol), {})
            
            if not target_stock:
                return self._create_error_result(symbol, "未在自适应推荐中找到目标股票")
            
            adaptive_score = target_stock.get('adaptive_score', 50)
            
            return AIAnalysisResult(
                symbol=symbol,
                overall_score=adaptive_score,
                confidence_level=adaptive_result.get('selected_strategy', {}).get('confidence', 0.6),
                recommendation=self._convert_score_to_recommendation(adaptive_score),
                risk_assessment=adaptive_result.get('risk_assessment', {}).get('overall_risk', '中等风险'),
                adaptive_strategy_score=adaptive_score,
                market_regime=adaptive_result.get('market_regime', '未知'),
                key_factors=[
                    f"市场环境: {adaptive_result.get('market_regime', '未知')}",
                    f"策略类型: {adaptive_result.get('selected_strategy', {}).get('type', '未知')}"
                ],
                risk_factors=[adaptive_result.get('risk_assessment', {}).get('overall_risk', '中等风险')],
                opportunity_factors=[adaptive_result.get('strategy_reasoning', '').split('\n')[0][:50] + '...']
            )
            
        except Exception as e:
            logger.error(f"❌ 自适应策略分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _pattern_based_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> AIAnalysisResult:
        """基于模式识别的分析"""
        try:
            if not self.pattern_recognizer or 'price_data' not in stock_data:
                return self._create_error_result(symbol, "模式识别器未初始化或缺少价格数据")
            
            patterns = self.pattern_recognizer.recognize_patterns(
                symbol, stock_data['price_data'],
                stock_data.get('volume_data', [])
            )
            
            if not patterns:
                return AIAnalysisResult(
                    symbol=symbol,
                    overall_score=50,
                    confidence_level=0.3,
                    recommendation='观望',
                    risk_assessment='数据不足',
                    pattern_recognition_score=50,
                    detected_patterns=['无明显模式'],
                    key_factors=['未检测到明显模式'],
                    risk_factors=['模式不明确'],
                    opportunity_factors=['需要更多数据']
                )
            
            # 计算模式综合评分
            pattern_score = self._calculate_pattern_score(patterns)
            
            # 获取最强模式
            strongest_pattern = max(patterns, key=lambda p: p.confidence * p.strength / 100)
            
            return AIAnalysisResult(
                symbol=symbol,
                overall_score=pattern_score,
                confidence_level=strongest_pattern.confidence,
                recommendation=strongest_pattern.expected_direction,
                risk_assessment=strongest_pattern.risk_level,
                pattern_recognition_score=pattern_score,
                detected_patterns=[p.description for p in patterns[:3]],
                key_factors=[f"主要模式: {strongest_pattern.pattern_type.value}"],
                risk_factors=[f"风险级别: {strongest_pattern.risk_level}"],
                opportunity_factors=[strongest_pattern.description]
            )
            
        except Exception as e:
            logger.error(f"❌ 模式识别分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _similarity_based_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> AIAnalysisResult:
        """基于相似性的分析"""
        try:
            if not self.similarity_engine:
                return self._create_error_result(symbol, "相似性引擎未初始化")
            
            # 简化的相似性分析 (需要候选股票列表才能完整运行)
            # 这里返回基于股票数据的基础评分
            
            basic_score = self._calculate_basic_similarity_score(stock_data)
            
            return AIAnalysisResult(
                symbol=symbol,
                overall_score=basic_score,
                confidence_level=0.6,
                recommendation=self._convert_score_to_recommendation(basic_score),
                risk_assessment='中等',
                similarity_score=basic_score,
                similar_stocks=[],  # 需要候选列表才能计算
                key_factors=['基于股票基本特征评分'],
                risk_factors=['需要更多相似股票对比'],
                opportunity_factors=['具备相似性分析潜力']
            )
            
        except Exception as e:
            logger.error(f"❌ 相似性分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _basic_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> AIAnalysisResult:
        """基础分析模式"""
        try:
            # 基于股票数据的简单评分
            basic_score = self._calculate_basic_score(stock_data)
            
            return AIAnalysisResult(
                symbol=symbol,
                overall_score=basic_score,
                confidence_level=0.4,
                recommendation=self._convert_score_to_recommendation(basic_score),
                risk_assessment='未评估',
                key_factors=['基于基础数据计算'],
                risk_factors=['未进行深度风险分析'],
                opportunity_factors=['基础评分结果']
            )
            
        except Exception as e:
            logger.error(f"❌ 基础分析失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _fuse_analysis_results(self, symbol: str, 
                             results: Dict[str, Any],
                             config: AISelectionConfig = None) -> AIAnalysisResult:
        """融合多个AI引擎的分析结果"""
        try:
            config = config or AISelectionConfig()
            
            # 初始化融合结果
            fused_result = AIAnalysisResult(
                symbol=symbol,
                overall_score=0.0,
                confidence_level=0.0,
                recommendation='观望',
                risk_assessment='未评估',
                key_factors=[],
                risk_factors=[],
                opportunity_factors=[]
            )
            
            total_weight = 0.0
            total_score = 0.0
            confidence_scores = []
            
            # 融合专家委员会结果
            if 'expert_result' in results and results['expert_result']:
                expert_result = results['expert_result']
                committee_decision = expert_result.get('committee_decision', {})
                
                score = committee_decision.get('score', 50)
                confidence = committee_decision.get('confidence', 0.5)
                weight = config.expert_committee_weight
                
                total_score += score * weight
                total_weight += weight
                confidence_scores.append(confidence * weight)
                
                fused_result.expert_committee_score = score
                fused_result.expert_analysis = expert_result
                fused_result.key_factors.extend(committee_decision.get('decision_factors', [])[:2])
                
            # 融合自适应策略结果
            if 'adaptive_result' in results and results['adaptive_result']:
                adaptive_result = results['adaptive_result']
                recommended_stocks = adaptive_result.get('recommended_stocks', [])
                
                if recommended_stocks:
                    target_stock = recommended_stocks[0] if recommended_stocks else {}
                    score = target_stock.get('adaptive_score', 50)
                    confidence = adaptive_result.get('selected_strategy', {}).get('confidence', 0.6)
                    weight = config.adaptive_strategy_weight
                    
                    total_score += score * weight
                    total_weight += weight
                    confidence_scores.append(confidence * weight)
                    
                    fused_result.adaptive_strategy_score = score
                    fused_result.market_regime = adaptive_result.get('market_regime', '未知')
                    fused_result.key_factors.append(f"市场环境: {adaptive_result.get('market_regime', '未知')}")
                    
            # 融合模式识别结果
            if 'pattern_result' in results and results['pattern_result']:
                patterns = results['pattern_result']
                if patterns:
                    pattern_score = self._calculate_pattern_score(patterns)
                    strongest_pattern = max(patterns, key=lambda p: p.confidence * p.strength / 100)
                    weight = config.pattern_recognition_weight
                    
                    total_score += pattern_score * weight
                    total_weight += weight
                    confidence_scores.append(strongest_pattern.confidence * weight)
                    
                    fused_result.pattern_recognition_score = pattern_score
                    fused_result.detected_patterns = [p.pattern_type.value for p in patterns[:3]]
                    fused_result.key_factors.append(f"主要模式: {strongest_pattern.pattern_type.value}")
                    fused_result.risk_factors.append(f"模式风险: {strongest_pattern.risk_level}")
                    
            # 计算综合评分和置信度
            if total_weight > 0:
                fused_result.overall_score = round(total_score / total_weight, 1)
                fused_result.confidence_level = round(sum(confidence_scores) / total_weight, 3)
            else:
                fused_result.overall_score = 50.0
                fused_result.confidence_level = 0.3
                
            # 生成综合建议
            fused_result.recommendation = self._generate_fused_recommendation(fused_result, results)
            fused_result.risk_assessment = self._generate_fused_risk_assessment(fused_result, results)
            
            # 清理和优化关键因素
            fused_result.key_factors = list(set(fused_result.key_factors))[:5]
            fused_result.risk_factors = list(set(fused_result.risk_factors))[:3]
            fused_result.opportunity_factors = list(set(fused_result.opportunity_factors))[:3]
            
            return fused_result
            
        except Exception as e:
            logger.error(f"❌ 结果融合失败: {symbol} - {e}")
            return self._create_error_result(symbol, str(e))
    
    def _generate_fused_recommendation(self, fused_result: AIAnalysisResult, 
                                     results: Dict[str, Any]) -> str:
        """生成融合建议"""
        try:
            score = fused_result.overall_score
            confidence = fused_result.confidence_level
            
            # 基于评分和置信度生成建议
            if score >= 80 and confidence >= 0.7:
                return "强烈推荐"
            elif score >= 70 and confidence >= 0.6:
                return "推荐"
            elif score >= 60 and confidence >= 0.5:
                return "谨慎推荐"
            elif score >= 50:
                return "观望"
            elif score >= 40:
                return "谨慎"
            else:
                return "不推荐"
                
        except Exception:
            return "观望"
    
    def _generate_fused_risk_assessment(self, fused_result: AIAnalysisResult,
                                      results: Dict[str, Any]) -> str:
        """生成融合风险评估"""
        try:
            # 综合各引擎的风险评估
            risk_indicators = []
            
            if fused_result.confidence_level < 0.5:
                risk_indicators.append("置信度较低")
            
            if fused_result.overall_score < 60:
                risk_indicators.append("评分偏低")
            
            if len(fused_result.risk_factors) > 2:
                risk_indicators.append("风险因素较多")
            
            # 根据风险指标数量判断整体风险
            risk_count = len(risk_indicators)
            if risk_count >= 3:
                return "高风险"
            elif risk_count == 2:
                return "中高风险"
            elif risk_count == 1:
                return "中等风险"
            else:
                return "低风险"
                
        except Exception:
            return "风险未评估"
    
    def _calculate_pattern_score(self, patterns: List[Any]) -> float:
        """计算模式综合评分"""
        try:
            if not patterns:
                return 50.0
                
            total_score = 0.0
            total_weight = 0.0
            
            for pattern in patterns:
                # 模式评分 = 置信度 * 强度
                pattern_score = pattern.confidence * pattern.strength / 100 * 100
                weight = pattern.confidence
                
                total_score += pattern_score * weight
                total_weight += weight
                
            return round(total_score / total_weight if total_weight > 0 else 50.0, 1)
            
        except Exception:
            return 50.0
    
    def _calculate_basic_score(self, stock_data: Dict[str, Any]) -> float:
        """计算基础评分"""
        try:
            score = 50.0  # 基础分
            
            # 价格变动
            price_change = stock_data.get('price_change_pct', 0)
            if price_change > 0:
                score += min(10, price_change * 2)
            else:
                score += max(-10, price_change * 2)
                
            # 市盈率
            pe_ratio = stock_data.get('pe_ratio', 20)
            if 10 <= pe_ratio <= 25:
                score += 5
            elif pe_ratio > 50:
                score -= 10
                
            # 市净率  
            pb_ratio = stock_data.get('pb_ratio', 2)
            if 1 <= pb_ratio <= 3:
                score += 5
            elif pb_ratio > 5:
                score -= 5
                
            return max(0, min(100, score))
            
        except Exception:
            return 50.0
            
    def _calculate_basic_similarity_score(self, stock_data: Dict[str, Any]) -> float:
        """计算基础相似性评分"""
        try:
            # 基于股票基本特征的评分
            score = 50.0
            
            # 基本面指标权重评分
            fundamentals = [
                ('roe', 0.15, 15),  # ROE 15%权重
                ('pe_ratio', -0.002, 20),  # PE适中加分
                ('revenue_growth', 0.3, 15),  # 营收增长
                ('market_cap', 0.00000001, 1000000000)  # 市值规模
            ]
            
            for key, weight, baseline in fundamentals:
                value = stock_data.get(key, baseline)
                if key == 'pe_ratio':
                    # PE适中为好
                    score += max(-10, min(10, (25 - abs(value - 15)) * weight))
                else:
                    score += min(10, max(-10, (value - baseline) * weight))
            
            return max(0, min(100, score))
            
        except Exception:
            return 50.0
    
    def _convert_score_to_recommendation(self, score: float) -> str:
        """将评分转换为投资建议"""
        if score >= 85:
            return "强烈推荐"
        elif score >= 75:
            return "推荐"  
        elif score >= 65:
            return "谨慎推荐"
        elif score >= 55:
            return "观望"
        elif score >= 45:
            return "谨慎"
        else:
            return "不推荐"
    
    def _assess_risk_from_expert_analysis(self, expert_result: Dict[str, Any]) -> str:
        """从专家分析中评估风险"""
        try:
            final_recommendation = expert_result.get('final_recommendation', {})
            risk_assessment = final_recommendation.get('risk_assessment', '中等风险')
            
            # 基于专家一致性调整风险评估
            consensus_level = expert_result.get('committee_decision', {}).get('consensus_level', '基本一致')
            
            if consensus_level == '意见分化':
                return '高风险'
            elif consensus_level == '存在分歧':
                return '中高风险'
            else:
                return risk_assessment
                
        except Exception:
            return '风险未评估'
    
    def _get_cached_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> Optional[AIAnalysisResult]:
        """获取缓存的分析结果"""
        try:
            cache_key = f"{symbol}_{hash(str(sorted(stock_data.items())))}"
            
            if cache_key in self.analysis_cache:
                cached_item = self.analysis_cache[cache_key]
                
                # 检查缓存是否过期
                if (datetime.now() - cached_item['timestamp']).total_seconds() < self.cache_ttl:
                    return cached_item['result']
                else:
                    # 删除过期缓存
                    del self.analysis_cache[cache_key]
            
            return None
            
        except Exception:
            return None
    
    def _cache_analysis(self, symbol: str, stock_data: Dict[str, Any], result: AIAnalysisResult):
        """缓存分析结果"""
        try:
            cache_key = f"{symbol}_{hash(str(sorted(stock_data.items())))}"
            
            self.analysis_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
            # 限制缓存大小
            if len(self.analysis_cache) > 1000:
                # 删除最旧的缓存项
                oldest_key = min(self.analysis_cache.keys(), 
                               key=lambda k: self.analysis_cache[k]['timestamp'])
                del self.analysis_cache[oldest_key]
                
        except Exception as e:
            logger.debug(f"缓存失败: {e}")
    
    def _update_performance_stats(self, processing_time: float):
        """更新性能统计"""
        try:
            self.performance_stats['total_analyses'] += 1
            
            # 更新平均处理时间
            total_time = (self.performance_stats['average_processing_time'] * 
                         (self.performance_stats['total_analyses'] - 1) + processing_time)
            self.performance_stats['average_processing_time'] = total_time / self.performance_stats['total_analyses']
            
        except Exception:
            pass
    
    def _create_error_result(self, symbol: str, error_msg: str, start_time: datetime = None) -> AIAnalysisResult:
        """创建错误结果"""
        processing_time = (datetime.now() - start_time).total_seconds() if start_time else 0.0
        
        return AIAnalysisResult(
            symbol=symbol,
            overall_score=30.0,  # 错误情况下给较低评分
            confidence_level=0.1,
            recommendation='数据不足',
            risk_assessment='分析失败',
            key_factors=[f'分析错误: {error_msg}'],
            risk_factors=['AI分析失败'],
            opportunity_factors=[],
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    
    def batch_analyze_stocks(self, stock_list: List[Dict[str, Any]], 
                           market_data: Dict[str, Any] = None,
                           config: AISelectionConfig = None) -> List[AIAnalysisResult]:
        """批量AI分析股票"""
        try:
            logger.info(f"🤖 [AI策略管理器] 开始批量AI分析，股票数量: {len(stock_list)}")
            logger.info(f"🔍 [批量分析] 开始对 {len(stock_list)} 只股票进行AI智能分析")
            logger.info(f"📊 [批量分析] 分析模式: {config.ai_mode.value if config else 'AI增强'}")
            
            results = []
            config = config or AISelectionConfig()
            
            # 显示批量分析进度
            total_stocks = len(stock_list)
            processed_count = 0
            successful_count = 0
            failed_count = 0
            
            # 根据配置决定是否并行处理
            if config.parallel_processing and len(stock_list) > 1:
                logger.info(f"⚡ [批量分析] 使用并行处理模式，并发数: {min(4, total_stocks)}")
                
                # 并行处理
                future_tasks = []
                
                for stock_info in stock_list:
                    symbol = stock_info.get('symbol', stock_info.get('ts_code', ''))
                    if symbol:
                        future_task = self.thread_pool.submit(
                            self.analyze_stock_with_ai,
                            symbol, stock_info, market_data, config
                        )
                        future_tasks.append((symbol, future_task))
                
                # 收集结果
                for symbol, future_task in future_tasks:
                    try:
                        processed_count += 1
                        result = future_task.result(timeout=config.timeout_seconds)
                        results.append(result)
                        successful_count += 1
                        
                        # 显示进度
                        if processed_count % 5 == 0 or processed_count == total_stocks:
                            logger.info(f"📊 [批量进度] 已处理 {processed_count}/{total_stocks} 只股票 (成功: {successful_count}, 失败: {failed_count})")
                        
                    except Exception as e:
                        processed_count += 1
                        failed_count += 1
                        logger.warning(f"⚠️ 批量分析失败: {symbol} - {e}")
                        results.append(self._create_error_result(symbol, str(e)))
                        
                        # 显示进度
                        if processed_count % 5 == 0 or processed_count == total_stocks:
                            logger.info(f"📊 [批量进度] 已处理 {processed_count}/{total_stocks} 只股票 (成功: {successful_count}, 失败: {failed_count})")
                        
            else:
                logger.info(f"🔄 [批量分析] 使用顺序处理模式")
                
                # 顺序处理
                for stock_info in stock_list:
                    symbol = stock_info.get('symbol', stock_info.get('ts_code', ''))
                    if symbol:
                        try:
                            processed_count += 1
                            result = self.analyze_stock_with_ai(symbol, stock_info, market_data, config)
                            results.append(result)
                            successful_count += 1
                            
                            # 显示进度
                            if processed_count % 5 == 0 or processed_count == total_stocks:
                                logger.info(f"📊 [批量进度] 已处理 {processed_count}/{total_stocks} 只股票 (成功: {successful_count}, 失败: {failed_count})")
                            
                        except Exception as e:
                            processed_count += 1
                            failed_count += 1
                            logger.warning(f"⚠️ 分析失败: {symbol} - {e}")
                            results.append(self._create_error_result(symbol, str(e)))
                            
                            # 显示进度
                            if processed_count % 5 == 0 or processed_count == total_stocks:
                                logger.info(f"📊 [批量进度] 已处理 {processed_count}/{total_stocks} 只股票 (成功: {successful_count}, 失败: {failed_count})")
            
            # 显示批量分析结果统计
            logger.info(f"🎉 [批量分析] 批量AI分析完成")
            logger.info(f"📊 [批量统计] 总股票数: {total_stocks}")
            logger.info(f"✅ [批量统计] 成功分析: {successful_count}")
            logger.info(f"❌ [批量统计] 分析失败: {failed_count}")
            logger.info(f"📈 [批量统计] 成功率: {successful_count/total_stocks*100:.1f}%")
            
            # 显示AI评分统计
            if results:
                ai_scores = [r.overall_score for r in results if r.overall_score > 0]
                if ai_scores:
                    avg_score = sum(ai_scores) / len(ai_scores)
                    max_score = max(ai_scores)
                    min_score = min(ai_scores)
                    logger.info(f"🎯 [批量统计] AI评分统计 - 平均: {avg_score:.1f}, 最高: {max_score:.1f}, 最低: {min_score:.1f}")
                    
                    # 评分分布
                    high_score_count = len([s for s in ai_scores if s >= 80])
                    medium_score_count = len([s for s in ai_scores if 60 <= s < 80])
                    low_score_count = len([s for s in ai_scores if s < 60])
                    logger.info(f"📊 [批量统计] 评分分布 - 优秀(≥80): {high_score_count}, 良好(60-79): {medium_score_count}, 一般(<60): {low_score_count}")
            
            logger.info(f"🤖 [AI策略管理器] 批量AI分析完成，成功分析: {len(results)} 只股票")
            return results
            
        except Exception as e:
            logger.error(f"❌ [AI策略管理器] 批量分析失败: {e}")
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取AI引擎性能摘要"""
        try:
            ai_engines_status = {
                'expert_committee': self.expert_committee is not None,
                'adaptive_engine': self.adaptive_engine is not None,
                'pattern_recognizer': self.pattern_recognizer is not None,
                'similarity_engine': self.similarity_engine is not None
            }
            
            # 计算可用引擎数量
            available_engines = sum(ai_engines_status.values())
            total_engines = len(ai_engines_status)
            availability_rate = (available_engines / total_engines * 100) if total_engines > 0 else 0
            
            return {
                'total_analyses': self.performance_stats['total_analyses'],
                'cache_hit_rate': (self.performance_stats['cache_hits'] / 
                                 max(1, self.performance_stats['total_analyses']) * 100),
                'average_processing_time': self.performance_stats['average_processing_time'],
                'cache_size': len(self.analysis_cache),
                'ai_engines_status': ai_engines_status,
                'engine_availability': {
                    'available_count': available_engines,
                    'total_count': total_engines,
                    'availability_rate': availability_rate
                },
                'engine_initialization': self.performance_stats.get('engine_initialization', {}),
                'ai_enabled': available_engines > 0,
                'fully_operational': available_engines == total_engines,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 性能摘要获取失败: {e}")
            return {
                'error': str(e),
                'ai_enabled': False,
                'ai_engines_status': {
                    'expert_committee': False,
                    'adaptive_engine': False,
                    'pattern_recognizer': False,
                    'similarity_engine': False
                }
            }
    
    def clear_cache(self):
        """清理分析缓存"""
        try:
            self.analysis_cache.clear()
            logger.info("🧹 AI分析缓存已清理")
        except Exception as e:
            logger.error(f"❌ 缓存清理失败: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
        except Exception:
            pass


# 全局AI策略管理器实例
_ai_strategy_manager = None

def get_ai_strategy_manager(config: Dict[str, Any] = None) -> AIStrategyManager:
    """获取全局AI策略管理器实例"""
    global _ai_strategy_manager
    if _ai_strategy_manager is None:
        _ai_strategy_manager = AIStrategyManager(config)
    return _ai_strategy_manager