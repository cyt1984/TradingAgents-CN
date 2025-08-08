#!/usr/bin/env python3
"""
相似股票智能推荐引擎
基于多维度特征分析，发现和推荐相似股票
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class SimilarityDimension(Enum):
    """相似性维度"""
    FUNDAMENTAL = "fundamental"         # 基本面相似性
    TECHNICAL = "technical"             # 技术面相似性
    INDUSTRY = "industry"               # 行业相似性
    SIZE = "size"                       # 规模相似性
    GROWTH = "growth"                   # 成长性相似性
    VALUATION = "valuation"             # 估值相似性
    SENTIMENT = "sentiment"             # 情绪相似性
    PATTERN = "pattern"                 # 模式相似性
    RISK = "risk"                       # 风险相似性


@dataclass
class SimilarityScore:
    """相似性评分"""
    dimension: SimilarityDimension      # 相似性维度
    score: float                        # 相似性评分 (0-1)
    weight: float                       # 维度权重
    details: Dict[str, Any]             # 详细信息
    confidence: float                   # 置信度


@dataclass
class StockSimilarity:
    """股票相似性结果"""
    target_symbol: str                  # 目标股票代码
    similar_symbol: str                 # 相似股票代码
    overall_similarity: float           # 综合相似度 (0-1)
    dimension_scores: Dict[SimilarityDimension, SimilarityScore]  # 各维度评分
    match_reasons: List[str]            # 匹配原因
    recommendation_strength: float      # 推荐强度
    risk_differential: float            # 风险差异
    expected_correlation: float         # 预期相关性
    timestamp: datetime                 # 分析时间


class SimilarityEngine:
    """相似股票推荐引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化相似性引擎
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 相似性权重配置
        self.dimension_weights = {
            SimilarityDimension.FUNDAMENTAL: 0.25,    # 基本面 25%
            SimilarityDimension.TECHNICAL: 0.20,      # 技术面 20%
            SimilarityDimension.INDUSTRY: 0.15,       # 行业 15%
            SimilarityDimension.SIZE: 0.10,           # 规模 10%
            SimilarityDimension.GROWTH: 0.12,         # 成长性 12%
            SimilarityDimension.VALUATION: 0.10,      # 估值 10%
            SimilarityDimension.SENTIMENT: 0.05,      # 情绪 5%
            SimilarityDimension.PATTERN: 0.03         # 模式 3%
        }
        
        # 相似性阈值
        self.similarity_thresholds = {
            'high_similarity': 0.8,       # 高相似度阈值
            'medium_similarity': 0.6,     # 中等相似度阈值
            'low_similarity': 0.4,        # 低相似度阈值
            'min_similarity': 0.3         # 最低相似度阈值
        }
        
        # 特征提取器
        self.feature_extractors = {
            SimilarityDimension.FUNDAMENTAL: self._extract_fundamental_features,
            SimilarityDimension.TECHNICAL: self._extract_technical_features,
            SimilarityDimension.INDUSTRY: self._extract_industry_features,
            SimilarityDimension.SIZE: self._extract_size_features,
            SimilarityDimension.GROWTH: self._extract_growth_features,
            SimilarityDimension.VALUATION: self._extract_valuation_features,
            SimilarityDimension.SENTIMENT: self._extract_sentiment_features,
            SimilarityDimension.PATTERN: self._extract_pattern_features
        }
        
        # 股票特征缓存
        self.feature_cache = {}
        
        # 相似性计算缓存
        self.similarity_cache = {}
        
        # 聚类模型
        self.cluster_models = {}
        
        logger.info("相似股票推荐引擎初始化完成")
        logger.info(f"   相似性维度: {len(SimilarityDimension)} 个")
        logger.info(f"   维度权重配置: {len(self.dimension_weights)} 项")

    def find_similar_stocks(self, target_symbol: str, 
                          target_data: Dict[str, Any],
                          candidate_stocks: List[Dict[str, Any]],
                          top_k: int = 10) -> List[StockSimilarity]:
        """
        找到相似股票
        
        Args:
            target_symbol: 目标股票代码
            target_data: 目标股票数据
            candidate_stocks: 候选股票列表
            top_k: 返回前K个相似股票
            
        Returns:
            相似股票列表，按相似度排序
        """
        try:
            logger.info(f"🔍 [相似性引擎] 为 {target_symbol} 寻找相似股票，候选数: {len(candidate_stocks)}")
            
            # 1. 提取目标股票特征
            target_features = self._extract_all_features(target_symbol, target_data)
            
            # 2. 计算与所有候选股票的相似度
            similarities = []
            
            for candidate in candidate_stocks:
                candidate_symbol = candidate.get('symbol', '')
                if candidate_symbol == target_symbol:
                    continue  # 跳过自己
                
                try:
                    # 提取候选股票特征
                    candidate_features = self._extract_all_features(candidate_symbol, candidate)
                    
                    # 计算相似度
                    similarity = self._calculate_similarity(
                        target_symbol, target_features,
                        candidate_symbol, candidate_features
                    )
                    
                    if similarity.overall_similarity >= self.similarity_thresholds['min_similarity']:
                        similarities.append(similarity)
                        
                except Exception as e:
                    logger.debug(f"⚠️ 计算相似度失败: {candidate_symbol} - {e}")
                    continue
            
            # 3. 排序并返回前K个
            similarities.sort(key=lambda x: x.overall_similarity, reverse=True)
            top_similarities = similarities[:top_k]
            
            logger.info(f"🔍 [相似性引擎] 找到 {len(top_similarities)} 只相似股票")
            
            # 4. 更新缓存
            cache_key = f"{target_symbol}_{datetime.now().strftime('%Y-%m-%d')}"
            self.similarity_cache[cache_key] = top_similarities
            
            return top_similarities
            
        except Exception as e:
            logger.error(f"❌ [相似性引擎] 查找失败: {target_symbol} - {e}")
            return []

    def _extract_all_features(self, symbol: str, stock_data: Dict[str, Any]) -> Dict[SimilarityDimension, np.ndarray]:
        """提取股票所有维度特征"""
        try:
            # 检查缓存
            cache_key = f"{symbol}_{hash(str(sorted(stock_data.items())))}"
            if cache_key in self.feature_cache:
                return self.feature_cache[cache_key]
            
            features = {}
            
            # 提取各维度特征
            for dimension, extractor in self.feature_extractors.items():
                try:
                    feature_vector = extractor(symbol, stock_data)
                    features[dimension] = feature_vector
                except Exception as e:
                    logger.debug(f"⚠️ 特征提取失败 {dimension.value}: {e}")
                    # 使用默认特征向量
                    features[dimension] = np.zeros(self._get_feature_dimension(dimension))
            
            # 更新缓存
            self.feature_cache[cache_key] = features
            
            return features
            
        except Exception as e:
            logger.error(f"❌ 特征提取失败: {symbol} - {e}")
            # 返回默认特征
            return {dim: np.zeros(self._get_feature_dimension(dim)) for dim in SimilarityDimension}

    def _get_feature_dimension(self, dimension: SimilarityDimension) -> int:
        """获取特征维度大小"""
        dimension_sizes = {
            SimilarityDimension.FUNDAMENTAL: 8,    # 8个基本面指标
            SimilarityDimension.TECHNICAL: 6,      # 6个技术指标
            SimilarityDimension.INDUSTRY: 5,       # 5个行业特征
            SimilarityDimension.SIZE: 3,           # 3个规模指标
            SimilarityDimension.GROWTH: 4,         # 4个成长指标
            SimilarityDimension.VALUATION: 4,      # 4个估值指标
            SimilarityDimension.SENTIMENT: 3,      # 3个情绪指标
            SimilarityDimension.PATTERN: 5         # 5个模式指标
        }
        return dimension_sizes.get(dimension, 5)

    def _extract_fundamental_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取基本面特征"""
        try:
            features = []
            
            # ROE (净资产收益率)
            roe = data.get('roe', 0.1)
            features.append(self._normalize_ratio(roe, 0, 0.3))
            
            # ROA (总资产收益率)
            roa = data.get('roa', 0.05)
            features.append(self._normalize_ratio(roa, 0, 0.2))
            
            # 毛利率
            gross_margin = data.get('gross_margin', 0.3)
            features.append(self._normalize_ratio(gross_margin, 0, 1))
            
            # 净利率
            net_margin = data.get('net_margin', 0.1)
            features.append(self._normalize_ratio(net_margin, 0, 0.5))
            
            # 负债率
            debt_ratio = data.get('debt_ratio', 0.4)
            features.append(self._normalize_ratio(debt_ratio, 0, 1))
            
            # 流动比率
            current_ratio = data.get('current_ratio', 1.5)
            features.append(self._normalize_ratio(current_ratio, 0.5, 3))
            
            # 资产周转率
            asset_turnover = data.get('asset_turnover', 1.0)
            features.append(self._normalize_ratio(asset_turnover, 0.2, 3))
            
            # 营收增长率
            revenue_growth = data.get('revenue_growth', 0.1)
            features.append(self._normalize_ratio(revenue_growth, -0.5, 1))
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"基本面特征提取失败: {e}")
            return np.zeros(8)

    def _extract_technical_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取技术面特征"""
        try:
            features = []
            
            # 价格动量 (近期涨跌幅)
            price_momentum = data.get('price_change_pct', 0) / 100
            features.append(self._normalize_ratio(price_momentum, -0.2, 0.2))
            
            # 相对强度 (相对大盘表现)
            relative_strength = data.get('relative_strength', 0)
            features.append(self._normalize_ratio(relative_strength, -0.1, 0.1))
            
            # 波动率
            volatility = data.get('volatility', 0.2)
            features.append(self._normalize_ratio(volatility, 0.1, 0.5))
            
            # 成交量比率
            volume_ratio = data.get('volume_ratio', 1.0)
            features.append(self._normalize_ratio(volume_ratio, 0.5, 3))
            
            # 技术评分
            technical_score = data.get('technical_score', 50) / 100
            features.append(technical_score)
            
            # 趋势强度
            trend_strength = data.get('trend_strength', 0.5)
            features.append(trend_strength)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"技术面特征提取失败: {e}")
            return np.zeros(6)

    def _extract_industry_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取行业特征"""
        try:
            features = []
            
            # 行业编码 (简化为几个主要行业)
            industry = data.get('industry', '其他')
            industry_encoding = self._encode_industry(industry)
            features.extend(industry_encoding)
            
            # 行业相对表现
            industry_performance = data.get('industry_performance', 0)
            features.append(self._normalize_ratio(industry_performance, -0.2, 0.2))
            
            # 行业排名 (在行业内的排名百分位)
            industry_ranking = data.get('industry_ranking', 0.5)
            features.append(industry_ranking)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"行业特征提取失败: {e}")
            return np.zeros(5)

    def _extract_size_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取规模特征"""
        try:
            features = []
            
            # 市值 (对数缩放)
            market_cap = data.get('market_cap', 1000000000)  # 默认10亿
            log_market_cap = math.log10(max(market_cap, 1000000))  # 最小100万
            features.append(self._normalize_ratio(log_market_cap, 6, 12))  # 100万到1万亿
            
            # 流通股本 (对数缩放)
            shares_outstanding = data.get('shares_outstanding', 100000000)  # 默认1亿股
            log_shares = math.log10(max(shares_outstanding, 1000000))
            features.append(self._normalize_ratio(log_shares, 6, 11))
            
            # 年营收 (对数缩放)
            revenue = data.get('revenue', 1000000000)  # 默认10亿
            log_revenue = math.log10(max(revenue, 1000000))
            features.append(self._normalize_ratio(log_revenue, 6, 12))
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"规模特征提取失败: {e}")
            return np.zeros(3)

    def _extract_growth_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取成长性特征"""
        try:
            features = []
            
            # 营收增长率
            revenue_growth = data.get('revenue_growth', 0.1)
            features.append(self._normalize_ratio(revenue_growth, -0.3, 1))
            
            # 净利润增长率
            profit_growth = data.get('profit_growth', 0.1)
            features.append(self._normalize_ratio(profit_growth, -0.5, 1.5))
            
            # EPS增长率
            eps_growth = data.get('eps_growth', 0.1)
            features.append(self._normalize_ratio(eps_growth, -0.5, 1.5))
            
            # 成长性评分
            growth_score = data.get('growth_score', 50) / 100
            features.append(growth_score)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"成长性特征提取失败: {e}")
            return np.zeros(4)

    def _extract_valuation_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取估值特征"""
        try:
            features = []
            
            # P/E比率 (对数缩放)
            pe_ratio = data.get('pe_ratio', 20)
            log_pe = math.log10(max(pe_ratio, 1))
            features.append(self._normalize_ratio(log_pe, 0, 2))  # 1到100倍
            
            # P/B比率 (对数缩放)
            pb_ratio = data.get('pb_ratio', 2)
            log_pb = math.log10(max(pb_ratio, 0.1))
            features.append(self._normalize_ratio(log_pb, -1, 1))  # 0.1到10倍
            
            # P/S比率
            ps_ratio = data.get('ps_ratio', 3)
            log_ps = math.log10(max(ps_ratio, 0.1))
            features.append(self._normalize_ratio(log_ps, -1, 1))
            
            # 估值评分
            valuation_score = data.get('valuation_score', 50) / 100
            features.append(valuation_score)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"估值特征提取失败: {e}")
            return np.zeros(4)

    def _extract_sentiment_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取情绪特征"""
        try:
            features = []
            
            # 新闻情绪
            news_sentiment = data.get('news_sentiment', 0)
            features.append(self._normalize_ratio(news_sentiment, -1, 1))
            
            # 社交媒体情绪
            social_sentiment = data.get('social_sentiment', 0)
            features.append(self._normalize_ratio(social_sentiment, -1, 1))
            
            # 情绪评分
            sentiment_score = data.get('sentiment_score', 50) / 100
            features.append(sentiment_score)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"情绪特征提取失败: {e}")
            return np.zeros(3)

    def _extract_pattern_features(self, symbol: str, data: Dict[str, Any]) -> np.ndarray:
        """提取模式特征"""
        try:
            features = []
            
            # 趋势模式强度
            trend_pattern = data.get('trend_pattern_strength', 0.5)
            features.append(trend_pattern)
            
            # 动量模式强度
            momentum_pattern = data.get('momentum_pattern_strength', 0.5)
            features.append(momentum_pattern)
            
            # 反转模式强度
            reversal_pattern = data.get('reversal_pattern_strength', 0.5)
            features.append(reversal_pattern)
            
            # 突破模式强度
            breakout_pattern = data.get('breakout_pattern_strength', 0.5)
            features.append(breakout_pattern)
            
            # 整体模式相似性
            pattern_similarity = data.get('pattern_similarity', 0.5)
            features.append(pattern_similarity)
            
            return np.array(features)
            
        except Exception as e:
            logger.debug(f"模式特征提取失败: {e}")
            return np.zeros(5)

    def _normalize_ratio(self, value: float, min_val: float, max_val: float) -> float:
        """归一化比率到 [0, 1] 区间"""
        try:
            if max_val <= min_val:
                return 0.5
            normalized = (value - min_val) / (max_val - min_val)
            return max(0, min(1, normalized))
        except:
            return 0.5

    def _encode_industry(self, industry: str) -> List[float]:
        """编码行业信息 (One-Hot编码简化版)"""
        try:
            # 简化的主要行业分类
            major_industries = ['金融', '科技', '消费', '医药', '制造']
            
            # One-hot编码 (但长度固定为3，取前3个匹配)
            encoding = [0.0, 0.0, 0.0]
            
            for i, major in enumerate(major_industries[:3]):
                if major in industry:
                    encoding[i] = 1.0
                    break
            
            # 如果没有匹配，使用默认编码
            if sum(encoding) == 0:
                encoding[2] = 1.0  # 默认为第3类
            
            return encoding
            
        except:
            return [0.0, 0.0, 1.0]  # 默认编码

    def _calculate_similarity(self, target_symbol: str, target_features: Dict[SimilarityDimension, np.ndarray],
                            candidate_symbol: str, candidate_features: Dict[SimilarityDimension, np.ndarray]) -> StockSimilarity:
        """计算两只股票的相似度"""
        try:
            dimension_scores = {}
            total_weighted_score = 0.0
            total_weight = 0.0
            
            # 计算各维度相似度
            for dimension in SimilarityDimension:
                if dimension in target_features and dimension in candidate_features:
                    target_vector = target_features[dimension]
                    candidate_vector = candidate_features[dimension]
                    
                    # 计算余弦相似度
                    similarity_score = self._calculate_cosine_similarity(target_vector, candidate_vector)
                    
                    # 维度权重
                    weight = self.dimension_weights.get(dimension, 0.1)
                    
                    # 置信度基于特征向量的有效性
                    confidence = self._calculate_feature_confidence(target_vector, candidate_vector)
                    
                    dimension_scores[dimension] = SimilarityScore(
                        dimension=dimension,
                        score=similarity_score,
                        weight=weight,
                        details={
                            'target_features': target_vector.tolist(),
                            'candidate_features': candidate_vector.tolist()
                        },
                        confidence=confidence
                    )
                    
                    # 累加加权得分
                    effective_weight = weight * confidence
                    total_weighted_score += similarity_score * effective_weight
                    total_weight += effective_weight
            
            # 计算综合相似度
            overall_similarity = total_weighted_score / total_weight if total_weight > 0 else 0.0
            
            # 生成匹配原因
            match_reasons = self._generate_match_reasons(dimension_scores)
            
            # 计算推荐强度
            recommendation_strength = self._calculate_recommendation_strength(overall_similarity, dimension_scores)
            
            # 计算风险差异 (简化)
            risk_differential = self._calculate_risk_differential(target_features, candidate_features)
            
            # 预期相关性
            expected_correlation = overall_similarity * 0.8  # 简化估计
            
            return StockSimilarity(
                target_symbol=target_symbol,
                similar_symbol=candidate_symbol,
                overall_similarity=overall_similarity,
                dimension_scores=dimension_scores,
                match_reasons=match_reasons,
                recommendation_strength=recommendation_strength,
                risk_differential=risk_differential,
                expected_correlation=expected_correlation,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {target_symbol} vs {candidate_symbol} - {e}")
            return StockSimilarity(
                target_symbol=target_symbol,
                similar_symbol=candidate_symbol,
                overall_similarity=0.0,
                dimension_scores={},
                match_reasons=["计算失败"],
                recommendation_strength=0.0,
                risk_differential=0.0,
                expected_correlation=0.0,
                timestamp=datetime.now()
            )

    def _calculate_cosine_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            # 处理零向量
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            cosine_sim = np.dot(vector1, vector2) / (norm1 * norm2)
            
            # 转换到 [0, 1] 区间
            return (cosine_sim + 1) / 2
            
        except Exception as e:
            logger.debug(f"余弦相似度计算失败: {e}")
            return 0.0

    def _calculate_feature_confidence(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算特征置信度"""
        try:
            # 基于特征向量的完整性和有效性
            non_zero_count1 = np.count_nonzero(vector1)
            non_zero_count2 = np.count_nonzero(vector2)
            
            completeness = (non_zero_count1 + non_zero_count2) / (len(vector1) + len(vector2))
            
            # 基于特征值的方差
            variance1 = np.var(vector1)
            variance2 = np.var(vector2)
            avg_variance = (variance1 + variance2) / 2
            
            # 综合置信度
            confidence = min(1.0, completeness + min(0.3, avg_variance))
            
            return max(0.1, confidence)  # 最低0.1的置信度
            
        except Exception:
            return 0.5

    def _generate_match_reasons(self, dimension_scores: Dict[SimilarityDimension, SimilarityScore]) -> List[str]:
        """生成匹配原因"""
        try:
            reasons = []
            
            # 按相似度排序
            sorted_dimensions = sorted(
                dimension_scores.items(),
                key=lambda x: x[1].score * x[1].weight,
                reverse=True
            )
            
            # 提取前几个最相似的维度
            for dimension, score in sorted_dimensions[:3]:
                if score.score > 0.7:
                    reason_map = {
                        SimilarityDimension.FUNDAMENTAL: f"基本面高度相似 ({score.score:.2%})",
                        SimilarityDimension.TECHNICAL: f"技术指标相似 ({score.score:.2%})",
                        SimilarityDimension.INDUSTRY: f"同行业公司 ({score.score:.2%})",
                        SimilarityDimension.SIZE: f"规模相当 ({score.score:.2%})",
                        SimilarityDimension.GROWTH: f"成长性相似 ({score.score:.2%})",
                        SimilarityDimension.VALUATION: f"估值水平接近 ({score.score:.2%})"
                    }
                    
                    reason = reason_map.get(dimension, f"{dimension.value}相似 ({score.score:.2%})")
                    reasons.append(reason)
            
            return reasons if reasons else ["整体特征相似"]
            
        except Exception as e:
            logger.debug(f"匹配原因生成失败: {e}")
            return ["相似性分析"]

    def _calculate_recommendation_strength(self, overall_similarity: float, 
                                        dimension_scores: Dict[SimilarityDimension, SimilarityScore]) -> float:
        """计算推荐强度"""
        try:
            base_strength = overall_similarity
            
            # 基于关键维度的加权
            key_dimensions = [SimilarityDimension.FUNDAMENTAL, SimilarityDimension.TECHNICAL, SimilarityDimension.GROWTH]
            
            key_dimension_boost = 0
            for dimension in key_dimensions:
                if dimension in dimension_scores:
                    score = dimension_scores[dimension]
                    if score.score > 0.8:
                        key_dimension_boost += 0.1 * score.confidence
            
            # 综合推荐强度
            recommendation_strength = min(1.0, base_strength + key_dimension_boost)
            
            return recommendation_strength
            
        except Exception:
            return overall_similarity

    def _calculate_risk_differential(self, target_features: Dict[SimilarityDimension, np.ndarray],
                                   candidate_features: Dict[SimilarityDimension, np.ndarray]) -> float:
        """计算风险差异"""
        try:
            # 简化的风险差异计算
            # 基于基本面和技术面特征的差异
            risk_diff = 0.0
            
            if (SimilarityDimension.FUNDAMENTAL in target_features and 
                SimilarityDimension.FUNDAMENTAL in candidate_features):
                
                target_risk = np.mean(target_features[SimilarityDimension.FUNDAMENTAL][[4, 6]])  # 负债率, 资产周转率
                candidate_risk = np.mean(candidate_features[SimilarityDimension.FUNDAMENTAL][[4, 6]])
                
                risk_diff += abs(target_risk - candidate_risk)
            
            if (SimilarityDimension.TECHNICAL in target_features and 
                SimilarityDimension.TECHNICAL in candidate_features):
                
                target_volatility = target_features[SimilarityDimension.TECHNICAL][2]  # 波动率
                candidate_volatility = candidate_features[SimilarityDimension.TECHNICAL][2]
                
                risk_diff += abs(target_volatility - candidate_volatility)
            
            return min(1.0, risk_diff)
            
        except Exception:
            return 0.5

    def build_similarity_clusters(self, stock_data_list: List[Dict[str, Any]], 
                                n_clusters: int = 10) -> Dict[str, Any]:
        """构建相似性聚类"""
        try:
            logger.info(f"🔗 [相似性引擎] 构建相似性聚类，股票数: {len(stock_data_list)}")
            
            # 提取所有股票特征
            stock_features = []
            stock_symbols = []
            
            for stock_data in stock_data_list:
                symbol = stock_data.get('symbol', '')
                if not symbol:
                    continue
                
                features = self._extract_all_features(symbol, stock_data)
                
                # 将所有维度特征连接成一个向量
                combined_features = np.concatenate([
                    features.get(dim, np.zeros(self._get_feature_dimension(dim)))
                    for dim in SimilarityDimension
                ])
                
                stock_features.append(combined_features)
                stock_symbols.append(symbol)
            
            if len(stock_features) < n_clusters:
                n_clusters = max(2, len(stock_features) // 2)
            
            # 标准化特征
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(stock_features)
            
            # K-means聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(normalized_features)
            
            # 组织聚类结果
            clusters = defaultdict(list)
            for symbol, label in zip(stock_symbols, cluster_labels):
                clusters[f"cluster_{label}"].append(symbol)
            
            # 保存聚类模型
            self.cluster_models['stock_similarity'] = {
                'kmeans': kmeans,
                'scaler': scaler,
                'feature_dimension': len(combined_features)
            }
            
            cluster_summary = {
                'total_stocks': len(stock_symbols),
                'n_clusters': n_clusters,
                'clusters': dict(clusters),
                'cluster_sizes': {k: len(v) for k, v in clusters.items()},
                'timestamp': datetime.now()
            }
            
            logger.info(f"🔗 [相似性引擎] 聚类完成，生成 {n_clusters} 个集群")
            return cluster_summary
            
        except Exception as e:
            logger.error(f"❌ 聚类构建失败: {e}")
            return {'error': str(e)}

    def recommend_from_cluster(self, target_symbol: str, 
                             cluster_info: Dict[str, Any],
                             top_k: int = 5) -> List[str]:
        """基于聚类推荐相似股票"""
        try:
            # 找到目标股票所在集群
            target_cluster = None
            for cluster_name, symbols in cluster_info.get('clusters', {}).items():
                if target_symbol in symbols:
                    target_cluster = cluster_name
                    break
            
            if not target_cluster:
                return []
            
            # 从同一集群中推荐其他股票
            cluster_stocks = cluster_info['clusters'][target_cluster]
            similar_stocks = [s for s in cluster_stocks if s != target_symbol]
            
            return similar_stocks[:top_k]
            
        except Exception as e:
            logger.error(f"❌ 聚类推荐失败: {e}")
            return []

    def get_similarity_insights(self, similarities: List[StockSimilarity]) -> Dict[str, Any]:
        """获取相似性分析洞察"""
        try:
            if not similarities:
                return {'insights': '无相似股票数据'}
            
            # 统计分析
            similarity_scores = [s.overall_similarity for s in similarities]
            
            # 维度分析
            dimension_stats = defaultdict(list)
            for similarity in similarities:
                for dim, score in similarity.dimension_scores.items():
                    dimension_stats[dim.value].append(score.score)
            
            # 生成洞察
            insights = {
                'total_similar_stocks': len(similarities),
                'avg_similarity': statistics.mean(similarity_scores),
                'max_similarity': max(similarity_scores),
                'min_similarity': min(similarity_scores),
                'high_similarity_count': len([s for s in similarity_scores if s > 0.8]),
                'medium_similarity_count': len([s for s in similarity_scores if 0.6 <= s <= 0.8]),
                'dimension_analysis': {},
                'top_match_reasons': [],
                'similarity_distribution': {
                    'very_high': len([s for s in similarity_scores if s > 0.9]),
                    'high': len([s for s in similarity_scores if 0.8 <= s <= 0.9]),
                    'medium': len([s for s in similarity_scores if 0.6 <= s < 0.8]),
                    'low': len([s for s in similarity_scores if s < 0.6])
                }
            }
            
            # 维度分析
            for dim, scores in dimension_stats.items():
                if scores:
                    insights['dimension_analysis'][dim] = {
                        'avg_score': statistics.mean(scores),
                        'max_score': max(scores),
                        'contribution': statistics.mean(scores) * self.dimension_weights.get(
                            getattr(SimilarityDimension, dim.upper(), SimilarityDimension.FUNDAMENTAL), 0.1
                        )
                    }
            
            # 收集最常见的匹配原因
            all_reasons = []
            for similarity in similarities[:10]:  # 前10个最相似的
                all_reasons.extend(similarity.match_reasons)
            
            reason_counts = defaultdict(int)
            for reason in all_reasons:
                reason_counts[reason] += 1
            
            insights['top_match_reasons'] = sorted(
                reason_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ 相似性洞察分析失败: {e}")
            return {'error': str(e)}