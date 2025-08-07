#!/usr/bin/env python3
"""
综合评分系统
整合数据融合、质量评分、情感分析等多个维度，生成综合投资评分
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
from enum import Enum
import math

# 导入相关模块
from .data_fusion_engine import get_fusion_engine, DataPoint, DataSourceType
from .data_quality_analyzer import get_quality_analyzer
from .sentiment_analyzer import SentimentAnalyzer
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class ScoreCategory(Enum):
    """评分类别"""
    TECHNICAL = "technical"         # 技术面评分
    FUNDAMENTAL = "fundamental"     # 基本面评分
    SENTIMENT = "sentiment"         # 情绪面评分
    QUALITY = "quality"            # 数据质量评分
    RISK = "risk"                  # 风险评分
    OVERALL = "overall"            # 综合评分


@dataclass
class CategoryScore:
    """类别评分"""
    category: ScoreCategory
    score: float                   # 评分 (0-100)
    confidence: float              # 置信度 (0-1)
    weight: float                  # 权重 (0-1)
    components: Dict[str, float]   # 子组件评分
    details: Dict[str, Any]        # 详细信息


@dataclass
class ComprehensiveScore:
    """综合评分结果"""
    symbol: str                    # 股票代码
    overall_score: float           # 综合评分 (0-100)
    grade: str                     # 评级 (A+/A/B+/B/C+/C/D)
    confidence: float              # 综合置信度 (0-1)
    category_scores: Dict[ScoreCategory, CategoryScore]  # 各类别评分
    recommendation: str            # 投资建议
    risk_level: str               # 风险级别
    key_factors: List[str]        # 关键因素
    timestamp: datetime           # 评分时间
    metadata: Dict[str, Any]      # 元数据


class ComprehensiveScoringSystem:
    """综合评分系统"""

    def __init__(self):
        """初始化综合评分系统"""
        # 各类别权重配置
        self.category_weights = {
            ScoreCategory.TECHNICAL: 0.25,      # 技术面 25%
            ScoreCategory.FUNDAMENTAL: 0.30,    # 基本面 30%
            ScoreCategory.SENTIMENT: 0.20,      # 情绪面 20%
            ScoreCategory.QUALITY: 0.15,        # 数据质量 15%
            ScoreCategory.RISK: 0.10           # 风险 10%
        }
        
        # 评级标准
        self.grade_thresholds = {
            90: "A+", 85: "A", 80: "A-",
            75: "B+", 70: "B", 65: "B-",
            60: "C+", 55: "C", 50: "C-",
            0: "D"
        }
        
        # 初始化依赖组件
        self.fusion_engine = get_fusion_engine()
        self.quality_analyzer = get_quality_analyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # 历史评分记录
        self.score_history = {}
        
        logger.info("综合评分系统初始化完成")
        logger.info(f"   评分类别: {len(self.category_weights)} 个")
        logger.info(f"   评级档次: {len(self.grade_thresholds)} 个")

    def calculate_comprehensive_score(self, symbol: str, 
                                    stock_data: Dict[str, Any],
                                    news_data: List[Dict[str, Any]] = None,
                                    additional_data: Dict[str, Any] = None) -> ComprehensiveScore:
        """
        计算综合评分
        
        Args:
            symbol: 股票代码
            stock_data: 股票数据 (多源数据)
            news_data: 新闻数据
            additional_data: 额外数据
            
        Returns:
            综合评分结果
        """
        try:
            logger.info(f"开始计算综合评分: {symbol}")
            
            # 计算各类别评分
            category_scores = {}
            
            # 技术面评分
            category_scores[ScoreCategory.TECHNICAL] = self._calculate_technical_score(symbol, stock_data)
            
            # 基本面评分
            category_scores[ScoreCategory.FUNDAMENTAL] = self._calculate_fundamental_score(symbol, stock_data, additional_data)
            
            # 情绪面评分
            category_scores[ScoreCategory.SENTIMENT] = self._calculate_sentiment_score(symbol, news_data)
            
            # 数据质量评分
            category_scores[ScoreCategory.QUALITY] = self._calculate_quality_score(symbol, stock_data, news_data)
            
            # 风险评分
            category_scores[ScoreCategory.RISK] = self._calculate_risk_score(symbol, stock_data)
            
            # 计算综合评分
            overall_score, overall_confidence = self._calculate_overall_score(category_scores)
            
            # 确定评级
            grade = self._determine_grade(overall_score)
            
            # 生成投资建议
            recommendation = self._generate_recommendation(overall_score, category_scores)
            
            # 计算风险级别
            risk_level = self._calculate_risk_level(category_scores)
            
            # 提取关键因素
            key_factors = self._extract_key_factors(category_scores)
            
            # 构造综合评分结果
            comprehensive_score = ComprehensiveScore(
                symbol=symbol,
                overall_score=round(overall_score, 2),
                grade=grade,
                confidence=round(overall_confidence, 3),
                category_scores=category_scores,
                recommendation=recommendation,
                risk_level=risk_level,
                key_factors=key_factors,
                timestamp=datetime.now(),
                metadata={
                    'data_sources': list(stock_data.keys()) if isinstance(stock_data, dict) else [],
                    'news_count': len(news_data) if news_data else 0,
                    'version': '3.0'
                }
            )
            
            # 更新历史记录
            self._update_score_history(symbol, comprehensive_score)
            
            logger.info(f"综合评分计算完成: {symbol} - {grade} ({overall_score:.2f})")
            return comprehensive_score
            
        except Exception as e:
            logger.error(f"综合评分计算失败: {symbol} - {str(e)}")
            return self._create_default_score(symbol, str(e))

    def _calculate_technical_score(self, symbol: str, stock_data: Dict[str, Any]) -> CategoryScore:
        """计算技术面评分"""
        try:
            components = {}
            technical_factors = []
            
            # 如果是多源数据，先进行融合
            if isinstance(stock_data, dict) and any(isinstance(v, dict) for v in stock_data.values()):
                # 多源数据融合
                fusion_result = self.fusion_engine.fuse_data_points(
                    self._convert_to_data_points(stock_data, DataSourceType.REAL_TIME_PRICE),
                    'adaptive_fusion'
                )
                if fusion_result.fused_value:
                    main_data = fusion_result.metadata.get('primary_data', {})
                else:
                    main_data = next(iter(stock_data.values())) if stock_data else {}
            else:
                main_data = stock_data
            
            # 价格动量评分
            change_pct = main_data.get('change_pct', 0)
            if change_pct > 5:
                momentum_score = 85
            elif change_pct > 2:
                momentum_score = 75
            elif change_pct > 0:
                momentum_score = 65
            elif change_pct > -2:
                momentum_score = 55
            elif change_pct > -5:
                momentum_score = 45
            else:
                momentum_score = 30
            
            components['momentum'] = momentum_score
            technical_factors.append(f"价格动量: {change_pct:+.2f}%")
            
            # 成交量评分 
            volume = main_data.get('volume', 0)
            turnover = main_data.get('turnover', 0)
            
            # 简化的成交量评分
            if volume > 0:
                if turnover and main_data.get('current_price'):
                    volume_ratio = turnover / (volume * main_data['current_price'])
                    if 0.8 <= volume_ratio <= 1.2:  # 成交量与价格匹配度
                        volume_score = 80
                    else:
                        volume_score = 60
                else:
                    volume_score = 70  # 有成交量但无法验证
            else:
                volume_score = 30
            
            components['volume'] = volume_score
            technical_factors.append(f"成交量活跃度: {volume:,}")
            
            # 价格位置评分 (相对于高低点的位置)
            current_price = main_data.get('current_price', 0)
            high_price = main_data.get('high', current_price)
            low_price = main_data.get('low', current_price)
            
            if high_price > low_price:
                price_position = (current_price - low_price) / (high_price - low_price)
                if price_position >= 0.8:
                    position_score = 85  # 接近高点
                elif price_position >= 0.6:
                    position_score = 75
                elif price_position >= 0.4:
                    position_score = 65
                elif price_position >= 0.2:
                    position_score = 45
                else:
                    position_score = 35  # 接近低点
            else:
                price_position = 0.5  # 无法判断时设为中位
                position_score = 50  # 无法判断
            
            components['position'] = position_score
            technical_factors.append(f"价格位置: {price_position:.1%}")
            
            # 计算技术面综合评分
            technical_score = statistics.mean(components.values())
            confidence = len([k for k, v in main_data.items() if v is not None]) / 10  # 基于数据完整度
            
            return CategoryScore(
                category=ScoreCategory.TECHNICAL,
                score=round(technical_score, 2),
                confidence=min(1.0, confidence),
                weight=self.category_weights[ScoreCategory.TECHNICAL],
                components=components,
                details={
                    'factors': technical_factors,
                    'data_completeness': confidence
                }
            )
            
        except Exception as e:
            logger.error(f"技术面评分失败: {e}")
            return self._create_default_category_score(ScoreCategory.TECHNICAL)

    def _calculate_fundamental_score(self, symbol: str, stock_data: Dict[str, Any], 
                                   additional_data: Dict[str, Any] = None) -> CategoryScore:
        """计算基本面评分"""
        try:
            components = {}
            fundamental_factors = []
            
            # 基本面数据通常需要额外数据源，这里做简化处理
            main_data = self._get_main_data(stock_data)
            
            # 市值规模评分 (基于价格和成交额估算)
            current_price = main_data.get('current_price', 0)
            turnover = main_data.get('turnover', 0)
            
            if current_price > 0 and turnover > 0:
                # 简单估算流通市值
                estimated_shares = turnover / current_price if current_price > 0 else 0
                estimated_market_cap = estimated_shares * current_price
                
                if estimated_market_cap > 10000000000:  # 100亿以上
                    market_cap_score = 80  # 大盘股
                elif estimated_market_cap > 5000000000:   # 50亿以上
                    market_cap_score = 75  # 中大盘股
                elif estimated_market_cap > 1000000000:   # 10亿以上
                    market_cap_score = 70  # 中盘股
                else:
                    market_cap_score = 60  # 小盘股
                    
                fundamental_factors.append(f"估算市值: {estimated_market_cap/100000000:.1f}亿")
            else:
                market_cap_score = 50
            
            components['market_cap'] = market_cap_score
            
            # 价格合理性评分
            if current_price > 0:
                if current_price < 10:
                    price_level_score = 85  # 低价股，可能有成长空间
                elif current_price < 30:
                    price_level_score = 75  # 中价股
                elif current_price < 100:
                    price_level_score = 65  # 高价股
                else:
                    price_level_score = 50  # 超高价股
                    
                fundamental_factors.append(f"股价水平: {current_price:.2f}元")
            else:
                price_level_score = 30
                
            components['price_level'] = price_level_score
            
            # 行业地位评分 (基于成交活跃度)
            volume = main_data.get('volume', 0)
            if volume > 100000000:  # 成交量超过1亿
                industry_score = 80
            elif volume > 50000000:   # 成交量超过5000万
                industry_score = 70
            elif volume > 10000000:   # 成交量超过1000万
                industry_score = 60
            else:
                industry_score = 50
                
            components['industry_position'] = industry_score
            fundamental_factors.append(f"流动性水平: {volume:,}股")
            
            # 如果有额外的基本面数据，可以在这里处理
            if additional_data:
                for key, value in additional_data.items():
                    if key in ['pe_ratio', 'pb_ratio', 'revenue_growth']:
                        # 处理财务指标
                        pass
            
            # 计算基本面综合评分
            fundamental_score = statistics.mean(components.values())
            confidence = 0.6  # 基本面评分置信度相对较低，因为缺少详细财务数据
            
            return CategoryScore(
                category=ScoreCategory.FUNDAMENTAL,
                score=round(fundamental_score, 2),
                confidence=confidence,
                weight=self.category_weights[ScoreCategory.FUNDAMENTAL],
                components=components,
                details={
                    'factors': fundamental_factors,
                    'note': '基于基础数据估算，建议结合财务报告'
                }
            )
            
        except Exception as e:
            logger.error(f"基本面评分失败: {e}")
            return self._create_default_category_score(ScoreCategory.FUNDAMENTAL)

    def _calculate_sentiment_score(self, symbol: str, 
                                 news_data: List[Dict[str, Any]] = None) -> CategoryScore:
        """计算情绪面评分"""
        try:
            components = {}
            sentiment_factors = []
            
            if not news_data:
                # 无新闻数据时的默认评分
                return CategoryScore(
                    category=ScoreCategory.SENTIMENT,
                    score=50.0,
                    confidence=0.3,
                    weight=self.category_weights[ScoreCategory.SENTIMENT],
                    components={'no_data': 50.0},
                    details={'factors': ['无新闻数据'], 'note': '建议补充新闻和社交媒体数据'}
                )
            
            # 使用情感分析器分析新闻
            sentiment_result = self.sentiment_analyzer.analyze_news_sentiment(news_data)
            
            # 新闻情感评分
            overall_sentiment = sentiment_result.get('overall_sentiment', 0)
            news_sentiment_score = 50 + overall_sentiment * 50  # 转换到0-100区间
            components['news_sentiment'] = news_sentiment_score
            sentiment_factors.append(f"新闻情感: {overall_sentiment:.2f}")
            
            # 新闻数量和质量评分
            news_count = sentiment_result.get('total_count', 0)
            if news_count >= 20:
                coverage_score = 85
            elif news_count >= 10:
                coverage_score = 75
            elif news_count >= 5:
                coverage_score = 65
            else:
                coverage_score = 50
                
            components['news_coverage'] = coverage_score
            sentiment_factors.append(f"新闻覆盖: {news_count}条")
            
            # 情感分布评分
            positive_ratio = sentiment_result.get('positive_ratio', 0)
            negative_ratio = sentiment_result.get('negative_ratio', 0)
            neutral_ratio = sentiment_result.get('neutral_ratio', 1)
            
            if positive_ratio > 0.6:
                sentiment_distribution_score = 85
            elif positive_ratio > 0.4:
                sentiment_distribution_score = 70
            elif negative_ratio > 0.6:
                sentiment_distribution_score = 30
            else:
                sentiment_distribution_score = 55
                
            components['sentiment_distribution'] = sentiment_distribution_score
            sentiment_factors.append(f"积极比例: {positive_ratio:.1%}")
            
            # 计算情绪面综合评分
            sentiment_score = statistics.mean(components.values())
            confidence = sentiment_result.get('confidence', 0.5)
            
            return CategoryScore(
                category=ScoreCategory.SENTIMENT,
                score=round(sentiment_score, 2),
                confidence=confidence,
                weight=self.category_weights[ScoreCategory.SENTIMENT],
                components=components,
                details={
                    'factors': sentiment_factors,
                    'sentiment_details': sentiment_result
                }
            )
            
        except Exception as e:
            logger.error(f"情绪面评分失败: {e}")
            return self._create_default_category_score(ScoreCategory.SENTIMENT)

    def _calculate_quality_score(self, symbol: str, stock_data: Dict[str, Any],
                               news_data: List[Dict[str, Any]] = None) -> CategoryScore:
        """计算数据质量评分"""
        try:
            components = {}
            quality_factors = []
            
            # 股票数据质量评分
            stock_quality_scores = []
            
            if isinstance(stock_data, dict):
                for source, data in stock_data.items():
                    if isinstance(data, dict):
                        quality_metrics = self.quality_analyzer.analyze_data_quality(
                            source, data, 'stock_price'
                        )
                        stock_quality_scores.append(quality_metrics.overall_score * 100)
                        quality_factors.append(f"{source}: {quality_metrics.quality_grade}")
            
            if stock_quality_scores:
                avg_stock_quality = statistics.mean(stock_quality_scores)
                components['stock_data_quality'] = avg_stock_quality
            else:
                components['stock_data_quality'] = 50
            
            # 新闻数据质量评分
            if news_data:
                news_quality_scores = []
                for news in news_data[:5]:  # 检查前5条新闻
                    source = news.get('source', 'unknown')
                    quality_metrics = self.quality_analyzer.analyze_data_quality(
                        source, news, 'news'
                    )
                    news_quality_scores.append(quality_metrics.overall_score * 100)
                
                if news_quality_scores:
                    avg_news_quality = statistics.mean(news_quality_scores)
                    components['news_data_quality'] = avg_news_quality
                    quality_factors.append(f"新闻质量平均: {avg_news_quality:.1f}")
            else:
                components['news_data_quality'] = 50
                quality_factors.append("无新闻数据")
            
            # 数据源多样性评分
            data_source_count = len(stock_data) if isinstance(stock_data, dict) else 1
            if data_source_count >= 3:
                diversity_score = 85
            elif data_source_count >= 2:
                diversity_score = 75
            else:
                diversity_score = 60
                
            components['source_diversity'] = diversity_score
            quality_factors.append(f"数据源数量: {data_source_count}")
            
            # 计算数据质量综合评分
            quality_score = statistics.mean(components.values())
            confidence = min(1.0, data_source_count / 5)  # 基于数据源数量的置信度
            
            return CategoryScore(
                category=ScoreCategory.QUALITY,
                score=round(quality_score, 2),
                confidence=confidence,
                weight=self.category_weights[ScoreCategory.QUALITY],
                components=components,
                details={
                    'factors': quality_factors,
                    'data_source_count': data_source_count
                }
            )
            
        except Exception as e:
            logger.error(f"数据质量评分失败: {e}")
            return self._create_default_category_score(ScoreCategory.QUALITY)

    def _calculate_risk_score(self, symbol: str, stock_data: Dict[str, Any]) -> CategoryScore:
        """计算风险评分"""
        try:
            components = {}
            risk_factors = []
            
            main_data = self._get_main_data(stock_data)
            
            # 价格波动风险
            change_pct = abs(main_data.get('change_pct', 0))
            if change_pct > 10:
                volatility_risk_score = 30  # 高波动 = 高风险 = 低评分
                risk_level = "高"
            elif change_pct > 5:
                volatility_risk_score = 50
                risk_level = "中高"
            elif change_pct > 2:
                volatility_risk_score = 70
                risk_level = "中等"
            else:
                volatility_risk_score = 85  # 低波动 = 低风险 = 高评分
                risk_level = "低"
            
            components['volatility_risk'] = volatility_risk_score
            risk_factors.append(f"价格波动: {change_pct:.2f}% ({risk_level}风险)")
            
            # 流动性风险
            volume = main_data.get('volume', 0)
            if volume > 50000000:  # 成交量大于5000万
                liquidity_risk_score = 85  # 高流动性 = 低风险
            elif volume > 10000000:  # 成交量大于1000万
                liquidity_risk_score = 70
            elif volume > 1000000:   # 成交量大于100万
                liquidity_risk_score = 50
            else:
                liquidity_risk_score = 30  # 低流动性 = 高风险
            
            components['liquidity_risk'] = liquidity_risk_score
            risk_factors.append(f"流动性: {volume:,}股")
            
            # 价格水平风险
            current_price = main_data.get('current_price', 0)
            if current_price < 5:
                price_level_risk_score = 40  # 低价股风险较高
            elif current_price < 20:
                price_level_risk_score = 70
            elif current_price < 100:
                price_level_risk_score = 80
            else:
                price_level_risk_score = 60  # 超高价股也有风险
            
            components['price_level_risk'] = price_level_risk_score
            risk_factors.append(f"价格水平: {current_price:.2f}元")
            
            # 计算风险综合评分
            risk_score = statistics.mean(components.values())
            confidence = 0.7  # 风险评分相对可靠
            
            return CategoryScore(
                category=ScoreCategory.RISK,
                score=round(risk_score, 2),
                confidence=confidence,
                weight=self.category_weights[ScoreCategory.RISK],
                components=components,
                details={
                    'factors': risk_factors,
                    'overall_risk_level': risk_level
                }
            )
            
        except Exception as e:
            logger.error(f"风险评分失败: {e}")
            return self._create_default_category_score(ScoreCategory.RISK)

    def _calculate_overall_score(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> Tuple[float, float]:
        """计算综合评分"""
        try:
            weighted_sum = 0.0
            total_weight = 0.0
            total_confidence = 0.0
            
            for category, score_obj in category_scores.items():
                weight = score_obj.weight
                score = score_obj.score
                confidence = score_obj.confidence
                
                weighted_sum += score * weight * confidence  # 考虑置信度权重
                total_weight += weight * confidence
                total_confidence += confidence
            
            overall_score = weighted_sum / total_weight if total_weight > 0 else 50.0
            overall_confidence = total_confidence / len(category_scores) if category_scores else 0.0
            
            return overall_score, overall_confidence
            
        except Exception as e:
            logger.error(f"计算综合评分失败: {e}")
            return 50.0, 0.5

    def _determine_grade(self, score: float) -> str:
        """确定评级"""
        for threshold, grade in sorted(self.grade_thresholds.items(), reverse=True):
            if score >= threshold:
                return grade
        return "D"

    def _generate_recommendation(self, overall_score: float, 
                               category_scores: Dict[ScoreCategory, CategoryScore]) -> str:
        """生成投资建议"""
        try:
            if overall_score >= 80:
                base_recommendation = "强烈推荐"
            elif overall_score >= 70:
                base_recommendation = "推荐"
            elif overall_score >= 60:
                base_recommendation = "谨慎推荐"
            elif overall_score >= 50:
                base_recommendation = "观望"
            else:
                base_recommendation = "不推荐"
            
            # 基于具体类别评分调整建议
            risk_score = category_scores.get(ScoreCategory.RISK, None)
            if risk_score and risk_score.score < 40:
                base_recommendation += " (高风险)"
            
            sentiment_score = category_scores.get(ScoreCategory.SENTIMENT, None)
            if sentiment_score and sentiment_score.score > 80:
                base_recommendation += " (市场情绪积极)"
            elif sentiment_score and sentiment_score.score < 40:
                base_recommendation += " (市场情绪谨慎)"
            
            return base_recommendation
            
        except Exception:
            return "数据不足，建议谨慎"

    def _calculate_risk_level(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> str:
        """计算风险级别"""
        try:
            risk_score = category_scores.get(ScoreCategory.RISK, None)
            if not risk_score:
                return "中等"
            
            if risk_score.score >= 80:
                return "低"
            elif risk_score.score >= 60:
                return "中等"
            elif risk_score.score >= 40:
                return "中高"
            else:
                return "高"
                
        except Exception:
            return "中等"

    def _extract_key_factors(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> List[str]:
        """提取关键因素"""
        try:
            key_factors = []
            
            # 找出最重要的正面和负面因素
            sorted_categories = sorted(
                category_scores.items(),
                key=lambda x: x[1].score,
                reverse=True
            )
            
            # 最强项
            if sorted_categories:
                best_category = sorted_categories[0]
                key_factors.append(f"优势: {best_category[0].value}评分 {best_category[1].score:.1f}")
            
            # 最弱项
            if len(sorted_categories) > 1:
                worst_category = sorted_categories[-1]
                if worst_category[1].score < 60:
                    key_factors.append(f"关注: {worst_category[0].value}评分较低 {worst_category[1].score:.1f}")
            
            # 添加具体因素
            for category, score_obj in category_scores.items():
                if hasattr(score_obj.details, 'get') and score_obj.details.get('factors'):
                    factors = score_obj.details['factors'][:2]  # 取前2个因素
                    key_factors.extend(factors)
            
            return key_factors[:5]  # 限制为5个关键因素
            
        except Exception as e:
            logger.error(f"提取关键因素失败: {e}")
            return ["数据不足"]

    def _get_main_data(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取主要数据"""
        if isinstance(stock_data, dict) and any(isinstance(v, dict) for v in stock_data.values()):
            # 多源数据，选择第一个
            return next(iter(stock_data.values()))
        else:
            return stock_data

    def _convert_to_data_points(self, stock_data: Dict[str, Any], 
                              data_type: DataSourceType) -> List[DataPoint]:
        """转换为数据点"""
        data_points = []
        
        for source, data in stock_data.items():
            if isinstance(data, dict) and 'current_price' in data:
                dp = DataPoint(
                    source=source,
                    data_type=data_type,
                    value=data['current_price'],
                    timestamp=datetime.now(),
                    quality_score=0.8,
                    confidence=0.8,
                    latency_ms=100,
                    metadata={'raw_data': data}
                )
                data_points.append(dp)
        
        return data_points

    def _create_default_category_score(self, category: ScoreCategory) -> CategoryScore:
        """创建默认类别评分"""
        return CategoryScore(
            category=category,
            score=50.0,
            confidence=0.3,
            weight=self.category_weights.get(category, 0.1),
            components={'default': 50.0},
            details={'error': True, 'factors': [f'{category.value}评分失败']}
        )

    def _create_default_score(self, symbol: str, error_msg: str) -> ComprehensiveScore:
        """创建默认综合评分"""
        default_categories = {}
        for category in ScoreCategory:
            if category != ScoreCategory.OVERALL:
                default_categories[category] = self._create_default_category_score(category)
        
        return ComprehensiveScore(
            symbol=symbol,
            overall_score=50.0,
            grade="C",
            confidence=0.3,
            category_scores=default_categories,
            recommendation="数据不足，建议谨慎",
            risk_level="未知",
            key_factors=[f"评分失败: {error_msg}"],
            timestamp=datetime.now(),
            metadata={'error': True, 'error_msg': error_msg}
        )

    def _update_score_history(self, symbol: str, score: ComprehensiveScore):
        """更新评分历史"""
        try:
            if symbol not in self.score_history:
                self.score_history[symbol] = []
            
            history = self.score_history[symbol]
            history.append({
                'timestamp': score.timestamp,
                'overall_score': score.overall_score,
                'grade': score.grade,
                'recommendation': score.recommendation
            })
            
            # 保持最近50条记录
            if len(history) > 50:
                history.pop(0)
                
        except Exception as e:
            logger.debug(f"更新评分历史失败: {e}")

    def get_score_trend(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """获取评分趋势"""
        try:
            if symbol not in self.score_history:
                return {'error': '无历史数据'}
            
            history = self.score_history[symbol]
            cutoff_time = datetime.now() - timedelta(days=days)
            
            recent_scores = [
                h for h in history
                if h['timestamp'] >= cutoff_time
            ]
            
            if not recent_scores:
                return {'error': f'无{days}天内的数据'}
            
            scores = [h['overall_score'] for h in recent_scores]
            
            return {
                'symbol': symbol,
                'period_days': days,
                'score_count': len(recent_scores),
                'current_score': recent_scores[-1]['overall_score'],
                'avg_score': statistics.mean(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'trend': 'up' if len(scores) > 1 and scores[-1] > scores[0] else 'down' if len(scores) > 1 and scores[-1] < scores[0] else 'stable',
                'recent_scores': recent_scores[-10:]  # 最近10次评分
            }
            
        except Exception as e:
            logger.error(f"获取评分趋势失败: {e}")
            return {'error': str(e)}


# 全局实例
_comprehensive_scoring_system = None

def get_comprehensive_scoring_system() -> ComprehensiveScoringSystem:
    """获取综合评分系统实例"""
    global _comprehensive_scoring_system
    if _comprehensive_scoring_system is None:
        _comprehensive_scoring_system = ComprehensiveScoringSystem()
    return _comprehensive_scoring_system


# 便捷函数
def calculate_comprehensive_score(symbol: str, stock_data: Dict[str, Any],
                                news_data: List[Dict[str, Any]] = None) -> ComprehensiveScore:
    """计算股票综合评分"""
    system = get_comprehensive_scoring_system()
    return system.calculate_comprehensive_score(symbol, stock_data, news_data)