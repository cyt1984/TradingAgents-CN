#!/usr/bin/env python3
"""
动态权重调整机制
根据数据源性能、可靠性、质量等实时调整融合权重
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math
from dataclasses import dataclass
from enum import Enum

# 导入相关模块
from .reliability_monitor import get_reliability_monitor, MonitoringStatus
from .data_quality_analyzer import get_quality_analyzer
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class AdjustmentStrategy(Enum):
    """权重调整策略"""
    CONSERVATIVE = "conservative"    # 保守策略 - 缓慢调整
    BALANCED = "balanced"           # 平衡策略 - 适中调整  
    AGGRESSIVE = "aggressive"       # 激进策略 - 快速调整
    ADAPTIVE = "adaptive"          # 自适应策略 - 根据情况调整


@dataclass
class WeightAdjustment:
    """权重调整记录"""
    timestamp: datetime
    source: str
    old_weight: float
    new_weight: float
    adjustment_reason: str
    strategy: AdjustmentStrategy
    confidence: float


@dataclass
class WeightRecommendation:
    """权重建议"""
    source: str
    current_weight: float
    recommended_weight: float
    confidence: float
    reasoning: List[str]
    risk_assessment: str


class DynamicWeightManager:
    """动态权重管理器"""

    def __init__(self, strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED):
        """初始化动态权重管理器"""
        self.strategy = strategy
        self.reliability_monitor = get_reliability_monitor()
        self.quality_analyzer = get_quality_analyzer()
        
        # 当前权重配置
        self.current_weights = {
            'eastmoney': 0.35,
            'tencent': 0.30,
            'sina': 0.25,
            'xueqiu': 0.15,
            'tushare': 0.20,
            'akshare': 0.10
        }
        
        # 权重历史记录
        self.weight_history = {}
        self.adjustment_history = []
        
        # 调整参数配置
        self.adjustment_params = {
            AdjustmentStrategy.CONSERVATIVE: {
                'learning_rate': 0.05,          # 学习率低
                'stability_threshold': 0.02,     # 稳定性阈值高
                'max_adjustment': 0.1,          # 最大调整幅度小
                'confidence_threshold': 0.8     # 需要高置信度
            },
            AdjustmentStrategy.BALANCED: {
                'learning_rate': 0.1,
                'stability_threshold': 0.05,
                'max_adjustment': 0.15,
                'confidence_threshold': 0.6
            },
            AdjustmentStrategy.AGGRESSIVE: {
                'learning_rate': 0.2,
                'stability_threshold': 0.1,
                'max_adjustment': 0.25,
                'confidence_threshold': 0.4
            },
            AdjustmentStrategy.ADAPTIVE: {
                'learning_rate': 0.1,  # 会动态调整
                'stability_threshold': 0.05,
                'max_adjustment': 0.2,
                'confidence_threshold': 0.5
            }
        }
        
        # 最小/最大权重限制
        self.weight_constraints = {
            'min_weight': 0.01,  # 最小权重1%
            'max_weight': 0.6,   # 最大权重60%
            'critical_source_min': 0.05  # 关键数据源最小权重5%
        }
        
        logger.info("动态权重管理器初始化完成")
        logger.info(f"   调整策略: {strategy.value}")
        logger.info(f"   管理数据源: {len(self.current_weights)} 个")

    def update_weights(self, performance_data: Dict[str, Any] = None) -> Dict[str, float]:
        """
        更新数据源权重
        
        Args:
            performance_data: 额外的性能数据
            
        Returns:
            更新后的权重字典
        """
        try:
            logger.info("开始动态权重调整...")
            
            # 收集性能指标
            performance_metrics = self._collect_performance_metrics(performance_data)
            
            # 计算权重建议
            weight_recommendations = self._calculate_weight_recommendations(performance_metrics)
            
            # 应用权重调整
            new_weights = self._apply_weight_adjustments(weight_recommendations)
            
            # 标准化权重
            new_weights = self._normalize_weights(new_weights)
            
            # 应用约束
            new_weights = self._apply_weight_constraints(new_weights)
            
            # 记录调整历史
            self._record_weight_adjustments(new_weights)
            
            # 更新当前权重
            old_weights = self.current_weights.copy()
            self.current_weights = new_weights
            
            # 记录权重历史
            self._update_weight_history()
            
            logger.info("动态权重调整完成")
            self._log_weight_changes(old_weights, new_weights)
            
            return new_weights.copy()
            
        except Exception as e:
            logger.error(f"动态权重调整失败: {e}")
            return self.current_weights.copy()

    def _collect_performance_metrics(self, additional_data: Dict[str, Any] = None) -> Dict[str, Dict[str, float]]:
        """收集性能指标"""
        try:
            metrics = {}
            
            # 从可靠性监控器获取指标
            monitoring_report = self.reliability_monitor.get_monitoring_report()
            
            for source, source_metrics in monitoring_report.source_metrics.items():
                metrics[source] = {
                    'reliability_score': self.reliability_monitor.get_source_reliability_score(source),
                    'response_time': source_metrics.avg_response_time,
                    'success_rate': source_metrics.success_rate,
                    'uptime': source_metrics.uptime_percentage,
                    'data_quality': source_metrics.data_quality_score,
                    'error_count': source_metrics.error_count,
                    'total_requests': source_metrics.total_requests,
                    'status_score': self._convert_status_to_score(source_metrics.status)
                }
            
            # 添加额外数据
            if additional_data:
                for source, extra_metrics in additional_data.items():
                    if source in metrics:
                        metrics[source].update(extra_metrics)
                    else:
                        metrics[source] = extra_metrics
            
            # 为没有监控数据的数据源设置默认值
            for source in self.current_weights:
                if source not in metrics:
                    metrics[source] = {
                        'reliability_score': 0.5,
                        'response_time': 1000,
                        'success_rate': 0.8,
                        'uptime': 0.8,
                        'data_quality': 0.7,
                        'error_count': 0,
                        'total_requests': 1,
                        'status_score': 0.7
                    }
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")
            return {}

    def _convert_status_to_score(self, status: MonitoringStatus) -> float:
        """将监控状态转换为评分"""
        status_scores = {
            MonitoringStatus.HEALTHY: 1.0,
            MonitoringStatus.WARNING: 0.7,
            MonitoringStatus.CRITICAL: 0.3,
            MonitoringStatus.OFFLINE: 0.1,
            MonitoringStatus.UNKNOWN: 0.5
        }
        return status_scores.get(status, 0.5)

    def _calculate_weight_recommendations(self, performance_metrics: Dict[str, Dict[str, float]]) -> List[WeightRecommendation]:
        """计算权重建议"""
        try:
            recommendations = []
            
            for source, metrics in performance_metrics.items():
                current_weight = self.current_weights.get(source, 0.1)
                
                # 计算综合性能评分
                performance_score = self._calculate_performance_score(metrics)
                
                # 计算推荐权重
                recommended_weight = self._calculate_recommended_weight(source, current_weight, performance_score, metrics)
                
                # 计算置信度
                confidence = self._calculate_adjustment_confidence(metrics)
                
                # 生成推荐理由
                reasoning = self._generate_adjustment_reasoning(source, current_weight, recommended_weight, metrics)
                
                # 风险评估
                risk_assessment = self._assess_adjustment_risk(source, current_weight, recommended_weight)
                
                recommendation = WeightRecommendation(
                    source=source,
                    current_weight=current_weight,
                    recommended_weight=recommended_weight,
                    confidence=confidence,
                    reasoning=reasoning,
                    risk_assessment=risk_assessment
                )
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"计算权重建议失败: {e}")
            return []

    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """计算综合性能评分"""
        try:
            # 性能指标权重
            weights = {
                'reliability_score': 0.25,
                'success_rate': 0.20,
                'uptime': 0.20,
                'data_quality': 0.15,
                'status_score': 0.15,
                'response_time_score': 0.05  # 响应时间评分需要转换
            }
            
            # 响应时间评分 (越低越好)
            response_time = metrics.get('response_time', 1000)
            response_time_score = max(0.1, 1.0 - response_time / 10000)  # 10秒为基准
            
            # 计算加权评分
            weighted_score = (
                metrics.get('reliability_score', 0.5) * weights['reliability_score'] +
                metrics.get('success_rate', 0.8) * weights['success_rate'] +
                metrics.get('uptime', 0.8) * weights['uptime'] +
                metrics.get('data_quality', 0.7) * weights['data_quality'] +
                metrics.get('status_score', 0.7) * weights['status_score'] +
                response_time_score * weights['response_time_score']
            )
            
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            logger.error(f"计算性能评分失败: {e}")
            return 0.5

    def _calculate_recommended_weight(self, source: str, current_weight: float, 
                                    performance_score: float, metrics: Dict[str, float]) -> float:
        """计算推荐权重"""
        try:
            # 获取调整参数
            params = self.adjustment_params[self.strategy]
            learning_rate = params['learning_rate']
            
            # 自适应策略需要动态调整学习率
            if self.strategy == AdjustmentStrategy.ADAPTIVE:
                learning_rate = self._adaptive_learning_rate(source, performance_score, metrics)
            
            # 基于性能评分计算目标权重
            # 性能越好，权重越高
            base_target_weight = performance_score * 0.4  # 基础目标权重
            
            # 考虑数据源的历史稳定性
            stability_factor = self._calculate_stability_factor(source)
            adjusted_target_weight = base_target_weight * stability_factor
            
            # 应用学习率进行平滑调整
            weight_diff = adjusted_target_weight - current_weight
            recommended_weight = current_weight + weight_diff * learning_rate
            
            # 应用最大调整限制
            max_adjustment = params['max_adjustment']
            if abs(recommended_weight - current_weight) > max_adjustment:
                if recommended_weight > current_weight:
                    recommended_weight = current_weight + max_adjustment
                else:
                    recommended_weight = current_weight - max_adjustment
            
            return max(0.01, min(0.6, recommended_weight))  # 基本约束
            
        except Exception as e:
            logger.error(f"计算推荐权重失败: {e}")
            return current_weight

    def _adaptive_learning_rate(self, source: str, performance_score: float, 
                              metrics: Dict[str, float]) -> float:
        """自适应学习率"""
        try:
            base_learning_rate = 0.1
            
            # 基于性能变化调整学习率
            if performance_score > 0.8:
                # 高性能数据源，可以更积极调整
                learning_rate_multiplier = 1.2
            elif performance_score < 0.4:
                # 低性能数据源，需要谨慎调整
                learning_rate_multiplier = 0.7
            else:
                learning_rate_multiplier = 1.0
            
            # 基于数据源稳定性调整
            stability_factor = self._calculate_stability_factor(source)
            if stability_factor > 0.8:
                learning_rate_multiplier *= 1.1  # 稳定的数据源可以更大调整
            elif stability_factor < 0.5:
                learning_rate_multiplier *= 0.8  # 不稳定的数据源需要更小调整
            
            return base_learning_rate * learning_rate_multiplier
            
        except Exception:
            return 0.1

    def _calculate_stability_factor(self, source: str) -> float:
        """计算数据源稳定性因子"""
        try:
            if source not in self.weight_history:
                return 0.8  # 新数据源给予中等稳定性
            
            # 分析权重变化的标准差
            recent_weights = self.weight_history[source][-20:]  # 最近20次权重
            if len(recent_weights) < 3:
                return 0.8
            
            weight_values = [w['weight'] for w in recent_weights]
            weight_std = statistics.stdev(weight_values)
            
            # 标准差越小，稳定性越高
            stability = max(0.3, 1.0 - weight_std * 5)  # 调整系数
            
            return stability
            
        except Exception:
            return 0.8

    def _calculate_adjustment_confidence(self, metrics: Dict[str, float]) -> float:
        """计算调整置信度"""
        try:
            confidence_factors = []
            
            # 基于数据完整性
            required_metrics = ['reliability_score', 'success_rate', 'uptime', 'data_quality']
            available_metrics = sum(1 for metric in required_metrics if metric in metrics and metrics[metric] > 0)
            data_completeness = available_metrics / len(required_metrics)
            confidence_factors.append(data_completeness)
            
            # 基于请求数量 (请求数量越多，置信度越高)
            total_requests = metrics.get('total_requests', 1)
            request_confidence = min(1.0, math.log(total_requests + 1) / math.log(100))  # 100次请求为满分
            confidence_factors.append(request_confidence)
            
            # 基于性能稳定性
            reliability_score = metrics.get('reliability_score', 0.5)
            if reliability_score > 0.8:
                stability_confidence = 0.9
            elif reliability_score > 0.6:
                stability_confidence = 0.7
            else:
                stability_confidence = 0.5
            confidence_factors.append(stability_confidence)
            
            return statistics.mean(confidence_factors)
            
        except Exception:
            return 0.5

    def _generate_adjustment_reasoning(self, source: str, current_weight: float, 
                                     recommended_weight: float, metrics: Dict[str, float]) -> List[str]:
        """生成调整理由"""
        try:
            reasoning = []
            
            weight_change = recommended_weight - current_weight
            change_pct = (weight_change / current_weight) * 100 if current_weight > 0 else 0
            
            if abs(change_pct) < 2:
                reasoning.append("权重保持稳定，性能表现良好")
                return reasoning
            
            # 权重增加的理由
            if weight_change > 0:
                if metrics.get('reliability_score', 0) > 0.8:
                    reasoning.append("可靠性评分优秀")
                if metrics.get('success_rate', 0) > 0.9:
                    reasoning.append("成功率表现突出")
                if metrics.get('response_time', 5000) < 1000:
                    reasoning.append("响应时间快速")
                if metrics.get('data_quality', 0) > 0.8:
                    reasoning.append("数据质量高")
            
            # 权重减少的理由
            else:
                if metrics.get('reliability_score', 0) < 0.5:
                    reasoning.append("可靠性评分偏低")
                if metrics.get('success_rate', 0) < 0.8:
                    reasoning.append("成功率需要改善")
                if metrics.get('response_time', 1000) > 5000:
                    reasoning.append("响应时间较长")
                if metrics.get('error_count', 0) > 10:
                    reasoning.append("错误次数较多")
            
            if not reasoning:
                reasoning.append(f"基于综合性能评分调整 ({change_pct:+.1f}%)")
            
            return reasoning
            
        except Exception:
            return ["权重调整基于性能指标"]

    def _assess_adjustment_risk(self, source: str, current_weight: float, recommended_weight: float) -> str:
        """评估调整风险"""
        try:
            weight_change = abs(recommended_weight - current_weight)
            change_ratio = weight_change / current_weight if current_weight > 0 else 1.0
            
            # 检查是否为关键数据源
            is_critical = current_weight > 0.2  # 权重超过20%认为是关键数据源
            
            if change_ratio > 0.5 and is_critical:
                return "高风险"
            elif change_ratio > 0.3:
                return "中等风险" 
            elif change_ratio > 0.1:
                return "低风险"
            else:
                return "极低风险"
                
        except Exception:
            return "未知风险"

    def _apply_weight_adjustments(self, recommendations: List[WeightRecommendation]) -> Dict[str, float]:
        """应用权重调整"""
        try:
            new_weights = self.current_weights.copy()
            params = self.adjustment_params[self.strategy]
            confidence_threshold = params['confidence_threshold']
            
            adjustments_made = []
            
            for rec in recommendations:
                # 检查置信度阈值
                if rec.confidence >= confidence_threshold:
                    # 检查风险等级
                    if rec.risk_assessment in ["极低风险", "低风险"] or (rec.risk_assessment == "中等风险" and rec.confidence > 0.8):
                        new_weights[rec.source] = rec.recommended_weight
                        
                        adjustment = WeightAdjustment(
                            timestamp=datetime.now(),
                            source=rec.source,
                            old_weight=rec.current_weight,
                            new_weight=rec.recommended_weight,
                            adjustment_reason="; ".join(rec.reasoning),
                            strategy=self.strategy,
                            confidence=rec.confidence
                        )
                        adjustments_made.append(adjustment)
                    else:
                        logger.warning(f"跳过高风险权重调整: {rec.source} ({rec.risk_assessment})")
                else:
                    logger.debug(f"置信度不足，跳过权重调整: {rec.source} (置信度: {rec.confidence:.2f})")
            
            # 记录调整
            self.adjustment_history.extend(adjustments_made)
            
            return new_weights
            
        except Exception as e:
            logger.error(f"应用权重调整失败: {e}")
            return self.current_weights.copy()

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """标准化权重使其和为1"""
        try:
            total_weight = sum(weights.values())
            if total_weight <= 0:
                # 如果总权重为0，平均分配
                equal_weight = 1.0 / len(weights)
                return {source: equal_weight for source in weights}
            
            # 标准化
            normalized = {source: weight / total_weight for source, weight in weights.items()}
            
            return normalized
            
        except Exception as e:
            logger.error(f"权重标准化失败: {e}")
            return weights

    def _apply_weight_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """应用权重约束"""
        try:
            constrained_weights = weights.copy()
            constraints = self.weight_constraints
            
            # 应用最小/最大权重限制
            for source, weight in constrained_weights.items():
                constrained_weights[source] = max(constraints['min_weight'], 
                                                min(constraints['max_weight'], weight))
            
            # 重新标准化
            constrained_weights = self._normalize_weights(constrained_weights)
            
            return constrained_weights
            
        except Exception as e:
            logger.error(f"应用权重约束失败: {e}")
            return weights

    def _record_weight_adjustments(self, new_weights: Dict[str, float]):
        """记录权重调整"""
        try:
            for source, new_weight in new_weights.items():
                old_weight = self.current_weights.get(source, 0)
                if abs(new_weight - old_weight) > 0.001:  # 有实际调整
                    logger.info(f"权重调整: {source} {old_weight:.3f} -> {new_weight:.3f}")
                    
        except Exception as e:
            logger.error(f"记录权重调整失败: {e}")

    def _update_weight_history(self):
        """更新权重历史"""
        try:
            current_time = datetime.now()
            
            for source, weight in self.current_weights.items():
                if source not in self.weight_history:
                    self.weight_history[source] = []
                
                history = self.weight_history[source]
                history.append({
                    'timestamp': current_time,
                    'weight': weight,
                    'strategy': self.strategy.value
                })
                
                # 保持最近200个记录
                if len(history) > 200:
                    history.pop(0)
                    
        except Exception as e:
            logger.error(f"更新权重历史失败: {e}")

    def _log_weight_changes(self, old_weights: Dict[str, float], new_weights: Dict[str, float]):
        """记录权重变化"""
        try:
            changes = []
            for source in old_weights:
                old_w = old_weights.get(source, 0)
                new_w = new_weights.get(source, 0)
                if abs(new_w - old_w) > 0.005:  # 超过0.5%的变化才记录
                    change_pct = ((new_w - old_w) / old_w * 100) if old_w > 0 else 0
                    changes.append(f"{source}: {change_pct:+.1f}%")
            
            if changes:
                logger.info(f"权重变化: {', '.join(changes)}")
            else:
                logger.info("权重保持稳定")
                
        except Exception as e:
            logger.error(f"记录权重变化失败: {e}")

    def get_current_weights(self) -> Dict[str, float]:
        """获取当前权重"""
        return self.current_weights.copy()

    def get_weight_history(self, source: str = None, days: int = 7) -> Dict[str, Any]:
        """获取权重历史"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            if source:
                # 特定数据源的历史
                if source not in self.weight_history:
                    return {'error': f'数据源 {source} 无历史记录'}
                
                history = self.weight_history[source]
                recent_history = [h for h in history if h['timestamp'] >= cutoff_time]
                
                return {
                    'source': source,
                    'period_days': days,
                    'record_count': len(recent_history),
                    'history': recent_history
                }
            else:
                # 所有数据源的历史
                all_history = {}
                for src, history in self.weight_history.items():
                    recent_history = [h for h in history if h['timestamp'] >= cutoff_time]
                    if recent_history:
                        all_history[src] = recent_history
                
                return {
                    'period_days': days,
                    'sources': list(all_history.keys()),
                    'history': all_history
                }
                
        except Exception as e:
            logger.error(f"获取权重历史失败: {e}")
            return {'error': str(e)}

    def get_adjustment_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取权重调整摘要"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            recent_adjustments = [
                adj for adj in self.adjustment_history
                if adj.timestamp >= cutoff_time
            ]
            
            summary = {
                'period_days': days,
                'total_adjustments': len(recent_adjustments),
                'sources_adjusted': len(set(adj.source for adj in recent_adjustments)),
                'strategy': self.strategy.value,
                'adjustments_by_source': {},
                'recent_adjustments': []
            }
            
            # 按数据源统计
            for adj in recent_adjustments:
                source = adj.source
                if source not in summary['adjustments_by_source']:
                    summary['adjustments_by_source'][source] = {
                        'count': 0,
                        'total_change': 0.0,
                        'avg_confidence': 0.0
                    }
                
                stats = summary['adjustments_by_source'][source]
                stats['count'] += 1
                stats['total_change'] += abs(adj.new_weight - adj.old_weight)
                stats['avg_confidence'] += adj.confidence
            
            # 计算平均置信度
            for source_stats in summary['adjustments_by_source'].values():
                if source_stats['count'] > 0:
                    source_stats['avg_confidence'] /= source_stats['count']
            
            # 最近调整记录
            summary['recent_adjustments'] = [
                {
                    'timestamp': adj.timestamp.isoformat(),
                    'source': adj.source,
                    'weight_change': adj.new_weight - adj.old_weight,
                    'reason': adj.adjustment_reason,
                    'confidence': adj.confidence
                }
                for adj in sorted(recent_adjustments, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"获取调整摘要失败: {e}")
            return {'error': str(e)}

    def set_strategy(self, new_strategy: AdjustmentStrategy):
        """设置权重调整策略"""
        try:
            old_strategy = self.strategy
            self.strategy = new_strategy
            
            logger.info(f"权重调整策略变更: {old_strategy.value} -> {new_strategy.value}")
            
        except Exception as e:
            logger.error(f"设置策略失败: {e}")

    def reset_weights(self, new_weights: Dict[str, float] = None):
        """重置权重"""
        try:
            if new_weights:
                self.current_weights = self._normalize_weights(new_weights.copy())
                logger.info("权重已重置为指定值")
            else:
                # 重置为默认权重
                default_weights = {
                    'eastmoney': 0.35,
                    'tencent': 0.30,
                    'sina': 0.25,
                    'xueqiu': 0.15,
                    'tushare': 0.20,
                    'akshare': 0.10
                }
                self.current_weights = self._normalize_weights(default_weights)
                logger.info("权重已重置为默认值")
            
            # 清空调整历史
            self.adjustment_history.clear()
            self.weight_history.clear()
            
        except Exception as e:
            logger.error(f"重置权重失败: {e}")


# 全局实例
_dynamic_weight_manager = None

def get_dynamic_weight_manager() -> DynamicWeightManager:
    """获取动态权重管理器实例"""
    global _dynamic_weight_manager
    if _dynamic_weight_manager is None:
        _dynamic_weight_manager = DynamicWeightManager()
    return _dynamic_weight_manager


# 便捷函数
def update_data_source_weights(performance_data: Dict[str, Any] = None) -> Dict[str, float]:
    """更新数据源权重"""
    manager = get_dynamic_weight_manager()
    return manager.update_weights(performance_data)

def get_current_data_source_weights() -> Dict[str, float]:
    """获取当前数据源权重"""
    manager = get_dynamic_weight_manager()
    return manager.get_current_weights()