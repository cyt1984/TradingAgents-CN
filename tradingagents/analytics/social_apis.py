"""
社交媒体API集成模块
集成微博、雪球、东方财富等免费数据源
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class WeiboAPI:
    """微博热搜API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_hot_search(self, keyword: str = None) -> Dict:
        """获取微博热搜数据"""
        try:
            # 微博热搜榜
            url = "https://s.weibo.com/top/summary"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                hot_list = []
                
                # 解析热搜列表
                items = soup.find_all('tr')[1:]  # 跳过表头
                for item in items[:50]:  # 前50条
                    try:
                        title_elem = item.find('td', class_='td-02')
                        if title_elem:
                            title = title_elem.find('a').get_text(strip=True)
                            hot_num = title_elem.find('span')
                            hot_score = int(hot_num.get_text(strip=True)) if hot_num else 0
                            
                            # 检查是否包含股票相关关键词
                            stock_keywords = ['股票', 'A股', '涨停', '跌停', '大盘', '股市', '券商', '基金']
                            is_stock_related = any(keyword in title for keyword in stock_keywords)
                            
                            hot_list.append({
                                'title': title,
                                'heat_score': hot_score,
                                'is_stock_related': is_stock_related,
                                'rank': len(hot_list) + 1
                            })
                    except Exception as e:
                        continue
                
                return {
                    'total_hot': len(hot_list),
                    'stock_related': [h for h in hot_list if h['is_stock_related']],
                    'max_heat': max([h['heat_score'] for h in hot_list]) if hot_list else 0
                }
            
        except Exception as e:
            logger.error(f"[ERROR] 微博热搜获取失败: {e}")
        
        return {'total_hot': 0, 'stock_related': [], 'max_heat': 0}


class XueqiuAPI:
    """雪球API"""
    
    def __init__(self):
        self.base_url = "https://xueqiu.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://xueqiu.com'
        })
    
    def get_stock_heat(self, symbol: str) -> Dict:
        """获取雪球股票热度"""
        try:
            # 雪球股票页面
            url = f"https://xueqiu.com/S/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取关注人数
                followers_elem = soup.find('span', {'data-role': 'followersCount'})
                followers = int(followers_elem.get_text(strip=True).replace(',', '')) if followers_elem else 0
                
                # 获取讨论数
                posts_count = len(soup.find_all('div', class_='status__item'))
                
                # 获取雪球热股榜
                hot_url = "https://xueqiu.com/hot/stocks"
                hot_response = self.session.get(hot_url, timeout=10)
                
                rank = None
                if hot_response.status_code == 200:
                    hot_soup = BeautifulSoup(hot_response.text, 'html.parser')
                    # 解析热股榜，查找当前股票排名
                    
                return {
                    'followers': followers,
                    'discussion_count': posts_count,
                    'rank': rank,
                    'score': min(followers / 1000 + posts_count * 10, 100)
                }
                
        except Exception as e:
            logger.error(f"[ERROR] 雪球热度获取失败 {symbol}: {e}")
        
        return {'followers': 0, 'discussion_count': 0, 'rank': None, 'score': 0}


class EastMoneyAPI:
    """东方财富股吧API"""
    
    def __init__(self):
        self.base_url = "https://guba.eastmoney.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_guba_heat(self, symbol: str) -> Dict:
        """获取股吧热度"""
        try:
            # 东方财富股吧
            url = f"https://guba.eastmoney.com/list,{symbol}.html"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取帖子数量
                post_count = len(soup.find_all('div', class_='articleh'))
                
                # 获取阅读数
                read_counts = []
                for item in soup.find_all('div', class_='articleh')[:10]:
                    read_elem = item.find('span', class_='l1')
                    if read_elem:
                        read_count = int(read_elem.get_text(strip=True).replace(',', ''))
                        read_counts.append(read_count)
                
                total_reads = sum(read_counts) if read_counts else 0
                
                return {
                    'post_count': post_count,
                    'total_reads': total_reads,
                    'avg_reads': total_reads / max(post_count, 1),
                    'score': min(total_reads / 10000 + post_count * 5, 100)
                }
                
        except Exception as e:
            logger.error(f"[ERROR] 股吧热度获取失败 {symbol}: {e}")
        
        return {'post_count': 0, 'total_reads': 0, 'avg_reads': 0, 'score': 0}


