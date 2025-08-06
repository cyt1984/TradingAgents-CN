#!/usr/bin/env python3
"""
新浪财经数据源工具
提供新浪财经API数据获取的统一接口，包括实时行情、新闻、财经资讯等数据
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


class SinaFinanceProvider:
    """新浪财经数据提供器"""

    def __init__(self):
        """初始化新浪财经提供器"""
        self.base_url = "https://hq.sinajs.cn"
        self.news_url = "https://finance.sina.com.cn"
        self.api_url = "https://money.finance.sina.com.cn"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("✅ 新浪财经数据提供器初始化成功")

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[str]:
        """发起HTTP请求，返回原始文本"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            response.encoding = 'gbk'  # 新浪财经使用GBK编码
            return response.text
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None

    def _parse_sina_stock_data(self, raw_data: str) -> Optional[Dict]:
        """解析新浪股票数据字符串"""
        try:
            # 新浪股票API返回格式: var hq_str_sh000001="平安银行,8.350,8.350,8.350,..."
            if not raw_data or '=' not in raw_data:
                return None
            
            # 提取变量名和数据
            parts = raw_data.split('=', 1)
            if len(parts) != 2:
                return None
            
            var_name = parts[0].strip()
            data_part = parts[1].strip()
            
            # 提取股票代码
            if 'hq_str_' in var_name:
                code_part = var_name.split('hq_str_')[1]
                if code_part.startswith('sh') or code_part.startswith('sz'):
                    stock_code = code_part[2:]
                else:
                    stock_code = code_part
            else:
                stock_code = ''
            
            # 清理数据部分
            if data_part.startswith('"') and data_part.endswith('";'):
                data_part = data_part[1:-2]
            elif data_part.startswith('"') and data_part.endswith('"'):
                data_part = data_part[1:-1]
            
            # 按逗号分割数据字段
            fields = data_part.split(',')
            if len(fields) < 30:
                return None
            
            return {
                'code': stock_code,
                'name': fields[0],           # 股票名称
                'open': float(fields[1]) if fields[1] else 0,             # 开盘价
                'prev_close': float(fields[2]) if fields[2] else 0,       # 昨收价
                'current_price': float(fields[3]) if fields[3] else 0,    # 当前价格
                'high': float(fields[4]) if fields[4] else 0,             # 最高价
                'low': float(fields[5]) if fields[5] else 0,              # 最低价
                'bid1': float(fields[6]) if fields[6] else 0,             # 买一价
                'ask1': float(fields[7]) if fields[7] else 0,             # 卖一价
                'volume': int(fields[8]) if fields[8] else 0,             # 成交量(股)
                'turnover': float(fields[9]) if fields[9] else 0,         # 成交额
                'bid1_volume': int(fields[10]) if fields[10] else 0,      # 买一量
                'bid1_price': float(fields[11]) if fields[11] else 0,     # 买一价
                'bid2_volume': int(fields[12]) if fields[12] else 0,      # 买二量
                'bid2_price': float(fields[13]) if fields[13] else 0,     # 买二价
                'bid3_volume': int(fields[14]) if fields[14] else 0,      # 买三量
                'bid3_price': float(fields[15]) if fields[15] else 0,     # 买三价
                'bid4_volume': int(fields[16]) if fields[16] else 0,      # 买四量
                'bid4_price': float(fields[17]) if fields[17] else 0,     # 买四价
                'bid5_volume': int(fields[18]) if fields[18] else 0,      # 买五量
                'bid5_price': float(fields[19]) if fields[19] else 0,     # 买五价
                'ask1_volume': int(fields[20]) if fields[20] else 0,      # 卖一量
                'ask2_volume': int(fields[22]) if len(fields) > 22 and fields[22] else 0,      # 卖二量
                'ask2_price': float(fields[23]) if len(fields) > 23 and fields[23] else 0,     # 卖二价
                'date': fields[30] if len(fields) > 30 else '',           # 日期
                'time': fields[31] if len(fields) > 31 else '',           # 时间
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 解析新浪股票数据失败: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            # 构造新浪股票代码格式
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    sina_code = f"sz{symbol}"  # 深交所
                else:
                    sina_code = f"sh{symbol}"  # 上交所
            else:
                sina_code = symbol.lower()

            url = f"{self.base_url}/list={sina_code}"
            
            raw_data = self._make_request(url)
            if not raw_data:
                return None
            
            stock_data = self._parse_sina_stock_data(raw_data)
            if not stock_data:
                return None
            
            # 计算涨跌幅
            if stock_data['prev_close'] > 0:
                change = stock_data['current_price'] - stock_data['prev_close']
                change_pct = (change / stock_data['prev_close']) * 100
            else:
                change = 0
                change_pct = 0
            
            return {
                'symbol': symbol,
                'name': stock_data['name'],
                'current_price': stock_data['current_price'],
                'prev_close': stock_data['prev_close'],
                'open': stock_data['open'],
                'high': stock_data['high'],
                'low': stock_data['low'],
                'volume': stock_data['volume'],
                'turnover': stock_data['turnover'],
                'change': change,
                'change_pct': change_pct,
                'bid1': stock_data['bid1'],
                'ask1': stock_data['ask1'],
                'bid1_volume': stock_data['bid1_volume'],
                'ask1_volume': stock_data['ask1_volume'],
                'timestamp': stock_data['timestamp'],
                'source': '新浪财经'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取新浪股票信息失败: {symbol}, 错误: {str(e)}")
            return None

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量获取多只股票信息"""
        try:
            # 构造批量查询代码
            sina_codes = []
            for symbol in symbols:
                if len(symbol) == 6 and symbol.isdigit():
                    if symbol.startswith(('00', '30')):
                        sina_codes.append(f"sz{symbol}")
                    else:
                        sina_codes.append(f"sh{symbol}")
                else:
                    sina_codes.append(symbol.lower())
            
            # 新浪API支持批量查询，用逗号分隔
            code_str = ','.join(sina_codes)
            url = f"{self.base_url}/list={code_str}"
            
            raw_data = self._make_request(url)
            if not raw_data:
                return {}
            
            results = {}
            # 按行分割处理每只股票的数据
            lines = raw_data.strip().split('\\n')
            
            for i, line in enumerate(lines):
                if i < len(symbols) and line.strip():
                    stock_data = self._parse_sina_stock_data(line)
                    if stock_data:
                        symbol = symbols[i]
                        # 计算涨跌幅
                        if stock_data['prev_close'] > 0:
                            change = stock_data['current_price'] - stock_data['prev_close']
                            change_pct = (change / stock_data['prev_close']) * 100
                        else:
                            change = 0
                            change_pct = 0
                        
                        results[symbol] = {
                            'symbol': symbol,
                            'name': stock_data['name'],
                            'current_price': stock_data['current_price'],
                            'change': change,
                            'change_pct': change_pct,
                            'volume': stock_data['volume'],
                            'turnover': stock_data['turnover'],
                            'timestamp': stock_data['timestamp'],
                            'source': '新浪财经'
                        }
            
            logger.info(f"✅ 新浪财经批量获取到 {len(results)} 只股票信息")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量获取股票信息失败: 错误: {str(e)}")
            return {}

    def get_stock_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取股票相关新闻（通过爬取网页获取）"""
        try:
            # 获取股票信息以获得股票名称
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return []
            
            stock_name = stock_info['name']
            
            # 新浪财经搜索页面
            search_url = f"{self.news_url}/realtime/search.html"
            params = {
                'keyword': stock_name,
                'range': 'all',
                'source': 'all',
                'time': 'all'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('div', class_='news-item')
            
            news_list = []
            count = 0
            
            for item in news_items:
                if count >= limit:
                    break
                
                try:
                    title_elem = item.find('h2') or item.find('h3') or item.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    time_elem = item.find('span', class_='time') or item.find('time')
                    publish_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    source_elem = item.find('span', class_='source')
                    source = source_elem.get_text(strip=True) if source_elem else '新浪财经'
                    
                    summary_elem = item.find('p') or item.find('div', class_='summary')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ''
                    
                    if title and stock_name in title:  # 确保新闻与股票相关
                        news_item = {
                            'title': title,
                            'summary': summary,
                            'url': url if url.startswith('http') else f"https://finance.sina.com.cn{url}",
                            'publish_time': publish_time,
                            'source': source,
                            'symbol': symbol,
                            'relevance_score': 0.8  # 基础相关性评分
                        }
                        news_list.append(news_item)
                        count += 1
                
                except Exception as e:
                    logger.debug(f"⚠️ 解析单条新闻失败: {str(e)}")
                    continue
            
            logger.info(f"✅ 获取到 {len(news_list)} 条新浪财经新闻: {symbol}")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取新浪财经新闻失败: {symbol}, 错误: {str(e)}")
            return []

    def get_market_overview(self) -> Dict[str, Any]:
        """获取市场总览"""
        try:
            # 获取主要指数信息
            indices = ['sh000001', 'sz399001', 'sz399006']  # 上证、深证、创业板
            index_data = self.get_multiple_stocks(indices)
            
            overview = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'indices': {}
            }
            
            index_names = {
                'sh000001': '上证指数',
                'sz399001': '深证成指', 
                'sz399006': '创业板指'
            }
            
            for code, name in index_names.items():
                if code in index_data:
                    overview['indices'][name] = index_data[code]
            
            return overview
            
        except Exception as e:
            logger.error(f"❌ 获取市场总览失败: 错误: {str(e)}")
            return {}

    def get_hot_stocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取热门股票（通过网页抓取）"""
        try:
            url = f"{self.news_url}/money/ztjb/"  # 涨停敢死队页面
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找股票表格或列表
            stock_items = soup.find_all('tr')[1:limit+1]  # 跳过表头
            
            hot_stocks = []
            for item in stock_items:
                try:
                    cells = item.find_all('td')
                    if len(cells) >= 4:
                        code = cells[0].get_text(strip=True)
                        name = cells[1].get_text(strip=True)
                        price = cells[2].get_text(strip=True)
                        change_pct = cells[3].get_text(strip=True)
                        
                        hot_stocks.append({
                            'symbol': code,
                            'name': name,
                            'current_price': float(price) if price.replace('.', '').isdigit() else 0,
                            'change_pct': float(change_pct.replace('%', '')) if change_pct.replace('%', '').replace('-', '').replace('.', '').isdigit() else 0,
                            'source': '新浪财经'
                        })
                except Exception as e:
                    logger.debug(f"⚠️ 解析热门股票数据失败: {str(e)}")
                    continue
            
            logger.info(f"✅ 获取到 {len(hot_stocks)} 只热门股票")
            return hot_stocks
            
        except Exception as e:
            logger.error(f"❌ 获取热门股票失败: 错误: {str(e)}")
            return []


# 全局实例
_sina_provider = None

def get_sina_provider() -> SinaFinanceProvider:
    """获取新浪财经数据提供器实例"""
    global _sina_provider
    if _sina_provider is None:
        _sina_provider = SinaFinanceProvider()
    return _sina_provider


# 便捷函数
def get_sina_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """获取股票基本信息"""
    return get_sina_provider().get_stock_info(symbol)

def get_sina_multiple_stocks(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """批量获取股票信息"""
    return get_sina_provider().get_multiple_stocks(symbols)

def get_sina_stock_news(symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
    """获取股票新闻"""
    return get_sina_provider().get_stock_news(symbol, limit)

def get_sina_market_overview() -> Dict[str, Any]:
    """获取市场总览"""
    return get_sina_provider().get_market_overview()

def get_sina_hot_stocks(limit: int = 50) -> List[Dict[str, Any]]:
    """获取热门股票"""
    return get_sina_provider().get_hot_stocks(limit)