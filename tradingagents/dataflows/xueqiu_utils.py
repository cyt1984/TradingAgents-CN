#!/usr/bin/env python3
"""
雪球论坛数据爬虫工具
提供雪球论坛股票讨论、情绪分析等数据获取功能
"""

import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, List
import warnings
from datetime import datetime, timedelta
import time
import re
from bs4 import BeautifulSoup

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')


class XueqiuProvider:
    """雪球数据提供器"""

    def __init__(self):
        """初始化雪球数据提供器"""
        self.base_url = "https://xueqiu.com"
        self.api_url = "https://stock.xueqiu.com/v5"
        self.discuss_url = "https://xueqiu.com/query/v1"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://xueqiu.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 初始化会话，获取必要的cookies
        self._init_session()
        
        logger.info("✅ 雪球数据提供器初始化成功")

    def _init_session(self):
        """初始化雪球会话，获取必要的cookies"""
        try:
            # 访问首页获取cookies
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                logger.debug("✅ 雪球会话初始化成功")
            else:
                logger.warning(f"⚠️ 雪球会话初始化异常，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 雪球会话初始化失败: {str(e)}")

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """发起HTTP请求"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # 尝试解析JSON响应
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.debug("⚠️ 响应不是JSON格式，返回原始文本")
                return {'raw_text': response.text}
                
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None

    def get_stock_discussions(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取股票讨论帖子"""
        try:
            # 雪球股票代码格式转换
            xq_symbol = self._convert_to_xueqiu_symbol(symbol)
            if not xq_symbol:
                return []
            
            # 构建讨论API URL
            url = f"{self.discuss_url}/query.json"
            params = {
                'count': limit,
                'source': 'all',
                'type': 'all',
                'q': xq_symbol,
            }
            
            data = self._make_request(url, params)
            if not data or 'list' not in data:
                return []
            
            discussions = []
            for item in data['list']:
                try:
                    discussion = {
                        'id': item.get('id', ''),
                        'title': item.get('title', ''),
                        'text': item.get('text', ''),
                        'user_name': item.get('user', {}).get('screen_name', ''),
                        'user_id': item.get('user', {}).get('id', ''),
                        'created_at': item.get('created_at', 0),
                        'reply_count': item.get('reply_count', 0),
                        'retweet_count': item.get('retweet_count', 0),
                        'fav_count': item.get('fav_count', 0),
                        'view_count': item.get('view_count', 0),
                        'sentiment_score': self._analyze_sentiment(item.get('text', '')),
                        'symbol': symbol,
                        'source': '雪球'
                    }
                    discussions.append(discussion)
                except Exception as e:
                    logger.debug(f"⚠️ 解析单条讨论失败: {str(e)}")
                    continue
            
            logger.info(f"✅ 获取到 {len(discussions)} 条雪球讨论: {symbol}")
            return discussions
            
        except Exception as e:
            logger.error(f"❌ 获取雪球讨论失败: {symbol}, 错误: {str(e)}")
            return []

    def get_stock_sentiment(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """获取股票情绪分析"""
        try:
            discussions = self.get_stock_discussions(symbol, limit=100)
            if not discussions:
                return {}
            
            # 计算情绪统计
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            total_interactions = 0
            
            for discussion in discussions:
                sentiment = discussion['sentiment_score']
                if sentiment > 0.1:
                    positive_count += 1
                elif sentiment < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
                
                # 统计互动数据
                total_interactions += (
                    discussion['reply_count'] + 
                    discussion['retweet_count'] + 
                    discussion['fav_count']
                )
            
            total_count = len(discussions)
            
            return {
                'symbol': symbol,
                'total_discussions': total_count,
                'positive_ratio': positive_count / total_count if total_count > 0 else 0,
                'negative_ratio': negative_count / total_count if total_count > 0 else 0,
                'neutral_ratio': neutral_count / total_count if total_count > 0 else 0,
                'total_interactions': total_interactions,
                'avg_interactions': total_interactions / total_count if total_count > 0 else 0,
                'sentiment_score': (positive_count - negative_count) / total_count if total_count > 0 else 0,
                'data_date': datetime.now().strftime('%Y-%m-%d'),
                'source': '雪球'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取雪球情绪分析失败: {symbol}, 错误: {str(e)}")
            return {}

    def get_user_portfolio(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户持仓信息（如果公开）"""
        try:
            url = f"{self.api_url}/stock/portfolio/stock/list.json"
            params = {
                'size': 100,
                'uid': user_id
            }
            
            data = self._make_request(url, params)
            if not data or 'data' not in data:
                return []
            
            portfolio = []
            for item in data['data']:
                try:
                    stock = {
                        'symbol': item.get('symbol', ''),
                        'name': item.get('name', ''),
                        'weight': item.get('weight', 0),
                        'profit': item.get('profit', 0),
                        'profit_rate': item.get('profit_rate', 0),
                        'user_id': user_id,
                        'source': '雪球'
                    }
                    portfolio.append(stock)
                except Exception as e:
                    logger.debug(f"⚠️ 解析持仓信息失败: {str(e)}")
                    continue
            
            logger.info(f"✅ 获取到用户持仓 {len(portfolio)} 只股票: {user_id}")
            return portfolio
            
        except Exception as e:
            logger.error(f"❌ 获取用户持仓失败: {user_id}, 错误: {str(e)}")
            return []

    def get_hot_topics(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门话题"""
        try:
            url = f"{self.discuss_url}/query.json"
            params = {
                'count': limit,
                'source': 'all',
                'type': 'status',
                'sort': 'time'
            }
            
            data = self._make_request(url, params)
            if not data or 'list' not in data:
                return []
            
            topics = []
            for item in data['list']:
                try:
                    # 提取股票相关话题
                    text = item.get('text', '')
                    symbols = self._extract_stock_symbols(text)
                    
                    topic = {
                        'id': item.get('id', ''),
                        'title': item.get('title', ''),
                        'text': text,
                        'user_name': item.get('user', {}).get('screen_name', ''),
                        'created_at': item.get('created_at', 0),
                        'reply_count': item.get('reply_count', 0),
                        'retweet_count': item.get('retweet_count', 0),
                        'fav_count': item.get('fav_count', 0),
                        'related_symbols': symbols,
                        'heat_score': item.get('reply_count', 0) + item.get('retweet_count', 0) * 2 + item.get('fav_count', 0),
                        'source': '雪球'
                    }
                    topics.append(topic)
                except Exception as e:
                    logger.debug(f"⚠️ 解析热门话题失败: {str(e)}")
                    continue
            
            # 按热度排序
            topics.sort(key=lambda x: x['heat_score'], reverse=True)
            
            logger.info(f"✅ 获取到 {len(topics)} 个雪球热门话题")
            return topics
            
        except Exception as e:
            logger.error(f"❌ 获取雪球热门话题失败: 错误: {str(e)}")
            return []

    def _convert_to_xueqiu_symbol(self, symbol: str) -> Optional[str]:
        """转换股票代码为雪球格式"""
        try:
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    return f"SZ{symbol}"  # 深交所
                else:
                    return f"SH{symbol}"  # 上交所
            elif symbol.upper().startswith(('SH', 'SZ')):
                return symbol.upper()
            else:
                return symbol.upper()
        except Exception:
            return None

    def _analyze_sentiment(self, text: str) -> float:
        """简单的情绪分析"""
        try:
            if not text:
                return 0.0
            
            # 积极词汇
            positive_words = ['涨', '牛', '好', '赚', '盈利', '上涨', '看多', '买入', '推荐', '优秀', '强势', '突破']
            # 消极词汇
            negative_words = ['跌', '熊', '亏', '损失', '下跌', '看空', '卖出', '风险', '危险', '暴跌', '套牢', '割肉']
            
            positive_score = sum(1 for word in positive_words if word in text)
            negative_score = sum(1 for word in negative_words if word in text)
            
            # 简单的情绪评分 (-1 到 1)
            total_words = len(text)
            sentiment = (positive_score - negative_score) / max(total_words / 10, 1)
            
            return max(-1, min(1, sentiment))
            
        except Exception:
            return 0.0

    def _extract_stock_symbols(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        try:
            symbols = []
            
            # 提取A股代码格式 (6位数字)
            a_stock_pattern = r'\b[0-9]{6}\b'
            matches = re.findall(a_stock_pattern, text)
            for match in matches:
                if match.startswith(('00', '30', '60')):  # 常见A股代码开头
                    symbols.append(match)
            
            # 提取雪球格式代码 (SH000001, SZ000001等)
            xq_pattern = r'\b(SH|SZ)[0-9]{6}\b'
            xq_matches = re.findall(xq_pattern, text, re.IGNORECASE)
            symbols.extend(xq_matches)
            
            # 提取美股代码格式 (大写字母)
            us_pattern = r'\$([A-Z]{1,5})\b'
            us_matches = re.findall(us_pattern, text)
            symbols.extend(us_matches)
            
            return list(set(symbols))  # 去重
            
        except Exception:
            return []

    def search_discussions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索相关讨论"""
        try:
            url = f"{self.discuss_url}/query.json"
            params = {
                'count': limit,
                'source': 'all',
                'type': 'all',
                'q': keyword
            }
            
            data = self._make_request(url, params)
            if not data or 'list' not in data:
                return []
            
            discussions = []
            for item in data['list']:
                try:
                    discussion = {
                        'id': item.get('id', ''),
                        'title': item.get('title', ''),
                        'text': item.get('text', ''),
                        'user_name': item.get('user', {}).get('screen_name', ''),
                        'created_at': item.get('created_at', 0),
                        'reply_count': item.get('reply_count', 0),
                        'related_symbols': self._extract_stock_symbols(item.get('text', '')),
                        'relevance_score': self._calculate_relevance(item.get('text', ''), keyword),
                        'keyword': keyword,
                        'source': '雪球'
                    }
                    discussions.append(discussion)
                except Exception as e:
                    logger.debug(f"⚠️ 解析搜索结果失败: {str(e)}")
                    continue
            
            # 按相关性排序
            discussions.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"✅ 搜索到 {len(discussions)} 条相关讨论: {keyword}")
            return discussions
            
        except Exception as e:
            logger.error(f"❌ 搜索雪球讨论失败: {keyword}, 错误: {str(e)}")
            return []

    def _calculate_relevance(self, text: str, keyword: str) -> float:
        """计算文本与关键词的相关性"""
        try:
            if not text or not keyword:
                return 0.0
            
            # 简单的相关性计算：关键词出现次数 / 总字数
            keyword_count = text.lower().count(keyword.lower())
            total_chars = len(text)
            
            if total_chars == 0:
                return 0.0
            
            return min(1.0, keyword_count / max(total_chars / 100, 1))
            
        except Exception:
            return 0.0


# 全局实例
_xueqiu_provider = None

def get_xueqiu_provider() -> XueqiuProvider:
    """获取雪球数据提供器实例"""
    global _xueqiu_provider
    if _xueqiu_provider is None:
        _xueqiu_provider = XueqiuProvider()
    return _xueqiu_provider


# 便捷函数
def get_xueqiu_discussions(symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
    """获取股票讨论"""
    return get_xueqiu_provider().get_stock_discussions(symbol, limit)

def get_xueqiu_sentiment(symbol: str, days: int = 7) -> Dict[str, Any]:
    """获取股票情绪分析"""
    return get_xueqiu_provider().get_stock_sentiment(symbol, days)

def get_xueqiu_hot_topics(limit: int = 20) -> List[Dict[str, Any]]:
    """获取热门话题"""
    return get_xueqiu_provider().get_hot_topics(limit)

def search_xueqiu_discussions(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """搜索相关讨论"""
    return get_xueqiu_provider().search_discussions(keyword, limit)