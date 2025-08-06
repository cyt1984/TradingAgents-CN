#!/usr/bin/env python3
"""
东方财富数据源工具
提供东方财富API数据获取的统一接口，包括实时行情、新闻、研报等数据
"""

import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, List
import warnings
from datetime import datetime, timedelta
import time
import re

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')


class EastMoneyProvider:
    """东方财富数据提供器"""

    def __init__(self):
        """初始化东方财富提供器"""
        self.base_url = "https://push2.eastmoney.com"
        self.api_url = "https://datacenter-web.eastmoney.com/api"
        self.news_url = "https://np-anotice-stock.eastmoney.com"
        self.quote_url = "https://push2.eastmoney.com"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("✅ 东方财富数据提供器初始化成功")

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """发起HTTP请求"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # 处理JSONP响应
            text = response.text
            if text.startswith('jQuery') or text.startswith('callback'):
                # 提取JSON部分
                start = text.find('(') + 1
                end = text.rfind(')')
                text = text[start:end]
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            # 转换股票代码格式 (000001 -> 0.000001)
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    code = f"0.{symbol}"  # 深交所
                else:
                    code = f"1.{symbol}"  # 上交所
            else:
                code = symbol

            url = f"{self.quote_url}/api/qt/stock/get"
            params = {
                'secid': code,
                'fields': 'f57,f58,f107,f137,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184',
                'fltt': '2'
            }
            
            data = self._make_request(url, params)
            if not data or 'data' not in data:
                return None
            
            stock_data = data['data']
            if not stock_data:
                return None
            
            return {
                'symbol': symbol,
                'name': stock_data.get('f58', ''),
                'current_price': stock_data.get('f43', 0) / 100,  # 当前价格
                'change': stock_data.get('f169', 0) / 100,  # 涨跌额
                'change_pct': stock_data.get('f170', 0) / 100,  # 涨跌幅
                'volume': stock_data.get('f47', 0),  # 成交量
                'turnover': stock_data.get('f48', 0) / 100,  # 成交额
                'high': stock_data.get('f44', 0) / 100,  # 最高价
                'low': stock_data.get('f45', 0) / 100,  # 最低价
                'open': stock_data.get('f46', 0) / 100,  # 开盘价
                'prev_close': stock_data.get('f60', 0) / 100,  # 昨收价
                'market_cap': stock_data.get('f116', 0),  # 总市值
                'pe_ratio': stock_data.get('f114', 0) / 100,  # 市盈率
                'pb_ratio': stock_data.get('f167', 0) / 100,  # 市净率
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取股票信息失败: {symbol}, 错误: {str(e)}")
            return None

    def get_stock_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取股票相关新闻"""
        try:
            # 先获取股票代码对应的数字ID
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return []
            
            url = f"{self.news_url}/api/announce/search"
            params = {
                'client': 'web',
                'type': '1',
                'keyword': stock_info['name'],
                'pageSize': str(limit),
                'pageIndex': '1'
            }
            
            data = self._make_request(url, params)
            if not data or 'data' not in data:
                return []
            
            news_list = []
            for item in data['data'].get('list', []):
                news_item = {
                    'title': item.get('title', ''),
                    'content': item.get('content', ''),
                    'publish_time': item.get('publishTime', ''),
                    'source': '东方财富',
                    'url': item.get('url', ''),
                    'type': item.get('type', ''),
                    'symbol': symbol
                }
                news_list.append(news_item)
            
            logger.info(f"✅ 获取到 {len(news_list)} 条东方财富新闻: {symbol}")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取东方财富新闻失败: {symbol}, 错误: {str(e)}")
            return []

    def get_market_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取市场情绪数据（资金流向等）"""
        try:
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    code = f"0.{symbol}"
                else:
                    code = f"1.{symbol}"
            else:
                code = symbol

            url = f"{self.quote_url}/api/qt/stock/fflow"
            params = {
                'secid': code,
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65'
            }
            
            data = self._make_request(url, params)
            if not data or 'data' not in data:
                return None
            
            flow_data = data['data']
            if not flow_data:
                return None
            
            return {
                'symbol': symbol,
                'main_inflow': flow_data.get('f62', 0),  # 主力净流入
                'main_inflow_rate': flow_data.get('f64', 0),  # 主力净流入率
                'super_inflow': flow_data.get('f60', 0),  # 超大单净流入
                'large_inflow': flow_data.get('f61', 0),  # 大单净流入
                'medium_inflow': flow_data.get('f62', 0),  # 中单净流入
                'small_inflow': flow_data.get('f63', 0),  # 小单净流入
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取资金流向数据失败: {symbol}, 错误: {str(e)}")
            return None

    def get_research_reports(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取研究报告"""
        try:
            stock_info = self.get_stock_info(symbol)
            if not stock_info:
                return []
            
            url = f"{self.api_url}/data/v1/get"
            params = {
                'sortColumns': 'PUBLISH_DATE',
                'sortTypes': '-1',
                'pageSize': str(limit),
                'pageNumber': '1',
                'reportName': 'RPT_INDUSTRY_SURVEYDETAIL',
                'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,PUBLISH_DATE,RESEARCHER_NAME,TITLE,RATE_NAME,TARGET_PRICE',
                'filter': f"(SECURITY_CODE=\"{symbol}\")"
            }
            
            data = self._make_request(url, params)
            if not data or 'result' not in data:
                return []
            
            reports = []
            for item in data['result'].get('data', []):
                report = {
                    'title': item.get('TITLE', ''),
                    'researcher': item.get('RESEARCHER_NAME', ''),
                    'rating': item.get('RATE_NAME', ''),
                    'target_price': item.get('TARGET_PRICE', 0),
                    'publish_date': item.get('PUBLISH_DATE', ''),
                    'source': '东方财富研报',
                    'symbol': symbol
                }
                reports.append(report)
            
            logger.info(f"✅ 获取到 {len(reports)} 份研究报告: {symbol}")
            return reports
            
        except Exception as e:
            logger.error(f"❌ 获取研究报告失败: {symbol}, 错误: {str(e)}")
            return []

    def get_financial_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取财务数据"""
        try:
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    code = f"SZ{symbol}"
                else:
                    code = f"SH{symbol}"
            else:
                code = symbol

            url = f"{self.api_url}/data/v1/get"
            params = {
                'sortColumns': 'REPORT_DATE',
                'sortTypes': '-1',
                'pageSize': '4',  # 获取最近4个季度数据
                'pageNumber': '1',
                'reportName': 'RPT_DMSK_FN_BALANCE',
                'columns': 'SECUCODE,SECURITY_CODE,REPORT_DATE,TOTAL_ASSETS,TOTAL_LIABILITIES,TOTAL_EQUITY,REVENUE,NET_PROFIT',
                'filter': f"(SECUCODE=\"{code}\")"
            }
            
            data = self._make_request(url, params)
            if not data or 'result' not in data:
                return None
            
            financial_data = data['result'].get('data', [])
            if not financial_data:
                return None
            
            latest = financial_data[0]  # 最新一期数据
            
            return {
                'symbol': symbol,
                'report_date': latest.get('REPORT_DATE', ''),
                'total_assets': latest.get('TOTAL_ASSETS', 0),
                'total_liabilities': latest.get('TOTAL_LIABILITIES', 0),
                'total_equity': latest.get('TOTAL_EQUITY', 0),
                'revenue': latest.get('REVENUE', 0),
                'net_profit': latest.get('NET_PROFIT', 0),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取财务数据失败: {symbol}, 错误: {str(e)}")
            return None

    def get_top_stocks(self, market: str = 'sh', limit: int = 50) -> List[Dict[str, Any]]:
        """获取热门股票榜单"""
        try:
            # market: 'sh' 沪市, 'sz' 深市, 'all' 全部
            market_map = {
                'sh': '1',
                'sz': '0', 
                'all': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23'
            }
            
            url = f"{self.quote_url}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': str(limit),
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': market_map.get(market, market_map['all']),
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }
            
            data = self._make_request(url, params)
            if not data or 'data' not in data:
                return []
            
            stocks = []
            for item in data['data'].get('diff', []):
                stock = {
                    'symbol': item.get('f12', ''),
                    'name': item.get('f14', ''),
                    'current_price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                    'change': item.get('f4', 0),
                    'volume': item.get('f5', 0),
                    'turnover': item.get('f6', 0),
                    'amplitude': item.get('f7', 0),
                    'high': item.get('f15', 0),
                    'low': item.get('f16', 0),
                    'open': item.get('f17', 0),
                    'prev_close': item.get('f18', 0)
                }
                stocks.append(stock)
            
            logger.info(f"✅ 获取到 {len(stocks)} 只热门股票")
            return stocks
            
        except Exception as e:
            logger.error(f"❌ 获取热门股票失败: 错误: {str(e)}")
            return []


# 全局实例
_eastmoney_provider = None

def get_eastmoney_provider() -> EastMoneyProvider:
    """获取东方财富数据提供器实例"""
    global _eastmoney_provider
    if _eastmoney_provider is None:
        _eastmoney_provider = EastMoneyProvider()
    return _eastmoney_provider


# 便捷函数
def get_eastmoney_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """获取股票基本信息"""
    return get_eastmoney_provider().get_stock_info(symbol)

def get_eastmoney_news(symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
    """获取股票新闻"""
    return get_eastmoney_provider().get_stock_news(symbol, limit)

def get_eastmoney_sentiment(symbol: str) -> Optional[Dict[str, Any]]:
    """获取市场情绪数据"""
    return get_eastmoney_provider().get_market_sentiment(symbol)

def get_eastmoney_reports(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """获取研究报告"""
    return get_eastmoney_provider().get_research_reports(symbol, limit)

def get_eastmoney_financials(symbol: str) -> Optional[Dict[str, Any]]:
    """获取财务数据"""
    return get_eastmoney_provider().get_financial_data(symbol)