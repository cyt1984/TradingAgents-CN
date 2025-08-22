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
import concurrent.futures

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

    def get_multiple_stocks(self, symbols: List[str], batch_size: int = 100, max_workers: int = 25) -> Dict[str, Dict[str, Any]]:
        """批量获取多只股票信息（支持大批量并发处理）"""
        try:
            if not symbols:
                return {}
                
            # 小批量使用新浪原生批量API
            if len(symbols) <= batch_size:
                return self._get_batch_via_api(symbols)
            
            # 大批量使用并发处理
            logger.info(f"🚀 新浪财经大批量处理: {len(symbols)} 只股票，使用 {max_workers} 并发")
            
            all_results = {}
            total_processed = 0
            total_failed = 0
            
            # 分批处理
            def process_batch(batch_symbols):
                """处理单个批次"""
                try:
                    time.sleep(0.03)  # 更小的延迟，新浪可以处理更快的请求
                    return self._get_batch_via_api(batch_symbols)
                except Exception as e:
                    logger.error(f"❌ 新浪财经批次处理失败: {str(e)}")
                    return {}
            
            # 创建批次
            batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
            
            # 并发处理批次
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {executor.submit(process_batch, batch): batch for batch in batches}
                
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        all_results.update(batch_results)
                        total_processed += len(batch_results)
                        
                        # 进度报告
                        current_total = total_processed + total_failed
                        if current_total % 300 == 0 or current_total >= len(symbols):
                            progress = current_total / len(symbols) * 100
                            logger.info(f"📈 新浪财经进度: {current_total}/{len(symbols)} ({progress:.1f}%) - 成功:{total_processed}")
                            
                    except Exception as e:
                        total_failed += len(batch)
                        logger.error(f"❌ 新浪财经批次结果处理失败: {str(e)}")
            
            success_rate = total_processed / len(symbols) * 100 if len(symbols) > 0 else 0
            logger.info(f"✅ 新浪财经批量完成: 总数:{len(symbols)} 成功:{total_processed} 失败:{total_failed} 成功率:{success_rate:.1f}%")
            
            return all_results
            
        except Exception as e:
            logger.error(f"❌ 新浪财经批量获取失败: {str(e)}")
            return {}
    
    def _get_batch_via_api(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """使用新浪原生API批量获取股票信息"""
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
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 新浪API批量获取失败: {str(e)}")
            return {}

    def get_stock_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取股票相关新闻（增强版）"""
        try:
            # 使用多种方式获取新闻
            all_news = []
            
            # 方法1: 通过API获取最新财经新闻
            api_news = self._get_news_from_api(symbol, limit // 2)
            all_news.extend(api_news)
            
            # 方法2: 通过爬取获取股票专栏新闻  
            web_news = self._get_news_from_web(symbol, limit // 2)
            all_news.extend(web_news)
            
            # 去重和排序
            unique_news = self._deduplicate_news(all_news)
            unique_news.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
            
            logger.info(f"✅ 获取到 {len(unique_news)} 条新浪财经新闻: {symbol}")
            return unique_news[:limit]
            
        except Exception as e:
            logger.error(f"❌ 获取新浪财经新闻失败: {symbol}, 错误: {str(e)}")
            return []

    def _get_news_from_api(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """通过API获取财经新闻"""
        try:
            # 获取股票信息
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return []
            
            stock_name = stock_info['name']
            
            # 新浪财经新闻API
            api_url = f"{self.api_url}/api/openapi.php/NewsService.getNewsByKeywords"
            params = {
                'keywords': f"{stock_name},股票,{symbol}",
                'category': 'finance',
                'count': limit,
                'format': 'json'
            }
            
            response = self.session.get(api_url, params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            try:
                data = response.json()
                if not data or 'result' not in data:
                    return []
                
                news_list = []
                for item in data['result'].get('data', []):
                    news_item = {
                        'title': item.get('title', ''),
                        'summary': item.get('intro', ''),
                        'url': item.get('url', ''),
                        'publish_time': item.get('ctime', ''),
                        'source': item.get('media_name', '新浪财经'),
                        'symbol': symbol,
                        'relevance_score': self._calculate_relevance(item.get('title', ''), stock_name),
                        'news_type': 'api'
                    }
                    
                    if news_item['relevance_score'] > 0.3:  # 相关性过滤
                        news_list.append(news_item)
                
                return news_list
                
            except json.JSONDecodeError:
                logger.debug("API响应不是有效JSON")
                return []
                
        except Exception as e:
            logger.debug(f"⚠️ API获取新闻失败: {str(e)}")
            return []

    def _get_news_from_web(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """通过网页爬取获取新闻"""
        try:
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return []
            
            stock_name = stock_info['name']
            
            # 新浪财经股票专栏页面
            stock_url = f"{self.news_url}/stock/s/{symbol}.shtml"
            response = self.session.get(stock_url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            
            # 查找新闻列表
            news_containers = [
                soup.find_all('div', class_='news-list'),
                soup.find_all('ul', class_='news-list'),
                soup.find_all('div', class_='news-item-list')
            ]
            
            count = 0
            for container_list in news_containers:
                for container in container_list:
                    if count >= limit:
                        break
                    
                    items = container.find_all(['li', 'div'], class_=['news-item', 'item'])
                    
                    for item in items:
                        if count >= limit:
                            break
                        
                        try:
                            # 提取标题和链接
                            title_elem = item.find('a') or item.find('h3') or item.find('h4')
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get('href', '')
                            
                            # 提取时间
                            time_elem = item.find('span', class_=['time', 'date']) or item.find('time')
                            publish_time = time_elem.get_text(strip=True) if time_elem else ''
                            
                            # 提取摘要
                            summary_elem = item.find('p') or item.find('div', class_='summary')
                            summary = summary_elem.get_text(strip=True) if summary_elem else ''
                            
                            # 确保链接完整
                            if url and not url.startswith('http'):
                                url = f"https://finance.sina.com.cn{url}"
                            
                            # 计算相关性
                            relevance = self._calculate_relevance(title, stock_name)
                            
                            if title and relevance > 0.3:
                                news_item = {
                                    'title': title,
                                    'summary': summary,
                                    'url': url,
                                    'publish_time': publish_time,
                                    'source': '新浪财经',
                                    'symbol': symbol,
                                    'relevance_score': relevance,
                                    'news_type': 'web'
                                }
                                news_list.append(news_item)
                                count += 1
                        
                        except Exception as e:
                            logger.debug(f"⚠️ 解析单条新闻失败: {str(e)}")
                            continue
                
                if count >= limit:
                    break
            
            return news_list
            
        except Exception as e:
            logger.debug(f"⚠️ 网页爬取新闻失败: {str(e)}")
            return []

    def _calculate_relevance(self, title: str, stock_name: str) -> float:
        """计算新闻与股票的相关性评分"""
        try:
            if not title or not stock_name:
                return 0.0
            
            title_lower = title.lower()
            stock_name_lower = stock_name.lower()
            
            score = 0.0
            
            # 直接包含股票名称
            if stock_name_lower in title_lower:
                score += 0.8
            
            # 包含股票相关关键词
            stock_keywords = ['股票', '股价', '涨停', '跌停', '涨幅', '跌幅', '买入', '卖出', '持股', '股东']
            for keyword in stock_keywords:
                if keyword in title_lower:
                    score += 0.1
            
            # 包含财经关键词
            finance_keywords = ['财报', '业绩', '营收', '利润', '分红', '重组', '并购', '投资']
            for keyword in finance_keywords:
                if keyword in title_lower:
                    score += 0.15
            
            return min(1.0, score)
            
        except Exception:
            return 0.5  # 默认中等相关性

    def _deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """新闻去重"""
        try:
            seen_titles = set()
            unique_news = []
            
            for news in news_list:
                title = news.get('title', '')
                # 使用标题的前50个字符作为去重依据
                title_key = title[:50] if len(title) > 50 else title
                
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_news.append(news)
            
            return unique_news
            
        except Exception as e:
            logger.error(f"❌ 新闻去重失败: {str(e)}")
            return news_list

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

    def get_deep_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取深度行情数据"""
        try:
            deep_data = {
                'symbol': symbol,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'basic_info': {},
                'depth_quotes': {},
                'technical_indicators': {},
                'market_metrics': {}
            }
            
            # 获取基础信息
            basic_info = self.get_stock_info(symbol)
            if basic_info:
                deep_data['basic_info'] = basic_info
            
            # 获取深度报价（五档行情）
            depth_quotes = self._get_depth_quotes(symbol)
            if depth_quotes:
                deep_data['depth_quotes'] = depth_quotes
            
            # 获取技术指标
            tech_indicators = self._get_technical_indicators(symbol)
            if tech_indicators:
                deep_data['technical_indicators'] = tech_indicators
            
            # 获取市场指标
            market_metrics = self._get_market_metrics(symbol)
            if market_metrics:
                deep_data['market_metrics'] = market_metrics
            
            logger.info(f"✅ 获取深度行情数据: {symbol}")
            return deep_data
            
        except Exception as e:
            logger.error(f"❌ 获取深度行情数据失败: {symbol}, 错误: {str(e)}")
            return {}

    def _get_depth_quotes(self, symbol: str) -> Dict[str, Any]:
        """获取深度报价数据（五档买卖盘）"""
        try:
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return {}
            
            return {
                'buy_orders': [
                    {'level': 1, 'price': stock_info.get('bid1', 0), 'volume': stock_info.get('bid1_volume', 0)},
                    {'level': 2, 'price': stock_info.get('bid2_price', 0), 'volume': stock_info.get('bid2_volume', 0)},
                    {'level': 3, 'price': stock_info.get('bid3_price', 0), 'volume': stock_info.get('bid3_volume', 0)},
                    {'level': 4, 'price': stock_info.get('bid4_price', 0), 'volume': stock_info.get('bid4_volume', 0)},
                    {'level': 5, 'price': stock_info.get('bid5_price', 0), 'volume': stock_info.get('bid5_volume', 0)}
                ],
                'sell_orders': [
                    {'level': 1, 'price': stock_info.get('ask1', 0), 'volume': stock_info.get('ask1_volume', 0)},
                    {'level': 2, 'price': stock_info.get('ask2_price', 0), 'volume': stock_info.get('ask2_volume', 0)},
                    {'level': 3, 'price': 0, 'volume': 0},  # 新浪数据有限
                    {'level': 4, 'price': 0, 'volume': 0},
                    {'level': 5, 'price': 0, 'volume': 0}
                ],
                'spread': stock_info.get('ask1', 0) - stock_info.get('bid1', 0),
                'total_buy_volume': sum([stock_info.get(f'bid{i}_volume', 0) for i in range(1, 6)]),
                'total_sell_volume': stock_info.get('ask1_volume', 0) + stock_info.get('ask2_volume', 0)
            }
            
        except Exception as e:
            logger.debug(f"⚠️ 获取深度报价失败: {str(e)}")
            return {}

    def _get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """获取技术指标数据"""
        try:
            # 构造新浪技术指标API URL
            if len(symbol) == 6 and symbol.isdigit():
                sina_code = f"sh{symbol}" if symbol.startswith(('6', '9')) else f"sz{symbol}"
            else:
                sina_code = symbol.lower()
            
            # 尝试获取技术指标数据（新浪可能不提供API）
            indicators = {
                'ma5': 0,      # 5日均线
                'ma10': 0,     # 10日均线
                'ma20': 0,     # 20日均线
                'rsi': 0,      # RSI指标
                'macd': 0,     # MACD指标
                'volume_ratio': 0,  # 量比
                'turnover_rate': 0   # 换手率
            }
            
            # 基于当前价格估算一些基础指标
            stock_info = self.get_stock_info(symbol)
            if stock_info:
                current_price = stock_info.get('current_price', 0)
                volume = stock_info.get('volume', 0)
                turnover = stock_info.get('turnover', 0)
                
                # 简单估算换手率（需要流通股本数据，这里用估值）
                if turnover > 0 and current_price > 0:
                    estimated_shares = turnover / current_price
                    indicators['turnover_rate'] = (volume / estimated_shares) * 100 if estimated_shares > 0 else 0
                
                # 量比估算（当日成交量/最近平均成交量，这里简化处理）
                indicators['volume_ratio'] = 1.0  # 默认值
            
            return indicators
            
        except Exception as e:
            logger.debug(f"⚠️ 获取技术指标失败: {str(e)}")
            return {}

    def _get_market_metrics(self, symbol: str) -> Dict[str, Any]:
        """获取市场指标"""
        try:
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return {}
            
            current_price = stock_info.get('current_price', 0)
            high = stock_info.get('high', 0)
            low = stock_info.get('low', 0)
            volume = stock_info.get('volume', 0)
            turnover = stock_info.get('turnover', 0)
            
            metrics = {
                'amplitude': ((high - low) / current_price * 100) if current_price > 0 else 0,  # 振幅
                'volume_weighted_price': (turnover / volume) if volume > 0 else current_price,    # 成交量加权平均价
                'relative_position': ((current_price - low) / (high - low)) if (high - low) > 0 else 0.5,  # 相对位置
                'market_cap_estimate': 0,  # 市值估算（需要股本数据）
                'liquidity_score': min(10, volume / 1000000),  # 流动性评分（简化）
                'volatility_score': min(10, ((high - low) / current_price * 100)) if current_price > 0 else 0  # 波动率评分
            }
            
            return metrics
            
        except Exception as e:
            logger.debug(f"⚠️ 获取市场指标失败: {str(e)}")
            return {}

    def get_historical_data(self, symbol: str, period: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史行情数据"""
        try:
            # 构造历史数据URL（新浪财经历史数据API）
            if len(symbol) == 6 and symbol.isdigit():
                sina_code = f"sh{symbol}" if symbol.startswith(('6', '9')) else f"sz{symbol}"
            else:
                sina_code = symbol.lower()
            
            # 新浪历史数据API（可能需要调整）
            api_url = f"{self.api_url}/api/jsonp.php/IO.XSRV2.CallbackList['hqChart']/JS.ChartData.getData"
            
            # 时间段参数
            period_map = {
                '1d': 'd',
                '1w': 'w', 
                '1m': 'm'
            }
            
            params = {
                'symbol': sina_code,
                'type': period_map.get(period, 'd'),
                'count': limit
            }
            
            response = self.session.get(api_url, params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            # 解析JSONP响应
            response_text = response.text
            if 'hqChart' in response_text:
                # 提取JSON数据（去除JSONP包装）
                start_index = response_text.find('(') + 1
                end_index = response_text.rfind(')')
                json_data = response_text[start_index:end_index]
                
                try:
                    data = json.loads(json_data)
                    historical_data = []
                    
                    for item in data:
                        if isinstance(item, list) and len(item) >= 6:
                            historical_data.append({
                                'date': item[0],
                                'open': float(item[1]),
                                'high': float(item[2]),
                                'low': float(item[3]),
                                'close': float(item[4]),
                                'volume': int(item[5]) if len(item) > 5 else 0,
                                'symbol': symbol
                            })
                    
                    logger.info(f"✅ 获取历史数据 {len(historical_data)} 条: {symbol}")
                    return historical_data
                    
                except json.JSONDecodeError:
                    logger.debug("历史数据JSON解析失败")
                    return []
            
            return []
            
        except Exception as e:
            logger.error(f"❌ 获取历史数据失败: {symbol}, 错误: {str(e)}")
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

def get_sina_deep_market_data(symbol: str) -> Dict[str, Any]:
    """获取深度行情数据"""
    return get_sina_provider().get_deep_market_data(symbol)

def get_sina_historical_data(symbol: str, period: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
    """获取历史行情数据"""
    return get_sina_provider().get_historical_data(symbol, period, limit)