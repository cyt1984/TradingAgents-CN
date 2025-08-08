#!/usr/bin/env python3
"""
自适应选股引擎
基于市场环境和历史表现动态调整选股策略
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
import math
from collections import defaultdict

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class MarketRegime(Enum):
    """市场环境类型"""
    BULL_MARKET = "bull_market"           # 牛市
    BEAR_MARKET = "bear_market"           # 熊市
    SIDEWAYS_MARKET = "sideways_market"   # 震荡市
    VOLATILE_MARKET = "volatile_market"   # 高波动市场
    RECOVERY_MARKET = "recovery_market"   # 复苏市场


class StrategyType(Enum):
    """策略类型"""
    GROWTH_FOCUSED = "growth_focused"         # 成长导向
    VALUE_FOCUSED = "value_focused"           # 价值导向
    MOMENTUM_FOCUSED = "momentum_focused"     # 动量导向
    QUALITY_FOCUSED = "quality_focused"       # 质量导向
    DEFENSIVE = "defensive"                   # 防御性
    AGGRESSIVE = "aggressive"                 # 进攻性
    BALANCED = "balanced"                     # 平衡型


@dataclass
class AdaptiveStrategy:
    """自适应策略"""
    strategy_type: StrategyType             # 策略类型
    market_regime: MarketRegime             # 适用市场环境
    weight_adjustments: Dict[str, float]    # 权重调整
    filter_adjustments: Dict[str, float]    # 筛选条件调整
    confidence_threshold: float             # 置信度阈值
    risk_tolerance: float                   # 风险承受度
    expected_performance: float             # 预期表现
    historical_accuracy: float              # 历史准确率
    last_updated: datetime                  # 最后更新时间
    performance_metrics: Dict[str, float]   # 表现指标


class AdaptiveEngine:
    """自适应选股引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化自适应引擎
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 市场环境检测参数
        self.market_detection_params = {
            'trend_window': 20,              # 趋势检测窗口
            'volatility_window': 15,         # 波动率计算窗口
            'volume_window': 10,             # 成交量分析窗口
            'bull_threshold': 0.05,          # 牛市阈值 (5%涨幅)
            'bear_threshold': -0.05,         # 熊市阈值 (5%跌幅)
            'volatility_threshold': 0.15     # 高波动阈值 (15%)
        }
        
        # 策略配置库
        self.strategy_library = self._initialize_strategy_library()
        
        # 历史表现记录
        self.performance_history = {}
        
        # 当前市场环境
        self.current_market_regime = None
        self.current_strategy = None
        
        # 自适应学习参数
        self.learning_params = {
            'adaptation_rate': 0.1,          # 学习速率
            'performance_memory': 50,        # 表现记忆长度
            'strategy_switch_threshold': 0.15 # 策略切换阈值
        }
        
        logger.info("自适应选股引擎初始化完成")
        logger.info(f"   策略类型: {len(StrategyType)} 种")
        logger.info(f"   市场环境: {len(MarketRegime)} 种")
        logger.info(f"   策略配置: {len(self.strategy_library)} 个")

    def _initialize_strategy_library(self) -> Dict[Tuple[MarketRegime, StrategyType], AdaptiveStrategy]:
        """初始化策略配置库"""
        strategies = {}
        
        # 牛市策略
        strategies[(MarketRegime.BULL_MARKET, StrategyType.GROWTH_FOCUSED)] = AdaptiveStrategy(
            strategy_type=StrategyType.GROWTH_FOCUSED,
            market_regime=MarketRegime.BULL_MARKET,
            weight_adjustments={
                'technical_score': 1.2,      # 增加技术面权重
                'momentum_score': 1.3,       # 增加动量权重
                'growth_metrics': 1.4        # 增加成长性权重
            },
            filter_adjustments={
                'min_score': 65.0,           # 降低最低评分要求
                'max_risk_level': 0.8,       # 提高风险容忍度
                'min_volume_ratio': 1.2      # 要求较高流动性
            },
            confidence_threshold=0.6,
            risk_tolerance=0.8,
            expected_performance=0.15,       # 预期15%收益
            historical_accuracy=0.72,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        strategies[(MarketRegime.BULL_MARKET, StrategyType.MOMENTUM_FOCUSED)] = AdaptiveStrategy(
            strategy_type=StrategyType.MOMENTUM_FOCUSED,
            market_regime=MarketRegime.BULL_MARKET,
            weight_adjustments={
                'technical_score': 1.4,
                'momentum_score': 1.5,
                'volume_score': 1.3
            },
            filter_adjustments={
                'min_score': 60.0,
                'min_momentum': 0.05,        # 要求5%以上动量
                'min_volume_spike': 1.5      # 要求成交量放大
            },
            confidence_threshold=0.65,
            risk_tolerance=0.9,
            expected_performance=0.20,
            historical_accuracy=0.68,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        # 熊市策略
        strategies[(MarketRegime.BEAR_MARKET, StrategyType.DEFENSIVE)] = AdaptiveStrategy(
            strategy_type=StrategyType.DEFENSIVE,
            market_regime=MarketRegime.BEAR_MARKET,
            weight_adjustments={
                'quality_score': 1.4,        # 增加质量权重
                'fundamental_score': 1.3,    # 增加基本面权重
                'risk_score': 1.5            # 增加风险评估权重
            },
            filter_adjustments={
                'min_score': 70.0,           # 提高最低评分要求
                'max_risk_level': 0.4,       # 降低风险容忍度
                'min_dividend_yield': 0.02   # 要求2%以上股息
            },
            confidence_threshold=0.75,
            risk_tolerance=0.3,
            expected_performance=-0.05,      # 预期小幅下跌但跑赢大盘
            historical_accuracy=0.75,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        strategies[(MarketRegime.BEAR_MARKET, StrategyType.VALUE_FOCUSED)] = AdaptiveStrategy(
            strategy_type=StrategyType.VALUE_FOCUSED,
            market_regime=MarketRegime.BEAR_MARKET,
            weight_adjustments={
                'fundamental_score': 1.5,
                'value_metrics': 1.4,
                'quality_score': 1.2
            },
            filter_adjustments={
                'min_score': 75.0,
                'max_pe_ratio': 15.0,        # PE限制在15以下
                'max_pb_ratio': 2.0,         # PB限制在2以下
                'min_roe': 0.10              # ROE不低于10%
            },
            confidence_threshold=0.8,
            risk_tolerance=0.4,
            expected_performance=0.05,       # 预期小幅上涨
            historical_accuracy=0.78,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        # 震荡市策略
        strategies[(MarketRegime.SIDEWAYS_MARKET, StrategyType.BALANCED)] = AdaptiveStrategy(
            strategy_type=StrategyType.BALANCED,
            market_regime=MarketRegime.SIDEWAYS_MARKET,
            weight_adjustments={
                'technical_score': 1.0,      # 均衡权重
                'fundamental_score': 1.0,
                'sentiment_score': 1.1,      # 略微增加情绪权重
                'quality_score': 1.1
            },
            filter_adjustments={
                'min_score': 65.0,
                'max_risk_level': 0.6,
                'min_trading_frequency': 0.8  # 要求较活跃的交易
            },
            confidence_threshold=0.7,
            risk_tolerance=0.6,
            expected_performance=0.08,
            historical_accuracy=0.70,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        # 高波动市场策略
        strategies[(MarketRegime.VOLATILE_MARKET, StrategyType.QUALITY_FOCUSED)] = AdaptiveStrategy(
            strategy_type=StrategyType.QUALITY_FOCUSED,
            market_regime=MarketRegime.VOLATILE_MARKET,
            weight_adjustments={
                'quality_score': 1.5,
                'stability_metrics': 1.4,
                'risk_score': 1.3
            },
            filter_adjustments={
                'min_score': 75.0,
                'max_volatility': 0.25,      # 限制波动率在25%以下
                'min_market_cap': 1000000000, # 要求10亿以上市值
                'min_liquidity': 0.8         # 要求高流动性
            },
            confidence_threshold=0.8,
            risk_tolerance=0.4,
            expected_performance=0.06,
            historical_accuracy=0.73,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        # 复苏市场策略
        strategies[(MarketRegime.RECOVERY_MARKET, StrategyType.AGGRESSIVE)] = AdaptiveStrategy(
            strategy_type=StrategyType.AGGRESSIVE,
            market_regime=MarketRegime.RECOVERY_MARKET,
            weight_adjustments={
                'growth_metrics': 1.4,
                'momentum_score': 1.3,
                'recovery_indicators': 1.5
            },
            filter_adjustments={
                'min_score': 60.0,
                'max_risk_level': 0.85,
                'min_growth_rate': 0.15,     # 要求15%以上增长
                'min_recovery_score': 70.0   # 复苏评分不低于70
            },
            confidence_threshold=0.65,
            risk_tolerance=0.85,
            expected_performance=0.25,
            historical_accuracy=0.69,
            last_updated=datetime.now(),
            performance_metrics={}
        )
        
        return strategies

    def detect_market_regime(self, market_data: Dict[str, Any]) -> MarketRegime:
        """
        检测当前市场环境
        
        Args:
            market_data: 市场数据 (包含指数价格、成交量等)
            
        Returns:
            检测到的市场环境
        """
        try:
            logger.info("🌡️ [自适应引擎] 开始检测市场环境")
            
            if not market_data or 'price_data' not in market_data:
                logger.warning("⚠️ 市场数据不足，使用默认环境")
                return MarketRegime.SIDEWAYS_MARKET
            
            price_data = market_data['price_data']
            if len(price_data) < self.market_detection_params['trend_window']:
                return MarketRegime.SIDEWAYS_MARKET
            
            # 提取价格序列
            closes = [float(p.get('close', 0)) for p in price_data]
            volumes = [float(p.get('volume', 0)) for p in price_data if p.get('volume')]
            
            # 1. 趋势分析
            trend_window = self.market_detection_params['trend_window']
            recent_trend = (closes[-1] - closes[-trend_window]) / closes[-trend_window]
            
            # 2. 波动率分析
            volatility_window = self.market_detection_params['volatility_window']
            returns = [(closes[i] - closes[i-1]) / closes[i-1] 
                      for i in range(1, min(len(closes), volatility_window + 1))]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # 3. 成交量分析
            volume_trend = 0
            if len(volumes) >= self.market_detection_params['volume_window']:
                volume_window = self.market_detection_params['volume_window']
                recent_volume = statistics.mean(volumes[-volume_window//2:])
                historic_volume = statistics.mean(volumes[-volume_window:-volume_window//2])
                volume_trend = (recent_volume - historic_volume) / historic_volume if historic_volume > 0 else 0
            
            # 4. 市场环境判断
            bull_threshold = self.market_detection_params['bull_threshold']
            bear_threshold = self.market_detection_params['bear_threshold']
            volatility_threshold = self.market_detection_params['volatility_threshold']
            
            # 高波动环境
            if volatility > volatility_threshold:
                detected_regime = MarketRegime.VOLATILE_MARKET
            # 牛市环境
            elif recent_trend > bull_threshold and volume_trend > 0.1:
                detected_regime = MarketRegime.BULL_MARKET
            # 熊市环境
            elif recent_trend < bear_threshold and volume_trend < -0.1:
                detected_regime = MarketRegime.BEAR_MARKET
            # 复苏环境 (从低点反弹)
            elif recent_trend > 0.02 and closes[-1] < max(closes[-trend_window:]) * 0.9:
                detected_regime = MarketRegime.RECOVERY_MARKET
            # 震荡环境
            else:
                detected_regime = MarketRegime.SIDEWAYS_MARKET
            
            self.current_market_regime = detected_regime
            
            logger.info(f"🌡️ [自适应引擎] 市场环境检测完成: {detected_regime.value}")
            logger.info(f"   趋势: {recent_trend:.2%}, 波动率: {volatility:.2%}, 成交量趋势: {volume_trend:.2%}")
            
            return detected_regime
            
        except Exception as e:
            logger.error(f"❌ 市场环境检测失败: {e}")
            return MarketRegime.SIDEWAYS_MARKET

    def select_optimal_strategy(self, market_regime: MarketRegime, 
                              historical_performance: Dict[str, float] = None) -> AdaptiveStrategy:
        """
        选择最优策略
        
        Args:
            market_regime: 市场环境
            historical_performance: 历史表现数据
            
        Returns:
            最优自适应策略
        """
        try:
            logger.info(f"🎯 [自适应引擎] 为 {market_regime.value} 环境选择最优策略")
            
            # 获取适用于当前市场环境的策略
            applicable_strategies = [
                strategy for (regime, strategy_type), strategy in self.strategy_library.items()
                if regime == market_regime
            ]
            
            if not applicable_strategies:
                logger.warning(f"⚠️ 未找到适用于 {market_regime.value} 的策略，使用平衡策略")
                return self._get_default_strategy(market_regime)
            
            # 基于历史表现选择最优策略
            best_strategy = None
            best_score = -float('inf')
            
            for strategy in applicable_strategies:
                # 计算策略评分
                performance_score = strategy.historical_accuracy
                expected_return_score = max(0, strategy.expected_performance) * 2
                confidence_score = (1.0 - strategy.confidence_threshold) * 0.5
                
                # 如果有历史表现数据，加入考量
                if historical_performance:
                    strategy_key = f"{market_regime.value}_{strategy.strategy_type.value}"
                    if strategy_key in historical_performance:
                        actual_performance = historical_performance[strategy_key]
                        performance_score += actual_performance * 0.3
                
                total_score = performance_score + expected_return_score + confidence_score
                
                logger.debug(f"   策略 {strategy.strategy_type.value}: 总分={total_score:.3f}")
                
                if total_score > best_score:
                    best_score = total_score
                    best_strategy = strategy
            
            if best_strategy:
                self.current_strategy = best_strategy
                logger.info(f"🎯 [自适应引擎] 选定策略: {best_strategy.strategy_type.value} (评分: {best_score:.3f})")
                return best_strategy
            else:
                return self._get_default_strategy(market_regime)
                
        except Exception as e:
            logger.error(f"❌ 策略选择失败: {e}")
            return self._get_default_strategy(market_regime)

    def _get_default_strategy(self, market_regime: MarketRegime) -> AdaptiveStrategy:
        """获取默认策略"""
        return AdaptiveStrategy(
            strategy_type=StrategyType.BALANCED,
            market_regime=market_regime,
            weight_adjustments={'all': 1.0},
            filter_adjustments={'min_score': 65.0},
            confidence_threshold=0.7,
            risk_tolerance=0.5,
            expected_performance=0.08,
            historical_accuracy=0.65,
            last_updated=datetime.now(),
            performance_metrics={}
        )

    def adapt_selection_criteria(self, base_criteria: Dict[str, Any], 
                               strategy: AdaptiveStrategy) -> Dict[str, Any]:
        """
        根据策略调整选股条件
        
        Args:
            base_criteria: 基础选股条件
            strategy: 自适应策略
            
        Returns:
            调整后的选股条件
        """
        try:
            logger.info(f"🔧 [自适应引擎] 应用策略调整: {strategy.strategy_type.value}")
            
            adapted_criteria = base_criteria.copy()
            
            # 应用权重调整
            if 'weights' in adapted_criteria:
                for weight_key, adjustment in strategy.weight_adjustments.items():
                    if weight_key in adapted_criteria['weights']:
                        adapted_criteria['weights'][weight_key] *= adjustment
                        logger.debug(f"   权重调整: {weight_key} *= {adjustment}")
            
            # 应用筛选条件调整
            for filter_key, adjustment in strategy.filter_adjustments.items():
                if filter_key in adapted_criteria:
                    if isinstance(adjustment, (int, float)):
                        adapted_criteria[filter_key] = adjustment
                        logger.debug(f"   筛选调整: {filter_key} = {adjustment}")
                    else:
                        # 对于复杂的调整逻辑，这里简化处理
                        adapted_criteria[filter_key] = adjustment
            
            # 调整置信度阈值
            adapted_criteria['confidence_threshold'] = strategy.confidence_threshold
            
            # 调整风险容忍度
            adapted_criteria['risk_tolerance'] = strategy.risk_tolerance
            
            logger.info(f"🔧 [自适应引擎] 策略调整完成，调整项目: {len(strategy.weight_adjustments + strategy.filter_adjustments)}")
            return adapted_criteria
            
        except Exception as e:
            logger.error(f"❌ 选股条件调整失败: {e}")
            return base_criteria

    def learn_from_performance(self, strategy_results: Dict[str, Any], 
                             actual_performance: float):
        """
        从表现结果中学习
        
        Args:
            strategy_results: 策略执行结果
            actual_performance: 实际表现
        """
        try:
            logger.info(f"📚 [自适应引擎] 从表现中学习: 实际收益 {actual_performance:.2%}")
            
            if not self.current_strategy or not self.current_market_regime:
                return
            
            strategy_key = f"{self.current_market_regime.value}_{self.current_strategy.strategy_type.value}"
            
            # 更新表现历史
            if strategy_key not in self.performance_history:
                self.performance_history[strategy_key] = []
            
            performance_record = {
                'timestamp': datetime.now(),
                'actual_performance': actual_performance,
                'expected_performance': self.current_strategy.expected_performance,
                'strategy_config': {
                    'weights': self.current_strategy.weight_adjustments,
                    'filters': self.current_strategy.filter_adjustments
                },
                'market_conditions': strategy_results.get('market_conditions', {})
            }
            
            self.performance_history[strategy_key].append(performance_record)
            
            # 保持最近的表现记录
            max_records = self.learning_params['performance_memory']
            if len(self.performance_history[strategy_key]) > max_records:
                self.performance_history[strategy_key] = self.performance_history[strategy_key][-max_records:]
            
            # 更新策略参数
            self._update_strategy_parameters(strategy_key, actual_performance)
            
            logger.info(f"📚 [自适应引擎] 学习完成，表现记录数: {len(self.performance_history[strategy_key])}")
            
        except Exception as e:
            logger.error(f"❌ 性能学习失败: {e}")

    def _update_strategy_parameters(self, strategy_key: str, actual_performance: float):
        """更新策略参数"""
        try:
            if strategy_key not in self.performance_history:
                return
            
            performance_records = self.performance_history[strategy_key]
            if len(performance_records) < 3:  # 需要足够的数据点
                return
            
            # 计算平均表现
            recent_performances = [r['actual_performance'] for r in performance_records[-10:]]
            avg_performance = statistics.mean(recent_performances)
            
            # 计算准确率
            accurate_predictions = sum(
                1 for r in performance_records[-10:]
                if (r['actual_performance'] > 0) == (r['expected_performance'] > 0)
            )
            current_accuracy = accurate_predictions / len(performance_records[-10:])
            
            # 找到对应的策略并更新
            for (regime, strategy_type), strategy in self.strategy_library.items():
                if f"{regime.value}_{strategy_type.value}" == strategy_key:
                    # 使用学习率更新参数
                    learning_rate = self.learning_params['adaptation_rate']
                    
                    # 更新历史准确率
                    strategy.historical_accuracy = (
                        (1 - learning_rate) * strategy.historical_accuracy + 
                        learning_rate * current_accuracy
                    )
                    
                    # 更新预期表现
                    strategy.expected_performance = (
                        (1 - learning_rate) * strategy.expected_performance + 
                        learning_rate * avg_performance
                    )
                    
                    # 更新表现指标
                    strategy.performance_metrics = {
                        'avg_performance': avg_performance,
                        'accuracy_rate': current_accuracy,
                        'prediction_count': len(recent_performances),
                        'last_performance': actual_performance
                    }
                    
                    strategy.last_updated = datetime.now()
                    
                    logger.debug(f"   策略更新: {strategy_key}")
                    logger.debug(f"   准确率: {strategy.historical_accuracy:.3f}")
                    logger.debug(f"   预期表现: {strategy.expected_performance:.3f}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ 策略参数更新失败: {e}")

    def get_adaptive_recommendations(self, market_data: Dict[str, Any], 
                                   stock_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取自适应选股推荐
        
        Args:
            market_data: 市场数据
            stock_candidates: 候选股票列表
            
        Returns:
            自适应推荐结果
        """
        try:
            logger.info(f"🤖 [自适应引擎] 开始自适应推荐，候选股票: {len(stock_candidates)}")
            
            # 1. 检测市场环境
            market_regime = self.detect_market_regime(market_data)
            
            # 2. 选择最优策略
            optimal_strategy = self.select_optimal_strategy(market_regime)
            
            # 3. 应用策略筛选
            filtered_candidates = self._apply_strategy_filtering(
                stock_candidates, optimal_strategy
            )
            
            # 4. 策略评分和排序
            scored_candidates = self._apply_strategy_scoring(
                filtered_candidates, optimal_strategy
            )
            
            # 5. 生成推荐结果
            recommendations = {
                'market_regime': market_regime.value,
                'selected_strategy': {
                    'type': optimal_strategy.strategy_type.value,
                    'confidence': optimal_strategy.confidence_threshold,
                    'risk_tolerance': optimal_strategy.risk_tolerance,
                    'expected_performance': optimal_strategy.expected_performance
                },
                'recommended_stocks': scored_candidates[:20],  # 推荐前20只
                'strategy_reasoning': self._generate_strategy_reasoning(
                    market_regime, optimal_strategy
                ),
                'risk_assessment': self._assess_portfolio_risk(scored_candidates[:20]),
                'adaptation_metrics': {
                    'total_candidates': len(stock_candidates),
                    'filtered_candidates': len(filtered_candidates),
                    'final_recommendations': len(scored_candidates[:20]),
                    'strategy_accuracy': optimal_strategy.historical_accuracy
                },
                'timestamp': datetime.now()
            }
            
            logger.info(f"🤖 [自适应引擎] 推荐完成: {len(scored_candidates[:20])} 只股票")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 自适应推荐失败: {e}")
            return {
                'error': str(e),
                'market_regime': 'unknown',
                'recommended_stocks': [],
                'timestamp': datetime.now()
            }

    def _apply_strategy_filtering(self, candidates: List[Dict[str, Any]], 
                                strategy: AdaptiveStrategy) -> List[Dict[str, Any]]:
        """应用策略筛选"""
        try:
            filtered = []
            
            for candidate in candidates:
                # 基础评分筛选
                if candidate.get('score', 0) < strategy.filter_adjustments.get('min_score', 0):
                    continue
                
                # 风险级别筛选
                risk_level = candidate.get('risk_level', 0.5)
                if risk_level > strategy.risk_tolerance:
                    continue
                
                # 策略特定筛选
                if not self._passes_strategy_specific_filters(candidate, strategy):
                    continue
                
                filtered.append(candidate)
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ 策略筛选失败: {e}")
            return candidates

    def _passes_strategy_specific_filters(self, candidate: Dict[str, Any], 
                                        strategy: AdaptiveStrategy) -> bool:
        """检查是否通过策略特定筛选"""
        try:
            # 根据策略类型应用特定筛选
            if strategy.strategy_type == StrategyType.GROWTH_FOCUSED:
                return candidate.get('growth_score', 0) >= 60
            elif strategy.strategy_type == StrategyType.VALUE_FOCUSED:
                return (candidate.get('pe_ratio', float('inf')) <= 20 and
                        candidate.get('pb_ratio', float('inf')) <= 3)
            elif strategy.strategy_type == StrategyType.MOMENTUM_FOCUSED:
                return candidate.get('momentum_score', 0) >= 65
            elif strategy.strategy_type == StrategyType.QUALITY_FOCUSED:
                return candidate.get('quality_score', 0) >= 70
            elif strategy.strategy_type == StrategyType.DEFENSIVE:
                return candidate.get('volatility', 1.0) <= 0.3
            else:
                return True  # 平衡策略或其他策略不应用额外筛选
                
        except Exception:
            return True  # 出错时默认通过

    def _apply_strategy_scoring(self, candidates: List[Dict[str, Any]], 
                              strategy: AdaptiveStrategy) -> List[Dict[str, Any]]:
        """应用策略评分"""
        try:
            for candidate in candidates:
                # 基础评分
                base_score = candidate.get('score', 50)
                
                # 应用权重调整
                adjusted_score = base_score
                
                for factor, weight in strategy.weight_adjustments.items():
                    if factor in candidate:
                        factor_score = candidate[factor]
                        adjusted_score += (factor_score - 50) * (weight - 1) * 0.1
                
                # 策略一致性奖励
                strategy_bonus = self._calculate_strategy_bonus(candidate, strategy)
                adjusted_score += strategy_bonus
                
                candidate['adaptive_score'] = min(100, max(0, adjusted_score))
            
            # 按自适应评分排序
            candidates.sort(key=lambda x: x.get('adaptive_score', 0), reverse=True)
            return candidates
            
        except Exception as e:
            logger.error(f"❌ 策略评分失败: {e}")
            return candidates

    def _calculate_strategy_bonus(self, candidate: Dict[str, Any], 
                                strategy: AdaptiveStrategy) -> float:
        """计算策略一致性奖励"""
        try:
            bonus = 0
            
            # 根据策略类型给予奖励
            if strategy.strategy_type == StrategyType.GROWTH_FOCUSED:
                if candidate.get('growth_score', 0) > 75:
                    bonus += 5
            elif strategy.strategy_type == StrategyType.VALUE_FOCUSED:
                if (candidate.get('pe_ratio', float('inf')) < 15 and 
                    candidate.get('pb_ratio', float('inf')) < 2):
                    bonus += 5
            elif strategy.strategy_type == StrategyType.MOMENTUM_FOCUSED:
                if candidate.get('momentum_score', 0) > 80:
                    bonus += 5
            elif strategy.strategy_type == StrategyType.QUALITY_FOCUSED:
                if candidate.get('quality_score', 0) > 85:
                    bonus += 5
            
            return bonus
            
        except Exception:
            return 0

    def _generate_strategy_reasoning(self, market_regime: MarketRegime, 
                                   strategy: AdaptiveStrategy) -> str:
        """生成策略推理说明"""
        reasoning = f"""
当前市场环境判断为 {market_regime.value}，因此选择 {strategy.strategy_type.value} 策略。

策略特点：
- 预期收益率: {strategy.expected_performance:.2%}
- 历史准确率: {strategy.historical_accuracy:.2%}
- 风险承受度: {strategy.risk_tolerance:.2%}
- 置信度要求: {strategy.confidence_threshold:.2%}

权重调整：
""" + "\n".join([f"- {k}: {v:.2f}倍" for k, v in strategy.weight_adjustments.items()]) + f"""

筛选条件：
""" + "\n".join([f"- {k}: {v}" for k, v in strategy.filter_adjustments.items()])
        
        return reasoning

    def _assess_portfolio_risk(self, recommended_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估投资组合风险"""
        try:
            if not recommended_stocks:
                return {'overall_risk': 'unknown'}
            
            # 收集风险指标
            risk_levels = [stock.get('risk_level', 0.5) for stock in recommended_stocks]
            volatilities = [stock.get('volatility', 0.2) for stock in recommended_stocks if stock.get('volatility')]
            correlations = []  # 简化处理，实际应计算股票间相关性
            
            # 计算风险指标
            avg_risk = statistics.mean(risk_levels)
            avg_volatility = statistics.mean(volatilities) if volatilities else 0.2
            
            # 风险级别判断
            if avg_risk > 0.7:
                risk_level = '高风险'
            elif avg_risk > 0.5:
                risk_level = '中等风险'
            else:
                risk_level = '低风险'
            
            return {
                'overall_risk': risk_level,
                'average_risk_score': round(avg_risk, 3),
                'average_volatility': round(avg_volatility, 3),
                'risk_distribution': {
                    'high_risk_count': len([r for r in risk_levels if r > 0.7]),
                    'medium_risk_count': len([r for r in risk_levels if 0.3 <= r <= 0.7]),
                    'low_risk_count': len([r for r in risk_levels if r < 0.3])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 风险评估失败: {e}")
            return {'overall_risk': 'unknown', 'error': str(e)}

    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """获取策略表现总结"""
        try:
            summary = {
                'total_strategies': len(self.strategy_library),
                'performance_records': len(self.performance_history),
                'strategies_performance': {}
            }
            
            for strategy_key, records in self.performance_history.items():
                if not records:
                    continue
                
                performances = [r['actual_performance'] for r in records]
                summary['strategies_performance'][strategy_key] = {
                    'total_predictions': len(records),
                    'average_return': statistics.mean(performances),
                    'best_return': max(performances),
                    'worst_return': min(performances),
                    'win_rate': len([p for p in performances if p > 0]) / len(performances),
                    'last_updated': records[-1]['timestamp'].strftime('%Y-%m-%d')
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 策略表现总结失败: {e}")
            return {'error': str(e)}