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
from .intelligent_sampling import get_intelligent_sampler, SamplingConfig, SamplingStrategy
from .batch_ai_processor import get_batch_ai_processor, BatchConfig, ProcessingStrategy
from ..analytics.longhubang_analyzer import get_longhubang_analyzer, LongHuBangAnalysisResult
from ..dataflows.longhubang_utils import get_longhubang_provider, RankingType

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
    
    # 智能采样选项
    enable_smart_sampling: bool = True                           # 启用智能采样
    sampling_config: Optional[SamplingConfig] = None            # 采样配置
    
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
        
        # 智能采样器
        self.intelligent_sampler = None
        
        # AI批次处理器
        self.batch_processor = None
        
        # 龙虎榜分析器
        self.longhubang_analyzer = None
        
        # 龙虎榜数据提供器
        self.longhubang_provider = None
        
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
            
            # 初始化智能采样器
            try:
                self.intelligent_sampler = get_intelligent_sampler()
                logger.info("✅ 智能采样器初始化成功")
            except Exception as sampling_error:
                logger.warning(f"⚠️ 智能采样器初始化失败: {sampling_error}")
                self.intelligent_sampler = None
            
            # 初始化AI批次处理器
            try:
                batch_config = BatchConfig(
                    batch_size=20,
                    max_workers=8,
                    strategy=ProcessingStrategy.HYBRID,
                    enable_progress_tracking=True,
                    enable_auto_scaling=True,
                    cache_results=True
                )
                self.batch_processor = get_batch_ai_processor(batch_config)
                logger.info("✅ AI批次处理器初始化成功")
            except Exception as batch_error:
                logger.warning(f"⚠️ AI批次处理器初始化失败: {batch_error}")
                self.batch_processor = None
            
            # 初始化龙虎榜分析器
            try:
                self.longhubang_analyzer = get_longhubang_analyzer()
                logger.info("✅ 龙虎榜分析器初始化成功")
            except Exception as longhubang_error:
                logger.warning(f"⚠️ 龙虎榜分析器初始化失败: {longhubang_error}")
                self.longhubang_analyzer = None
            
            # 初始化龙虎榜数据提供器
            try:
                self.longhubang_provider = get_longhubang_provider()
                logger.info("✅ 龙虎榜数据提供器初始化成功")
            except Exception as provider_error:
                logger.warning(f"⚠️ 龙虎榜数据提供器初始化失败: {provider_error}")
                self.longhubang_provider = None
            
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
            
            # 准备股票代码列表
            stock_symbols = []
            stock_symbol_to_data = {}
            
            for _, row in stock_data.iterrows():
                symbol = row.get('ts_code', '')
                if symbol:
                    stock_symbols.append(symbol)
                    stock_info = row.to_dict()
                    
                    # 获取额外的股票数据
                    try:
                        if hasattr(self, 'data_manager') and self.data_manager:
                            basic_data = self.data_manager.get_latest_price_data(symbol)
                            if basic_data:
                                stock_info.update(basic_data)
                    except Exception as e:
                        logger.debug(f"获取 {symbol} 基础数据失败: {e}")
                    
                    stock_symbol_to_data[symbol] = stock_info
            
            # 使用新的批次处理器进行AI分析
            ai_results = []
            if self.batch_processor and stock_symbols:
                logger.info(f"🚀 使用AI批次处理器分析 {len(stock_symbols)} 只股票...")
                
                # 定义分析回调函数
                def ai_analysis_callback(symbol: str) -> Dict[str, Any]:
                    """AI分析回调函数"""
                    try:
                        stock_info = stock_symbol_to_data.get(symbol, {})
                        
                        # 准备市场数据（如果需要）
                        market_data = None
                        if ai_config.market_data_required:
                            try:
                                market_data = {
                                    'market_type': 'A股',
                                    'timestamp': datetime.now(),
                                    'news_data': []
                                }
                            except Exception:
                                market_data = None
                        
                        # 调用AI策略管理器进行分析
                        batch_results = self.ai_strategy_manager.batch_analyze_stocks(
                            [stock_info], market_data=market_data, config=ai_config
                        )
                        
                        if batch_results and len(batch_results) > 0:
                            return {
                                'symbol': symbol,
                                'ai_result': batch_results[0],
                                'success': True
                            }
                        else:
                            return {
                                'symbol': symbol,
                                'ai_result': None,
                                'success': False,
                                'error': 'AI分析返回空结果'
                            }
                            
                    except Exception as e:
                        logger.debug(f"AI分析回调失败 {symbol}: {e}")
                        return {
                            'symbol': symbol,
                            'ai_result': None,
                            'success': False,
                            'error': str(e)
                        }
                
                # 执行批量处理
                processing_report = self.batch_processor.process_stocks(
                    stock_symbols, 
                    analysis_callback=ai_analysis_callback
                )
                
                # 处理批次处理结果
                for symbol in stock_symbols:
                    # 从批处理器的缓存中获取结果
                    if hasattr(self.batch_processor, '_results_cache') and symbol in self.batch_processor._results_cache:
                        batch_result = self.batch_processor._results_cache[symbol]
                        if batch_result.success and batch_result.analysis_result:
                            # 提取社交信号数据
                            if 'social_signals' in batch_result.analysis_result:
                                idx = enriched_data[enriched_data['ts_code'] == symbol].index
                                if len(idx) > 0:
                                    enriched_data.at[idx[0], 'social_signals'] = ','.join(batch_result.analysis_result['social_signals'])
                            
                            # 提取社交评分数据
                            if 'analyst_results' in batch_result.analysis_result and 'social' in batch_result.analysis_result['analyst_results']:
                                social_data = batch_result.analysis_result['analyst_results']['social']
                                idx = enriched_data[enriched_data['ts_code'] == symbol].index
                                if len(idx) > 0:
                                    enriched_data.at[idx[0], 'social_score'] = social_data.get('social_score', 50)
                                    xueqiu_data = social_data.get('xueqiu_sentiment', {})
                                    enriched_data.at[idx[0], 'social_heat'] = xueqiu_data.get('total_discussions', 0)
                                    enriched_data.at[idx[0], 'social_sentiment'] = xueqiu_data.get('sentiment_score', 0)
                            
                            ai_result_data = batch_result.analysis_result.get('ai_result')
                            if ai_result_data:
                                ai_results.append(ai_result_data)
                            else:
                                # 创建默认结果
                                default_result = self._create_default_ai_result(symbol, enriched_data)
                                ai_results.append(default_result)
                        else:
                            # 创建默认结果
                            default_result = self._create_default_ai_result(symbol, enriched_data)
                            ai_results.append(default_result)
                    else:
                        # 创建默认结果
                        default_result = self._create_default_ai_result(symbol, enriched_data)
                        ai_results.append(default_result)
                
                # 记录处理统计
                logger.info(f"🤖 AI批次处理完成:")
                logger.info(f"📊 总股票数: {processing_report.total_stocks}")
                logger.info(f"✅ 成功处理: {processing_report.successful_stocks}")
                logger.info(f"❌ 失败数量: {processing_report.failed_stocks}")
                logger.info(f"⏱️ 总耗时: {processing_report.total_time:.2f}秒")
                logger.info(f"🚀 处理吞吐量: {processing_report.throughput:.2f}股票/秒")
                logger.info(f"💾 内存峰值: {processing_report.memory_peak:.1f}%")
                
            else:
                # 回退到原有的批处理方式
                logger.warning("⚠️ AI批次处理器不可用，使用传统批处理方式")
                ai_results = self._fallback_ai_processing(stock_symbol_to_data, ai_config, enriched_data)
            
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
    
    def _create_default_ai_result(self, symbol: str, enriched_data: pd.DataFrame):
        """创建默认AI分析结果"""
        try:
            # 尝试从现有数据中获取基础评分
            default_score = 50.0
            if 'overall_score' in enriched_data.columns:
                symbol_data = enriched_data[enriched_data.get('ts_code', '') == symbol]
                if not symbol_data.empty:
                    default_score = float(symbol_data['overall_score'].iloc[0])
        except:
            default_score = 50.0
        
        return type('AIResult', (), {
            'symbol': symbol,
            'overall_score': default_score,
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
    
    def _fallback_ai_processing(self, stock_symbol_to_data: Dict[str, Dict], 
                               ai_config, enriched_data: pd.DataFrame) -> List:
        """回退的AI处理方式（原有的批处理逻辑）"""
        try:
            stock_list = list(stock_symbol_to_data.values())
            ai_results = []
            
            # 简化的批处理
            batch_size = 15
            for i in range(0, len(stock_list), batch_size):
                batch = stock_list[i:i + batch_size]
                
                try:
                    # 准备市场数据
                    market_data = None
                    if ai_config.market_data_required:
                        market_data = {
                            'market_type': 'A股',
                            'timestamp': datetime.now(),
                            'news_data': []
                        }
                    
                    batch_results = self.ai_strategy_manager.batch_analyze_stocks(
                        batch, market_data=market_data, config=ai_config
                    )
                    
                    if batch_results:
                        ai_results.extend(batch_results)
                    else:
                        # 创建默认结果
                        for stock_info in batch:
                            symbol = stock_info.get('ts_code', '')
                            default_result = self._create_default_ai_result(symbol, enriched_data)
                            ai_results.append(default_result)
                
                except Exception as e:
                    logger.warning(f"❌ 回退批处理失败: {e}")
                    # 创建默认结果
                    for stock_info in batch:
                        symbol = stock_info.get('ts_code', '')
                        default_result = self._create_default_ai_result(symbol, enriched_data)
                        ai_results.append(default_result)
                
                # 添加延迟
                if i + batch_size < len(stock_list):
                    time.sleep(0.2)
            
            return ai_results
            
        except Exception as e:
            logger.error(f"❌ 回退AI处理失败: {e}")
            return []
    
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
            
            # 2. 智能采样 (大幅减少需要详细分析的股票数量)
            if criteria.enable_smart_sampling and self.intelligent_sampler and len(stock_data) > (criteria.limit or 100) * 2:
                logger.info(f"🎯 启用智能采样，优化数据获取流程...")
                
                # 创建采样配置
                sampling_config = criteria.sampling_config or SamplingConfig(
                    strategy=SamplingStrategy.HYBRID,
                    max_candidates=min(800, max((criteria.limit or 100) * 4, len(stock_data) // 4)),  # 智能确定采样数量
                    min_market_cap=5.0,  # 5亿最小市值
                    min_daily_volume=5000000,  # 500万最小成交额
                    min_price=1.0,
                    max_price=300.0,
                    exclude_st_stocks=True,
                    activity_days=30,
                    enable_cache=True
                )
                
                logger.info(f"📈 采样目标: {len(stock_data)} -> {sampling_config.max_candidates}")
                
                # 执行智能采样
                sampling_result = self.intelligent_sampler.smart_sample(stock_data, sampling_config)
                
                if sampling_result.sampled_stocks:
                    # 过滤到采样的股票
                    sampled_symbols = set(sampling_result.sampled_stocks)
                    if 'ts_code' in stock_data.columns:
                        stock_data = stock_data[stock_data['ts_code'].isin(sampled_symbols)].reset_index(drop=True)
                    
                    logger.info(f"✅ 智能采样完成: {sampling_result.original_count} -> {len(stock_data)} 只股票")
                    logger.info(f"🎯 采样策略: {sampling_result.strategy_used.value}")
                    logger.info(f"⏱️ 采样耗时: {sampling_result.execution_time:.2f}秒")
                    logger.info(f"🌟 质量评分: {sampling_result.quality_score:.2f}")
                else:
                    logger.warning("⚠️ 智能采样未返回有效结果，继续使用全量数据")
            else:
                if not criteria.enable_smart_sampling:
                    logger.info("📊 智能采样已禁用，使用全量数据")
                elif not self.intelligent_sampler:
                    logger.warning("⚠️ 智能采样器不可用，使用全量数据")
                else:
                    logger.info(f"📊 数据量较小({len(stock_data)})，无需智能采样")
            
            # 3. 丰富股票数据
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
            
            # 更新实际候选数量（考虑智能采样后的数量）
            actual_candidates = len(stock_data)
            
            # 4. 智能排序 - 结合AI评分和传统评分
            sort_column = criteria.sort_by
            
            # 创建综合评分列用于排序
            if criteria.ai_mode != AIMode.BASIC and 'ai_overall_score' in filtered_data.columns:
                logger.info("🤖 使用AI增强排序策略")
                
                # 计算综合智能评分（包含社交数据）
                ai_weight = 0.5  # AI评分权重50%
                traditional_weight = 0.3  # 传统评分权重30%
                social_weight = 0.2  # 社交评分权重20%
                
                # 标准化评分到0-100范围
                ai_scores = filtered_data['ai_overall_score'].fillna(50)
                traditional_scores = filtered_data.get('overall_score', pd.Series([50] * len(filtered_data)))
                social_scores = filtered_data.get('social_score', pd.Series([50] * len(filtered_data)))
                
                # 如果有置信度，根据置信度调整权重
                if 'ai_confidence' in filtered_data.columns:
                    confidence_scores = filtered_data['ai_confidence'].fillna(0.5)
                    # 高置信度时增加AI权重，低置信度时降低AI权重
                    # 动态调整权重基于置信度
                    confidence_factor = confidence_scores.mean()
                    
                    # 根据置信度调整各部分权重
                    dynamic_ai_weight = ai_weight * (0.5 + confidence_factor * 0.5)  # 0.25-0.5
                    dynamic_traditional_weight = traditional_weight * (1.5 - confidence_factor * 0.5)  # 0.3-0.45
                    dynamic_social_weight = social_weight  # 社交权重保持稳定
                    
                    # 归一化权重
                    total_weight = dynamic_ai_weight + dynamic_traditional_weight + dynamic_social_weight
                    dynamic_ai_weight /= total_weight
                    dynamic_traditional_weight /= total_weight
                    dynamic_social_weight /= total_weight
                    
                    filtered_data['intelligent_score'] = (
                        ai_scores * dynamic_ai_weight + 
                        traditional_scores * dynamic_traditional_weight +
                        social_scores * dynamic_social_weight
                    )
                    logger.info(f"🎯 使用动态权重智能评分 (AI:{dynamic_ai_weight:.2f}, 传统:{dynamic_traditional_weight:.2f}, 社交:{dynamic_social_weight:.2f})")
                else:
                    # 固定权重
                    filtered_data['intelligent_score'] = (
                        ai_scores * ai_weight + 
                        traditional_scores * traditional_weight +
                        social_scores * social_weight
                    )
                    logger.info(f"⚖️ 使用固定权重智能评分 (AI:{ai_weight:.1f}, 传统:{traditional_weight:.1f}, 社交:{social_weight:.1f})")
                
                # 添加社交信号加成
                if 'social_signals' in filtered_data.columns:
                    # 对有强烈社交信号的股票进行加减分
                    for idx, row in filtered_data.iterrows():
                        signals = str(row.get('social_signals', '')).split(',')
                        if 'STRONG_BULLISH' in signals or 'SENTIMENT_SURGE' in signals:
                            filtered_data.at[idx, 'intelligent_score'] = min(100, filtered_data.at[idx, 'intelligent_score'] + 5)
                        elif 'HIGH_HEAT_WARNING' in signals:
                            filtered_data.at[idx, 'intelligent_score'] = max(0, filtered_data.at[idx, 'intelligent_score'] - 5)
                
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
            
            # 在摘要中添加智能采样信息
            if criteria.enable_smart_sampling and actual_candidates != total_candidates:
                summary['intelligent_sampling'] = {
                    'enabled': True,
                    'original_candidates': total_candidates,
                    'sampled_candidates': actual_candidates,
                    'sampling_ratio': actual_candidates / max(total_candidates, 1),
                    'sampling_efficiency': f"{100 * (1 - actual_candidates / max(total_candidates, 1)):.1f}% 数据量减少"
                }
            
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
            ) if ai_mode != AIMode.BASIC else None,
            # 启用智能采样
            enable_smart_sampling=True,
            sampling_config=SamplingConfig(
                strategy=SamplingStrategy.HYBRID,
                max_candidates=min(1000, limit * 10),  # 采样数量为目标的10倍
                min_market_cap=min_market_cap if min_market_cap > 0 else 5.0,
                min_daily_volume=10000000,  # 1000万最小成交额
                min_price=2.0,
                exclude_st_stocks=True,
                enable_cache=True
            )
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
            ai_config=ai_config,
            # AI增强选股启用更激进的智能采样
            enable_smart_sampling=True,
            sampling_config=SamplingConfig(
                strategy=SamplingStrategy.HYBRID,
                max_candidates=min(1500, limit * 15),  # AI模式使用更大的采样池
                min_market_cap=8.0,  # 8亿最小市值
                min_daily_volume=15000000,  # 1500万最小成交额
                min_price=3.0,
                exclude_st_stocks=True,
                enable_momentum_filter=True,
                momentum_threshold=-15.0,  # 过滤掉跌幅过大的
                enable_cache=True
            )
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

    def switch_ai_model(self, model_key: str) -> bool:
        """
        切换AI模型
        
        Args:
            model_key: 模型键值
            
        Returns:
            是否切换成功
        """
        try:
            logger.info(f"🔄 [选股引擎] 切换AI模型: {model_key}")
            
            if self.ai_strategy_manager:
                success = self.ai_strategy_manager.switch_ai_model(model_key)
                if success:
                    logger.info(f"✅ [选股引擎] AI模型切换成功: {model_key}")
                    # 清理缓存以使新模型生效
                    self.clear_ai_cache()
                    return True
                else:
                    logger.error(f"❌ [选股引擎] AI模型切换失败: {model_key}")
                    return False
            else:
                # 如果AI策略管理器未初始化，直接设置全局模型
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                success = llm_manager.set_current_model(model_key)
                if success:
                    logger.info(f"✅ [选股引擎] 全局AI模型设置成功: {model_key}")
                    return True
                else:
                    logger.error(f"❌ [选股引擎] 全局AI模型设置失败: {model_key}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ [选股引擎] AI模型切换异常: {e}")
            return False

    def get_available_ai_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的AI模型列表"""
        try:
            if self.ai_strategy_manager:
                return self.ai_strategy_manager.get_available_ai_models()
            else:
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                return llm_manager.get_enabled_models()
        except Exception as e:
            logger.error(f"❌ [选股引擎] 获取可用模型失败: {e}")
            return {}

    def get_current_ai_model_info(self) -> Optional[Dict[str, Any]]:
        """获取当前AI模型信息"""
        try:
            if self.ai_strategy_manager:
                return self.ai_strategy_manager.get_current_ai_model_info()
            else:
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                current_config = llm_manager.get_current_config()
                if current_config:
                    return {
                        'provider': current_config.provider,
                        'model_name': current_config.model_name,
                        'display_name': current_config.display_name,
                        'description': current_config.description,
                        'temperature': current_config.temperature,
                        'max_tokens': current_config.max_tokens
                    }
                return None
        except Exception as e:
            logger.error(f"❌ [选股引擎] 获取当前模型信息失败: {e}")
            return None

    def longhubang_enhanced_select(self, 
                                  date: str = None,
                                  ranking_type: RankingType = RankingType.DAILY,
                                  min_longhubang_score: float = 60.0,
                                  enable_ai_analysis: bool = True,
                                  ai_mode: AIMode = AIMode.AI_ENHANCED,
                                  limit: int = 50) -> SelectionResult:
        """
        龙虎榜增强选股 - 基于龙虎榜数据进行股票选择和分析
        这是解决5000+股票扫描性能问题的核心解决方案
        
        Args:
            date: 查询日期，默认为今天
            ranking_type: 龙虎榜类型
            min_longhubang_score: 最小龙虎榜综合评分
            enable_ai_analysis: 是否启用AI分析
            ai_mode: AI分析模式
            limit: 返回结果数量限制
            
        Returns:
            SelectionResult: 龙虎榜增强选股结果
        """
        start_time = time.time()
        logger.info("🐉 开始龙虎榜增强选股...")
        
        try:
            if not self.longhubang_analyzer or not self.longhubang_provider:
                logger.error("❌ 龙虎榜分析器或数据提供器未初始化")
                return SelectionResult(
                    symbols=[],
                    data=pd.DataFrame(),
                    summary={'error': '龙虎榜组件未初始化'},
                    criteria=SelectionCriteria(),
                    execution_time=time.time() - start_time,
                    total_candidates=0,
                    filtered_count=0
                )
            
            # 1. 获取龙虎榜数据 (50-200只股票，相比5000+大幅减少)
            logger.info(f"📋 获取{date or '今日'}龙虎榜数据...")
            longhubang_results = self.longhubang_analyzer.get_top_ranking_stocks(
                date=date,
                ranking_type=ranking_type,
                min_score=min_longhubang_score,
                limit=limit * 3  # 获取3倍数量以便筛选
            )
            
            if not longhubang_results:
                logger.warning("⚠️ 未获取到符合条件的龙虎榜股票")
                return SelectionResult(
                    symbols=[],
                    data=pd.DataFrame(),
                    summary={'error': '未获取到龙虎榜数据'},
                    criteria=SelectionCriteria(),
                    execution_time=time.time() - start_time,
                    total_candidates=0,
                    filtered_count=0
                )
            
            total_candidates = len(longhubang_results)
            logger.info(f"🎯 获取到{total_candidates}只龙虎榜股票，相比全市场5000+股票大幅减少")
            
            # 2. 转换为DataFrame格式
            longhubang_data_list = []
            for result in longhubang_results:
                try:
                    # 基础股票信息
                    stock_info = {
                        'ts_code': result.symbol,
                        'name': result.name,
                        'current_price': result.longhubang_data.current_price,
                        'change_pct': result.longhubang_data.change_pct,
                        'turnover': result.longhubang_data.turnover,
                        'turnover_rate': result.longhubang_data.turnover_rate,
                        
                        # 龙虎榜评分信息
                        'longhubang_overall_score': result.score.overall_score,
                        'longhubang_seat_quality_score': result.score.seat_quality_score,
                        'longhubang_capital_flow_score': result.score.capital_flow_score,
                        'longhubang_follow_potential_score': result.score.follow_potential_score,
                        'longhubang_risk_score': result.score.risk_score,
                        'longhubang_confidence': result.score.confidence,
                        
                        # 市场情绪和操作模式
                        'market_sentiment': result.market_sentiment.value,
                        'operation_pattern': result.operation_pattern.value,
                        
                        # 投资建议
                        'investment_suggestion': result.investment_suggestion,
                        'risk_warning': result.risk_warning,
                        'follow_recommendation': result.follow_recommendation,
                        
                        # 席位分析摘要
                        'buy_seat_count': len(result.longhubang_data.buy_seats),
                        'sell_seat_count': len(result.longhubang_data.sell_seats),
                        'net_inflow': result.longhubang_data.get_net_flow(),
                        
                        # 数据质量
                        'data_quality': result.data_quality,
                        'analysis_timestamp': result.analysis_timestamp
                    }
                    
                    # 席位分析详情
                    if result.seat_analysis:
                        battle_analysis = result.seat_analysis.get('battle_analysis', {})
                        stock_info.update({
                            'battle_result': battle_analysis.get('battle_result', ''),
                            'battle_winner': battle_analysis.get('winner', ''),
                            'battle_confidence': battle_analysis.get('confidence', 0),
                            'buy_power': battle_analysis.get('buy_power', 0),
                            'sell_power': battle_analysis.get('sell_power', 0)
                        })
                        
                        # 协同交易检测
                        coordination = result.seat_analysis.get('coordination_analysis', {})
                        stock_info.update({
                            'coordinated_trading': coordination.get('coordinated', False),
                            'coordination_confidence': coordination.get('confidence', 0),
                            'coordination_signals': '; '.join(coordination.get('signals', []))
                        })
                    
                    longhubang_data_list.append(stock_info)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 处理龙虎榜数据失败 {result.symbol}: {e}")
                    continue
            
            if not longhubang_data_list:
                logger.warning("⚠️ 龙虎榜数据处理后为空")
                return SelectionResult(
                    symbols=[],
                    data=pd.DataFrame(),
                    summary={'error': '龙虎榜数据处理失败'},
                    criteria=SelectionCriteria(),
                    execution_time=time.time() - start_time,
                    total_candidates=total_candidates,
                    filtered_count=0
                )
            
            # 创建DataFrame
            stock_data = pd.DataFrame(longhubang_data_list)
            logger.info(f"✅ 龙虎榜数据转换完成: {len(stock_data)}只股票")
            
            # 3. AI增强分析 (可选，仅对龙虎榜股票进行AI分析)
            if enable_ai_analysis and self.ai_strategy_manager:
                logger.info(f"🤖 对{len(stock_data)}只龙虎榜股票进行AI增强分析...")
                
                ai_config = AISelectionConfig(
                    ai_mode=ai_mode,
                    min_ai_score=50.0,  # 龙虎榜股票已经是高质量的，可以放宽AI评分
                    min_confidence=0.5,
                    parallel_processing=True,
                    enable_caching=True,
                    timeout_seconds=30.0  # 龙虎榜股票数量少，可以给每只股票更多分析时间
                )
                
                stock_data = self._enrich_stock_data_with_ai(stock_data, ai_config)
                logger.info("✅ 龙虎榜股票AI增强分析完成")
            
            # 4. 应用筛选和排序
            # 按龙虎榜综合评分排序
            stock_data = stock_data.sort_values(
                by='longhubang_overall_score', 
                ascending=False
            )
            
            # 如果启用了AI分析，使用智能综合评分
            if enable_ai_analysis and 'ai_overall_score' in stock_data.columns:
                logger.info("🧠 使用龙虎榜+AI综合评分排序")
                
                # 龙虎榜评分权重60%，AI评分权重40%
                longhubang_weight = 0.6
                ai_weight = 0.4
                
                longhubang_scores = stock_data['longhubang_overall_score'].fillna(50)
                ai_scores = stock_data['ai_overall_score'].fillna(50)
                
                stock_data['longhubang_ai_combined_score'] = (
                    longhubang_scores * longhubang_weight + 
                    ai_scores * ai_weight
                )
                
                # 按综合评分重新排序
                stock_data = stock_data.sort_values(
                    by='longhubang_ai_combined_score', 
                    ascending=False
                )
                logger.info(f"📊 使用龙虎榜({longhubang_weight:.1f})+AI({ai_weight:.1f})综合评分排序")
            
            # 5. 限制结果数量
            if len(stock_data) > limit:
                stock_data = stock_data.head(limit)
                logger.info(f"✂️ 限制结果数量为: {limit}")
            
            filtered_count = len(stock_data)
            symbols = stock_data['ts_code'].tolist()
            
            # 6. 生成增强摘要
            summary = self._generate_longhubang_summary(stock_data, total_candidates, filtered_count)
            
            execution_time = time.time() - start_time
            
            # 创建选股标准对象
            criteria = SelectionCriteria(
                filters=[],
                sort_by='longhubang_ai_combined_score' if enable_ai_analysis else 'longhubang_overall_score',
                sort_ascending=False,
                limit=limit,
                include_scores=True,
                include_basic_info=True,
                ai_mode=ai_mode if enable_ai_analysis else AIMode.BASIC
            )
            
            result = SelectionResult(
                symbols=symbols,
                data=stock_data,
                summary=summary,
                criteria=criteria,
                execution_time=execution_time,
                total_candidates=total_candidates,
                filtered_count=filtered_count
            )
            
            logger.info(f"🎉 龙虎榜增强选股完成: {filtered_count}只股票, 耗时 {execution_time:.2f}秒")
            logger.info(f"🚀 性能提升: 相比全市场5000+股票扫描，处理时间大幅减少")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 龙虎榜增强选股失败: {e}")
            return SelectionResult(
                symbols=[],
                data=pd.DataFrame(),
                summary={'error': str(e)},
                criteria=SelectionCriteria(),
                execution_time=time.time() - start_time,
                total_candidates=0,
                filtered_count=0
            )
    
    def _generate_longhubang_summary(self, data: pd.DataFrame, total_candidates: int, filtered_count: int) -> Dict[str, Any]:
        """生成龙虎榜选股统计摘要"""
        if data.empty:
            return {
                'total_candidates': total_candidates,
                'filtered_count': 0,
                'success_rate': 0.0,
                'longhubang_statistics': {},
                'selection_type': 'longhubang_enhanced'
            }
        
        summary = {
            'total_candidates': total_candidates,
            'filtered_count': filtered_count,
            'success_rate': filtered_count / max(total_candidates, 1) * 100,
            'selection_type': 'longhubang_enhanced',
            'data_source': '龙虎榜',
            'longhubang_statistics': {}
        }
        
        # 龙虎榜特有统计
        if 'longhubang_overall_score' in data.columns:
            summary['longhubang_statistics']['average_longhubang_score'] = float(data['longhubang_overall_score'].mean())
            summary['longhubang_statistics']['max_longhubang_score'] = float(data['longhubang_overall_score'].max())
            summary['longhubang_statistics']['min_longhubang_score'] = float(data['longhubang_overall_score'].min())
        
        # 市场情绪分布
        if 'market_sentiment' in data.columns:
            sentiment_counts = data['market_sentiment'].value_counts()
            summary['sentiment_distribution'] = sentiment_counts.to_dict()
        
        # 操作模式分布
        if 'operation_pattern' in data.columns:
            pattern_counts = data['operation_pattern'].value_counts()
            summary['operation_pattern_distribution'] = pattern_counts.to_dict()
        
        # 实力对比统计
        if 'battle_winner' in data.columns:
            battle_counts = data['battle_winner'].value_counts()
            summary['battle_result_distribution'] = battle_counts.to_dict()
        
        # 协同交易统计
        if 'coordinated_trading' in data.columns:
            coordinated_count = data['coordinated_trading'].sum()
            summary['coordinated_trading_ratio'] = coordinated_count / len(data) if len(data) > 0 else 0
        
        # 资金流向统计
        if 'net_inflow' in data.columns:
            net_inflow_positive = len(data[data['net_inflow'] > 0])
            summary['net_inflow_positive_ratio'] = net_inflow_positive / len(data) if len(data) > 0 else 0
            summary['average_net_inflow'] = float(data['net_inflow'].mean())
        
        # 跟随建议分布
        if 'follow_recommendation' in data.columns:
            follow_counts = data['follow_recommendation'].value_counts()
            summary['follow_recommendation_distribution'] = follow_counts.to_dict()
        
        return summary
    
    def get_longhubang_statistics(self, date: str = None) -> Dict[str, Any]:
        """
        获取龙虎榜市场统计信息
        
        Args:
            date: 查询日期
            
        Returns:
            龙虎榜市场统计信息
        """
        try:
            if not self.longhubang_provider:
                return {'error': '龙虎榜数据提供器未初始化'}
            
            return self.longhubang_provider.get_statistics(date)
            
        except Exception as e:
            logger.error(f"❌ 获取龙虎榜统计信息失败: {e}")
            return {'error': str(e)}
    
    def search_seat_activity(self, seat_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        搜索特定席位的活动记录
        
        Args:
            seat_name: 席位名称(支持模糊匹配)
            days: 搜索最近几天
            
        Returns:
            席位活动记录列表
        """
        try:
            if not self.longhubang_provider:
                logger.error("❌ 龙虎榜数据提供器未初始化")
                return []
            
            longhubang_stocks = self.longhubang_provider.search_stocks_by_seat(seat_name, days)
            
            # 转换为简化格式
            activity_records = []
            for stock_data in longhubang_stocks:
                record = {
                    'symbol': stock_data.symbol,
                    'name': stock_data.name,
                    'date': stock_data.date,
                    'change_pct': stock_data.change_pct,
                    'turnover': stock_data.turnover,
                    'ranking_reason': stock_data.ranking_reason,
                    'seat_found_in': '买方' if any(seat_name in seat.seat_name for seat in stock_data.buy_seats) else '卖方'
                }
                activity_records.append(record)
            
            logger.info(f"✅ 席位活动搜索完成: {seat_name}, 找到{len(activity_records)}条记录")
            return activity_records
            
        except Exception as e:
            logger.error(f"❌ 搜索席位活动失败: {e}")
            return []
    
    def analyze_seat_influence(self, seat_name: str, days: int = 30) -> Dict[str, Any]:
        """
        分析特定席位的市场影响力
        
        Args:
            seat_name: 席位名称
            days: 分析时间范围
            
        Returns:
            席位影响力分析结果
        """
        try:
            # 获取席位活动记录
            activity_records = self.search_seat_activity(seat_name, days)
            
            if not activity_records:
                return {
                    'seat_name': seat_name,
                    'influence_score': 0,
                    'activity_count': 0,
                    'analysis_period': days,
                    'error': '未找到席位活动记录'
                }
            
            # 计算影响力指标
            total_activities = len(activity_records)
            buy_activities = len([r for r in activity_records if r['seat_found_in'] == '买方'])
            sell_activities = total_activities - buy_activities
            
            # 计算平均涨跌幅
            avg_change_pct = sum(r['change_pct'] for r in activity_records) / total_activities
            
            # 计算成功率 (涨跌符合买卖方向的比例)
            successful_activities = 0
            for record in activity_records:
                if record['seat_found_in'] == '买方' and record['change_pct'] > 0:
                    successful_activities += 1
                elif record['seat_found_in'] == '卖方' and record['change_pct'] < 0:
                    successful_activities += 1
            
            success_rate = successful_activities / total_activities if total_activities > 0 else 0
            
            # 计算影响力评分
            base_score = 50
            activity_bonus = min(20, total_activities * 2)  # 活动频率加分
            success_bonus = success_rate * 30  # 成功率加分
            influence_score = base_score + activity_bonus + success_bonus
            
            analysis_result = {
                'seat_name': seat_name,
                'influence_score': round(influence_score, 2),
                'activity_count': total_activities,
                'buy_activities': buy_activities,
                'sell_activities': sell_activities,
                'success_rate': round(success_rate * 100, 2),
                'average_change_pct': round(avg_change_pct, 2),
                'analysis_period': days,
                'activity_frequency': round(total_activities / days, 2),
                'recent_activities': activity_records[:5]  # 最近5条记录
            }
            
            logger.info(f"✅ 席位影响力分析完成: {seat_name}, 影响力评分: {influence_score:.2f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 席位影响力分析失败: {e}")
            return {
                'seat_name': seat_name,
                'error': str(e)
            }


# 全局选股引擎实例
_stock_selector = None

def get_stock_selector(cache_enabled: bool = True) -> StockSelector:
    """获取全局选股引擎实例"""
    global _stock_selector
    if _stock_selector is None:
        _stock_selector = StockSelector(cache_enabled=cache_enabled)
    return _stock_selector