class BaiduIndexAPI:
    """百度指数API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_search_trend(self, keyword: str) -> Dict:
        """获取搜索趋势"""
        try:
            # 百度指数API需要认证，这里使用模拟数据
            # 实际应用中需要申请API key
            
            # 模拟搜索趋势数据
            import random
            base_score = random.uniform(20, 80)
            
            # 生成7天趋势
            trend_data = []
            for i in range(7):
                daily_score = base_score + random.uniform(-20, 20)
                trend_data.append({
                    'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                    'index': max(0, daily_score)
                })
            
            # 计算变化率
            if len(trend_data) >= 2:
                change_7d = ((trend_data[0]['index'] - trend_data[-1]['index']) / max(trend_data[-1]['index'], 1)) * 100
            else:
                change_7d = 0
            
            return {
                'score': base_score,
                'trend': trend_data,
                'change_7d': change_7d,
                'peak_hours': ['09:30', '10:00', '14:00', '15:00']
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 百度指数获取失败: {e}")
        
        return {'score': 0, 'trend': [], 'change_7d': 0, 'peak_hours': []}


class SocialMediaAPI:
    """社交媒体API统一管理"""
    
    def __init__(self):
        self.weibo = WeiboAPI()
        self.xueqiu = XueqiuAPI()
        self.eastmoney = EastMoneyAPI()
        self.baidu = BaiduIndexAPI()
    
    def get_social_heat(self, symbol: str) -> Dict:
        """获取综合社交媒体热度"""
        try:
            # 获取股票名称用于搜索
            stock_name = self._get_stock_name(symbol)
            
            # 并行获取各平台数据
            import concurrent.futures
            
            def fetch_weibo():
                return self.weibo.get_hot_search(stock_name)
            
            def fetch_xueqiu():
                return self.xueqiu.get_stock_heat(symbol)
            
            def fetch_eastmoney():
                return self.eastmoney.get_guba_heat(symbol)
            
            def fetch_baidu():
                return self.baidu.get_search_trend(stock_name)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    'weibo': executor.submit(fetch_weibo),
                    'xueqiu': executor.submit(fetch_xueqiu),
                    'eastmoney': executor.submit(fetch_eastmoney),
                    'baidu': executor.submit(fetch_baidu)
                }
                
                results = {}
                for platform, future in futures.items():
                    try:
                        results[platform] = future.result(timeout=8)
                    except Exception as e:
                        logger.warning(f"[WARN] {platform} 数据获取失败: {e}")
                        results[platform] = {'score': 0}
            
            # 计算综合得分
            total_score = (
                results['weibo'].get('max_heat', 0) / 1000 * 0.2 +
                results['xueqiu'].get('score', 0) * 0.3 +
                results['eastmoney'].get('score', 0) * 0.3 +
                results['baidu'].get('score', 0) * 0.2
            )
            
            # 计算趋势
            trend_data = results['baidu'].get('trend', [])
            if len(trend_data) >= 2:
                change_24h = ((trend_data[-1]['index'] - trend_data[0]['index']) / max(trend_data[0]['index'], 1)) * 100
            else:
                change_24h = 0
            
            return {
                'score': min(total_score, 100),
                'platforms': results,
                'trend': {
                    'direction': 'up' if change_24h > 0 else 'down',
                    'change_24h': change_24h,
                    'momentum': 'strong' if abs(change_24h) > 50 else 'weak'
                },
                'risk_level': 'high' if total_score > 80 else 'medium' if total_score > 50 else 'low'
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 社交媒体热度获取失败 {symbol}: {e}")
        
        return {
            'score': 0,
            'platforms': {},
            'trend': {'direction': 'stable', 'change_24h': 0, 'momentum': 'neutral'},
            'risk_level': 'low'
        }
    
    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称用于搜索"""
        # 这里应该集成股票信息API
        # 暂时返回股票代码
        return symbol
    
    def get_real_time_mentions(self, keyword: str, limit: int = 10) -> List[Dict]:
        """获取实时提及数据"""
        try:
            # 实时获取各平台最新提及
            mentions = []
            
            # 微博实时
            weibo_data = self.weibo.get_hot_search(keyword)
            for item in weibo_data.get('stock_related', [])[:limit]:
                mentions.append({
                    'platform': 'weibo',
                    'content': item['title'],
                    'heat': item['heat_score'],
                    'timestamp': datetime.now().isoformat()
                })
            
            return mentions
            
        except Exception as e:
            logger.error(f"[ERROR] 实时提及获取失败: {e}")
        
        return []
    
    def get_heat_ranking(self, symbols: List[str]) -> List[Dict]:
        """获取热度排行榜"""
        results = []
        
        for symbol in symbols:
            try:
                heat_data = self.get_social_heat(symbol)
                results.append({
                    'symbol': symbol,
                    'heat_score': heat_data.get('score', 0),
                    'platforms': heat_data.get('platforms', {}),
                    'trend': heat_data.get('trend', {})
                })
            except Exception as e:
                logger.error(f"[ERROR] 热度排行获取失败 {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'heat_score': 0,
                    'error': str(e)
                })
        
        # 按热度排序
        results.sort(key=lambda x: x.get('heat_score', 0), reverse=True)
        return results