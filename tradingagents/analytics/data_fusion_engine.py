#!/usr/bin/env python3
"""
智能数据融合引擎
实现多源数据的智能融合、质量评分和动态权重调整
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import statistics
from dataclasses import dataclass
from enum import Enum

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class DataSourceType(Enum):
    """数据源类型"""
    REAL_TIME_PRICE = "real_time_price"      # 实时价格数据
    NEWS = "news"                            # 新闻数据
    SENTIMENT = "sentiment"                  # 情感数据
    TECHNICAL = "technical"                  # 技术指标数据
    FUNDAMENTAL = "fundamental"              # 基本面数据


class DataQuality(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"    # 优秀 (>90%)
    GOOD = "good"             # 良好 (70-90%)
    FAIR = "fair"             # 一般 (50-70%) 
    POOR = "poor"             # 较差 (<50%)


@dataclass
class DataPoint:
    """数据点结构"""
    source: str                     # 数据源名称
    data_type: DataSourceType       # 数据类型
    value: Any                      # 数据值
    timestamp: datetime             # 时间戳
    quality_score: float            # 质量评分 (0-1)
    confidence: float               # 置信度 (0-1)
    latency_ms: float              # 数据延迟(毫秒)
    metadata: Dict[str, Any]        # 元数据


@dataclass
class FusionResult:
    """融合结果"""
    fused_value: Any               # 融合后的值
    confidence: float              # 综合置信度
    quality_score: float           # 综合质量评分
    source_weights: Dict[str, float]  # 各源权重
    contributing_sources: List[str]   # 参与融合的数据源
    fusion_method: str             # 融合方法
    metadata: Dict[str, Any]       # 融合元数据


class DataFusionEngine:
    """智能数据融合引擎"""

    def __init__(self):
        """初始化融合引擎"""
        # 数据源基础权重配置
        self.base_weights = {
            'eastmoney': 0.35,      # 东方财富 - 数据丰富度高
            'tencent': 0.30,        # 腾讯财经 - 更新及时
            'sina': 0.25,           # 新浪财经 - 新闻内容丰富
            'xueqiu': 0.15,         # 雪球 - 社交媒体数据
            'tushare': 0.20,        # Tushare - 专业金融数据
            'akshare': 0.10         # AkShare - 开源数据
        }
        
        # 数据源历史表现记录
        self.source_performance = {}
        
        # 质量评分历史
        self.quality_history = {}
        
        # 融合算法配置
        self.fusion_algorithms = {
            'weighted_average': self._weighted_average,
            'median_fusion': self._median_fusion,
            'confidence_weighted': self._confidence_weighted,
            'quality_weighted': self._quality_weighted,
            'adaptive_fusion': self._adaptive_fusion
        }
        
        logger.info("智能数据融合引擎初始化完成")
        logger.info(f"   支持融合算法: {list(self.fusion_algorithms.keys())}")
        logger.info(f"   数据源权重配置: {len(self.base_weights)} 个")

    def fuse_data_points(self, data_points: List[DataPoint], 
                        fusion_method: str = 'adaptive_fusion') -> FusionResult:
        """
        融合多个数据点
        
        Args:
            data_points: 待融合的数据点列表
            fusion_method: 融合方法名称
            
        Returns:
            融合结果
        """
        try:
            if not data_points:
                return self._create_empty_result("无数据点")
            
            # 数据预处理和验证
            valid_points = self._validate_data_points(data_points)
            if not valid_points:
                return self._create_empty_result("无有效数据点")
            
            # 计算动态权重
            dynamic_weights = self._calculate_dynamic_weights(valid_points)
            
            # 应用融合算法
            if fusion_method not in self.fusion_algorithms:
                logger.warning(f"未知融合方法: {fusion_method}, 使用默认方法")
                fusion_method = 'adaptive_fusion'
            
            fusion_func = self.fusion_algorithms[fusion_method]
            fused_value, fusion_confidence = fusion_func(valid_points, dynamic_weights)
            
            # 计算综合质量评分
            quality_score = self._calculate_overall_quality(valid_points, dynamic_weights)
            
            # 更新数据源性能统计
            self._update_source_performance(valid_points)
            
            # 构造融合结果
            result = FusionResult(
                fused_value=fused_value,
                confidence=fusion_confidence,
                quality_score=quality_score,
                source_weights=dynamic_weights,
                contributing_sources=[dp.source for dp in valid_points],
                fusion_method=fusion_method,
                metadata={
                    'timestamp': datetime.now(),
                    'input_count': len(data_points),
                    'valid_count': len(valid_points),
                    'fusion_engine_version': '3.0'
                }
            )
            
            logger.info(f"数据融合完成: {len(valid_points)}个源, 质量评分: {quality_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"数据融合失败: {str(e)}")
            return self._create_empty_result(f"融合错误: {str(e)}")

    def _validate_data_points(self, data_points: List[DataPoint]) -> List[DataPoint]:
        """验证数据点有效性"""
        valid_points = []
        
        for dp in data_points:
            try:
                # 检查基本字段
                if not dp.source or dp.value is None:
                    continue
                
                # 检查时间戳有效性（不超过1小时前）
                if dp.timestamp and (datetime.now() - dp.timestamp) > timedelta(hours=1):
                    logger.debug(f"{dp.source} 数据过期，跳过")
                    continue
                
                # 检查质量评分范围
                if not (0 <= dp.quality_score <= 1):
                    dp.quality_score = 0.5  # 设置默认值
                
                # 检查置信度范围
                if not (0 <= dp.confidence <= 1):
                    dp.confidence = 0.5  # 设置默认值
                
                valid_points.append(dp)
                
            except Exception as e:
                logger.debug(f"验证数据点失败 {dp.source}: {e}")
                continue
        
        return valid_points

    def _calculate_dynamic_weights(self, data_points: List[DataPoint]) -> Dict[str, float]:
        """计算动态权重"""
        try:
            weights = {}
            total_weight = 0
            
            for dp in data_points:
                source = dp.source
                
                # 基础权重
                base_weight = self.base_weights.get(source, 0.1)
                
                # 质量权重调整
                quality_factor = dp.quality_score ** 2  # 质量权重平方，突出高质量
                
                # 置信度权重调整
                confidence_factor = dp.confidence
                
                # 延迟权重调整（延迟越低权重越高）
                if dp.latency_ms > 0:
                    latency_factor = 1.0 / (1.0 + dp.latency_ms / 1000.0)  # 延迟秒数
                else:
                    latency_factor = 1.0
                
                # 历史表现权重调整
                performance_factor = self._get_source_performance_factor(source)
                
                # 综合权重计算
                dynamic_weight = (base_weight * 
                                quality_factor * 
                                confidence_factor * 
                                latency_factor * 
                                performance_factor)
                
                weights[source] = dynamic_weight
                total_weight += dynamic_weight
            
            # 归一化权重
            if total_weight > 0:
                weights = {k: v/total_weight for k, v in weights.items()}
            
            return weights
            
        except Exception as e:
            logger.error(f"计算动态权重失败: {e}")
            # 返回平均权重
            equal_weight = 1.0 / len(data_points)
            return {dp.source: equal_weight for dp in data_points}

    def _get_source_performance_factor(self, source: str) -> float:
        """获取数据源历史表现因子"""
        if source not in self.source_performance:
            return 1.0  # 新数据源默认权重
        
        perf = self.source_performance[source]
        
        # 基于准确率和可靠性计算
        accuracy = perf.get('accuracy', 0.5)
        reliability = perf.get('reliability', 0.5)
        
        # 性能因子计算（范围0.5-1.5）
        performance_factor = 0.5 + (accuracy + reliability)
        
        return min(1.5, max(0.5, performance_factor))

    def _weighted_average(self, data_points: List[DataPoint], 
                         weights: Dict[str, float]) -> Tuple[float, float]:
        """加权平均融合算法"""
        try:
            if not data_points:
                return 0.0, 0.0
            
            # 提取数值
            values = []
            confidences = []
            point_weights = []
            
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    values.append(float(dp.value))
                    confidences.append(dp.confidence)
                    point_weights.append(weights.get(dp.source, 0.1))
            
            if not values:
                return 0.0, 0.0
            
            # 加权平均计算
            weighted_sum = sum(v * w for v, w in zip(values, point_weights))
            weight_sum = sum(point_weights)
            
            if weight_sum == 0:
                return statistics.mean(values), statistics.mean(confidences)
            
            fused_value = weighted_sum / weight_sum
            fused_confidence = sum(c * w for c, w in zip(confidences, point_weights)) / weight_sum
            
            return fused_value, fused_confidence
            
        except Exception as e:
            logger.error(f"加权平均融合失败: {e}")
            return 0.0, 0.0

    def _median_fusion(self, data_points: List[DataPoint], 
                      weights: Dict[str, float]) -> Tuple[float, float]:
        """中位数融合算法（抗异常值）"""
        try:
            values = []
            confidences = []
            
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    values.append(float(dp.value))
                    confidences.append(dp.confidence)
            
            if not values:
                return 0.0, 0.0
            
            fused_value = statistics.median(values)
            fused_confidence = statistics.mean(confidences)
            
            return fused_value, fused_confidence
            
        except Exception as e:
            logger.error(f"中位数融合失败: {e}")
            return 0.0, 0.0

    def _confidence_weighted(self, data_points: List[DataPoint], 
                           weights: Dict[str, float]) -> Tuple[float, float]:
        """置信度加权融合"""
        try:
            values = []
            confidences = []
            
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    values.append(float(dp.value))
                    confidences.append(dp.confidence)
            
            if not values:
                return 0.0, 0.0
            
            # 使用置信度作为权重
            confidence_sum = sum(confidences)
            if confidence_sum == 0:
                return statistics.mean(values), 0.0
            
            weighted_sum = sum(v * c for v, c in zip(values, confidences))
            fused_value = weighted_sum / confidence_sum
            fused_confidence = statistics.mean(confidences)
            
            return fused_value, fused_confidence
            
        except Exception as e:
            logger.error(f"置信度加权融合失败: {e}")
            return 0.0, 0.0

    def _quality_weighted(self, data_points: List[DataPoint], 
                         weights: Dict[str, float]) -> Tuple[float, float]:
        """质量加权融合"""
        try:
            values = []
            qualities = []
            confidences = []
            
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    values.append(float(dp.value))
                    qualities.append(dp.quality_score)
                    confidences.append(dp.confidence)
            
            if not values:
                return 0.0, 0.0
            
            # 使用质量评分的平方作为权重，突出高质量数据
            quality_weights = [q**2 for q in qualities]
            weight_sum = sum(quality_weights)
            
            if weight_sum == 0:
                return statistics.mean(values), statistics.mean(confidences)
            
            weighted_sum = sum(v * w for v, w in zip(values, quality_weights))
            fused_value = weighted_sum / weight_sum
            
            # 置信度也按质量加权
            weighted_confidence = sum(c * w for c, w in zip(confidences, quality_weights)) / weight_sum
            
            return fused_value, weighted_confidence
            
        except Exception as e:
            logger.error(f"质量加权融合失败: {e}")
            return 0.0, 0.0

    def _adaptive_fusion(self, data_points: List[DataPoint], 
                        weights: Dict[str, float]) -> Tuple[float, float]:
        """自适应融合算法（综合多种方法）"""
        try:
            if len(data_points) < 2:
                # 单数据源直接返回
                if data_points:
                    dp = data_points[0]
                    return float(dp.value) if isinstance(dp.value, (int, float)) else 0.0, dp.confidence
                return 0.0, 0.0
            
            # 提取数值数据
            numeric_points = [dp for dp in data_points if isinstance(dp.value, (int, float))]
            if not numeric_points:
                return 0.0, 0.0
            
            values = [float(dp.value) for dp in numeric_points]
            
            # 计算数据分散度
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            mean_value = statistics.mean(values)
            
            # 根据分散度选择融合策略
            if std_dev / max(abs(mean_value), 1) < 0.05:  # 数据一致性高，使用加权平均
                return self._weighted_average(numeric_points, weights)
            elif std_dev / max(abs(mean_value), 1) > 0.2:  # 数据分散，使用中位数
                return self._median_fusion(numeric_points, weights)
            else:  # 中等分散，使用质量加权
                return self._quality_weighted(numeric_points, weights)
            
        except Exception as e:
            logger.error(f"自适应融合失败: {e}")
            return 0.0, 0.0

    def _calculate_overall_quality(self, data_points: List[DataPoint], 
                                  weights: Dict[str, float]) -> float:
        """计算综合数据质量评分"""
        try:
            if not data_points:
                return 0.0
            
            # 加权质量评分
            weighted_quality = 0.0
            total_weight = 0.0
            
            for dp in data_points:
                weight = weights.get(dp.source, 0.1)
                weighted_quality += dp.quality_score * weight
                total_weight += weight
            
            if total_weight == 0:
                return statistics.mean([dp.quality_score for dp in data_points])
            
            base_quality = weighted_quality / total_weight
            
            # 数据源多样性奖励（更多数据源 = 更高质量）
            diversity_bonus = min(0.1, len(data_points) * 0.02)
            
            # 一致性奖励（数值一致性高 = 质量高）
            consistency_bonus = self._calculate_consistency_bonus(data_points)
            
            final_quality = min(1.0, base_quality + diversity_bonus + consistency_bonus)
            
            return final_quality
            
        except Exception as e:
            logger.error(f"计算综合质量失败: {e}")
            return 0.5

    def _calculate_consistency_bonus(self, data_points: List[DataPoint]) -> float:
        """计算数据一致性奖励"""
        try:
            numeric_values = []
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    numeric_values.append(float(dp.value))
            
            if len(numeric_values) < 2:
                return 0.0
            
            # 计算变异系数（CV = 标准差/平均值）
            mean_val = statistics.mean(numeric_values)
            if abs(mean_val) < 1e-6:  # 避免除零
                return 0.05  # 小奖励
            
            std_val = statistics.stdev(numeric_values)
            cv = std_val / abs(mean_val)
            
            # CV越小，一致性越高，奖励越大
            if cv < 0.01:
                return 0.1   # 高一致性
            elif cv < 0.05:
                return 0.05  # 中等一致性
            elif cv < 0.1:
                return 0.02  # 低一致性
            else:
                return 0.0   # 无奖励
            
        except Exception:
            return 0.0

    def _update_source_performance(self, data_points: List[DataPoint]):
        """更新数据源性能统计"""
        try:
            for dp in data_points:
                source = dp.source
                
                if source not in self.source_performance:
                    self.source_performance[source] = {
                        'accuracy': 0.5,
                        'reliability': 0.5,
                        'call_count': 0,
                        'last_update': datetime.now()
                    }
                
                perf = self.source_performance[source]
                perf['call_count'] += 1
                perf['last_update'] = datetime.now()
                
                # 基于质量评分和置信度更新准确率
                new_accuracy = (dp.quality_score + dp.confidence) / 2
                alpha = 0.1  # 学习率
                perf['accuracy'] = (1 - alpha) * perf['accuracy'] + alpha * new_accuracy
                
                # 基于数据新鲜度更新可靠性
                if dp.timestamp:
                    age_minutes = (datetime.now() - dp.timestamp).total_seconds() / 60
                    freshness = max(0.1, 1.0 - age_minutes / 60)  # 1小时内有效
                    perf['reliability'] = (1 - alpha) * perf['reliability'] + alpha * freshness
                
        except Exception as e:
            logger.error(f"更新数据源性能失败: {e}")

    def _create_empty_result(self, reason: str) -> FusionResult:
        """创建空融合结果"""
        return FusionResult(
            fused_value=None,
            confidence=0.0,
            quality_score=0.0,
            source_weights={},
            contributing_sources=[],
            fusion_method='none',
            metadata={
                'timestamp': datetime.now(),
                'error_reason': reason,
                'fusion_engine_version': '3.0'
            }
        )

    def get_source_performance_report(self) -> Dict[str, Any]:
        """获取数据源性能报告"""
        try:
            report = {
                'timestamp': datetime.now(),
                'total_sources': len(self.source_performance),
                'source_details': {},
                'top_performers': [],
                'underperformers': []
            }
            
            # 整理数据源详情
            for source, perf in self.source_performance.items():
                overall_score = (perf['accuracy'] + perf['reliability']) / 2
                
                report['source_details'][source] = {
                    'accuracy': round(perf['accuracy'], 3),
                    'reliability': round(perf['reliability'], 3),
                    'overall_score': round(overall_score, 3),
                    'call_count': perf['call_count'],
                    'last_update': perf['last_update'].strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # 找出表现最好和最差的数据源
            sorted_sources = sorted(
                report['source_details'].items(),
                key=lambda x: x[1]['overall_score'],
                reverse=True
            )
            
            if sorted_sources:
                report['top_performers'] = [
                    {'source': s[0], 'score': s[1]['overall_score']} 
                    for s in sorted_sources[:3]
                ]
                report['underperformers'] = [
                    {'source': s[0], 'score': s[1]['overall_score']} 
                    for s in sorted_sources[-3:]
                ]
            
            return report
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return {'error': str(e)}

    def suggest_weight_adjustments(self) -> Dict[str, float]:
        """建议权重调整"""
        try:
            suggestions = {}
            
            for source, perf in self.source_performance.items():
                current_weight = self.base_weights.get(source, 0.1)
                performance_score = (perf['accuracy'] + perf['reliability']) / 2
                
                # 基于性能建议调整
                if performance_score > 0.8:
                    suggested_weight = min(0.4, current_weight * 1.2)
                elif performance_score < 0.3:
                    suggested_weight = max(0.05, current_weight * 0.8)
                else:
                    suggested_weight = current_weight
                
                suggestions[source] = round(suggested_weight, 3)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成权重建议失败: {e}")
            return {}


# 全局实例
_fusion_engine = None

def get_fusion_engine() -> DataFusionEngine:
    """获取数据融合引擎实例"""
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = DataFusionEngine()
    return _fusion_engine


# 便捷函数
def fuse_stock_prices(price_data: Dict[str, Dict[str, Any]], 
                     symbol: str = None) -> FusionResult:
    """融合股票价格数据"""
    try:
        fusion_engine = get_fusion_engine()
        data_points = []
        
        for source, data in price_data.items():
            if 'current_price' in data and data['current_price']:
                dp = DataPoint(
                    source=source,
                    data_type=DataSourceType.REAL_TIME_PRICE,
                    value=data['current_price'],
                    timestamp=datetime.now(),
                    quality_score=data.get('quality_score', 0.8),
                    confidence=data.get('confidence', 0.8),
                    latency_ms=data.get('latency_ms', 100),
                    metadata={'symbol': symbol, 'raw_data': data}
                )
                data_points.append(dp)
        
        return fusion_engine.fuse_data_points(data_points, 'adaptive_fusion')
        
    except Exception as e:
        logger.error(f"融合股票价格失败: {e}")
        return DataFusionEngine()._create_empty_result(str(e))