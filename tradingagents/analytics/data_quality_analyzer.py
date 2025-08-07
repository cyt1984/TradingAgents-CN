#!/usr/bin/env python3
"""
多源数据质量评分算法
实现数据完整性、准确性、时效性、一致性等多维度质量评估
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import re
from dataclasses import dataclass
from enum import Enum
import math

# 导入日志模块  
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class QualityDimension(Enum):
    """数据质量维度"""
    COMPLETENESS = "completeness"        # 完整性
    ACCURACY = "accuracy"               # 准确性  
    TIMELINESS = "timeliness"          # 时效性
    CONSISTENCY = "consistency"         # 一致性
    VALIDITY = "validity"              # 有效性
    RELIABILITY = "reliability"         # 可靠性


@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float      # 完整性评分 (0-1)
    accuracy: float         # 准确性评分 (0-1) 
    timeliness: float       # 时效性评分 (0-1)
    consistency: float      # 一致性评分 (0-1)
    validity: float         # 有效性评分 (0-1)
    reliability: float      # 可靠性评分 (0-1)
    overall_score: float    # 综合评分 (0-1)
    quality_grade: str      # 质量等级
    details: Dict[str, Any] # 详细信息


@dataclass  
class DataQualityProfile:
    """数据质量档案"""
    source: str                    # 数据源
    data_type: str                 # 数据类型
    sample_count: int              # 样本数量
    quality_metrics: QualityMetrics # 质量指标
    historical_scores: List[float]  # 历史评分
    last_updated: datetime         # 最后更新时间
    benchmark_comparison: Dict[str, float] # 基准对比


class DataQualityAnalyzer:
    """数据质量分析器"""

    def __init__(self):
        """初始化质量分析器"""
        # 质量维度权重配置
        self.dimension_weights = {
            QualityDimension.COMPLETENESS: 0.20,  # 完整性
            QualityDimension.ACCURACY: 0.25,     # 准确性
            QualityDimension.TIMELINESS: 0.20,   # 时效性  
            QualityDimension.CONSISTENCY: 0.15,  # 一致性
            QualityDimension.VALIDITY: 0.15,     # 有效性
            QualityDimension.RELIABILITY: 0.05   # 可靠性
        }
        
        # 数据源质量基准
        self.quality_benchmarks = {
            'eastmoney': {'accuracy': 0.85, 'timeliness': 0.90, 'completeness': 0.88},
            'tencent': {'accuracy': 0.82, 'timeliness': 0.92, 'completeness': 0.85},
            'sina': {'accuracy': 0.78, 'timeliness': 0.85, 'completeness': 0.80},
            'xueqiu': {'accuracy': 0.75, 'timeliness': 0.80, 'completeness': 0.75},
            'tushare': {'accuracy': 0.90, 'timeliness': 0.70, 'completeness': 0.95},
            'akshare': {'accuracy': 0.70, 'timeliness': 0.75, 'completeness': 0.85}
        }
        
        # 质量历史记录
        self.quality_history = {}
        
        # 股票数据字段重要性权重
        self.field_importance = {
            'current_price': 1.0,      # 当前价格 - 最重要
            'volume': 0.8,             # 成交量
            'change_pct': 0.9,         # 涨跌幅
            'open': 0.7,               # 开盘价
            'high': 0.7,               # 最高价
            'low': 0.7,                # 最低价
            'prev_close': 0.6,         # 前收盘价
            'turnover': 0.5,           # 成交额
            'name': 0.3                # 股票名称
        }
        
        logger.info("数据质量分析器初始化完成")
        logger.info(f"   质量维度: {len(self.dimension_weights)} 个")
        logger.info(f"   数据源基准: {len(self.quality_benchmarks)} 个")

    def analyze_data_quality(self, source: str, data: Dict[str, Any], 
                            data_type: str = 'stock_price') -> QualityMetrics:
        """
        分析数据质量
        
        Args:
            source: 数据源名称
            data: 待分析的数据
            data_type: 数据类型
            
        Returns:
            质量指标结果
        """
        try:
            # 计算各维度质量评分
            completeness_score = self._calculate_completeness(data, data_type)
            accuracy_score = self._calculate_accuracy(source, data, data_type)
            timeliness_score = self._calculate_timeliness(data)
            consistency_score = self._calculate_consistency(data, data_type)
            validity_score = self._calculate_validity(data, data_type)
            reliability_score = self._calculate_reliability(source, data)
            
            # 计算综合评分
            overall_score = self._calculate_overall_score({
                QualityDimension.COMPLETENESS: completeness_score,
                QualityDimension.ACCURACY: accuracy_score,
                QualityDimension.TIMELINESS: timeliness_score,
                QualityDimension.CONSISTENCY: consistency_score,
                QualityDimension.VALIDITY: validity_score,
                QualityDimension.RELIABILITY: reliability_score
            })
            
            # 确定质量等级
            quality_grade = self._determine_quality_grade(overall_score)
            
            # 构造质量指标
            metrics = QualityMetrics(
                completeness=round(completeness_score, 3),
                accuracy=round(accuracy_score, 3),
                timeliness=round(timeliness_score, 3),
                consistency=round(consistency_score, 3),
                validity=round(validity_score, 3),
                reliability=round(reliability_score, 3),
                overall_score=round(overall_score, 3),
                quality_grade=quality_grade,
                details={
                    'source': source,
                    'data_type': data_type,
                    'analysis_time': datetime.now(),
                    'sample_size': len(data) if isinstance(data, dict) else 1
                }
            )
            
            # 更新历史记录
            self._update_quality_history(source, data_type, overall_score)
            
            logger.info(f"数据质量分析完成: {source} - {quality_grade} ({overall_score:.3f})")
            return metrics
            
        except Exception as e:
            logger.error(f"数据质量分析失败: {source} - {str(e)}")
            return self._create_default_metrics(source, data_type)

    def _calculate_completeness(self, data: Dict[str, Any], data_type: str) -> float:
        """计算完整性评分"""
        try:
            if not data:
                return 0.0
            
            if data_type == 'stock_price':
                return self._calculate_stock_completeness(data)
            elif data_type == 'news':
                return self._calculate_news_completeness(data)
            else:
                # 通用完整性计算
                return self._calculate_generic_completeness(data)
                
        except Exception as e:
            logger.debug(f"计算完整性失败: {e}")
            return 0.5

    def _calculate_stock_completeness(self, data: Dict[str, Any]) -> float:
        """计算股票数据完整性"""
        try:
            required_fields = ['current_price', 'volume', 'change_pct']
            optional_fields = ['open', 'high', 'low', 'prev_close', 'turnover', 'name']
            
            # 计算必需字段完整性
            required_score = 0.0
            for field in required_fields:
                if field in data and data[field] is not None and data[field] != '':
                    field_weight = self.field_importance.get(field, 0.5)
                    required_score += field_weight
            
            required_score /= sum(self.field_importance.get(f, 0.5) for f in required_fields)
            
            # 计算可选字段完整性
            optional_score = 0.0
            for field in optional_fields:
                if field in data and data[field] is not None and data[field] != '':
                    field_weight = self.field_importance.get(field, 0.3)
                    optional_score += field_weight
            
            optional_score /= sum(self.field_importance.get(f, 0.3) for f in optional_fields)
            
            # 综合完整性 (必需字段70%，可选字段30%)
            completeness = required_score * 0.7 + optional_score * 0.3
            
            return min(1.0, completeness)
            
        except Exception as e:
            logger.debug(f"计算股票完整性失败: {e}")
            return 0.5

    def _calculate_news_completeness(self, data: Dict[str, Any]) -> float:
        """计算新闻数据完整性"""
        try:
            required_fields = ['title']
            important_fields = ['summary', 'publish_time', 'source']
            optional_fields = ['url', 'relevance_score']
            
            scores = []
            
            # 必需字段
            for field in required_fields:
                if field in data and data[field] and str(data[field]).strip():
                    scores.append(1.0)
                else:
                    scores.append(0.0)
            
            # 重要字段  
            for field in important_fields:
                if field in data and data[field] and str(data[field]).strip():
                    scores.append(0.8)
                else:
                    scores.append(0.0)
            
            # 可选字段
            for field in optional_fields:
                if field in data and data[field]:
                    scores.append(0.5)
                else:
                    scores.append(0.0)
            
            return statistics.mean(scores) if scores else 0.0
            
        except Exception as e:
            logger.debug(f"计算新闻完整性失败: {e}")
            return 0.5

    def _calculate_generic_completeness(self, data: Dict[str, Any]) -> float:
        """计算通用数据完整性"""
        try:
            if not data:
                return 0.0
            
            total_fields = len(data)
            complete_fields = 0
            
            for key, value in data.items():
                if value is not None and str(value).strip():
                    complete_fields += 1
            
            return complete_fields / total_fields if total_fields > 0 else 0.0
            
        except Exception:
            return 0.5

    def _calculate_accuracy(self, source: str, data: Dict[str, Any], data_type: str) -> float:
        """计算准确性评分"""
        try:
            if data_type == 'stock_price':
                return self._calculate_stock_accuracy(source, data)
            elif data_type == 'news':
                return self._calculate_news_accuracy(source, data)
            else:
                # 基于基准的准确性评估
                benchmark = self.quality_benchmarks.get(source, {})
                return benchmark.get('accuracy', 0.5)
                
        except Exception as e:
            logger.debug(f"计算准确性失败: {e}")
            return 0.5

    def _calculate_stock_accuracy(self, source: str, data: Dict[str, Any]) -> float:
        """计算股票数据准确性"""
        try:
            accuracy_factors = []
            
            # 价格合理性检查
            current_price = data.get('current_price', 0)
            if current_price and current_price > 0:
                open_price = data.get('open', current_price)
                high_price = data.get('high', current_price)
                low_price = data.get('low', current_price)
                
                # 检查价格逻辑关系
                if low_price <= current_price <= high_price:
                    accuracy_factors.append(0.9)
                else:
                    accuracy_factors.append(0.3)
                
                # 检查价格变化幅度合理性
                change_pct = data.get('change_pct', 0)
                if abs(change_pct) <= 20:  # 涨跌幅在±20%内认为正常
                    accuracy_factors.append(0.8)
                elif abs(change_pct) <= 50:
                    accuracy_factors.append(0.5)
                else:
                    accuracy_factors.append(0.2)
            else:
                accuracy_factors.append(0.1)
            
            # 数值精度检查
            if self._check_price_precision(data):
                accuracy_factors.append(0.8)
            else:
                accuracy_factors.append(0.6)
            
            # 基于数据源历史准确性
            benchmark_accuracy = self.quality_benchmarks.get(source, {}).get('accuracy', 0.7)
            accuracy_factors.append(benchmark_accuracy)
            
            return statistics.mean(accuracy_factors)
            
        except Exception as e:
            logger.debug(f"计算股票准确性失败: {e}")
            return 0.5

    def _calculate_news_accuracy(self, source: str, data: Dict[str, Any]) -> float:
        """计算新闻数据准确性"""
        try:
            accuracy_factors = []
            
            # 标题质量检查
            title = data.get('title', '')
            if title:
                # 检查是否包含明显错误或垃圾信息
                if len(title) >= 10 and not re.search(r'^[a-zA-Z0-9\s]*$', title):
                    accuracy_factors.append(0.8)
                else:
                    accuracy_factors.append(0.6)
            
            # 相关性评分
            relevance_score = data.get('relevance_score', 0.5)
            accuracy_factors.append(relevance_score)
            
            # 时间戳合理性
            publish_time = data.get('publish_time', '')
            if publish_time:
                accuracy_factors.append(0.7)
            else:
                accuracy_factors.append(0.4)
            
            # 数据源可靠性
            benchmark_accuracy = self.quality_benchmarks.get(source, {}).get('accuracy', 0.6)
            accuracy_factors.append(benchmark_accuracy)
            
            return statistics.mean(accuracy_factors)
            
        except Exception as e:
            logger.debug(f"计算新闻准确性失败: {e}")
            return 0.5

    def _calculate_timeliness(self, data: Dict[str, Any]) -> float:
        """计算时效性评分"""
        try:
            current_time = datetime.now()
            
            # 查找时间戳字段
            timestamp_fields = ['timestamp', 'update_time', 'publish_time', 'time']
            data_timestamp = None
            
            for field in timestamp_fields:
                if field in data and data[field]:
                    try:
                        if isinstance(data[field], datetime):
                            data_timestamp = data[field]
                            break
                        elif isinstance(data[field], str):
                            # 尝试解析时间字符串
                            data_timestamp = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                            break
                    except:
                        continue
            
            if not data_timestamp:
                return 0.5  # 无时间戳，给中等评分
            
            # 计算时间差
            time_diff = current_time - data_timestamp
            hours_old = time_diff.total_seconds() / 3600
            
            # 时效性评分曲线
            if hours_old <= 0.5:      # 30分钟内
                return 1.0
            elif hours_old <= 2:      # 2小时内
                return 0.9
            elif hours_old <= 6:      # 6小时内
                return 0.7
            elif hours_old <= 24:     # 24小时内
                return 0.5
            elif hours_old <= 72:     # 3天内
                return 0.3
            else:                     # 3天以上
                return 0.1
                
        except Exception as e:
            logger.debug(f"计算时效性失败: {e}")
            return 0.5

    def _calculate_consistency(self, data: Dict[str, Any], data_type: str) -> float:
        """计算一致性评分"""
        try:
            if data_type == 'stock_price':
                return self._calculate_stock_consistency(data)
            else:
                return self._calculate_generic_consistency(data)
                
        except Exception as e:
            logger.debug(f"计算一致性失败: {e}")
            return 0.5

    def _calculate_stock_consistency(self, data: Dict[str, Any]) -> float:
        """计算股票数据一致性"""
        try:
            consistency_checks = []
            
            # 价格关系一致性
            current_price = data.get('current_price')
            open_price = data.get('open')
            high_price = data.get('high')
            low_price = data.get('low')
            prev_close = data.get('prev_close')
            
            if all(p is not None and p > 0 for p in [current_price, open_price, high_price, low_price]):
                # 检查 low <= current_price <= high
                if low_price <= current_price <= high_price:
                    consistency_checks.append(1.0)
                else:
                    consistency_checks.append(0.2)
                
                # 检查 low <= open <= high
                if low_price <= open_price <= high_price:
                    consistency_checks.append(1.0)
                else:
                    consistency_checks.append(0.2)
            
            # 涨跌幅计算一致性
            if current_price and prev_close and prev_close > 0:
                calculated_change_pct = ((current_price - prev_close) / prev_close) * 100
                reported_change_pct = data.get('change_pct', calculated_change_pct)
                
                # 允许0.1%的误差
                if abs(calculated_change_pct - reported_change_pct) <= 0.1:
                    consistency_checks.append(1.0)
                elif abs(calculated_change_pct - reported_change_pct) <= 0.5:
                    consistency_checks.append(0.7)
                else:
                    consistency_checks.append(0.3)
            
            # 成交量和成交额一致性
            volume = data.get('volume')
            turnover = data.get('turnover')
            if volume and turnover and current_price:
                # 简单检查：成交额应该接近成交量*价格
                estimated_turnover = volume * current_price
                if turnover > 0:
                    ratio = min(estimated_turnover, turnover) / max(estimated_turnover, turnover)
                    if ratio >= 0.8:
                        consistency_checks.append(0.8)
                    else:
                        consistency_checks.append(0.5)
            
            return statistics.mean(consistency_checks) if consistency_checks else 0.5
            
        except Exception as e:
            logger.debug(f"计算股票一致性失败: {e}")
            return 0.5

    def _calculate_generic_consistency(self, data: Dict[str, Any]) -> float:
        """计算通用数据一致性"""
        try:
            # 基于数据格式一致性
            consistency_score = 0.8  # 基础分数
            
            # 检查数据类型一致性
            numeric_fields = []
            string_fields = []
            
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(key)
                elif isinstance(value, str):
                    string_fields.append(key)
            
            # 简单的一致性评估
            if len(data) > 0:
                return consistency_score
            else:
                return 0.0
                
        except Exception:
            return 0.5

    def _calculate_validity(self, data: Dict[str, Any], data_type: str) -> float:
        """计算有效性评分"""
        try:
            if data_type == 'stock_price':
                return self._calculate_stock_validity(data)
            elif data_type == 'news':
                return self._calculate_news_validity(data)
            else:
                return self._calculate_generic_validity(data)
                
        except Exception as e:
            logger.debug(f"计算有效性失败: {e}")
            return 0.5

    def _calculate_stock_validity(self, data: Dict[str, Any]) -> float:
        """计算股票数据有效性"""
        try:
            validity_checks = []
            
            # 价格有效性
            current_price = data.get('current_price')
            if current_price is not None:
                if 0 < current_price < 1000000:  # 合理价格范围
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.1)
            
            # 成交量有效性
            volume = data.get('volume')
            if volume is not None:
                if volume >= 0:  # 成交量不能为负
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.0)
            
            # 涨跌幅有效性
            change_pct = data.get('change_pct')
            if change_pct is not None:
                if -20 <= change_pct <= 20:  # 正常涨跌幅范围
                    validity_checks.append(1.0)
                elif -50 <= change_pct <= 50:  # 极端但可能的涨跌幅
                    validity_checks.append(0.7)
                else:
                    validity_checks.append(0.2)
            
            # 股票代码有效性
            symbol = data.get('symbol', '')
            if symbol:
                if re.match(r'^[0-9]{6}$', symbol):  # A股6位数字代码
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.7)  # 可能是其他市场代码
            
            return statistics.mean(validity_checks) if validity_checks else 0.5
            
        except Exception as e:
            logger.debug(f"计算股票有效性失败: {e}")
            return 0.5

    def _calculate_news_validity(self, data: Dict[str, Any]) -> float:
        """计算新闻数据有效性"""
        try:
            validity_checks = []
            
            # 标题有效性
            title = data.get('title', '')
            if title:
                if len(title.strip()) >= 5:
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.3)
            
            # URL有效性
            url = data.get('url', '')
            if url:
                if url.startswith(('http://', 'https://')):
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.5)
            
            # 相关性评分有效性
            relevance_score = data.get('relevance_score')
            if relevance_score is not None:
                if 0 <= relevance_score <= 1:
                    validity_checks.append(1.0)
                else:
                    validity_checks.append(0.3)
            
            return statistics.mean(validity_checks) if validity_checks else 0.5
            
        except Exception as e:
            logger.debug(f"计算新闻有效性失败: {e}")
            return 0.5

    def _calculate_generic_validity(self, data: Dict[str, Any]) -> float:
        """计算通用数据有效性"""
        try:
            if not data:
                return 0.0
            
            valid_fields = 0
            total_fields = len(data)
            
            for key, value in data.items():
                if value is not None and str(value).strip():
                    valid_fields += 1
            
            return valid_fields / total_fields if total_fields > 0 else 0.0
            
        except Exception:
            return 0.5

    def _calculate_reliability(self, source: str, data: Dict[str, Any]) -> float:
        """计算可靠性评分"""
        try:
            # 基于数据源历史表现
            benchmark = self.quality_benchmarks.get(source, {})
            base_reliability = benchmark.get('accuracy', 0.5)
            
            # 基于数据完整度调整
            completeness_bonus = self._calculate_generic_completeness(data) * 0.2
            
            # 基于数据新鲜度调整
            timeliness_bonus = self._calculate_timeliness(data) * 0.1
            
            reliability = base_reliability + completeness_bonus + timeliness_bonus
            
            return min(1.0, reliability)
            
        except Exception as e:
            logger.debug(f"计算可靠性失败: {e}")
            return 0.5

    def _calculate_overall_score(self, dimension_scores: Dict[QualityDimension, float]) -> float:
        """计算综合质量评分"""
        try:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for dimension, score in dimension_scores.items():
                weight = self.dimension_weights.get(dimension, 0.1)
                weighted_sum += score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception:
            return 0.5

    def _determine_quality_grade(self, overall_score: float) -> str:
        """确定质量等级"""
        if overall_score >= 0.9:
            return "优秀"
        elif overall_score >= 0.7:
            return "良好"
        elif overall_score >= 0.5:
            return "一般"
        else:
            return "较差"

    def _check_price_precision(self, data: Dict[str, Any]) -> bool:
        """检查价格精度"""
        try:
            price_fields = ['current_price', 'open', 'high', 'low', 'prev_close']
            
            for field in price_fields:
                price = data.get(field)
                if price and isinstance(price, (int, float)):
                    # 检查小数位数是否合理（通常2位小数）
                    decimal_places = len(str(price).split('.')[1]) if '.' in str(price) else 0
                    if decimal_places > 4:  # 超过4位小数认为精度异常
                        return False
            
            return True
            
        except Exception:
            return True

    def _update_quality_history(self, source: str, data_type: str, score: float):
        """更新质量历史记录"""
        try:
            key = f"{source}_{data_type}"
            
            if key not in self.quality_history:
                self.quality_history[key] = []
            
            # 保持最近100个评分记录
            history = self.quality_history[key]
            history.append({
                'score': score,
                'timestamp': datetime.now()
            })
            
            if len(history) > 100:
                history.pop(0)
                
        except Exception as e:
            logger.debug(f"更新质量历史失败: {e}")

    def _create_default_metrics(self, source: str, data_type: str) -> QualityMetrics:
        """创建默认质量指标"""
        return QualityMetrics(
            completeness=0.5,
            accuracy=0.5,
            timeliness=0.5,
            consistency=0.5,
            validity=0.5,
            reliability=0.5,
            overall_score=0.5,
            quality_grade="一般",
            details={
                'source': source,
                'data_type': data_type,
                'analysis_time': datetime.now(),
                'error': True
            }
        )

    def get_quality_summary(self, source: str = None) -> Dict[str, Any]:
        """获取质量汇总报告"""
        try:
            summary = {
                'timestamp': datetime.now(),
                'total_analyses': len(self.quality_history),
                'source_summary': {},
                'overall_trends': {}
            }
            
            if source:
                # 特定数据源的质量汇总
                source_histories = {k: v for k, v in self.quality_history.items() if k.startswith(source)}
                summary['source_summary'][source] = self._analyze_source_quality_trend(source_histories)
            else:
                # 所有数据源的质量汇总
                for key, history in self.quality_history.items():
                    source_name = key.split('_')[0]
                    if source_name not in summary['source_summary']:
                        summary['source_summary'][source_name] = []
                    
                    if history:
                        recent_scores = [h['score'] for h in history[-10:]]  # 最近10次
                        avg_score = statistics.mean(recent_scores)
                        summary['source_summary'][source_name].append({
                            'data_type': key.split('_', 1)[1],
                            'avg_quality': round(avg_score, 3),
                            'sample_count': len(history)
                        })
            
            return summary
            
        except Exception as e:
            logger.error(f"生成质量汇总失败: {e}")
            return {'error': str(e)}

    def _analyze_source_quality_trend(self, source_histories: Dict[str, List]) -> Dict[str, Any]:
        """分析数据源质量趋势"""
        try:
            if not source_histories:
                return {}
            
            trends = {}
            for key, history in source_histories.items():
                if len(history) >= 2:
                    recent_scores = [h['score'] for h in history[-10:]]
                    older_scores = [h['score'] for h in history[-20:-10]] if len(history) >= 20 else []
                    
                    current_avg = statistics.mean(recent_scores)
                    previous_avg = statistics.mean(older_scores) if older_scores else current_avg
                    
                    trend = "上升" if current_avg > previous_avg + 0.05 else "下降" if current_avg < previous_avg - 0.05 else "稳定"
                    
                    trends[key] = {
                        'current_quality': round(current_avg, 3),
                        'trend': trend,
                        'change': round(current_avg - previous_avg, 3)
                    }
            
            return trends
            
        except Exception:
            return {}


# 全局实例
_quality_analyzer = None

def get_quality_analyzer() -> DataQualityAnalyzer:
    """获取数据质量分析器实例"""
    global _quality_analyzer
    if _quality_analyzer is None:
        _quality_analyzer = DataQualityAnalyzer()
    return _quality_analyzer


# 便捷函数
def analyze_stock_quality(source: str, stock_data: Dict[str, Any]) -> QualityMetrics:
    """分析股票数据质量"""
    analyzer = get_quality_analyzer()
    return analyzer.analyze_data_quality(source, stock_data, 'stock_price')

def analyze_news_quality(source: str, news_data: Dict[str, Any]) -> QualityMetrics:
    """分析新闻数据质量"""
    analyzer = get_quality_analyzer()
    return analyzer.analyze_data_quality(source, news_data, 'news')