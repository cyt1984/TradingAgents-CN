#!/usr/bin/env python3
"""
Web界面数据接口
为Web应用提供统一的数据接口，使用增强数据管理器
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import warnings

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager

logger = get_logger('web_interface')
warnings.filterwarnings('ignore')


class WebDataInterface:
    """Web界面数据接口"""
    
    def __init__(self):
        """初始化Web数据接口"""
        self.data_manager = get_enhanced_data_manager()
        logger.info("✅ Web数据接口初始化完成")
    
    def get_stock_display_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票展示数据（Web界面专用）
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 包含股票信息、数据质量和来源的完整数据
        """
        try:
            # 获取综合股票信息
            stock_info = self.data_manager.get_comprehensive_stock_info(symbol)
            
            if not stock_info:
                return {
                    'error': f'无法获取股票 {symbol} 的数据',
                    'symbol': symbol,
                    'status': 'failed'
                }
            
            # 格式化展示数据
            formatted_data = {
                'symbol': stock_info.get('symbol', symbol),
                'name': stock_info.get('name', f'股票{symbol}'),
                'current_price': stock_info.get('current_price', 0),
                'change': stock_info.get('change', 0),
                'change_pct': stock_info.get('change_pct', 0),
                'volume': stock_info.get('volume', 0),
                'turnover': stock_info.get('turnover', 0),
                'high': stock_info.get('high', 0),
                'low': stock_info.get('low', 0),
                'open': stock_info.get('open', 0),
                'prev_close': stock_info.get('prev_close', 0),
                'market_cap': stock_info.get('market_cap', 0),
                'pe_ratio': stock_info.get('pe_ratio', 0),
                'pb_ratio': stock_info.get('pb_ratio', 0),
                'timestamp': stock_info.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'data_sources': stock_info.get('sources', []),
                'primary_source': stock_info.get('primary_source', 'unknown'),
                'data_quality_score': stock_info.get('data_quality_score', 0),
                'data_sources_count': stock_info.get('data_sources_count', 0),
                'price_variance': stock_info.get('price_variance', 0),
                'status': 'success'
            }
            
            # 添加数据质量评估
            quality_score = formatted_data['data_quality_score']
            if quality_score >= 0.8:
                formatted_data['quality_grade'] = '优秀'
            elif quality_score >= 0.6:
                formatted_data['quality_grade'] = '良好'
            elif quality_score >= 0.4:
                formatted_data['quality_grade'] = '一般'
            else:
                formatted_data['quality_grade'] = '较差'
            
            # 格式化数值显示
            formatted_data.update({
                'price_display': f"¥{formatted_data['current_price']:.2f}",
                'change_display': f"{formatted_data['change']:+.2f}",
                'change_pct_display': f"{formatted_data['change_pct']:+.2f}%",
                'volume_display': self._format_volume(formatted_data['volume']),
                'turnover_display': f"¥{formatted_data['turnover']:,.0f}",
                'market_cap_display': self._format_market_cap(formatted_data['market_cap']),
                'sources_display': ', '.join(formatted_data['data_sources'])
            })
            
            logger.info(f"✅ Web接口成功获取股票展示数据: {symbol}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"❌ Web接口获取股票数据失败: {symbol}, 错误: {str(e)}")
            return {
                'error': str(e),
                'symbol': symbol,
                'status': 'failed'
            }
    
    def get_enhanced_stock_data(self, symbol: str, include_news: bool = True, include_sentiment: bool = True) -> Dict[str, Any]:
        """
        获取增强股票数据（包含新闻和情绪分析）
        
        Args:
            symbol: 股票代码
            include_news: 是否包含新闻数据
            include_sentiment: 是否包含情绪分析
            
        Returns:
            Dict: 完整的增强股票数据
        """
        try:
            # 基础股票信息
            stock_data = self.get_stock_display_data(symbol)
            
            if stock_data.get('status') == 'failed':
                return stock_data
            
            # 增强数据容器
            enhanced_data = {
                'stock_info': stock_data,
                'news_data': [],
                'sentiment_data': {},
                'social_discussions': [],
                'market_context': {}
            }
            
            # 新闻数据
            if include_news:
                try:
                    news_data = self.data_manager.get_comprehensive_news(symbol, limit=10)
                    enhanced_data['news_data'] = news_data
                except Exception as e:
                    logger.warning(f"⚠️ 获取新闻数据失败: {symbol}, 错误: {str(e)}")
            
            # 情绪分析数据
            if include_sentiment:
                try:
                    sentiment_data = self.data_manager.get_comprehensive_sentiment(symbol)
                    enhanced_data['sentiment_data'] = sentiment_data
                except Exception as e:
                    logger.warning(f"⚠️ 获取情绪数据失败: {symbol}, 错误: {str(e)}")
            
            # 社交讨论数据
            try:
                social_data = self.data_manager.get_social_discussions(symbol, limit=20)
                enhanced_data['social_discussions'] = social_data
            except Exception as e:
                logger.warning(f"⚠️ 获取社交讨论数据失败: {symbol}, 错误: {str(e)}")
            
            # 市场背景
            try:
                market_context = self.data_manager.get_market_overview()
                enhanced_data['market_context'] = market_context
            except Exception as e:
                logger.warning(f"⚠️ 获取市场背景数据失败: {symbol}, 错误: {str(e)}")
            
            # 添加数据汇总信息
            enhanced_data['summary'] = {
                'total_data_sources': len(stock_data.get('data_sources', [])),
                'news_count': len(enhanced_data['news_data']),
                'sentiment_score': enhanced_data['sentiment_data'].get('overall_sentiment', 0),
                'social_discussion_count': len(enhanced_data['social_discussions']),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✅ Web接口成功获取增强股票数据: {symbol}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Web接口获取增强股票数据失败: {symbol}, 错误: {str(e)}")
            return {
                'error': str(e),
                'symbol': symbol,
                'status': 'failed'
            }
    
    def get_data_sources_status(self) -> Dict[str, Any]:
        """获取数据源状态信息"""
        try:
            status = self.data_manager.get_provider_status()
            
            # 格式化状态信息
            formatted_status = {}
            for source, is_active in status.items():
                formatted_status[source] = {
                    'name': self._get_source_display_name(source),
                    'status': '可用' if is_active else '不可用',
                    'is_active': is_active,
                    'priority': self._get_source_priority(source)
                }
            
            return {
                'sources_status': formatted_status,
                'total_active': sum(1 for s in status.values() if s),
                'total_sources': len(status),
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取数据源状态失败: {str(e)}")
            return {}
    
    def test_all_data_sources(self, test_symbol: str = '000001') -> Dict[str, Any]:
        """测试所有数据源"""
        try:
            test_results = self.data_manager.test_all_providers(test_symbol)
            
            # 格式化测试结果
            formatted_results = {
                'test_symbol': test_symbol,
                'total_sources': len(test_results),
                'successful_sources': 0,
                'failed_sources': 0,
                'results': {}
            }
            
            for source, result in test_results.items():
                formatted_results['results'][source] = {
                    'status': result.get('status', 'unknown'),
                    'success': result.get('data', False),
                    'error': result.get('error', '')
                }
                
                if result.get('data', False):
                    formatted_results['successful_sources'] += 1
                else:
                    formatted_results['failed_sources'] += 1
            
            formatted_results['success_rate'] = formatted_results['successful_sources'] / formatted_results['total_sources'] if formatted_results['total_sources'] > 0 else 0
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ 测试数据源失败: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def _format_volume(self, volume: int) -> str:
        """格式化成交量显示"""
        try:
            if volume >= 1_000_000:
                return f"{volume/1_000_000:.1f}M"
            elif volume >= 1_000:
                return f"{volume/1_000:.1f}K"
            else:
                return str(volume)
        except:
            return str(volume)
    
    def _format_market_cap(self, market_cap: float) -> str:
        """格式化市值显示"""
        try:
            if market_cap >= 1_000_000_000:
                return f"{market_cap/1_000_000_000:.1f}B"
            elif market_cap >= 1_000_000:
                return f"{market_cap/1_000_000:.1f}M"
            else:
                return f"{market_cap:.0f}"
        except:
            return str(market_cap)
    
    def _get_source_display_name(self, source: str) -> str:
        """获取数据源显示名称"""
        display_names = {
            'eastmoney': '东方财富',
            'tencent': '腾讯财经',
            'sina': '新浪财经',
            'xueqiu': '雪球',
            'guba': '东方财富股吧',
            'tushare': 'Tushare',
            'akshare': 'AKShare'
        }
        return display_names.get(source, source)
    
    def _get_source_priority(self, source: str) -> int:
        """获取数据源优先级"""
        priority_order = ['eastmoney', 'tencent', 'sina', 'xueqiu', 'tushare', 'akshare']
        try:
            return priority_order.index(source) + 1
        except ValueError:
            return 99


# 全局Web接口实例
_web_interface = None

def get_web_data_interface() -> WebDataInterface:
    """获取Web数据接口实例"""
    global _web_interface
    if _web_interface is None:
        _web_interface = WebDataInterface()
    return _web_interface


# 便捷函数
def get_web_stock_data(symbol: str) -> Dict[str, Any]:
    """获取Web展示用的股票数据"""
    interface = get_web_data_interface()
    return interface.get_stock_display_data(symbol)

def get_web_enhanced_stock_data(symbol: str, include_news: bool = True, include_sentiment: bool = True) -> Dict[str, Any]:
    """获取Web增强股票数据"""
    interface = get_web_data_interface()
    return interface.get_enhanced_stock_data(symbol, include_news, include_sentiment)

def get_web_data_sources_status() -> Dict[str, Any]:
    """获取Web数据源状态"""
    interface = get_web_data_interface()
    return interface.get_data_sources_status()

def test_web_data_sources(symbol: str = '000001') -> Dict[str, Any]:
    """测试Web数据源"""
    interface = get_web_data_interface()
    return interface.test_all_data_sources(symbol)