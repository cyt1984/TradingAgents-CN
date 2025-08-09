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
from ..utils.logging_manager import get_logger
from .ai_strategies.ai_strategy_manager import get_ai_strategy_manager, AIMode, AISelectionConfig

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
    
    # AI增强选项
    ai_mode: AIMode = AIMode.BASIC                               # AI模式
    ai_config: Optional[AISelectionConfig] = None               # AI配置
    
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
        self._stock_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 缓存5分钟
        
        # AI策略管理器
        self.ai_strategy_manager = None
        
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
            
            
            # 初始化AI策略管理器
            try:
                self.ai_strategy_manager = get_ai_strategy_manager()
                logger.info("✅ AI策略管理器初始化成功")
            except Exception as ai_error:
                logger.warning(f"⚠️ AI策略管理器初始化失败，将使用基础模式: {ai_error}")
                self.ai_strategy_manager = None
            
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
        """获取股票列表 - 仅使用免费数据源"""
        # 检查缓存
        if (self.cache_enabled and 
            self._stock_cache is not None and 
            self._cache_timestamp and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            logger.info("从缓存获取股票列表")
            return self._stock_cache.copy()
        
        try:
            # 仅使用增强数据管理器获取A股数据，避免Tushare权限问题
            if self.data_manager and hasattr(self.data_manager, 'get_stock_list'):
                stock_data = self.data_manager.get_stock_list('A')
                if stock_data and len(stock_data) > 0:
                    # 将列表转换为DataFrame
                    stock_list = pd.DataFrame(stock_data)
                    # 重命名列以保持一致性
                    if 'symbol' in stock_list.columns and 'name' in stock_list.columns:
                        stock_list = stock_list.rename(columns={'symbol': 'ts_code', 'name': 'name'})
                    logger.info(f"从增强数据管理器获取A股列表成功: {len(stock_list)}只股票")
                    
                    # 更新缓存
                    if self.cache_enabled:
                        self._stock_cache = stock_list.copy()
                        self._cache_timestamp = time.time()
                    
                    return stock_list
            
            logger.warning("获取的股票列表为空")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
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
    
    def _enrich_stock_data_with_ai(self, stock_data: pd.DataFrame, 
                                  ai_config: AISelectionConfig = None) -> pd.DataFrame:
        """使用AI增强股票数据"""
        if stock_data.empty:
            logger.warning("⚠️ 股票数据为空，跳过AI增强")
            return stock_data
        
        if not self.ai_strategy_manager:
            logger.warning("⚠️ AI策略管理器未初始化，跳过AI增强")
            return stock_data
            
        try:
            logger.info(f"🤖 开始AI增强数据处理，股票数量: {len(stock_data)}")
            
            ai_config = ai_config or AISelectionConfig()
            enriched_data = stock_data.copy()
            
            # 检查AI引擎可用性
            ai_status = self.ai_strategy_manager.get_performance_summary()
            available_engines = ai_status.get('engine_availability', {}).get('available_count', 0)
            
            if available_engines == 0:
                logger.warning("⚠️ 没有可用的AI引擎，使用基础评分")
                # 添加基础AI评分列以保持兼容性
                enriched_data['ai_overall_score'] = enriched_data.get('overall_score', 50)
                enriched_data['ai_confidence'] = 0.3
                enriched_data['ai_recommendation'] = '数据不足'
                enriched_data['ai_risk_assessment'] = '未评估'
                return enriched_data
            
            logger.info(f"🤖 发现 {available_engines} 个可用AI引擎")
            
            # 准备股票数据列表
            stock_list = []
            for _, row in stock_data.iterrows():
                stock_info = row.to_dict()
                # 获取额外的股票数据
                symbol = stock_info.get('ts_code', '')
                if symbol:
                    try:
                        # 获取基础数据
                        if hasattr(self, 'data_manager') and self.data_manager:
                            basic_data = self.data_manager.get_latest_price_data(symbol)
                            if basic_data:
                                stock_info.update(basic_data)
                    except Exception as e:
                        logger.debug(f"获取 {symbol} 基础数据失败: {e}")
                
                stock_list.append(stock_info)
            
            # 动态调整批次大小
            total_stocks = len(stock_list)
            if total_stocks <= 10:
                batch_size = total_stocks  # 小批量直接处理
            elif total_stocks <= 50:
                batch_size = 10
            elif total_stocks <= 200:
                batch_size = 15
            else:
                batch_size = 20
            
            logger.info(f"🤖 使用批次大小: {batch_size}，总批次: {(total_stocks + batch_size - 1) // batch_size}")
            
            ai_results = []
            successful_batches = 0
            failed_batches = 0
            
            for i in range(0, len(stock_list), batch_size):
                batch = stock_list[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                try:
                    logger.debug(f"🤖 处理批次 {batch_num}：{len(batch)} 只股票")
                    
                    # 准备市场数据（如果需要）
                    market_data = None
                    if ai_config.market_data_required:
                        try:
                            # 简单的市场数据（可以后续扩展）
                            market_data = {
                                'market_type': 'A股',
                                'timestamp': datetime.now(),
                                'news_data': []  # 可以添加新闻数据
                            }
                        except Exception:
                            market_data = None
                    
                    batch_results = self.ai_strategy_manager.batch_analyze_stocks(
                        batch, market_data=market_data, config=ai_config
                    )
                    
                    if batch_results:
                        ai_results.extend(batch_results)
                        successful_batches += 1
                        logger.debug(f"✅ 批次 {batch_num} 处理成功，获得 {len(batch_results)} 个分析结果")
                    else:
                        logger.warning(f"⚠️ 批次 {batch_num} 返回空结果")
                        failed_batches += 1
                        
                except Exception as e:
                    logger.warning(f"❌ AI批量分析失败 (批次 {batch_num}): {e}")
                    failed_batches += 1
                    
                    # 为失败的批次创建默认结果
                    for stock_info in batch:
                        symbol = stock_info.get('ts_code', stock_info.get('symbol', ''))
                        # 创建简单的默认结果对象
                        default_result = type('AIResult', (), {
                            'symbol': symbol,
                            'overall_score': enriched_data.loc[enriched_data.get('ts_code', '') == symbol, 'overall_score'].iloc[0] if 'overall_score' in enriched_data.columns and len(enriched_data.loc[enriched_data.get('ts_code', '') == symbol]) > 0 else 50.0,
                            'confidence_level': 0.2,
                            'recommendation': '数据不足',
                            'risk_assessment': 'AI分析失败',
                            'expert_committee_score': None,
                            'adaptive_strategy_score': None,
                            'pattern_recognition_score': None,
                            'market_regime': None,
                            'detected_patterns': [],
                            'key_factors': ['AI分析失败'],
                            'processing_time': 0.0
                        })()
                        ai_results.append(default_result)
                
                # 添加延迟避免过载（仅在多批次时）
                if i + batch_size < len(stock_list):
                    import time
                    time.sleep(0.3)
            
            # 处理统计信息
            total_batches = successful_batches + failed_batches
            success_rate = (successful_batches / total_batches * 100) if total_batches > 0 else 0
            
            logger.info(f"🤖 AI批量处理完成: {successful_batches}/{total_batches} 批次成功 ({success_rate:.1f}%)")
            
            # 将AI分析结果合并到数据中
            if ai_results:
                ai_scores = []
                for ai_result in ai_results:
                    # 安全地获取属性值
                    ai_score_entry = {
                        'ts_code': getattr(ai_result, 'symbol', ''),
                        'ai_overall_score': float(getattr(ai_result, 'overall_score', 50.0)),
                        'ai_confidence': float(getattr(ai_result, 'confidence_level', 0.5)),
                        'ai_recommendation': str(getattr(ai_result, 'recommendation', '观望')),
                        'ai_risk_assessment': str(getattr(ai_result, 'risk_assessment', '未评估')),
                    }
                    
                    # 可选的AI引擎特定评分
                    if hasattr(ai_result, 'expert_committee_score') and ai_result.expert_committee_score is not None:
                        ai_score_entry['expert_committee_score'] = float(ai_result.expert_committee_score)
                    
                    if hasattr(ai_result, 'adaptive_strategy_score') and ai_result.adaptive_strategy_score is not None:
                        ai_score_entry['adaptive_strategy_score'] = float(ai_result.adaptive_strategy_score)
                        
                    if hasattr(ai_result, 'pattern_recognition_score') and ai_result.pattern_recognition_score is not None:
                        ai_score_entry['pattern_recognition_score'] = float(ai_result.pattern_recognition_score)
                    
                    if hasattr(ai_result, 'market_regime') and ai_result.market_regime:
                        ai_score_entry['market_regime'] = str(ai_result.market_regime)
                    
                    # 转换列表为字符串
                    detected_patterns = getattr(ai_result, 'detected_patterns', [])
                    if detected_patterns and isinstance(detected_patterns, (list, tuple)):
                        ai_score_entry['detected_patterns'] = str(detected_patterns)
                    elif detected_patterns:
                        ai_score_entry['detected_patterns'] = str(detected_patterns)
                    
                    key_factors = getattr(ai_result, 'key_factors', [])
                    if key_factors and isinstance(key_factors, (list, tuple)):
                        ai_score_entry['key_factors'] = str(key_factors)
                    elif key_factors:
                        ai_score_entry['key_factors'] = str(key_factors)
                    
                    ai_scores.append(ai_score_entry)
                
                if ai_scores:
                    ai_scores_df = pd.DataFrame(ai_scores)
                    # 使用左连接确保不丢失原始数据
                    enriched_data = enriched_data.merge(ai_scores_df, on='ts_code', how='left')
                    
                    logger.info(f"✅ AI增强数据处理完成: {len(ai_scores_df)} 条AI分析结果已合并")
                    
                    # 填充缺失的AI分析数据
                    ai_columns = ['ai_overall_score', 'ai_confidence', 'ai_recommendation', 'ai_risk_assessment']
                    for col in ai_columns:
                        if col in enriched_data.columns:
                            if col == 'ai_overall_score':
                                enriched_data[col].fillna(enriched_data.get('overall_score', 50), inplace=True)
                            elif col == 'ai_confidence':
                                enriched_data[col].fillna(0.3, inplace=True)
                            elif col == 'ai_recommendation':
                                enriched_data[col].fillna('数据不足', inplace=True)
                            elif col == 'ai_risk_assessment':
                                enriched_data[col].fillna('未评估', inplace=True)
                else:
                    logger.warning("⚠️ AI分析结果处理后为空")
            else:
                logger.warning("⚠️ 未获取到任何AI分析结果，添加默认AI列")
                # 添加默认AI列以保持兼容性
                enriched_data['ai_overall_score'] = enriched_data.get('overall_score', 50)
                enriched_data['ai_confidence'] = 0.3
                enriched_data['ai_recommendation'] = '数据不足'
                enriched_data['ai_risk_assessment'] = '未分析'
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"❌ AI增强数据处理失败: {e}")
            return stock_data
    
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
                
                # 基础数据丰富
                stock_data = self._enrich_stock_data(
                    stock_data, 
                    include_scores=criteria.include_scores
                )
                
                # AI增强数据丰富
                if criteria.ai_mode != AIMode.BASIC and self.ai_strategy_manager:
                    logger.info(f"🤖 启用AI增强模式: {criteria.ai_mode.value}")
                    stock_data = self._enrich_stock_data_with_ai(
                        stock_data,
                        criteria.ai_config
                    )
            
            # 3. 应用筛选条件
            if criteria.filters:
                logger.info("🔍 正在应用筛选条件...")
                filtered_data = self._apply_filters(stock_data, criteria.filters)
            else:
                filtered_data = stock_data.copy()
            
            # 4. 智能排序 - 结合AI评分和传统评分
            sort_column = criteria.sort_by
            
            # 创建综合评分列用于排序
            if criteria.ai_mode != AIMode.BASIC and 'ai_overall_score' in filtered_data.columns:
                logger.info("🤖 使用AI增强排序策略")
                
                # 计算综合智能评分
                ai_weight = 0.7  # AI评分权重70%
                traditional_weight = 0.3  # 传统评分权重30%
                
                # 标准化评分到0-100范围
                ai_scores = filtered_data['ai_overall_score'].fillna(50)
                traditional_scores = filtered_data.get('overall_score', pd.Series([50] * len(filtered_data)))
                
                # 如果有置信度，根据置信度调整权重
                if 'ai_confidence' in filtered_data.columns:
                    confidence_scores = filtered_data['ai_confidence'].fillna(0.5)
                    # 高置信度时增加AI权重，低置信度时降低AI权重
                    dynamic_ai_weight = ai_weight * confidence_scores + (1 - confidence_scores) * 0.4
                    dynamic_traditional_weight = 1 - dynamic_ai_weight
                    
                    filtered_data['intelligent_score'] = (
                        ai_scores * dynamic_ai_weight + 
                        traditional_scores * dynamic_traditional_weight
                    )
                    logger.info("🎯 使用动态权重智能评分 (基于AI置信度)")
                else:
                    # 固定权重
                    filtered_data['intelligent_score'] = (
                        ai_scores * ai_weight + 
                        traditional_scores * traditional_weight
                    )
                    logger.info(f"⚖️ 使用固定权重智能评分 (AI:{ai_weight:.1f}, 传统:{traditional_weight:.1f})")
                
                # 优先使用智能评分排序
                if sort_column in ['overall_score', 'ai_overall_score'] or not sort_column:
                    sort_column = 'intelligent_score'
                    logger.info("🧠 使用智能综合评分排序")
            
            # 执行排序
            if sort_column and sort_column in filtered_data.columns:
                logger.info(f"📈 按 {sort_column} 排序...")
                filtered_data = filtered_data.sort_values(
                    by=sort_column, 
                    ascending=criteria.sort_ascending
                )
            elif 'ai_overall_score' in filtered_data.columns:
                # 如果指定的排序字段不存在，但有AI评分，则使用AI评分
                logger.info("🤖 默认使用AI综合评分排序")
                filtered_data = filtered_data.sort_values(
                    by='ai_overall_score',
                    ascending=False
                )
            elif 'overall_score' in filtered_data.columns:
                # 最后使用传统评分
                logger.info("📊 使用传统综合评分排序")
                filtered_data = filtered_data.sort_values(
                    by='overall_score',
                    ascending=False
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
        
        # 检查AI是否可用，自动启用AI增强模式
        ai_mode = AIMode.BASIC
        if self.ai_strategy_manager:
            ai_status = self.ai_strategy_manager.get_performance_summary()
            if ai_status.get('ai_enabled', False):
                ai_mode = AIMode.AI_ENHANCED
                logger.info("🤖 快速选股自动启用AI增强模式")
        
        criteria = SelectionCriteria(
            filters=filters,
            sort_by='overall_score',  # 将在AI增强时自动转换为智能评分
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=ai_mode,
            ai_config=AISelectionConfig(
                ai_mode=ai_mode,
                min_ai_score=min_score,
                min_confidence=0.6,
                parallel_processing=True,
                enable_caching=True
            ) if ai_mode != AIMode.BASIC else None
        )
        
        return self.select_stocks(criteria)
    
    def ai_enhanced_select(self,
                          ai_mode: AIMode = AIMode.AI_ENHANCED,
                          min_ai_score: float = 70.0,
                          min_confidence: float = 0.6,
                          max_risk_level: str = "中等",
                          limit: int = 50) -> SelectionResult:
        """
        AI增强选股 - 使用AI策略进行智能选股
        
        Args:
            ai_mode: AI模式
            min_ai_score: 最小AI评分
            min_confidence: 最小置信度
            max_risk_level: 最大风险级别
            limit: 结果数量限制
            
        Returns:
            SelectionResult: AI选股结果
        """
        if not self.ai_strategy_manager:
            logger.warning("⚠️ AI策略管理器未初始化，使用基础选股模式")
            return self.quick_select(min_score=min_ai_score, limit=limit)
        
        # 创建AI配置
        ai_config = AISelectionConfig(
            ai_mode=ai_mode,
            min_ai_score=min_ai_score,
            min_confidence=min_confidence,
            max_risk_level=max_risk_level,
            enable_caching=True,
            parallel_processing=True
        )
        
        # 基础筛选条件 (使用AI评分)
        filters = []
        
        # 基础条件保证数据质量
        filters.append(self.create_numeric_filter(
            'market_cap', FilterOperator.GREATER_EQUAL, 10.0  # 至少10亿市值
        ))
        
        criteria = SelectionCriteria(
            filters=filters,
            sort_by='ai_overall_score',  # 使用AI评分排序
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=ai_mode,
            ai_config=ai_config
        )
        
        return self.select_stocks(criteria)
    
    def expert_committee_select(self,
                              min_expert_score: float = 75.0,
                              min_consensus: str = "基本一致",
                              limit: int = 30) -> SelectionResult:
        """
        专家委员会选股 - 基于AI专家委员会的集体决策
        
        Args:
            min_expert_score: 专家委员会最小评分
            min_consensus: 最小一致性要求
            limit: 结果数量限制
            
        Returns:
            SelectionResult: 专家委员会选股结果
        """
        ai_config = AISelectionConfig(
            ai_mode=AIMode.EXPERT_COMMITTEE,
            expert_committee_weight=1.0,
            min_ai_score=min_expert_score,
            min_confidence=0.7,
            enable_caching=True
        )
        
        criteria = SelectionCriteria(
            filters=[],
            sort_by='expert_committee_score',
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=AIMode.EXPERT_COMMITTEE,
            ai_config=ai_config
        )
        
        return self.select_stocks(criteria)
    
    def adaptive_strategy_select(self,
                               market_data: Dict[str, Any] = None,
                               limit: int = 40) -> SelectionResult:
        """
        自适应策略选股 - 根据市场环境自动调整选股策略
        
        Args:
            market_data: 市场数据 (用于环境检测)
            limit: 结果数量限制
            
        Returns:
            SelectionResult: 自适应策略选股结果
        """
        ai_config = AISelectionConfig(
            ai_mode=AIMode.ADAPTIVE,
            adaptive_strategy_weight=1.0,
            min_ai_score=65.0,
            min_confidence=0.6,
            market_data_required=True
        )
        
        criteria = SelectionCriteria(
            filters=[],
            sort_by='adaptive_strategy_score',
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=AIMode.ADAPTIVE,
            ai_config=ai_config
        )
        
        return self.select_stocks(criteria)
    
    def pattern_based_select(self,
                           pattern_types: List[str] = None,
                           min_pattern_score: float = 70.0,
                           limit: int = 35) -> SelectionResult:
        """
        基于模式识别的选股 - 寻找具有特定技术模式的股票
        
        Args:
            pattern_types: 期望的模式类型列表
            min_pattern_score: 最小模式评分
            limit: 结果数量限制
            
        Returns:
            SelectionResult: 模式驱动选股结果
        """
        ai_config = AISelectionConfig(
            ai_mode=AIMode.PATTERN_BASED,
            pattern_recognition_weight=1.0,
            min_ai_score=min_pattern_score,
            min_confidence=0.65,
            pattern_analysis_enabled=True
        )
        
        criteria = SelectionCriteria(
            filters=[],
            sort_by='pattern_recognition_score',
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=AIMode.PATTERN_BASED,
            ai_config=ai_config
        )
        
        return self.select_stocks(criteria)
    
    def full_ai_select(self,
                      min_overall_score: float = 80.0,
                      min_confidence: float = 0.7,
                      risk_tolerance: str = "中等",
                      limit: int = 20) -> SelectionResult:
        """
        完整AI选股 - 使用所有AI引擎进行全面分析
        
        Args:
            min_overall_score: 最小综合评分
            min_confidence: 最小置信度
            risk_tolerance: 风险承受度
            limit: 结果数量限制
            
        Returns:
            SelectionResult: 完整AI选股结果
        """
        ai_config = AISelectionConfig(
            ai_mode=AIMode.FULL_AI,
            min_ai_score=min_overall_score,
            min_confidence=min_confidence,
            max_risk_level=risk_tolerance,
            parallel_processing=True,
            timeout_seconds=60.0,  # 完整AI分析需要更多时间
            market_data_required=True,
            news_analysis_enabled=True,
            pattern_analysis_enabled=True,
            similarity_analysis_enabled=True
        )
        
        criteria = SelectionCriteria(
            filters=[],
            sort_by='ai_overall_score',
            sort_ascending=False,
            limit=limit,
            include_scores=True,
            include_basic_info=True,
            ai_mode=AIMode.FULL_AI,
            ai_config=ai_config
        )
        
        return self.select_stocks(criteria)
    
    def get_ai_performance_summary(self) -> Dict[str, Any]:
        """
        获取AI选股引擎性能摘要
        
        Returns:
            AI引擎性能数据
        """
        if self.ai_strategy_manager:
            return self.ai_strategy_manager.get_performance_summary()
        else:
            return {
                'status': 'AI策略管理器未初始化',
                'ai_enabled': False
            }
    
    def clear_ai_cache(self):
        """
        清理AI分析缓存
        """
        if self.ai_strategy_manager:
            self.ai_strategy_manager.clear_cache()
            logger.info("🧹 AI分析缓存已清理")
        else:
            logger.warning("⚠️ AI策略管理器未初始化")


# 全局选股引擎实例
_stock_selector = None

def get_stock_selector(cache_enabled: bool = True) -> StockSelector:
    """获取全局选股引擎实例"""
    global _stock_selector
    if _stock_selector is None:
        _stock_selector = StockSelector(cache_enabled=cache_enabled)
    return _stock_selector