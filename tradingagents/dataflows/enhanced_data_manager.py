#!/usr/bin/env python3
"""
增强数据源管理器
统一管理所有中国股票数据源，包括新增的东方财富、腾讯、新浪、雪球等
"""

import os
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import warnings
import pandas as pd
from datetime import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
from tradingagents.config.data_source_config import get_data_source_config

logger = get_logger('agents')
warnings.filterwarnings('ignore')

# 导入所有数据源
from .eastmoney_utils import get_eastmoney_provider
from .tencent_utils import get_tencent_provider  
from .sina_utils import get_sina_provider
from .xueqiu_utils import get_xueqiu_provider
from .eastmoney_guba_utils import get_eastmoney_guba_provider

try:
    from .akshare_utils import AKShareProvider
except ImportError:
    AKShareProvider = None

try:
    from .tushare_adapter import get_tushare_adapter
except ImportError:
    get_tushare_adapter = None


class DataSourceType(Enum):
    """数据源类型枚举"""
    PRICE_DATA = "price_data"          # 价格行情数据
    NEWS_DATA = "news_data"            # 新闻资讯数据
    SOCIAL_DATA = "social_data"        # 社交媒体数据
    FINANCIAL_DATA = "financial_data"  # 财务数据
    SENTIMENT_DATA = "sentiment_data"  # 情绪分析数据


