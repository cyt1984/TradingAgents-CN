#!/usr/bin/env python3
"""
东方财富股吧数据爬虫工具
提供东方财富股吧讨论、股评、情绪分析等数据获取功能
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


class EastMoneyGubaProvider:
    """东方财富股吧数据提供器"""

    def __init__(self):
        """初始化东方财富股吧数据提供器"""
        self.base_url = "https://guba.eastmoney.com"
        self.api_url = "https://gbapi.eastmoney.com"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://guba.eastmoney.com/',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("✅ 东方财富股吧数据提供器初始化成功")

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[requests.Response]:
        """发起HTTP请求，返回Response对象"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None

    def _make_json_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """发起HTTP请求，返回JSON数据"""
        try:
            response = self._make_request(url, params, timeout)
            if not response:
                return None
            
            # 尝试解析JSON响应
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.debug("⚠️ 响应不是JSON格式")
                return None
                
        except Exception as e:
            logger.error(f"❌ JSON请求失败: {url}, 错误: {str(e)}")
            return None

    def get_stock_discussions(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取股票讨论帖子"""
        try:
            # 构建股吧URL
            guba_url = f"{self.base_url}/list,{symbol}.html"
            
            response = self._make_request(guba_url)
            if not response:
                return []
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            discussions = []
            
            # 查找讨论列表
            post_items = soup.find_all('div', class_='articleh')[:limit]
            
            for item in post_items:
                try:
                    # 提取标题和链接
                    title_elem = item.find('span', class_='l3') or item.find('a')
                    if not title_elem:
                        continue
                    
                    title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    post_url = title_link.get('href', '')
                    if post_url and not post_url.startswith('http'):
                        post_url = f"{self.base_url}{post_url}"
                    
                    # 提取发帖时间
                    time_elem = item.find('div', class_='l5')
                    post_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    # 提取用户名
                    user_elem = item.find('div', class_='l2')
                    user_name = user_elem.get_text(strip=True) if user_elem else ''
                    
                    # 提取回帖数和阅读数
                    read_elem = item.find('div', class_='l1')
                    reply_elem = item.find('div', class_='l4')
                    
                    read_count = 0
                    reply_count = 0
                    
                    if read_elem:
                        read_text = read_elem.get_text(strip=True)
                        read_match = re.search(r'(\d+)', read_text)
                        read_count = int(read_match.group(1)) if read_match else 0
                    
                    if reply_elem:
                        reply_text = reply_elem.get_text(strip=True)
                        reply_match = re.search(r'(\d+)', reply_text)
                        reply_count = int(reply_match.group(1)) if reply_match else 0
                    
                    # 获取帖子内容摘要
                    content_summary = self._get_post_summary(post_url)
                    
                    discussion = {
                        'title': title,
                        'url': post_url,
                        'content_summary': content_summary,
                        'user_name': user_name,
                        'post_time': post_time,
                        'read_count': read_count,
                        'reply_count': reply_count,
                        'heat_score': read_count + reply_count * 10,  # 热度评分
                        'sentiment_score': self._analyze_sentiment(title + ' ' + content_summary),
                        'symbol': symbol,
                        'source': '东方财富股吧'
                    }
                    discussions.append(discussion)
                    
                except Exception as e:
                    logger.debug(f"⚠️ 解析单条讨论失败: {str(e)}")
                    continue
            
            # 按热度排序
            discussions.sort(key=lambda x: x['heat_score'], reverse=True)
            
            logger.info(f"✅ 获取到 {len(discussions)} 条东方财富股吧讨论: {symbol}")
            return discussions
            
        except Exception as e:
            logger.error(f"❌ 获取东方财富股吧讨论失败: {symbol}, 错误: {str(e)}")
            return []

    def _get_post_summary(self, post_url: str, max_length: int = 200) -> str:
        """获取帖子内容摘要"""
        try:
            if not post_url:
                return ''
            
            response = self._make_request(post_url, timeout=15)
            if not response:
                return ''
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找帖子内容
            content_elem = (
                soup.find('div', class_='stockcodec') or 
                soup.find('div', class_='article-body') or
                soup.find('div', id='zwconttb')
            )
            
            if content_elem:
                # 提取文本内容
                content_text = content_elem.get_text(strip=True)
                # 清理和截取
                content_text = re.sub(r'\s+', ' ', content_text)
                if len(content_text) > max_length:
                    content_text = content_text[:max_length] + '...'
                return content_text
            
            return ''
            
        except Exception as e:
            logger.debug(f"⚠️ 获取帖子摘要失败: {str(e)}")
            return ''

    def get_stock_sentiment_analysis(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """获取股票情绪分析"""
        try:
            discussions = self.get_stock_discussions(symbol, limit=100)
            if not discussions:
                return {}
            
            # 计算情绪统计
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            total_heat = 0
            total_interactions = 0
            
            for discussion in discussions:
                sentiment = discussion['sentiment_score']
                if sentiment > 0.1:
                    positive_count += 1
                elif sentiment < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
                
                total_heat += discussion['heat_score']
                total_interactions += discussion['reply_count'] + discussion['read_count']
            
            total_count = len(discussions)
            
            # 计算热门关键词
            hot_keywords = self._extract_hot_keywords(discussions)
            
            return {
                'symbol': symbol,
                'total_discussions': total_count,
                'positive_ratio': positive_count / total_count if total_count > 0 else 0,
                'negative_ratio': negative_count / total_count if total_count > 0 else 0,
                'neutral_ratio': neutral_count / total_count if total_count > 0 else 0,
                'total_heat_score': total_heat,
                'avg_heat_score': total_heat / total_count if total_count > 0 else 0,
                'total_interactions': total_interactions,
                'avg_interactions': total_interactions / total_count if total_count > 0 else 0,
                'sentiment_score': (positive_count - negative_count) / total_count if total_count > 0 else 0,
                'hot_keywords': hot_keywords,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'source': '东方财富股吧'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取股吧情绪分析失败: {symbol}, 错误: {str(e)}")
            return {}

    def get_hot_stocks_discussions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门股票讨论"""
        try:
            # 访问股吧首页获取热门股票
            hot_url = f"{self.base_url}/default,99,f,0.html"
            
            response = self._make_request(hot_url)
            if not response:
                return []
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            hot_discussions = []
            
            # 查找热门帖子列表
            post_items = soup.find_all('div', class_='articleh')[:limit]
            
            for item in post_items:
                try:
                    # 提取股票代码
                    code_elem = item.find('a')
                    if not code_elem:
                        continue
                    
                    href = code_elem.get('href', '')
                    symbol_match = re.search(r'list,(\w+)\.html', href)
                    symbol = symbol_match.group(1) if symbol_match else ''
                    
                    # 提取标题
                    title = code_elem.get_text(strip=True)
                    
                    # 提取其他信息（类似上面的方法）
                    time_elem = item.find('div', class_='l5')
                    post_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    user_elem = item.find('div', class_='l2')
                    user_name = user_elem.get_text(strip=True) if user_elem else ''
                    
                    read_elem = item.find('div', class_='l1')
                    reply_elem = item.find('div', class_='l4')
                    
                    read_count = 0
                    reply_count = 0
                    
                    if read_elem:
                        read_text = read_elem.get_text(strip=True)
                        read_match = re.search(r'(\d+)', read_text)
                        read_count = int(read_match.group(1)) if read_match else 0
                    
                    if reply_elem:
                        reply_text = reply_elem.get_text(strip=True)
                        reply_match = re.search(r'(\d+)', reply_text)
                        reply_count = int(reply_match.group(1)) if reply_match else 0
                    
                    discussion = {
                        'symbol': symbol,
                        'title': title,
                        'user_name': user_name,
                        'post_time': post_time,
                        'read_count': read_count,
                        'reply_count': reply_count,
                        'heat_score': read_count + reply_count * 10,
                        'sentiment_score': self._analyze_sentiment(title),
                        'source': '东方财富股吧'
                    }
                    hot_discussions.append(discussion)
                    
                except Exception as e:
                    logger.debug(f"⚠️ 解析热门讨论失败: {str(e)}")
                    continue
            
            # 按热度排序
            hot_discussions.sort(key=lambda x: x['heat_score'], reverse=True)
            
            logger.info(f"✅ 获取到 {len(hot_discussions)} 条热门股吧讨论")
            return hot_discussions
            
        except Exception as e:
            logger.error(f"❌ 获取热门股吧讨论失败: 错误: {str(e)}")
            return []

    def search_discussions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索相关讨论"""
        try:
            # 构建搜索URL
            search_url = f"{self.base_url}/search"
            params = {
                'type': '1',  # 帖子搜索
                'keyword': keyword,
                'p': '1'
            }
            
            response = self._make_request(search_url, params)
            if not response:
                return []
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            discussions = []
            
            # 查找搜索结果
            result_items = soup.find_all('div', class_='result-item')[:limit]
            
            for item in result_items:
                try:
                    # 提取标题和链接
                    title_elem = item.find('h3') or item.find('a')
                    if not title_elem:
                        continue
                    
                    title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                    title = title_link.get_text(strip=True) if title_link else ''
                    post_url = title_link.get('href', '') if title_link else ''
                    
                    if post_url and not post_url.startswith('http'):
                        post_url = f"{self.base_url}{post_url}"
                    
                    # 提取摘要
                    summary_elem = item.find('p', class_='summary') or item.find('div', class_='summary')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ''
                    
                    # 提取时间和用户
                    meta_elem = item.find('div', class_='meta') or item.find('span', class_='meta')
                    meta_text = meta_elem.get_text(strip=True) if meta_elem else ''
                    
                    # 提取股票代码（如果有）
                    symbol_match = re.search(r'(\d{6})', title + summary)
                    symbol = symbol_match.group(1) if symbol_match else ''
                    
                    discussion = {
                        'title': title,
                        'summary': summary,
                        'url': post_url,
                        'meta_info': meta_text,
                        'symbol': symbol,
                        'relevance_score': self._calculate_relevance(title + ' ' + summary, keyword),
                        'sentiment_score': self._analyze_sentiment(title + ' ' + summary),
                        'keyword': keyword,
                        'source': '东方财富股吧'
                    }
                    discussions.append(discussion)
                    
                except Exception as e:
                    logger.debug(f"⚠️ 解析搜索结果失败: {str(e)}")
                    continue
            
            # 按相关性排序
            discussions.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"✅ 搜索到 {len(discussions)} 条相关股吧讨论: {keyword}")
            return discussions
            
        except Exception as e:
            logger.error(f"❌ 搜索股吧讨论失败: {keyword}, 错误: {str(e)}")
            return []

    def _analyze_sentiment(self, text: str) -> float:
        """简单的情绪分析"""
        try:
            if not text:
                return 0.0
            
            # 积极词汇
            positive_words = [
                '涨', '牛', '好', '赚', '盈利', '上涨', '看多', '买入', '推荐', '优秀', 
                '强势', '突破', '利好', '机会', '抄底', '反弹', '爆发', '飞'
            ]
            
            # 消极词汇
            negative_words = [
                '跌', '熊', '亏', '损失', '下跌', '看空', '卖出', '风险', '危险', 
                '暴跌', '套牢', '割肉', '利空', '跳水', '崩盘', '血亏', '腰斩'
            ]
            
            positive_score = sum(1 for word in positive_words if word in text)
            negative_score = sum(1 for word in negative_words if word in text)
            
            # 简单的情绪评分 (-1 到 1)
            total_words = len(text)
            sentiment = (positive_score - negative_score) / max(total_words / 20, 1)
            
            return max(-1, min(1, sentiment))
            
        except Exception:
            return 0.0

    def _extract_hot_keywords(self, discussions: List[Dict], top_k: int = 10) -> List[str]:
        """提取热门关键词"""
        try:
            keyword_freq = {}
            
            for discussion in discussions:
                text = discussion.get('title', '') + ' ' + discussion.get('content_summary', '')
                
                # 简单的关键词提取（可以改进为更复杂的NLP方法）
                words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)  # 提取中文词汇
                
                for word in words:
                    if len(word) >= 2 and word not in ['股票', '公司', '今天', '明天', '现在']:
                        keyword_freq[word] = keyword_freq.get(word, 0) + 1
            
            # 按频率排序，返回前top_k个
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
            return [keyword for keyword, freq in sorted_keywords[:top_k]]
            
        except Exception:
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
            
            return min(1.0, keyword_count / max(total_chars / 50, 1))
            
        except Exception:
            return 0.0


# 全局实例
_eastmoney_guba_provider = None

def get_eastmoney_guba_provider() -> EastMoneyGubaProvider:
    """获取东方财富股吧数据提供器实例"""
    global _eastmoney_guba_provider
    if _eastmoney_guba_provider is None:
        _eastmoney_guba_provider = EastMoneyGubaProvider()
    return _eastmoney_guba_provider


# 便捷函数
def get_guba_discussions(symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
    """获取股票股吧讨论"""
    return get_eastmoney_guba_provider().get_stock_discussions(symbol, limit)

def get_guba_sentiment_analysis(symbol: str, days: int = 7) -> Dict[str, Any]:
    """获取股吧情绪分析"""
    return get_eastmoney_guba_provider().get_stock_sentiment_analysis(symbol, days)

def get_guba_hot_discussions(limit: int = 20) -> List[Dict[str, Any]]:
    """获取热门股吧讨论"""
    return get_eastmoney_guba_provider().get_hot_stocks_discussions(limit)

def search_guba_discussions(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """搜索股吧讨论"""
    return get_eastmoney_guba_provider().search_discussions(keyword, limit)