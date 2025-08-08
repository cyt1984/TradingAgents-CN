#!/usr/bin/env python3
"""
智能选股核心引擎
基于多源数据融合和综合评分系统的A股选股引擎
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import time
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入相关模块
from .filter_conditions import (
    FilterCondition, FilterGroup, FilterLogic, STOCK_FILTER_FIELDS,
    NumericFilter, EnumFilter, BooleanFilter, FilterOperator
)
from ..analytics.comprehensive_scoring_system import get_comprehensive_scoring_system, ComprehensiveScore
from ..analytics.data_fusion_engine import get_fusion_engine
from ..dataflows.enhanced_data_manager import EnhancedDataManager
from ..dataflows.tushare_utils import get_tushare_provider
from ..utils.logging_manager import get_logger

logger = get_logger('agents')


@dataclass
class SelectionCriteria:
    """选股标准"""
    filters: List[Union[FilterCondition, FilterGroup]] = field(default_factory=list)  # 筛选条件
    sort_by: Optional[str] = 'overall_score'                     # 排序字段
    sort_ascending: bool = False                                 # 排序方向
    limit: Optional[int] = 100                                   # 结果数量限制
    include_scores: bool = True                                  # 是否包含评分数据
    include_basic_info: bool = True                              # 是否包含基本信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'filters': [f.to_dict() if hasattr(f, 'to_dict') else str(f) for f in self.filters],
            'sort_by': self.sort_by,
            'sort_ascending': self.sort_ascending,
            'limit': self.limit,
            'include_scores': self.include_scores,
            'include_basic_info': self.include_basic_info
        }


@dataclass  
class SelectionResult:
    """选股结果"""
    symbols: List[str]                          # 股票代码列表
    data: pd.DataFrame                          # 详细数据
    summary: Dict[str, Any]                     # 统计摘要
    criteria: SelectionCriteria                 # 选股标准
    execution_time: float                       # 执行时间
    total_candidates: int                       # 候选股票总数
    filtered_count: int                         # 筛选后数量
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbols': self.symbols,
            'data': self.data.to_dict('records') if not self.data.empty else [],
            'summary': self.summary,
            'criteria': self.criteria.to_dict(),
            'execution_time': self.execution_time,
            'total_candidates': self.total_candidates,
            'filtered_count': self.filtered_count
        }


class StockSelector:
    """智能选股引擎"""
    
    def __init__(self, cache_enabled: bool = True):
        """
        初始化选股引擎
        
        Args:
            cache_enabled: 是否启用缓存机制
        """
        self.cache_enabled = cache_enabled
        self.data_manager = None
        self.scoring_system = None
        self.fusion_engine = None
        self.tushare_provider = None
        self._stock_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 缓存5分钟
        
        # 初始化组件
        self._init_components()
    
    def _init_components(self):
        """初始化相关组件"""
        try:
            # 初始化数据管理器
            self.data_manager = EnhancedDataManager()
            logger.info("✅ 数据管理器初始化成功")
            
            # 初始化综合评分系统
            self.scoring_system = get_comprehensive_scoring_system()
            logger.info("✅ 综合评分系统初始化成功")
            
            # 初始化数据融合引擎
            self.fusion_engine = get_fusion_engine()
            logger.info("✅ 数据融合引擎初始化成功")
            
            # 初始化Tushare数据提供者
            self.tushare_provider = get_tushare_provider()
            logger.info("✅ Tushare数据提供者初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            raise
    
    def get_available_fields(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的筛选字段"""
        return STOCK_FILTER_FIELDS.copy()
    
    def create_numeric_filter(
        self, 
        field_name: str, 
        operator: FilterOperator, 
        value: Union[float, int, Tuple[float, float]]
    ) -> NumericFilter:
        """创建数值筛选条件"""
        field_info = STOCK_FILTER_FIELDS.get(field_name, {})
        return NumericFilter(
            field_name=field_name,
            field_display_name=field_info.get('name', field_name),
            operator=operator,
            value=value,
            description=field_info.get('description', '')
        )
    
    def create_enum_filter(
        self, 
        field_name: str, 
        operator: FilterOperator, 
        value: Union[str, List[str]]
    ) -> EnumFilter:
        """创建枚举筛选条件"""
        field_info = STOCK_FILTER_FIELDS.get(field_name, {})
        return EnumFilter(
            field_name=field_name,
            field_display_name=field_info.get('name', field_name),
            operator=operator,
            value=value,
            allowed_values=field_info.get('allowed_values'),
            description=field_info.get('description', '')
        )
    
    def create_boolean_filter(
        self, 
        field_name: str, 
        operator: FilterOperator, 
        value: bool
    ) -> BooleanFilter:
        """创建布尔筛选条件"""
        field_info = STOCK_FILTER_FIELDS.get(field_name, {})
        return BooleanFilter(
            field_name=field_name,
            field_display_name=field_info.get('name', field_name),
            operator=operator,
            value=value,
            description=field_info.get('description', '')
        )
    
    def _get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        # 检查缓存
        if (self.cache_enabled and 
            self._stock_cache and 
            self._cache_timestamp and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            logger.info("📦 从缓存获取股票列表")
            return self._stock_cache.copy()
        
        try:
            # 从Tushare获取股票列表
            stock_list = self.tushare_provider.get_stock_list()
            
            if stock_list.empty:
                logger.warning("⚠️ 获取的股票列表为空")
                return pd.DataFrame()
            
            # 更新缓存
            if self.cache_enabled:
                self._stock_cache = stock_list.copy()
                self._cache_timestamp = time.time()
            
            logger.info(f"✅ 获取股票列表成功: {len(stock_list)}只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def _enrich_stock_data(self, stock_data: pd.DataFrame, include_scores: bool = True) -> pd.DataFrame:
        """丰富股票数据"""
        if stock_data.empty:
            return stock_data
        
        enriched_data = stock_data.copy()
        
        # 添加综合评分数据
        if include_scores and self.scoring_system:
            try:
                logger.info("🔄 正在获取综合评分数据...")
                
                # 批量获取评分（限制并发数量避免API限制）
                batch_size = 10
                symbols = enriched_data['ts_code'].tolist()
                all_scores = []
                
                for i in range(0, len(symbols), batch_size):
                    batch_symbols = symbols[i:i + batch_size]
                    batch_scores = []
                    
                    for symbol in batch_symbols:
                        try:
                            # 获取基础数据用于评分
                            basic_data = self.data_manager.get_latest_price_data(symbol)
                            if basic_data:
                                score = self.scoring_system.calculate_comprehensive_score(symbol, basic_data)
                                batch_scores.append({
                                    'ts_code': symbol,
                                    'overall_score': score.overall_score,
                                    'grade': score.grade,
                                    'technical_score': score.category_scores.get('technical', {}).get('score', 0),
                                    'fundamental_score': score.category_scores.get('fundamental', {}).get('score', 0),
                                    'sentiment_score': score.category_scores.get('sentiment', {}).get('score', 0),
                                    'quality_score': score.category_scores.get('quality', {}).get('score', 0),
                                    'risk_score': score.category_scores.get('risk', {}).get('score', 0)
                                })
                        except Exception as e:
                            logger.warning(f"⚠️ 获取 {symbol} 评分失败: {e}")
                            continue
                    
                    all_scores.extend(batch_scores)
                    
                    # 添加延迟避免API限制
                    if i + batch_size < len(symbols):
                        time.sleep(0.1)
                
                if all_scores:
                    scores_df = pd.DataFrame(all_scores)
                    enriched_data = enriched_data.merge(scores_df, on='ts_code', how='left')
                    logger.info(f"✅ 添加评分数据成功: {len(scores_df)}条记录")
                else:
                    logger.warning("⚠️ 未获取到有效的评分数据")
                    
            except Exception as e:
                logger.error(f"❌ 获取综合评分数据失败: {e}")
        
        return enriched_data
    
    def _apply_filters(self, data: pd.DataFrame, filters: List[Union[FilterCondition, FilterGroup]]) -> pd.DataFrame:
        """应用筛选条件"""
        if not filters or data.empty:
            return data
        
        # 创建总的筛选组
        main_group = FilterGroup(conditions=filters, logic=FilterLogic.AND)
        
        try:
            # 应用筛选
            filter_mask = main_group.apply_filter(data)
            filtered_data = data[filter_mask].copy()
            
            logger.info(f"🔍 筛选完成: {len(data)} -> {len(filtered_data)}只股票")
            return filtered_data
            
        except Exception as e:
            logger.error(f"❌ 应用筛选条件失败: {e}")
            return data
    
    def _generate_summary(self, data: pd.DataFrame, total_candidates: int) -> Dict[str, Any]:
        """生成统计摘要"""
        if data.empty:
            return {
                'total_candidates': total_candidates,
                'filtered_count': 0,
                'success_rate': 0.0,
                'statistics': {}
            }
        
        summary = {
            'total_candidates': total_candidates,
            'filtered_count': len(data),
            'success_rate': len(data) / max(total_candidates, 1) * 100,
            'statistics': {}
        }
        
        # 基础统计
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in data.columns and not data[col].isna().all():
                summary['statistics'][col] = {
                    'mean': float(data[col].mean()),
                    'median': float(data[col].median()),
                    'std': float(data[col].std()),
                    'min': float(data[col].min()),
                    'max': float(data[col].max()),
                    'count': int(data[col].count())
                }
        
        # 行业分布
        if 'industry' in data.columns:
            industry_counts = data['industry'].value_counts().head(10)
            summary['industry_distribution'] = industry_counts.to_dict()
        
        # 评级分布
        if 'grade' in data.columns:
            grade_counts = data['grade'].value_counts()
            summary['grade_distribution'] = grade_counts.to_dict()
        
        return summary
    
    def select_stocks(self, criteria: SelectionCriteria) -> SelectionResult:
        """
        执行选股操作
        
        Args:
            criteria: 选股标准
            
        Returns:
            SelectionResult: 选股结果
        """
        start_time = time.time()
        logger.info("🚀 开始执行智能选股...")
        
        try:
            # 1. 获取基础股票列表
            logger.info("📋 获取股票列表...")
            stock_data = self._get_stock_list()
            
            if stock_data.empty:
                logger.warning("⚠️ 未获取到股票数据")
                return SelectionResult(
                    symbols=[],
                    data=pd.DataFrame(),
                    summary={'error': '未获取到股票数据'},
                    criteria=criteria,
                    execution_time=time.time() - start_time,
                    total_candidates=0,
                    filtered_count=0
                )
            
            total_candidates = len(stock_data)
            logger.info(f"📊 候选股票总数: {total_candidates}")
            
            # 2. 丰富股票数据
            if criteria.include_scores or criteria.include_basic_info:
                logger.info("🔄 正在丰富股票数据...")
                stock_data = self._enrich_stock_data(
                    stock_data, 
                    include_scores=criteria.include_scores
                )
            
            # 3. 应用筛选条件
            if criteria.filters:
                logger.info("🔍 正在应用筛选条件...")
                filtered_data = self._apply_filters(stock_data, criteria.filters)
            else:
                filtered_data = stock_data.copy()
            
            # 4. 排序
            if criteria.sort_by and criteria.sort_by in filtered_data.columns:
                logger.info(f"📈 按 {criteria.sort_by} 排序...")
                filtered_data = filtered_data.sort_values(
                    by=criteria.sort_by, 
                    ascending=criteria.sort_ascending
                )
            
            # 5. 限制结果数量
            if criteria.limit and len(filtered_data) > criteria.limit:
                filtered_data = filtered_data.head(criteria.limit)
                logger.info(f"✂️ 限制结果数量为: {criteria.limit}")
            
            # 6. 生成结果
            symbols = filtered_data['ts_code'].tolist() if 'ts_code' in filtered_data.columns else []
            summary = self._generate_summary(filtered_data, total_candidates)
            
            execution_time = time.time() - start_time
            
            result = SelectionResult(
                symbols=symbols,
                data=filtered_data,
                summary=summary,
                criteria=criteria,
                execution_time=execution_time,
                total_candidates=total_candidates,
                filtered_count=len(filtered_data)
            )
            
            logger.info(f"✅ 选股完成: {len(symbols)}只股票, 耗时 {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"❌ 选股操作失败: {e}")
            return SelectionResult(
                symbols=[],
                data=pd.DataFrame(),
                summary={'error': str(e)},
                criteria=criteria,
                execution_time=time.time() - start_time,
                total_candidates=0,
                filtered_count=0
            )
    
    def quick_select(
        self, 
        min_score: float = 70.0, 
        min_market_cap: float = 50.0,
        max_pe_ratio: float = 30.0,
        grades: List[str] = None,
        limit: int = 50
    ) -> SelectionResult:
        """
        快速选股 - 使用预设的常用条件
        
        Args:
            min_score: 最小综合评分
            min_market_cap: 最小市值（亿元）
            max_pe_ratio: 最大市盈率
            grades: 投资等级列表
            limit: 结果数量限制
            
        Returns:
            SelectionResult: 选股结果
        """
        filters = []
        
        # 综合评分筛选
        filters.append(self.create_numeric_filter(
            'overall_score', FilterOperator.GREATER_EQUAL, min_score
        ))
        
        # 市值筛选
        if min_market_cap > 0:
            filters.append(self.create_numeric_filter(
                'market_cap', FilterOperator.GREATER_EQUAL, min_market_cap
            ))
        
        # 市盈率筛选
        if max_pe_ratio > 0:
            filters.append(self.create_numeric_filter(
                'pe_ratio', FilterOperator.LESS_EQUAL, max_pe_ratio
            ))
        
        # 投资等级筛选
        if grades:
            filters.append(self.create_enum_filter(
                'grade', FilterOperator.IN, grades
            ))
        
        criteria = SelectionCriteria(
            filters=filters,
            sort_by='overall_score',
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True
        )
        
        return self.select_stocks(criteria)


# 全局选股引擎实例
_stock_selector = None

def get_stock_selector(cache_enabled: bool = True) -> StockSelector:
    """获取全局选股引擎实例"""
    global _stock_selector
    if _stock_selector is None:
        _stock_selector = StockSelector(cache_enabled=cache_enabled)
    return _stock_selector