class EnhancedDataManager:
    """增强数据源管理器"""

    def __init__(self):
        """初始化增强数据源管理器"""
        self.providers = {}
        self.provider_status = {}
        self.config = get_data_source_config()
        
        # 初始化所有数据源提供器
        self._init_providers()
        
        logger.info("🚀 增强数据源管理器初始化完成")
        logger.info(f"   可用数据源: {list(self.providers.keys())}")
        logger.info(f"   数据源优先级: {self.config.get_priority_order()}")
        
    def _init_providers(self):
        """初始化所有数据源提供器"""
        priority_order = self.config.get_priority_order()
        
        for source in priority_order:
            if not self.config.is_source_enabled(source):
                logger.info(f"⏭️ 数据源 {source} 已禁用，跳过初始化")
                continue
                
            try:
                if source == 'eastmoney':
                    self.providers['eastmoney'] = get_eastmoney_provider()
                    self.provider_status['eastmoney'] = True
                    logger.info("✅ 东方财富数据源初始化成功")
                elif source == 'tencent':
                    self.providers['tencent'] = get_tencent_provider()
                    self.provider_status['tencent'] = True
                    logger.info("✅ 腾讯财经数据源初始化成功")
                elif source == 'sina':
                    self.providers['sina'] = get_sina_provider()
                    self.provider_status['sina'] = True
                    logger.info("✅ 新浪财经数据源初始化成功")
                elif source == 'xueqiu':
                    self.providers['xueqiu'] = get_xueqiu_provider()
                    self.provider_status['xueqiu'] = True
                    logger.info("✅ 雪球数据源初始化成功")
                elif source == 'guba':
                    self.providers['guba'] = get_eastmoney_guba_provider()
                    self.provider_status['guba'] = True
                    logger.info("✅ 东方财富股吧数据源初始化成功")
                elif source == 'akshare' and AKShareProvider:
                    self.providers['akshare'] = AKShareProvider()
                    self.provider_status['akshare'] = True
                    logger.info("✅ AKShare数据源初始化成功")
                elif source == 'tushare' and get_tushare_adapter:
                    self.providers['tushare'] = get_tushare_adapter()
                    self.provider_status['tushare'] = True
                    logger.info("✅ Tushare数据源初始化成功")
                    
            except Exception as e:
                logger.warning(f"⚠️ {source} 数据源初始化失败: {e}")
                self.provider_status[source] = False

    def get_comprehensive_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取综合股票信息，整合多个数据源"""
        try:
            comprehensive_data = {
                'symbol': symbol,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sources': [],
                'data_quality_score': 0.0,
                'primary_source': None
            }
            
            # 按优先级从多个数据源获取价格数据
            priority_order = self.config.get_priority_order()
            price_sources = [source for source in priority_order 
                           if source in ['eastmoney', 'tencent', 'sina', 'tushare', 'akshare']]
            
            price_data = {}
            valid_sources = 0
            
            for source in price_sources:
                if source in self.providers and self.provider_status.get(source, False):
                    try:
                        logger.info(f"🔄 尝试从 {source} 获取 {symbol} 数据...")
                        provider = self.providers[source]
                        data = provider.get_stock_info(symbol)
                        if data and data.get('current_price', 0) > 0:
                            price_data[source] = data
                            comprehensive_data['sources'].append(source)
                            valid_sources += 1
                            
                            # 设置主数据源（第一个成功的）
                            if not comprehensive_data['primary_source']:
                                comprehensive_data['primary_source'] = source
                                
                            logger.info(f"✅ {source} 成功获取数据: {data.get('name', symbol)} ¥{data.get('current_price', 0):.2f}")
                            
                            # 如果启用了智能选择，获取到高质量数据就停止
                            if not self.config.get_strategy_config().get('enable_multi_source', True):
                                break
                                
                    except Exception as e:
                        logger.debug(f"⚠️ {source}获取股票信息失败: {e}")
                        continue
            
            # 整合价格数据（智能融合）
            if price_data:
                comprehensive_data.update(self._merge_price_data_smart(price_data))
                comprehensive_data['data_quality_score'] = min(1.0, valid_sources / len(price_sources))
            
            logger.info(f"✅ 获取到综合股票信息: {symbol}, 数据源: {comprehensive_data['sources']}, 质量评分: {comprehensive_data['data_quality_score']:.2f}")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"❌ 获取综合股票信息失败: {symbol}, 错误: {str(e)}")
            return {}

    def get_comprehensive_news(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取综合新闻数据，整合多个新闻源"""
        try:
            all_news = []
            
            # 从多个数据源获取新闻
            news_sources = ['eastmoney', 'sina']
            
            for source in news_sources:
                if source in self.providers and self.provider_status.get(source, False):
                    try:
                        provider = self.providers[source]
                        if source == 'eastmoney':
                            news = provider.get_stock_news(symbol, limit // len(news_sources))
                        elif source == 'sina':
                            news = provider.get_stock_news(symbol, limit // len(news_sources))
                        
                        for item in news:
                            item['data_source'] = source
                            all_news.append(item)
                            
                    except Exception as e:
                        logger.debug(f"⚠️ {source}获取新闻失败: {e}")
            
            # 按时间排序，去重
            all_news = self._deduplicate_news(all_news)
            all_news.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
            
            logger.info(f"✅ 获取到综合新闻 {len(all_news)} 条: {symbol}")
            return all_news[:limit]
            
        except Exception as e:
            logger.error(f"❌ 获取综合新闻失败: {symbol}, 错误: {str(e)}")
            return []

    def get_comprehensive_sentiment(self, symbol: str) -> Dict[str, Any]:
        """获取综合情绪分析，整合社交媒体数据"""
        try:
            sentiment_data = {
                'symbol': symbol,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sources': [],
                'overall_sentiment': 0.0,
                'confidence': 0.0,
                'details': {}
            }
            
            # 从多个社交数据源获取情绪
            social_sources = ['xueqiu', 'guba']
            sentiment_scores = []
            
            for source in social_sources:
                if source in self.providers and self.provider_status.get(source, False):
                    try:
                        provider = self.providers[source]
                        if source == 'xueqiu':
                            data = provider.get_stock_sentiment(symbol)
                        elif source == 'guba':
                            data = provider.get_stock_sentiment_analysis(symbol)
                        
                        if data and 'sentiment_score' in data:
                            sentiment_scores.append(data['sentiment_score'])
                            sentiment_data['sources'].append(source)
                            sentiment_data['details'][source] = data
                            
                    except Exception as e:
                        logger.debug(f"⚠️ {source}获取情绪分析失败: {e}")
            
            # 计算综合情绪评分
            if sentiment_scores:
                sentiment_data['overall_sentiment'] = sum(sentiment_scores) / len(sentiment_scores)
                sentiment_data['confidence'] = min(1.0, len(sentiment_scores) / len(social_sources))
            
            logger.info(f"✅ 获取到综合情绪分析: {symbol}, 评分: {sentiment_data['overall_sentiment']:.2f}")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ 获取综合情绪分析失败: {symbol}, 错误: {str(e)}")
            return {}

    def get_social_discussions(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取社交媒体讨论数据"""
        try:
            all_discussions = []
            
            # 从雪球和股吧获取讨论
            social_sources = [
                ('xueqiu', 'get_stock_discussions'),
                ('guba', 'get_stock_discussions')
            ]
            
            for source, method_name in social_sources:
                if source in self.providers and self.provider_status.get(source, False):
                    try:
                        provider = self.providers[source]
                        method = getattr(provider, method_name, None)
                        if method:
                            discussions = method(symbol, limit // len(social_sources))
                            for item in discussions:
                                item['data_source'] = source
                                all_discussions.append(item)
                    except Exception as e:
                        logger.debug(f"⚠️ {source}获取讨论失败: {e}")
            
            # 按热度排序
            all_discussions.sort(key=lambda x: x.get('heat_score', 0), reverse=True)
            
            logger.info(f"✅ 获取到社交讨论 {len(all_discussions)} 条: {symbol}")
            return all_discussions[:limit]
            
        except Exception as e:
            logger.error(f"❌ 获取社交讨论失败: {symbol}, 错误: {str(e)}")
            return []

    def get_market_overview(self) -> Dict[str, Any]:
        """获取市场总览"""
        try:
            overview = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'indices': {},
                'hot_stocks': [],
                'market_sentiment': {}
            }
            
            # 获取主要指数
            indices = ['sh000001', 'sz399001', 'sz399006']  # 上证、深证、创业板
            
            if 'sina' in self.providers and self.provider_status.get('sina', False):
                try:
                    sina_overview = self.providers['sina'].get_market_overview()
                    if sina_overview and 'indices' in sina_overview:
                        overview['indices'].update(sina_overview['indices'])
                except Exception as e:
                    logger.debug(f"⚠️ 新浪市场总览获取失败: {e}")
            
            # 获取热门股票
            if 'eastmoney' in self.providers and self.provider_status.get('eastmoney', False):
                try:
                    hot_stocks = self.providers['eastmoney'].get_top_stocks(limit=20)
                    overview['hot_stocks'] = hot_stocks
                except Exception as e:
                    logger.debug(f"⚠️ 东方财富热门股票获取失败: {e}")
            
            # 获取市场情绪
            if 'xueqiu' in self.providers and self.provider_status.get('xueqiu', False):
                try:
                    hot_topics = self.providers['xueqiu'].get_hot_topics(limit=10)
                    if hot_topics:
                        # 分析热门话题的情绪
                        positive_count = sum(1 for topic in hot_topics if 'sentiment' in str(topic).lower())
                        overview['market_sentiment'] = {
                            'hot_topics_count': len(hot_topics),
                            'positive_ratio': positive_count / len(hot_topics) if hot_topics else 0
                        }
                except Exception as e:
                    logger.debug(f"⚠️ 雪球市场情绪获取失败: {e}")
            
            logger.info("✅ 获取到市场总览数据")
            return overview
            
        except Exception as e:
            logger.error(f"❌ 获取市场总览失败: 错误: {str(e)}")
            return {}

    def _merge_price_data(self, price_data: Dict[str, Dict]) -> Dict[str, Any]:
        """合并多个数据源的价格数据（保持向后兼容）"""
        return self._merge_price_data_smart(price_data)
    
    def _merge_price_data_smart(self, price_data: Dict[str, Dict]) -> Dict[str, Any]:
        """智能合并多个数据源的价格数据"""
        try:
            merged = {}
            
            # 获取所有字段
            all_fields = set()
            for data in price_data.values():
                all_fields.update(data.keys())
            
            # 数据源权重（基于优先级）
            source_weights = {
                'eastmoney': 0.4,    # 东方财富权重最高
                'tencent': 0.3,      # 腾讯财经
                'sina': 0.2,         # 新浪财经
                'tushare': 0.05,     # Tushare
                'akshare': 0.05      # AKShare
            }
            
            for field in all_fields:
                values = []
                weights = []
                sources_used = []
                
                for source, data in price_data.items():
                    if field in data and data[field] is not None:
                        value = data[field]
                        if isinstance(value, (int, float)) and abs(value) > 0:
                            # 过滤异常值
                            if self._is_valid_value(field, value, values):
                                values.append(value)
                                weights.append(source_weights.get(source, 0.1))
                                sources_used.append(source)
                        elif isinstance(value, str) and value.strip():
                            # 字符串类型，取第一个非空值
                            if field not in merged:
                                merged[field] = value.strip()
                
                # 数值类型使用加权平均
                if values and field not in merged:
                    total_weight = sum(weights)
                    if total_weight > 0:
                        weighted_value = sum(v * w for v, w in zip(values, weights)) / total_weight
                        merged[field] = round(weighted_value, 2) if field in ['current_price', 'open', 'high', 'low', 'prev_close'] else int(weighted_value)
                        
                        # 添加数据质量信息
                        if field == 'current_price':
                            merged['price_sources'] = sources_used
                            merged['price_variance'] = self._calculate_variance(values)
                    else:
                        merged[field] = values[0]
            
            # 添加数据质量指标
            merged['data_sources_count'] = len(price_data)
            merged['data_sources_list'] = list(price_data.keys())
            
            return merged
            
        except Exception as e:
            logger.error(f"❌ 智能合并价格数据失败: {str(e)}")
            return {}
    
    def _is_valid_value(self, field: str, value: float, existing_values: List[float]) -> bool:
        """检查数值是否在合理范围内"""
        try:
            if not existing_values:
                return True
            
            # 计算现有值的平均值
            avg_value = sum(existing_values) / len(existing_values)
            
            # 价格字段允许5%偏差，成交量允许20%偏差
            max_deviation = 0.05 if 'price' in field.lower() else 0.2
            
            deviation = abs(value - avg_value) / avg_value if avg_value > 0 else 0
            return deviation <= max_deviation
            
        except Exception:
            return True
    
    def _calculate_variance(self, values: List[float]) -> float:
        """计算数值方差"""
        try:
            if len(values) < 2:
                return 0.0
            
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            return round(variance ** 0.5, 4)  # 返回标准差
        except Exception:
            return 0.0

    def _deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """新闻去重"""
        try:
            seen_titles = set()
            unique_news = []
            
            for news in news_list:
                title = news.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_news.append(news)
            
            return unique_news
            
        except Exception as e:
            logger.error(f"❌ 新闻去重失败: {str(e)}")
            return news_list

    def get_provider_status(self) -> Dict[str, bool]:
        """获取所有数据源状态"""
        return self.provider_status.copy()

    def test_all_providers(self, test_symbol: str = '000001') -> Dict[str, Any]:
        """测试所有数据源"""
        test_results = {}
        
        for source, provider in self.providers.items():
            try:
                if hasattr(provider, 'get_stock_info'):
                    result = provider.get_stock_info(test_symbol)
                    test_results[source] = {
                        'status': 'success' if result else 'no_data',
                        'data': bool(result)
                    }
                else:
                    test_results[source] = {
                        'status': 'no_method',
                        'data': False
                    }
            except Exception as e:
                test_results[source] = {
                    'status': 'error',
                    'error': str(e),
                    'data': False
                }
        
        logger.info(f"📊 数据源测试完成: {test_symbol}")
        return test_results


# 全局实例
_enhanced_data_manager = None

def get_enhanced_data_manager() -> EnhancedDataManager:
    """获取增强数据源管理器实例"""
    global _enhanced_data_manager
    if _enhanced_data_manager is None:
        _enhanced_data_manager = EnhancedDataManager()
    return _enhanced_data_manager


# 便捷函数
def get_comprehensive_stock_data(symbol: str) -> Dict[str, Any]:
    """获取综合股票数据"""
    return get_enhanced_data_manager().get_comprehensive_stock_info(symbol)

def get_comprehensive_news_data(symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
    """获取综合新闻数据"""
    return get_enhanced_data_manager().get_comprehensive_news(symbol, limit)

def get_comprehensive_sentiment_data(symbol: str) -> Dict[str, Any]:
    """获取综合情绪数据"""
    return get_enhanced_data_manager().get_comprehensive_sentiment(symbol)

def get_social_discussions_data(symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
    """获取社交讨论数据"""
    return get_enhanced_data_manager().get_social_discussions(symbol, limit)