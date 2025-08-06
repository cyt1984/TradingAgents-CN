#!/usr/bin/env python3
"""
腾讯财经数据源工具
提供腾讯财经API数据获取的统一接口，包括实时行情、新闻、资讯等数据
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


class TencentFinanceProvider:
    """腾讯财经数据提供器"""

    def __init__(self):
        """初始化腾讯财经提供器"""
        self.base_url = "https://qt.gtimg.cn"
        self.news_url = "https://finance.qq.com"
        self.api_url = "https://web.ifzq.gtimg.cn"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.qq.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("腾讯财经数据提供器初始化成功")

    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[str]:
        """发起HTTP请求，返回原始文本"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None

    def _parse_stock_data(self, raw_data: str) -> Optional[Dict]:
        """解析股票数据字符串"""
        try:
            # 腾讯股票API返回格式: v_sh000001="51~平安银行~000001~..."
            if not raw_data or '=' not in raw_data:
                return None
            
            # 提取数据部分
            data_part = raw_data.split('=')[1].strip()
            if data_part.startswith('"') and data_part.endswith('"'):
                data_part = data_part[1:-1]
            
            # 按~分割数据字段
            fields = data_part.split('~')
            if len(fields) < 30:
                return None
            
            return {
                'code': fields[2],           # 股票代码
                'name': fields[1],           # 股票名称
                'current_price': float(fields[3]) if fields[3] else 0,    # 当前价格
                'prev_close': float(fields[4]) if fields[4] else 0,       # 昨收价
                'open': float(fields[5]) if fields[5] else 0,             # 开盘价
                'volume': int(fields[6]) if fields[6] else 0,             # 成交量(手)
                'bid_volume': int(fields[7]) if fields[7] else 0,         # 外盘
                'ask_volume': int(fields[8]) if fields[8] else 0,         # 内盘
                'bid1': float(fields[9]) if fields[9] else 0,             # 买一价
                'bid1_volume': int(fields[10]) if fields[10] else 0,      # 买一量
                'bid2': float(fields[11]) if fields[11] else 0,           # 买二价
                'bid2_volume': int(fields[12]) if fields[12] else 0,      # 买二量
                'ask1': float(fields[19]) if fields[19] else 0,           # 卖一价
                'ask1_volume': int(fields[20]) if fields[20] else 0,      # 卖一量
                'ask2': float(fields[21]) if fields[21] else 0,           # 卖二价
                'ask2_volume': int(fields[22]) if fields[22] else 0,      # 卖二量
                'turnover': float(fields[37]) if len(fields) > 37 and fields[37] else 0,  # 成交额
                'high': float(fields[33]) if len(fields) > 33 and fields[33] else 0,      # 最高价
                'low': float(fields[34]) if len(fields) > 34 and fields[34] else 0,       # 最低价
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ 解析股票数据失败: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            # 构造腾讯股票代码格式
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    tencent_code = f"sz{symbol}"  # 深交所
                else:
                    tencent_code = f"sh{symbol}"  # 上交所
            else:
                tencent_code = symbol.lower()

            url = f"{self.base_url}/q={tencent_code}"
            
            raw_data = self._make_request(url)
            if not raw_data:
                return None
            
            stock_data = self._parse_stock_data(raw_data)
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
                'volume': stock_data['volume'] * 100,  # 转换为股数
                'turnover': stock_data['turnover'],
                'change': change,
                'change_pct': change_pct,
                'bid1': stock_data['bid1'],
                'ask1': stock_data['ask1'],
                'timestamp': stock_data['timestamp'],
                'source': '腾讯财经'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取腾讯股票信息失败: {symbol}, 错误: {str(e)}")
            return None

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量获取多只股票信息"""
        try:
            # 构造批量查询代码
            tencent_codes = []
            for symbol in symbols:
                if len(symbol) == 6 and symbol.isdigit():
                    if symbol.startswith(('00', '30')):
                        tencent_codes.append(f"sz{symbol}")
                    else:
                        tencent_codes.append(f"sh{symbol}")
                else:
                    tencent_codes.append(symbol.lower())
            
            # 腾讯API支持批量查询，用逗号分隔
            code_str = ','.join(tencent_codes)
            url = f"{self.base_url}/q={code_str}"
            
            raw_data = self._make_request(url)
            if not raw_data:
                return {}
            
            results = {}
            # 按行分割处理每只股票的数据
            lines = raw_data.strip().split('\\n')
            
            for i, line in enumerate(lines):
                if i < len(symbols) and line.strip():
                    stock_data = self._parse_stock_data(line)
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
                            'volume': stock_data['volume'] * 100,
                            'turnover': stock_data['turnover'],
                            'timestamp': stock_data['timestamp'],
                            'source': '腾讯财经'
                        }
            
            logger.info(f"✅ 腾讯财经批量获取到 {len(results)} 只股票信息")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量获取股票信息失败: 错误: {str(e)}")
            return {}

    def get_stock_kline(self, symbol: str, period: str = 'day', count: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据 - 使用腾讯财经API"""
        try:
            # 构造腾讯股票代码格式
            if len(symbol) == 6 and symbol.isdigit():
                if symbol.startswith(('00', '30')):
                    tencent_code = f"sz{symbol}"
                else:
                    tencent_code = f"sh{symbol}"
            else:
                tencent_code = symbol.lower()

            # 使用更简单的腾讯K线API
            url = f"{self.api_url}/appstock/app/kline/kline"
            params = {
                'param': f'{tencent_code},day,,{count},qfq',
                '_var': 'kline_day',
                'r': str(int(time.time() * 1000))
            }
            
            raw_data = self._make_request(url, params)
            if not raw_data:
                return None
            
            # 解析JSONP
            try:
                start_idx = raw_data.find('{')
                if start_idx == -1:
                    return None
                    
                json_str = raw_data[start_idx:].split('\n')[0]  # 清理多余字符
                data = json.loads(json_str)
                
                if 'data' not in data or tencent_code not in data['data']:
                    return None
                
                day_data = data['data'][tencent_code].get('day', [])
                if not day_data:
                    return None
                
                # 转换为DataFrame
                df_data = []
                for item in day_data:
                    if isinstance(item, list) and len(item) >= 6:
                        try:
                            df_data.append({
                                'date': str(item[0]),
                                'open': float(item[1]),
                                'close': float(item[2]),
                                'high': float(item[3]),
                                'low': float(item[4]),
                                'volume': int(item[5])
                            })
                        except (ValueError, IndexError):
                            continue
                
                if not df_data:
                    return None
                
                df = pd.DataFrame(df_data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()
                
                logger.info(f"Retrieved {len(df)} K-line records for {symbol}")
                return df
                
            except Exception as e:
                logger.error(f"Parse K-line data failed: {symbol}, {e}")
                return None
            
        except Exception as e:
            logger.error(f"Get K-line data failed: {symbol}, {e}")
            return None

    def get_market_index(self, index_code: str = 'sh000001') -> Optional[Dict[str, Any]]:
        """获取市场指数信息"""
        try:
            # 指数代码映射
            index_map = {
                'sh000001': 'sh000001',  # 上证指数
                'sz399001': 'sz399001',  # 深证成指
                'sz399006': 'sz399006',  # 创业板指
                'sh000300': 'sh000300',  # 沪深300
            }
            
            code = index_map.get(index_code, index_code)
            return self.get_stock_info(code)
            
        except Exception as e:
            logger.error(f"❌ 获取市场指数失败: {index_code}, 错误: {str(e)}")
            return None

    def get_sector_info(self, sector_type: str = 'industry') -> List[Dict[str, Any]]:
        """获取板块信息"""
        try:
            # 腾讯板块数据相对复杂，这里提供基础实现
            # 可以根据需要扩展具体的板块分类
            
            url = f"{self.base_url}/q=s_sh000001,s_sz399001,s_sz399006"  # 主要指数
            raw_data = self._make_request(url)
            
            if not raw_data:
                return []
            
            # 这里简化处理，实际可以扩展为完整的板块数据
            sectors = [
                {'name': '上证指数', 'code': 'sh000001', 'type': 'index'},
                {'name': '深证成指', 'code': 'sz399001', 'type': 'index'},
                {'name': '创业板指', 'code': 'sz399006', 'type': 'index'}
            ]
            
            return sectors
            
        except Exception as e:
            logger.error(f"❌ 获取板块信息失败: 错误: {str(e)}")
            return []


# 全局实例
_tencent_provider = None

def get_tencent_provider() -> TencentFinanceProvider:
    """获取腾讯财经数据提供器实例"""
    global _tencent_provider
    if _tencent_provider is None:
        _tencent_provider = TencentFinanceProvider()
    return _tencent_provider


# 便捷函数
def get_tencent_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """获取股票基本信息"""
    return get_tencent_provider().get_stock_info(symbol)

def get_tencent_multiple_stocks(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """批量获取股票信息"""
    return get_tencent_provider().get_multiple_stocks(symbols)

def get_tencent_kline(symbol: str, period: str = 'day', count: int = 100) -> Optional[pd.DataFrame]:
    """获取K线数据"""
    return get_tencent_provider().get_stock_kline(symbol, period, count)

def get_tencent_market_index(index_code: str = 'sh000001') -> Optional[Dict[str, Any]]:
    """获取市场指数"""
    return get_tencent_provider().get_market_index(index_code)