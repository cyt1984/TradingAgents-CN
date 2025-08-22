#!/usr/bin/env python3
"""
智能数据采样模块
通过预筛选和智能采样大幅减少需要详细分析的股票数量，从而加速智能选股流程

核心策略:
1. 活跃度筛选 - 优先选择近期交易活跃的股票
2. 基础指标预筛选 - 使用轻量级指标快速过滤
3. 分层采样 - 按市值、行业等维度分层采样
4. 动态批次调整 - 根据系统负载调整处理批次大小
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

from ..utils.logging_manager import get_logger
from ..dataflows.enhanced_data_manager import EnhancedDataManager

logger = get_logger('intelligent_sampling')


class SamplingStrategy(Enum):
    """采样策略枚举"""
    ACTIVITY_BASED = "activity_based"        # 基于活跃度
    MARKET_CAP_WEIGHTED = "market_cap_weighted"  # 市值加权
    INDUSTRY_BALANCED = "industry_balanced"  # 行业均衡
    RISK_ADJUSTED = "risk_adjusted"         # 风险调整
    MOMENTUM_FOCUSED = "momentum_focused"    # 动量聚焦
    VALUE_ORIENTED = "value_oriented"       # 价值导向
    HYBRID = "hybrid"                       # 混合策略


@dataclass
class SamplingConfig:
    """智能采样配置"""
    strategy: SamplingStrategy = SamplingStrategy.HYBRID
    max_candidates: int = 500                    # 最大候选股票数
    min_market_cap: float = 10.0                # 最小市值(亿元)
    min_daily_volume: float = 10000000          # 最小日成交额(元)
    min_price: float = 2.0                      # 最小股价(元)
    max_price: float = 200.0                    # 最大股价(元)
    exclude_st_stocks: bool = True              # 排除ST股票
    exclude_suspend: bool = True                # 排除停牌股票
    activity_days: int = 30                     # 活跃度计算天数
    industry_max_ratio: float = 0.3             # 单行业最大占比
    enable_momentum_filter: bool = True         # 启用动量筛选
    momentum_threshold: float = -10.0           # 动量阈值(%)
    enable_cache: bool = True                   # 启用缓存
    cache_ttl: int = 3600                       # 缓存TTL(秒)


@dataclass
class SamplingResult:
    """采样结果"""
    sampled_stocks: List[str]                   # 采样得到的股票列表
    original_count: int                         # 原始股票数量
    filtered_count: int                         # 过滤后数量
    sampling_ratio: float                       # 采样比例
    strategy_used: SamplingStrategy             # 使用的策略
    execution_time: float                       # 执行时间
    quality_score: float                        # 质量评分
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息


class IntelligentSampler:
    """智能数据采样器"""
    
    def __init__(self, data_manager: EnhancedDataManager = None):
        """
        初始化智能采样器
        
        Args:
            data_manager: 数据管理器实例
        """
        self.data_manager = data_manager or EnhancedDataManager()
        self._cache = {}
        self._cache_timestamps = {}
        
        logger.info("🎯 智能数据采样器初始化完成")
    
    def smart_sample(self, stock_list: pd.DataFrame, config: SamplingConfig) -> SamplingResult:
        """
        智能采样主入口
        
        Args:
            stock_list: 原始股票列表
            config: 采样配置
            
        Returns:
            SamplingResult: 采样结果
        """
        start_time = time.time()
        original_count = len(stock_list)
        
        logger.info(f"🚀 开始智能采样: {original_count}只股票 -> 目标:{config.max_candidates}只")
        logger.info(f"📋 采样策略: {config.strategy.value}")
        
        try:
            # 1. 基础筛选 (快速过滤明显不合适的股票)
            logger.info("🔍 执行基础筛选...")
            basic_filtered = self._basic_filter(stock_list, config)
            logger.info(f"✅ 基础筛选完成: {len(basic_filtered)}只股票通过")
            
            # 2. 活跃度计算 (如果需要)
            if config.strategy in [SamplingStrategy.ACTIVITY_BASED, SamplingStrategy.HYBRID]:
                logger.info("📊 计算股票活跃度...")
                basic_filtered = self._calculate_activity_scores(basic_filtered, config)
                logger.info("✅ 活跃度计算完成")
            
            # 3. 应用采样策略
            logger.info(f"🎯 应用采样策略: {config.strategy.value}...")
            sampled_stocks = self._apply_sampling_strategy(basic_filtered, config)
            
            # 4. 质量评估
            quality_score = self._evaluate_sample_quality(sampled_stocks, basic_filtered, config)
            
            execution_time = time.time() - start_time
            
            result = SamplingResult(
                sampled_stocks=sampled_stocks['ts_code'].tolist() if 'ts_code' in sampled_stocks.columns else [],
                original_count=original_count,
                filtered_count=len(basic_filtered),
                sampling_ratio=len(sampled_stocks) / max(original_count, 1),
                strategy_used=config.strategy,
                execution_time=execution_time,
                quality_score=quality_score,
                details={
                    'basic_filter_ratio': len(basic_filtered) / max(original_count, 1),
                    'final_sample_count': len(sampled_stocks),
                    'strategies_applied': [config.strategy.value]
                }
            )
            
            logger.info(f"✅ 智能采样完成: {len(sampled_stocks)}只股票, 耗时{execution_time:.2f}秒")
            logger.info(f"📈 采样比例: {result.sampling_ratio:.1%}, 质量评分: {quality_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 智能采样失败: {e}")
            execution_time = time.time() - start_time
            return SamplingResult(
                sampled_stocks=[],
                original_count=original_count,
                filtered_count=0,
                sampling_ratio=0.0,
                strategy_used=config.strategy,
                execution_time=execution_time,
                quality_score=0.0,
                details={'error': str(e)}
            )
    
    def _basic_filter(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """基础筛选 - 快速过滤明显不合适的股票"""
        if stock_list.empty:
            return stock_list
        
        filtered = stock_list.copy()
        original_count = len(filtered)
        
        # 1. 排除ST股票
        if config.exclude_st_stocks:
            if 'name' in filtered.columns:
                st_mask = ~filtered['name'].str.contains('ST|\\*ST|退', na=False)
                filtered = filtered[st_mask]
                logger.info(f"🚫 排除ST股票: {original_count} -> {len(filtered)}")
        
        # 2. 基础价格筛选
        if 'current_price' in filtered.columns:
            price_mask = (
                (filtered['current_price'] >= config.min_price) & 
                (filtered['current_price'] <= config.max_price) &
                (filtered['current_price'] > 0)
            )
            filtered = filtered[price_mask]
            logger.info(f"💰 价格筛选 ({config.min_price}-{config.max_price}元): {len(filtered)}只股票通过")
        
        # 3. 市值筛选
        if 'market_cap' in filtered.columns:
            market_cap_mask = filtered['market_cap'] >= config.min_market_cap * 100000000  # 转换为元
            filtered = filtered[market_cap_mask]
            logger.info(f"🏢 市值筛选 (≥{config.min_market_cap}亿): {len(filtered)}只股票通过")
        
        # 4. 成交量筛选 (如果有数据)
        if 'turnover' in filtered.columns:
            volume_mask = filtered['turnover'] >= config.min_daily_volume
            filtered = filtered[volume_mask]
            logger.info(f"📊 成交额筛选 (≥{config.min_daily_volume/10000:.0f}万): {len(filtered)}只股票通过")
        
        return filtered.reset_index(drop=True)
    
    def _calculate_activity_scores(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """计算股票活跃度评分"""
        if stock_list.empty:
            return stock_list
        
        enhanced_list = stock_list.copy()
        enhanced_list['activity_score'] = 0.0
        
        # 简化的活跃度计算 (避免过多API调用)
        if 'turnover' in enhanced_list.columns and 'volume' in enhanced_list.columns:
            # 基于现有数据计算活跃度
            enhanced_list['turnover_score'] = enhanced_list['turnover'].rank(pct=True)
            enhanced_list['volume_score'] = enhanced_list['volume'].rank(pct=True)
            
            # 综合活跃度评分
            enhanced_list['activity_score'] = (
                enhanced_list['turnover_score'] * 0.6 + 
                enhanced_list['volume_score'] * 0.4
            )
            
            # 加入换手率因子 (如果有数据)
            if 'turnover_rate' in enhanced_list.columns:
                enhanced_list['turnover_rate_score'] = enhanced_list['turnover_rate'].rank(pct=True)
                enhanced_list['activity_score'] = (
                    enhanced_list['activity_score'] * 0.7 +
                    enhanced_list['turnover_rate_score'] * 0.3
                )
        
        # 如果没有基础数据，使用简单的随机评分 + 市值权重
        else:
            if 'market_cap' in enhanced_list.columns:
                enhanced_list['activity_score'] = enhanced_list['market_cap'].rank(pct=True) * 0.6 + np.random.rand(len(enhanced_list)) * 0.4
            else:
                enhanced_list['activity_score'] = np.random.rand(len(enhanced_list))
        
        # 标准化到 0-1 范围
        if enhanced_list['activity_score'].std() > 0:
            enhanced_list['activity_score'] = (
                (enhanced_list['activity_score'] - enhanced_list['activity_score'].min()) /
                (enhanced_list['activity_score'].max() - enhanced_list['activity_score'].min())
            )
        
        return enhanced_list
    
    def _apply_sampling_strategy(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """应用具体的采样策略"""
        if len(stock_list) <= config.max_candidates:
            logger.info(f"📊 股票数量({len(stock_list)})未超过目标({config.max_candidates})，无需采样")
            return stock_list
        
        strategy = config.strategy
        
        if strategy == SamplingStrategy.ACTIVITY_BASED:
            return self._activity_based_sampling(stock_list, config)
        elif strategy == SamplingStrategy.MARKET_CAP_WEIGHTED:
            return self._market_cap_weighted_sampling(stock_list, config)
        elif strategy == SamplingStrategy.INDUSTRY_BALANCED:
            return self._industry_balanced_sampling(stock_list, config)
        elif strategy == SamplingStrategy.RISK_ADJUSTED:
            return self._risk_adjusted_sampling(stock_list, config)
        elif strategy == SamplingStrategy.MOMENTUM_FOCUSED:
            return self._momentum_focused_sampling(stock_list, config)
        elif strategy == SamplingStrategy.VALUE_ORIENTED:
            return self._value_oriented_sampling(stock_list, config)
        elif strategy == SamplingStrategy.HYBRID:
            return self._hybrid_sampling(stock_list, config)
        else:
            # 默认使用随机采样
            return stock_list.sample(n=min(config.max_candidates, len(stock_list)), random_state=42)
    
    def _activity_based_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """基于活跃度的采样"""
        if 'activity_score' not in stock_list.columns:
            logger.warning("⚠️ 缺少活跃度数据，使用随机采样")
            return stock_list.sample(n=min(config.max_candidates, len(stock_list)), random_state=42)
        
        # 按活跃度评分排序，选择前N个
        sorted_stocks = stock_list.sort_values('activity_score', ascending=False)
        top_candidates = sorted_stocks.head(config.max_candidates)
        
        logger.info(f"🎯 活跃度采样: 选择活跃度最高的 {len(top_candidates)} 只股票")
        return top_candidates
    
    def _market_cap_weighted_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """市值加权采样"""
        if 'market_cap' not in stock_list.columns:
            logger.warning("⚠️ 缺少市值数据，使用随机采样")
            return stock_list.sample(n=min(config.max_candidates, len(stock_list)), random_state=42)
        
        # 根据市值进行加权随机采样
        weights = stock_list['market_cap'] / stock_list['market_cap'].sum()
        sampled = stock_list.sample(
            n=min(config.max_candidates, len(stock_list)), 
            weights=weights, 
            random_state=42
        )
        
        logger.info(f"⚖️ 市值加权采样: 选择 {len(sampled)} 只股票")
        return sampled
    
    def _industry_balanced_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """行业均衡采样"""
        if 'industry' not in stock_list.columns:
            logger.warning("⚠️ 缺少行业数据，使用随机采样")
            return stock_list.sample(n=min(config.max_candidates, len(stock_list)), random_state=42)
        
        # 按行业分组，每个行业最多选择一定比例
        industry_counts = stock_list['industry'].value_counts()
        max_per_industry = max(1, int(config.max_candidates * config.industry_max_ratio))
        
        sampled_list = []
        for industry in industry_counts.index:
            industry_stocks = stock_list[stock_list['industry'] == industry]
            # 如果该行业有活跃度数据，优先选择活跃的
            if 'activity_score' in industry_stocks.columns:
                industry_sample = industry_stocks.nlargest(
                    min(max_per_industry, len(industry_stocks)), 
                    'activity_score'
                )
            else:
                industry_sample = industry_stocks.sample(
                    n=min(max_per_industry, len(industry_stocks)), 
                    random_state=42
                )
            sampled_list.append(industry_sample)
            
            if sum(len(df) for df in sampled_list) >= config.max_candidates:
                break
        
        result = pd.concat(sampled_list, ignore_index=True)
        if len(result) > config.max_candidates:
            result = result.head(config.max_candidates)
        
        logger.info(f"🏭 行业均衡采样: 选择 {len(result)} 只股票，覆盖 {len(sampled_list)} 个行业")
        return result
    
    def _risk_adjusted_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """风险调整采样"""
        # 简化的风险评估：基于价格波动性
        risk_adjusted = stock_list.copy()
        
        # 使用市值和价格作为风险代理指标
        if 'market_cap' in risk_adjusted.columns and 'current_price' in risk_adjusted.columns:
            # 大市值股票风险较低，价格适中的股票风险较低
            risk_adjusted['risk_score'] = (
                risk_adjusted['market_cap'].rank(pct=True) * 0.6 +
                (1 - np.abs(risk_adjusted['current_price'] - risk_adjusted['current_price'].median()).rank(pct=True)) * 0.4
            )
        else:
            risk_adjusted['risk_score'] = np.random.rand(len(risk_adjusted))
        
        # 选择风险适中的股票
        sampled = risk_adjusted.nlargest(config.max_candidates, 'risk_score')
        logger.info(f"⚡ 风险调整采样: 选择风险评分最佳的 {len(sampled)} 只股票")
        return sampled
    
    def _momentum_focused_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """动量聚焦采样"""
        momentum_stocks = stock_list.copy()
        
        # 简化的动量计算
        if 'change_pct' in momentum_stocks.columns:
            # 过滤掉表现过差的股票
            momentum_filter = momentum_stocks['change_pct'] >= config.momentum_threshold
            momentum_stocks = momentum_stocks[momentum_filter]
            
            # 按涨跌幅排序选择
            sampled = momentum_stocks.nlargest(
                min(config.max_candidates, len(momentum_stocks)), 
                'change_pct'
            )
        else:
            # 如果没有涨跌幅数据，随机选择
            sampled = momentum_stocks.sample(
                n=min(config.max_candidates, len(momentum_stocks)), 
                random_state=42
            )
        
        logger.info(f"🚀 动量聚焦采样: 选择 {len(sampled)} 只股票")
        return sampled
    
    def _value_oriented_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """价值导向采样"""
        value_stocks = stock_list.copy()
        
        # 基于市盈率等估值指标选择
        if 'pe_ratio' in value_stocks.columns:
            # 过滤掉异常PE值
            pe_filter = (value_stocks['pe_ratio'] > 0) & (value_stocks['pe_ratio'] < 100)
            value_filtered = value_stocks[pe_filter]
            
            if not value_filtered.empty:
                # 选择PE较低的股票
                sampled = value_filtered.nsmallest(
                    min(config.max_candidates, len(value_filtered)), 
                    'pe_ratio'
                )
            else:
                sampled = value_stocks.sample(
                    n=min(config.max_candidates, len(value_stocks)), 
                    random_state=42
                )
        else:
            sampled = value_stocks.sample(
                n=min(config.max_candidates, len(value_stocks)), 
                random_state=42
            )
        
        logger.info(f"💎 价值导向采样: 选择 {len(sampled)} 只股票")
        return sampled
    
    def _hybrid_sampling(self, stock_list: pd.DataFrame, config: SamplingConfig) -> pd.DataFrame:
        """混合策略采样 - 综合多种方法"""
        logger.info("🎭 执行混合策略采样...")
        
        total_target = config.max_candidates
        
        # 策略分配比例
        strategies = [
            ('activity', 0.4),      # 40% 基于活跃度
            ('market_cap', 0.25),   # 25% 基于市值
            ('industry', 0.2),      # 20% 行业均衡
            ('risk', 0.15)          # 15% 风险调整
        ]
        
        sampled_parts = []
        used_symbols = set()
        
        for strategy_name, ratio in strategies:
            strategy_target = int(total_target * ratio)
            if strategy_target == 0:
                continue
                
            # 从未选择的股票中采样
            remaining_stocks = stock_list[~stock_list.index.isin(used_symbols)]
            if remaining_stocks.empty:
                break
            
            logger.info(f"🔄 {strategy_name}策略采样: 目标 {strategy_target} 只")
            
            if strategy_name == 'activity':
                strategy_sample = self._activity_based_sampling(
                    remaining_stocks, 
                    SamplingConfig(max_candidates=strategy_target)
                )
            elif strategy_name == 'market_cap':
                strategy_sample = self._market_cap_weighted_sampling(
                    remaining_stocks,
                    SamplingConfig(max_candidates=strategy_target)
                )
            elif strategy_name == 'industry':
                strategy_sample = self._industry_balanced_sampling(
                    remaining_stocks,
                    SamplingConfig(max_candidates=strategy_target, industry_max_ratio=0.5)
                )
            elif strategy_name == 'risk':
                strategy_sample = self._risk_adjusted_sampling(
                    remaining_stocks,
                    SamplingConfig(max_candidates=strategy_target)
                )
            
            if not strategy_sample.empty:
                sampled_parts.append(strategy_sample)
                used_symbols.update(strategy_sample.index)
                logger.info(f"✅ {strategy_name}策略完成: 选择 {len(strategy_sample)} 只股票")
        
        # 合并所有采样结果
        if sampled_parts:
            final_sample = pd.concat(sampled_parts, ignore_index=True)
            
            # 如果还没达到目标数量，随机补充
            if len(final_sample) < total_target:
                remaining_stocks = stock_list[~stock_list.index.isin(used_symbols)]
                if not remaining_stocks.empty:
                    additional_needed = total_target - len(final_sample)
                    additional_sample = remaining_stocks.sample(
                        n=min(additional_needed, len(remaining_stocks)),
                        random_state=42
                    )
                    final_sample = pd.concat([final_sample, additional_sample], ignore_index=True)
            
            # 去重并限制数量
            final_sample = final_sample.drop_duplicates(subset=['ts_code'] if 'ts_code' in final_sample.columns else None)
            final_sample = final_sample.head(total_target)
            
            logger.info(f"🎯 混合策略采样完成: 最终选择 {len(final_sample)} 只股票")
            return final_sample
        else:
            # 回退到随机采样
            logger.warning("⚠️ 混合策略失败，使用随机采样")
            return stock_list.sample(n=min(total_target, len(stock_list)), random_state=42)
    
    def _evaluate_sample_quality(self, sampled_stocks: pd.DataFrame, 
                                original_stocks: pd.DataFrame, 
                                config: SamplingConfig) -> float:
        """评估采样质量"""
        if sampled_stocks.empty or original_stocks.empty:
            return 0.0
        
        quality_score = 0.0
        
        # 1. 覆盖性评分 (采样比例)
        coverage_score = len(sampled_stocks) / min(config.max_candidates, len(original_stocks))
        quality_score += coverage_score * 0.3
        
        # 2. 多样性评分 (行业分布)
        if 'industry' in sampled_stocks.columns:
            sampled_industries = sampled_stocks['industry'].nunique()
            original_industries = original_stocks['industry'].nunique()
            diversity_score = sampled_industries / max(original_industries, 1)
            quality_score += diversity_score * 0.3
        
        # 3. 代表性评分 (市值分布)
        if 'market_cap' in sampled_stocks.columns:
            sampled_market_cap_std = sampled_stocks['market_cap'].std()
            original_market_cap_std = original_stocks['market_cap'].std()
            if original_market_cap_std > 0:
                representation_score = min(1.0, sampled_market_cap_std / original_market_cap_std)
                quality_score += representation_score * 0.2
        
        # 4. 活跃度评分
        if 'activity_score' in sampled_stocks.columns:
            avg_activity = sampled_stocks['activity_score'].mean()
            quality_score += avg_activity * 0.2
        
        return min(1.0, quality_score)


# 全局采样器实例
_intelligent_sampler = None

def get_intelligent_sampler() -> IntelligentSampler:
    """获取全局智能采样器实例"""
    global _intelligent_sampler
    if _intelligent_sampler is None:
        _intelligent_sampler = IntelligentSampler()
    return _intelligent_sampler