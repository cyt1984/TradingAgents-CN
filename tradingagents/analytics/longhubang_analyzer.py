#!/usr/bin/env python3
"""
龙虎榜综合分析引擎
整合席位分析、资金流向、市场情绪等多维度信息
为智能选股提供高质量的龙虎榜分析结果
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.longhubang_utils import LongHuBangProvider, LongHuBangData, RankingType, get_longhubang_provider
from tradingagents.analytics.seat_analyzer import SeatAnalyzer, get_seat_analyzer, SeatType

logger = get_logger('longhubang_analyzer')


class MarketSentiment(Enum):
    """市场情绪枚举"""
    EXTREMELY_BULLISH = "extremely_bullish"    # 极度看多
    BULLISH = "bullish"                        # 看多
    NEUTRAL = "neutral"                        # 中性
    BEARISH = "bearish"                        # 看空
    EXTREMELY_BEARISH = "extremely_bearish"    # 极度看空


class OperationPattern(Enum):
    """操作模式枚举"""
    INSTITUTIONAL_BUYING = "institutional_buying"      # 机构买入
    INSTITUTIONAL_SELLING = "institutional_selling"    # 机构卖出
    HOT_MONEY_SPECULATION = "hot_money_speculation"     # 游资炒作
    RETAIL_FOLLOWING = "retail_following"               # 散户跟风
    COORDINATED_OPERATION = "coordinated_operation"     # 协同操作
    MIXED_PATTERN = "mixed_pattern"                     # 混合模式


@dataclass
class LongHuBangScore:
    """龙虎榜综合评分"""
    overall_score: float                               # 综合评分(0-100)
    seat_quality_score: float                         # 席位质量评分
    capital_flow_score: float                         # 资金流向评分
    follow_potential_score: float                     # 跟风潜力评分
    risk_score: float                                 # 风险评分
    confidence: float                                 # 置信度
    
    # 分项评分
    buy_seat_score: float = 0.0                       # 买方席位评分
    sell_seat_score: float = 0.0                      # 卖方席位评分
    net_inflow_score: float = 0.0                     # 净流入评分
    sentiment_score: float = 0.0                      # 情绪评分


@dataclass
class LongHuBangAnalysisResult:
    """龙虎榜分析结果"""
    symbol: str                                        # 股票代码
    name: str                                         # 股票名称
    longhubang_data: LongHuBangData                   # 原始龙虎榜数据
    score: LongHuBangScore                            # 综合评分
    
    # 分析结果
    market_sentiment: MarketSentiment                 # 市场情绪
    operation_pattern: OperationPattern               # 操作模式
    seat_analysis: Dict[str, Any]                     # 席位分析
    capital_flow_analysis: Dict[str, Any]             # 资金流向分析
    
    # 投资建议
    investment_suggestion: str                        # 投资建议
    risk_warning: str                                 # 风险提示
    follow_recommendation: str                        # 跟随建议
    
    # 元数据
    analysis_timestamp: str                           # 分析时间
    data_quality: float                              # 数据质量评分


class LongHuBangAnalyzer:
    """龙虎榜综合分析器"""
    
    def __init__(self):
        """初始化龙虎榜分析器"""
        self.longhubang_provider = get_longhubang_provider()
        self.seat_analyzer = get_seat_analyzer()
        
        # 评分权重配置
        self.score_weights = {
            'seat_quality': 0.35,      # 席位质量权重35%
            'capital_flow': 0.30,      # 资金流向权重30%
            'follow_potential': 0.20,  # 跟风潜力权重20%
            'risk_adjustment': 0.15    # 风险调整权重15%
        }
        
        logger.info("✅ 龙虎榜综合分析器初始化成功")
    
    def analyze_single_stock(self, symbol: str, date: str = None) -> Optional[LongHuBangAnalysisResult]:
        """
        分析单只股票的龙虎榜数据
        
        Args:
            symbol: 股票代码
            date: 日期，默认为今天
            
        Returns:
            分析结果或None
        """
        try:
            # 获取龙虎榜数据
            daily_rankings = self.longhubang_provider.get_daily_ranking(date)
            stock_data = None
            
            for ranking in daily_rankings:
                if ranking.symbol == symbol:
                    stock_data = ranking
                    break
            
            if not stock_data:
                logger.debug(f"未找到 {symbol} 的龙虎榜数据")
                return None
            
            return self._analyze_longhubang_data(stock_data)
            
        except Exception as e:
            logger.error(f"❌ 分析单只股票龙虎榜失败: {symbol}, 错误: {e}")
            return None
    
    def analyze_batch_stocks(self, symbols: List[str], date: str = None) -> List[LongHuBangAnalysisResult]:
        """
        批量分析股票龙虎榜数据
        
        Args:
            symbols: 股票代码列表
            date: 日期
            
        Returns:
            分析结果列表
        """
        results = []
        
        try:
            # 获取当日所有龙虎榜数据
            daily_rankings = self.longhubang_provider.get_daily_ranking(date)
            
            # 创建快速查找字典
            ranking_dict = {ranking.symbol: ranking for ranking in daily_rankings}
            
            for symbol in symbols:
                if symbol in ranking_dict:
                    result = self._analyze_longhubang_data(ranking_dict[symbol])
                    if result:
                        results.append(result)
            
            logger.info(f"✅ 批量分析完成: {len(symbols)}只股票, 找到{len(results)}只龙虎榜股票")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量分析龙虎榜失败: {e}")
            return results
    
    def get_top_ranking_stocks(self, date: str = None, 
                              ranking_type: RankingType = RankingType.DAILY,
                              min_score: float = 60.0,
                              limit: int = 50) -> List[LongHuBangAnalysisResult]:
        """
        获取顶级龙虎榜股票
        
        Args:
            date: 日期
            ranking_type: 龙虎榜类型
            min_score: 最低评分
            limit: 返回数量限制
            
        Returns:
            排序后的分析结果列表
        """
        try:
            # 获取龙虎榜数据
            rankings = self.longhubang_provider.get_daily_ranking(date, ranking_type)
            
            # 分析所有股票
            results = []
            for ranking in rankings:
                analysis_result = self._analyze_longhubang_data(ranking)
                if analysis_result and analysis_result.score.overall_score >= min_score:
                    results.append(analysis_result)
            
            # 按综合评分排序
            results.sort(key=lambda x: x.score.overall_score, reverse=True)
            
            logger.info(f"✅ 获取顶级龙虎榜股票: 总数{len(rankings)}, 符合条件{len(results)}只, 返回前{min(limit, len(results))}只")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"❌ 获取顶级龙虎榜股票失败: {e}")
            return []
    
    def _analyze_longhubang_data(self, longhubang_data: LongHuBangData) -> LongHuBangAnalysisResult:
        """
        分析龙虎榜数据
        
        Args:
            longhubang_data: 龙虎榜数据
            
        Returns:
            分析结果
        """
        try:
            # 席位分析
            seat_analysis = self.seat_analyzer.analyze_comprehensive_seats(longhubang_data)
            
            # 资金流向分析
            capital_flow_analysis = self._analyze_capital_flow(longhubang_data)
            
            # 计算各项评分
            seat_quality_score = self._calculate_seat_quality_score(seat_analysis)
            capital_flow_score = self._calculate_capital_flow_score(capital_flow_analysis)
            follow_potential_score = self._calculate_follow_potential_score(seat_analysis, capital_flow_analysis)
            risk_score = self._calculate_risk_score(seat_analysis, longhubang_data)
            
            # 计算综合评分
            overall_score = self._calculate_overall_score(
                seat_quality_score, capital_flow_score, follow_potential_score, risk_score
            )
            
            # 创建评分对象
            score = LongHuBangScore(
                overall_score=overall_score,
                seat_quality_score=seat_quality_score,
                capital_flow_score=capital_flow_score,
                follow_potential_score=follow_potential_score,
                risk_score=risk_score,
                confidence=self._calculate_confidence(seat_analysis, capital_flow_analysis),
                buy_seat_score=self._calculate_buy_seat_score(seat_analysis),
                sell_seat_score=self._calculate_sell_seat_score(seat_analysis),
                net_inflow_score=capital_flow_analysis.get('net_inflow_score', 50),
                sentiment_score=self._calculate_sentiment_score(longhubang_data, seat_analysis)
            )
            
            # 判断市场情绪和操作模式
            market_sentiment = self._determine_market_sentiment(score, seat_analysis)
            operation_pattern = self._determine_operation_pattern(seat_analysis, capital_flow_analysis)
            
            # 生成投资建议
            investment_suggestion = self._generate_investment_suggestion(score, market_sentiment, operation_pattern)
            risk_warning = self._generate_risk_warning(seat_analysis, operation_pattern, score)
            follow_recommendation = self._generate_follow_recommendation(score, seat_analysis)
            
            # 数据质量评估
            data_quality = self._assess_data_quality(longhubang_data, seat_analysis)
            
            return LongHuBangAnalysisResult(
                symbol=longhubang_data.symbol,
                name=longhubang_data.name,
                longhubang_data=longhubang_data,
                score=score,
                market_sentiment=market_sentiment,
                operation_pattern=operation_pattern,
                seat_analysis=seat_analysis,
                capital_flow_analysis=capital_flow_analysis,
                investment_suggestion=investment_suggestion,
                risk_warning=risk_warning,
                follow_recommendation=follow_recommendation,
                analysis_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data_quality=data_quality
            )
            
        except Exception as e:
            logger.error(f"❌ 分析龙虎榜数据失败: {longhubang_data.symbol}, 错误: {e}")
            return None
    
    def _analyze_capital_flow(self, longhubang_data: LongHuBangData) -> Dict[str, Any]:
        """分析资金流向"""
        total_buy = longhubang_data.get_total_buy_amount()
        total_sell = longhubang_data.get_total_sell_amount()
        net_flow = longhubang_data.get_net_flow()
        
        # 资金流向强度
        total_amount = total_buy + total_sell
        if total_amount > 0:
            buy_ratio = total_buy / total_amount
            sell_ratio = total_sell / total_amount
            net_ratio = abs(net_flow) / total_amount
        else:
            buy_ratio = sell_ratio = net_ratio = 0
        
        # 流向评级
        if net_flow > 20000:  # 净流入超过2亿
            flow_level = "大幅净流入"
            flow_score = 90
        elif net_flow > 5000:   # 净流入超过5000万
            flow_level = "明显净流入"
            flow_score = 75
        elif net_flow > 0:
            flow_level = "小幅净流入"
            flow_score = 60
        elif net_flow > -5000:
            flow_level = "小幅净流出"
            flow_score = 40
        elif net_flow > -20000:
            flow_level = "明显净流出"
            flow_score = 25
        else:
            flow_level = "大幅净流出"
            flow_score = 10
        
        # 单向性评估
        if net_ratio > 0.7:
            directional_strength = "单向交易"
        elif net_ratio > 0.4:
            directional_strength = "偏向性交易"
        else:
            directional_strength = "分歧交易"
        
        return {
            'total_buy_amount': total_buy,
            'total_sell_amount': total_sell,
            'net_flow': net_flow,
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio,
            'net_ratio': net_ratio,
            'flow_level': flow_level,
            'flow_score': flow_score,
            'directional_strength': directional_strength,
            'net_inflow_score': flow_score
        }
    
    def _calculate_seat_quality_score(self, seat_analysis: Dict[str, Any]) -> float:
        """计算席位质量评分"""
        try:
            buy_results = seat_analysis.get('buy_seat_analysis', [])
            sell_results = seat_analysis.get('sell_seat_analysis', [])
            
            # 计算买方席位平均质量
            buy_scores = [result.analysis_score for result in buy_results]
            avg_buy_score = statistics.mean(buy_scores) if buy_scores else 30
            
            # 计算卖方席位平均质量
            sell_scores = [result.analysis_score for result in sell_results]
            avg_sell_score = statistics.mean(sell_scores) if sell_scores else 30
            
            # 综合考虑买卖双方，买方权重更大
            quality_score = avg_buy_score * 0.7 + avg_sell_score * 0.3
            
            # 根据高质量席位数量加分
            high_quality_buy = len([s for s in buy_scores if s > 80])
            high_quality_sell = len([s for s in sell_scores if s > 80])
            
            if high_quality_buy >= 2:
                quality_score += 10
            elif high_quality_buy >= 1:
                quality_score += 5
            
            if high_quality_sell >= 2:
                quality_score -= 5  # 卖方高质量席位多反而不好
            
            return min(100, max(0, quality_score))
            
        except Exception as e:
            logger.error(f"计算席位质量评分失败: {e}")
            return 50.0
    
    def _calculate_capital_flow_score(self, capital_flow_analysis: Dict[str, Any]) -> float:
        """计算资金流向评分"""
        return capital_flow_analysis.get('flow_score', 50.0)
    
    def _calculate_follow_potential_score(self, seat_analysis: Dict[str, Any], 
                                        capital_flow_analysis: Dict[str, Any]) -> float:
        """计算跟风潜力评分"""
        base_score = 50.0
        
        # 根据买方席位类型调整
        buy_results = seat_analysis.get('buy_seat_analysis', [])
        for result in buy_results:
            if hasattr(result, 'seat_profile') and result.seat_profile:
                if result.seat_profile.seat_type.value in ['famous_investor', 'private_fund']:
                    base_score += 15
                elif result.seat_profile.seat_type.value == 'public_fund':
                    base_score += 10
                elif result.seat_profile.seat_type.value == 'hot_money':
                    base_score += 5  # 游资跟风潜力中等
        
        # 根据资金流向调整
        net_ratio = capital_flow_analysis.get('net_ratio', 0)
        if net_ratio > 0.5:  # 明显净流入
            base_score += 10
        elif net_ratio < -0.5:  # 明显净流出
            base_score -= 15
        
        # 根据席位模式调整
        battle_analysis = seat_analysis.get('battle_analysis', {})
        if battle_analysis.get('winner') == 'buy' and battle_analysis.get('confidence', 0) > 0.3:
            base_score += 10
        
        return min(100, max(0, base_score))
    
    def _calculate_risk_score(self, seat_analysis: Dict[str, Any], longhubang_data: LongHuBangData) -> float:
        """计算风险评分（分数越高风险越低）"""
        base_score = 50.0
        
        # 根据股票涨跌幅调整风险
        change_pct = longhubang_data.change_pct
        if abs(change_pct) > 15:  # 涨跌幅超过15%
            base_score -= 20
        elif abs(change_pct) > 10:  # 涨跌幅超过10%
            base_score -= 10
        elif abs(change_pct) > 5:   # 涨跌幅超过5%
            base_score -= 5
        
        # 根据席位类型调整风险
        buy_results = seat_analysis.get('buy_seat_analysis', [])
        hot_money_count = 0
        institution_count = 0
        
        for result in buy_results:
            if hasattr(result, 'seat_profile') and result.seat_profile:
                seat_type = result.seat_profile.seat_type.value
                if seat_type == 'hot_money':
                    hot_money_count += 1
                elif seat_type in ['famous_investor', 'private_fund', 'public_fund']:
                    institution_count += 1
        
        # 游资多风险高
        if hot_money_count >= 3:
            base_score -= 15
        elif hot_money_count >= 2:
            base_score -= 10
        
        # 机构多风险低
        if institution_count >= 2:
            base_score += 10
        elif institution_count >= 1:
            base_score += 5
        
        # 协同交易风险
        coordination = seat_analysis.get('coordination_analysis', {})
        if coordination.get('coordinated', False):
            base_score -= 10
        
        return min(100, max(0, base_score))
    
    def _calculate_overall_score(self, seat_quality_score: float, capital_flow_score: float,
                               follow_potential_score: float, risk_score: float) -> float:
        """计算综合评分"""
        overall_score = (
            seat_quality_score * self.score_weights['seat_quality'] +
            capital_flow_score * self.score_weights['capital_flow'] +
            follow_potential_score * self.score_weights['follow_potential'] +
            risk_score * self.score_weights['risk_adjustment']
        )
        
        return min(100, max(0, overall_score))
    
    def _calculate_confidence(self, seat_analysis: Dict[str, Any], 
                            capital_flow_analysis: Dict[str, Any]) -> float:
        """计算置信度"""
        confidence_factors = []
        
        # 席位识别置信度
        buy_results = seat_analysis.get('buy_seat_analysis', [])
        sell_results = seat_analysis.get('sell_seat_analysis', [])
        
        all_confidences = []
        for result in buy_results + sell_results:
            if hasattr(result, 'confidence'):
                all_confidences.append(result.confidence)
        
        if all_confidences:
            confidence_factors.append(statistics.mean(all_confidences))
        
        # 资金流向确定性
        net_ratio = capital_flow_analysis.get('net_ratio', 0)
        confidence_factors.append(abs(net_ratio))
        
        # 席位数量（席位越多越可信）
        total_seats = len(buy_results) + len(sell_results)
        seat_confidence = min(1.0, total_seats / 10)  # 10个席位为满分
        confidence_factors.append(seat_confidence)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _calculate_buy_seat_score(self, seat_analysis: Dict[str, Any]) -> float:
        """计算买方席位评分"""
        buy_results = seat_analysis.get('buy_seat_analysis', [])
        if not buy_results:
            return 30.0
        
        scores = [result.analysis_score for result in buy_results]
        return statistics.mean(scores)
    
    def _calculate_sell_seat_score(self, seat_analysis: Dict[str, Any]) -> float:
        """计算卖方席位评分"""
        sell_results = seat_analysis.get('sell_seat_analysis', [])
        if not sell_results:
            return 30.0
        
        scores = [result.analysis_score for result in sell_results]
        return statistics.mean(scores)
    
    def _calculate_sentiment_score(self, longhubang_data: LongHuBangData, 
                                 seat_analysis: Dict[str, Any]) -> float:
        """计算情绪评分"""
        base_score = 50.0
        
        # 根据涨跌幅判断情绪
        change_pct = longhubang_data.change_pct
        if change_pct > 9:      # 涨停或接近涨停
            base_score = 90
        elif change_pct > 5:    # 大涨
            base_score = 75
        elif change_pct > 0:    # 上涨
            base_score = 60
        elif change_pct > -5:   # 小跌
            base_score = 40
        elif change_pct > -9:   # 大跌
            base_score = 25
        else:                   # 跌停或接近跌停
            base_score = 10
        
        # 根据席位情绪调整
        battle_result = seat_analysis.get('battle_analysis', {}).get('battle_result', '')
        if battle_result == '买方占优':
            base_score += 10
        elif battle_result == '卖方占优':
            base_score -= 10
        
        return min(100, max(0, base_score))
    
    def _determine_market_sentiment(self, score: LongHuBangScore, 
                                  seat_analysis: Dict[str, Any]) -> MarketSentiment:
        """判断市场情绪"""
        sentiment_score = score.sentiment_score
        
        if sentiment_score >= 85:
            return MarketSentiment.EXTREMELY_BULLISH
        elif sentiment_score >= 65:
            return MarketSentiment.BULLISH
        elif sentiment_score >= 35:
            return MarketSentiment.NEUTRAL
        elif sentiment_score >= 15:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.EXTREMELY_BEARISH
    
    def _determine_operation_pattern(self, seat_analysis: Dict[str, Any], 
                                   capital_flow_analysis: Dict[str, Any]) -> OperationPattern:
        """判断操作模式"""
        # 检查协同交易
        coordination = seat_analysis.get('coordination_analysis', {})
        if coordination.get('coordinated', False):
            return OperationPattern.COORDINATED_OPERATION
        
        # 分析买方主导类型
        buy_pattern = seat_analysis.get('battle_analysis', {}).get('buy_pattern', {})
        sell_pattern = seat_analysis.get('battle_analysis', {}).get('sell_pattern', {})
        
        dominant_buy_type = buy_pattern.get('dominant_type', '')
        dominant_sell_type = sell_pattern.get('dominant_type', '')
        
        battle_winner = seat_analysis.get('battle_analysis', {}).get('winner', '')
        
        if battle_winner == 'buy':
            if dominant_buy_type in ['famous_investor', 'private_fund', 'public_fund']:
                return OperationPattern.INSTITUTIONAL_BUYING
            elif dominant_buy_type == 'hot_money':
                return OperationPattern.HOT_MONEY_SPECULATION
            else:
                return OperationPattern.RETAIL_FOLLOWING
        elif battle_winner == 'sell':
            if dominant_sell_type in ['famous_investor', 'private_fund', 'public_fund']:
                return OperationPattern.INSTITUTIONAL_SELLING
            else:
                return OperationPattern.MIXED_PATTERN
        else:
            return OperationPattern.MIXED_PATTERN
    
    def _generate_investment_suggestion(self, score: LongHuBangScore, 
                                      sentiment: MarketSentiment, 
                                      pattern: OperationPattern) -> str:
        """生成投资建议"""
        suggestions = []
        
        # 基于综合评分
        if score.overall_score > 80:
            suggestions.append("综合评分优秀，强烈推荐关注")
        elif score.overall_score > 60:
            suggestions.append("综合评分良好，建议关注")
        elif score.overall_score > 40:
            suggestions.append("综合评分一般，谨慎观察")
        else:
            suggestions.append("综合评分较低，建议回避")
        
        # 基于操作模式
        if pattern == OperationPattern.INSTITUTIONAL_BUYING:
            suggestions.append("机构买入主导，可考虑跟随")
        elif pattern == OperationPattern.HOT_MONEY_SPECULATION:
            suggestions.append("游资炒作，适合短线投机")
        elif pattern == OperationPattern.INSTITUTIONAL_SELLING:
            suggestions.append("机构卖出主导，建议观望")
        elif pattern == OperationPattern.COORDINATED_OPERATION:
            suggestions.append("存在协同操作，需额外谨慎")
        
        # 基于市场情绪
        if sentiment in [MarketSentiment.EXTREMELY_BULLISH, MarketSentiment.BULLISH]:
            suggestions.append("市场情绪积极")
        elif sentiment in [MarketSentiment.EXTREMELY_BEARISH, MarketSentiment.BEARISH]:
            suggestions.append("市场情绪悲观")
        
        return "; ".join(suggestions)
    
    def _generate_risk_warning(self, seat_analysis: Dict[str, Any], 
                             pattern: OperationPattern, score: LongHuBangScore) -> str:
        """生成风险提示"""
        warnings = []
        
        # 风险评分提示
        if score.risk_score < 30:
            warnings.append("风险等级：高风险")
        elif score.risk_score < 50:
            warnings.append("风险等级：中等风险")
        
        # 操作模式风险
        if pattern == OperationPattern.HOT_MONEY_SPECULATION:
            warnings.append("游资炒作风险，注意波动")
        elif pattern == OperationPattern.COORDINATED_OPERATION:
            warnings.append("协同操作风险，可能存在操纵")
        
        # 席位风险
        buy_results = seat_analysis.get('buy_seat_analysis', [])
        hot_money_count = sum(1 for result in buy_results 
                             if hasattr(result, 'seat_profile') and result.seat_profile and 
                             result.seat_profile.seat_type.value == 'hot_money')
        
        if hot_money_count >= 3:
            warnings.append("游资席位过多，注意追高风险")
        
        return "; ".join(warnings) if warnings else "风险相对可控"
    
    def _generate_follow_recommendation(self, score: LongHuBangScore, 
                                      seat_analysis: Dict[str, Any]) -> str:
        """生成跟随建议"""
        if score.overall_score > 75 and score.follow_potential_score > 70:
            return "强烈建议跟随"
        elif score.overall_score > 60 and score.follow_potential_score > 60:
            return "建议跟随"
        elif score.overall_score > 40:
            return "谨慎跟随"
        else:
            return "不建议跟随"
    
    def _assess_data_quality(self, longhubang_data: LongHuBangData, 
                           seat_analysis: Dict[str, Any]) -> float:
        """评估数据质量"""
        quality_score = 80.0  # 基础分
        
        # 席位数量
        total_seats = len(longhubang_data.buy_seats) + len(longhubang_data.sell_seats)
        if total_seats >= 10:
            quality_score += 10
        elif total_seats >= 5:
            quality_score += 5
        elif total_seats < 3:
            quality_score -= 10
        
        # 交易金额
        total_amount = longhubang_data.get_total_buy_amount() + longhubang_data.get_total_sell_amount()
        if total_amount > 100000:  # 超过10亿
            quality_score += 10
        elif total_amount > 50000:  # 超过5亿
            quality_score += 5
        elif total_amount < 10000:  # 小于1亿
            quality_score -= 10
        
        # 席位识别成功率
        successful_identifications = 0
        total_identifications = 0
        
        for result in seat_analysis.get('buy_seat_analysis', []) + seat_analysis.get('sell_seat_analysis', []):
            total_identifications += 1
            if hasattr(result, 'confidence') and result.confidence > 0.7:
                successful_identifications += 1
        
        if total_identifications > 0:
            identification_rate = successful_identifications / total_identifications
            quality_score += identification_rate * 10
        
        return min(100, max(0, quality_score))


# 全局实例
_longhubang_analyzer = None

def get_longhubang_analyzer() -> LongHuBangAnalyzer:
    """获取龙虎榜分析器单例"""
    global _longhubang_analyzer
    if _longhubang_analyzer is None:
        _longhubang_analyzer = LongHuBangAnalyzer()
    return _longhubang_analyzer


# 便捷函数
def analyze_stock_longhubang(symbol: str, date: str = None) -> Optional[LongHuBangAnalysisResult]:
    """分析单只股票龙虎榜"""
    analyzer = get_longhubang_analyzer()
    return analyzer.analyze_single_stock(symbol, date)


def get_top_longhubang_stocks(min_score: float = 70.0, limit: int = 20) -> List[LongHuBangAnalysisResult]:
    """获取顶级龙虎榜股票"""
    analyzer = get_longhubang_analyzer()
    return analyzer.get_top_ranking_stocks(min_score=min_score, limit=limit)


def batch_analyze_longhubang(symbols: List[str], date: str = None) -> List[LongHuBangAnalysisResult]:
    """批量分析龙虎榜"""
    analyzer = get_longhubang_analyzer()
    return analyzer.analyze_batch_stocks(symbols, date)


if __name__ == "__main__":
    # 测试代码
    analyzer = get_longhubang_analyzer()
    
    # 获取顶级龙虎榜股票
    top_stocks = analyzer.get_top_ranking_stocks(min_score=60.0, limit=10)
    print(f"顶级龙虎榜股票: {len(top_stocks)}只")
    
    for stock in top_stocks:
        print(f"{stock.symbol} {stock.name}: 综合评分{stock.score.overall_score:.1f}, "
              f"情绪{stock.market_sentiment.value}, 模式{stock.operation_pattern.value}")
        print(f"  投资建议: {stock.investment_suggestion}")
        print(f"  风险提示: {stock.risk_warning}")
        print("---")