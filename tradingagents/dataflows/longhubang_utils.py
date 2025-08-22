#!/usr/bin/env python3
"""
龙虎榜数据获取引擎
提供龙虎榜数据获取、席位信息解析等功能
支持多维度龙虎榜查询和详细席位分析
"""

import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import time
import re
from dataclasses import dataclass, field
from enum import Enum

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('longhubang')


class RankingType(Enum):
    """龙虎榜类型枚举"""
    DAILY = "daily"                    # 日榜
    LIMIT_UP = "limit_up"             # 涨停板
    LIMIT_DOWN = "limit_down"         # 跌停板
    TURNOVER = "turnover"             # 成交额榜
    AMPLITUDE = "amplitude"           # 振幅榜
    VOLUME = "volume"                 # 成交量榜
    TURNOVER_RATE = "turnover_rate"   # 换手率榜


@dataclass
class SeatInfo:
    """席位信息"""
    seat_name: str                    # 席位名称
    buy_amount: float = 0.0          # 买入金额(万元)
    sell_amount: float = 0.0         # 卖出金额(万元)
    net_amount: float = 0.0          # 净买入金额(万元)
    seat_type: str = "unknown"       # 席位类型
    influence_score: float = 0.0     # 影响力评分


@dataclass
class LongHuBangData:
    """龙虎榜数据"""
    symbol: str                       # 股票代码
    name: str                        # 股票名称
    current_price: float             # 当前价格
    change_pct: float                # 涨跌幅(%)
    turnover: float                  # 成交额(万元)
    turnover_rate: float             # 换手率(%)
    net_inflow: float                # 净流入(万元)
    buy_seats: List[SeatInfo] = field(default_factory=list)    # 买方席位
    sell_seats: List[SeatInfo] = field(default_factory=list)   # 卖方席位
    ranking_reason: str = ""         # 上榜原因
    date: str = ""                   # 日期
    
    def get_total_buy_amount(self) -> float:
        """获取总买入金额"""
        return sum(seat.buy_amount for seat in self.buy_seats)
    
    def get_total_sell_amount(self) -> float:
        """获取总卖出金额"""
        return sum(seat.sell_amount for seat in self.sell_seats)
    
    def get_net_flow(self) -> float:
        """获取净流入"""
        return self.get_total_buy_amount() - self.get_total_sell_amount()


class LongHuBangProvider:
    """龙虎榜数据提供器"""
    
    def __init__(self):
        """初始化龙虎榜提供器"""
        self.base_url = "https://datacenter-web.eastmoney.com/api"
        self.quote_url = "https://push2.eastmoney.com"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://data.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 缓存设置
        self._cache = {}
        self._cache_ttl = 3600  # 1小时缓存
        
        logger.info("✅ 龙虎榜数据提供器初始化成功")
    
    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """发起HTTP请求"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # 处理JSONP响应
            text = response.text
            if text.startswith('(') and text.endswith(')'):
                text = text[1:-1]
            elif '(' in text and ')' in text:
                start = text.find('(') + 1
                end = text.rfind(')')
                text = text[start:end]
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"❌ 请求失败: {url}, 错误: {str(e)}")
            return None
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method] + [f"{k}_{v}" for k, v in sorted(kwargs.items())]
        return "_".join(key_parts)
    
    def _check_cache(self, cache_key: str) -> Optional[Any]:
        """检查缓存"""
        if cache_key in self._cache:
            cache_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cache_data
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        self._cache[cache_key] = (data, time.time())
    
    def _get_latest_trading_date(self) -> str:
        """获取最近的交易日期"""
        now = datetime.now()
        
        # 从今天开始往前找交易日
        for days_back in range(10):  # 最多往前找10天
            check_date = (now - timedelta(days=days_back))
            
            # 跳过周末
            if check_date.weekday() >= 5:  # 周六(5)或周日(6)
                continue
                
            date_str = check_date.strftime('%Y-%m-%d')
            
            # 快速检查这一天是否有数据
            if self._check_date_has_data(date_str):
                logger.info(f"🗓️ 找到最近交易日: {date_str}")
                return date_str
        
        # 如果都没找到，返回最近的工作日
        for days_back in range(10):
            check_date = (now - timedelta(days=days_back))
            if check_date.weekday() < 5:  # 工作日
                date_str = check_date.strftime('%Y-%m-%d')
                logger.warning(f"⚠️ 未找到有数据的交易日，使用最近工作日: {date_str}")
                return date_str
        
        # 最后的fallback
        return now.strftime('%Y-%m-%d')
    
    def _check_date_has_data(self, date_str: str) -> bool:
        """检查指定日期是否有龙虎榜数据"""
        try:
            # 使用基础参数快速检查
            url = f"{self.base_url}/data/v1/get"
            params = {
                'sortColumns': 'SECURITY_CODE',
                'sortTypes': '1',
                'pageSize': '1',  # 只取1条记录
                'pageNumber': '1',
                'reportName': 'RPT_DAILYBILLBOARD_DETAILS',
                'columns': 'SECURITY_CODE',
                'filter': f'(TRADE_DATE=\'{date_str}\')'
            }
            
            data = self._make_request(url, params, timeout=5)
            if data and data.get('success') and data.get('result') and data['result'].get('data'):
                return len(data['result']['data']) > 0
                
        except Exception:
            pass
        
        return False
    
    def get_daily_ranking(self, date: str = None, ranking_type: RankingType = RankingType.DAILY) -> List[LongHuBangData]:
        """
        获取指定日期的龙虎榜数据
        
        Args:
            date: 日期，格式YYYY-MM-DD，默认为今天
            ranking_type: 龙虎榜类型
            
        Returns:
            龙虎榜数据列表
        """
        if date is None:
            # 智能获取最近交易日
            date = self._get_latest_trading_date()
        
        cache_key = self._get_cache_key("daily_ranking", date=date, type=ranking_type.value)
        cached_data = self._check_cache(cache_key)
        if cached_data:
            logger.info(f"📋 使用缓存的龙虎榜数据: {date}")
            return cached_data
        
        try:
            # 检查是否为交易日（简单检查周末）
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            if date_obj.weekday() >= 5:  # 周六(5)或周日(6)
                logger.warning(f"⚠️ {date} 为周末，可能无龙虎榜数据")
            
            # 东方财富龙虎榜API
            url = f"{self.base_url}/data/v1/get"
            
            # 根据类型设置不同的参数
            if ranking_type == RankingType.DAILY:
                params = {
                    'sortColumns': 'SECURITY_CODE',
                    'sortTypes': '1',
                    'pageSize': '200',
                    'pageNumber': '1',
                    'reportName': 'RPT_DAILYBILLBOARD_DETAILS',
                    'columns': 'SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,CLOSE_PRICE,CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_DEAL_AMT,TURNOVERRATE',
                    'filter': f'(TRADE_DATE=\'{date}\')'
                }
            elif ranking_type == RankingType.LIMIT_UP:
                params = {
                    'sortColumns': 'SECURITY_CODE',
                    'sortTypes': '1', 
                    'pageSize': '200',
                    'pageNumber': '1',
                    'reportName': 'RPT_DAILYBILLBOARD_DETAILS',
                    'columns': 'SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,CLOSE_PRICE,CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_DEAL_AMT,TURNOVERRATE',
                    'filter': f'(TRADE_DATE=\'{date}\')(CHANGE_RATE>=9.5)'
                }
            else:
                # 其他类型使用默认参数
                params = {
                    'sortColumns': 'SECURITY_CODE',
                    'sortTypes': '1',
                    'pageSize': '200',
                    'pageNumber': '1',
                    'reportName': 'RPT_DAILYBILLBOARD_DETAILS',
                    'columns': 'SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,CLOSE_PRICE,CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_DEAL_AMT,TURNOVERRATE',
                    'filter': f'(TRADE_DATE=\'{date}\')'
                }
            
            data = self._make_request(url, params)
            if not data or 'result' not in data or data['result'] is None or 'data' not in data['result'] or data['result']['data'] is None:
                logger.warning(f"⚠️ 未获取到龙虎榜数据: {date}")
                
                # 如果是今天且没有数据，尝试获取最近一个交易日的数据
                if date == datetime.now().strftime('%Y-%m-%d'):
                    logger.info("🔄 尝试获取最近交易日的龙虎榜数据...")
                    for i in range(1, 8):  # 尝试过去一周
                        prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                        prev_cache_key = self._get_cache_key("daily_ranking", date=prev_date, type=ranking_type.value)
                        prev_cached_data = self._check_cache(prev_cache_key)
                        if prev_cached_data:
                            logger.info(f"📋 使用最近交易日缓存数据: {prev_date}")
                            return prev_cached_data
                        
                        # 尝试获取前一天的数据
                        prev_params = params.copy()
                        prev_params['filter'] = prev_params['filter'].replace(date, prev_date)
                        prev_data = self._make_request(url, prev_params)
                        if prev_data and 'result' in prev_data and prev_data['result'] is not None and 'data' in prev_data['result'] and prev_data['result']['data']:
                            logger.info(f"✅ 找到最近交易日数据: {prev_date}")
                            # 递归调用处理前一天的数据
                            return self.get_daily_ranking(prev_date, ranking_type)
                
                # 按照CLAUDE.md规范：无法获取真实数据时返回空结果，不使用演示数据
                logger.warning(f"⚠️ 无法获取{date}的真实龙虎榜数据，返回空结果")
                return []
            
            ranking_list = []
            for item in data['result']['data']:
                try:
                    # 解析基础数据
                    ranking_data = LongHuBangData(
                        symbol=item.get('SECURITY_CODE', ''),
                        name=item.get('SECURITY_NAME_ABBR', ''),
                        current_price=float(item.get('CLOSE_PRICE', 0)),
                        change_pct=float(item.get('CHANGE_RATE', 0)),
                        turnover=float(item.get('BILLBOARD_DEAL_AMT', 0)) / 10000,  # 转换为万元
                        turnover_rate=float(item.get('TURNOVERRATE', 0)),
                        net_inflow=float(item.get('BILLBOARD_NET_AMT', 0)) / 10000,  # 转换为万元
                        ranking_reason=item.get('REASON', ''),
                        date=date
                    )
                    
                    # 获取详细席位信息
                    seat_details = self.get_seat_details(ranking_data.symbol, date)
                    if seat_details:
                        ranking_data.buy_seats = seat_details['buy_seats']
                        ranking_data.sell_seats = seat_details['sell_seats']
                    
                    ranking_list.append(ranking_data)
                    
                except Exception as e:
                    logger.error(f"❌ 解析龙虎榜数据失败: {item}, 错误: {e}")
                    continue
            
            # 缓存结果
            self._set_cache(cache_key, ranking_list)
            
            logger.info(f"✅ 获取龙虎榜数据成功: {date}, 共{len(ranking_list)}只股票")
            return ranking_list
            
        except Exception as e:
            logger.error(f"❌ 获取龙虎榜数据失败: {date}, 错误: {e}")
            return []
    
    def get_seat_details(self, symbol: str, date: str = None) -> Optional[Dict[str, List[SeatInfo]]]:
        """
        获取股票的详细席位信息
        
        Args:
            symbol: 股票代码
            date: 日期，默认为今天
            
        Returns:
            包含买卖席位信息的字典
        """
        if date is None:
            # 智能获取最近交易日
            date = self._get_latest_trading_date()
        
        cache_key = self._get_cache_key("seat_details", symbol=symbol, date=date)
        cached_data = self._check_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # 席位详情功能暂时禁用，需要进一步调研API字段
            logger.debug(f"⚠️ 席位详情功能暂时禁用: {symbol} {date}")
            return None
            
            # TODO: 重新调研席位详情API的正确字段名称
            # 获取席位详细信息
            url = f"{self.base_url}/data/v1/get"
            params = {
                'sortColumns': 'OPERATEDEPT_CODE',
                'sortTypes': '1',
                'pageSize': '50',
                'pageNumber': '1',
                'reportName': 'RPT_BILLBOARD_DAILYDETAILS',
                'columns': 'SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,OPERATEDEPT_CODE,OPERATEDEPT_NAME,TRADE_DATE,SIDE_NAME,RANK,BUY,SELL,NET',
                'filter': f'(SECURITY_CODE=\"{symbol}\")(TRADE_DATE=\'{date}\')'
            }
            
            data = self._make_request(url, params)
            if not data or 'result' not in data or data['result'] is None or 'data' not in data['result'] or data['result']['data'] is None:
                logger.debug(f"⚠️ 未获取到席位详情: {symbol} {date}")
                return None
            
            buy_seats = []
            sell_seats = []
            
            for item in data['result']['data']:
                try:
                    seat_info = SeatInfo(
                        seat_name=item.get('OPERATEDEPT_NAME', ''),
                        buy_amount=float(item.get('BUY', 0)) / 10000,   # 转换为万元
                        sell_amount=float(item.get('SELL', 0)) / 10000, # 转换为万元
                        net_amount=float(item.get('NET', 0)) / 10000    # 转换为万元
                    )
                    
                    # 根据买卖方向分类
                    side = item.get('SIDE_NAME', '')
                    if side == '买方' or seat_info.buy_amount > 0:
                        buy_seats.append(seat_info)
                    elif side == '卖方' or seat_info.sell_amount > 0:
                        sell_seats.append(seat_info)
                    
                except Exception as e:
                    logger.error(f"❌ 解析席位信息失败: {item}, 错误: {e}")
                    continue
            
            result = {
                'buy_seats': buy_seats,
                'sell_seats': sell_seats
            }
            
            # 缓存结果
            self._set_cache(cache_key, result)
            
            logger.debug(f"✅ 获取席位详情成功: {symbol}, 买方{len(buy_seats)}席位, 卖方{len(sell_seats)}席位")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取席位详情失败: {symbol} {date}, 错误: {e}")
            return None
    
    def get_historical_rankings(self, days: int = 7) -> List[LongHuBangData]:
        """
        获取历史龙虎榜数据
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            历史龙虎榜数据列表
        """
        historical_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_data = self.get_daily_ranking(date)
            historical_data.extend(daily_data)
        
        logger.info(f"✅ 获取历史龙虎榜数据: 最近{days}天, 共{len(historical_data)}条记录")
        return historical_data
    
    def get_limit_up_stocks(self, date: str = None) -> List[LongHuBangData]:
        """
        获取涨停板股票
        
        Args:
            date: 日期，默认为今天
            
        Returns:
            涨停板龙虎榜数据
        """
        return self.get_daily_ranking(date, RankingType.LIMIT_UP)
    
    def get_stocks_by_change_pct(self, min_change_pct: float = 5.0, 
                                max_change_pct: float = 20.0,
                                date: str = None) -> List[LongHuBangData]:
        """
        根据涨跌幅筛选龙虎榜股票
        
        Args:
            min_change_pct: 最小涨跌幅
            max_change_pct: 最大涨跌幅
            date: 日期
            
        Returns:
            符合条件的龙虎榜数据
        """
        all_data = self.get_daily_ranking(date)
        filtered_data = [
            data for data in all_data 
            if min_change_pct <= data.change_pct <= max_change_pct
        ]
        
        logger.info(f"✅ 按涨跌幅筛选: {min_change_pct}%-{max_change_pct}%, 筛选出{len(filtered_data)}只股票")
        return filtered_data
    
    def get_stocks_by_turnover(self, min_turnover: float = 10000, date: str = None) -> List[LongHuBangData]:
        """
        根据成交额筛选龙虎榜股票
        
        Args:
            min_turnover: 最小成交额(万元)
            date: 日期
            
        Returns:
            符合条件的龙虎榜数据
        """
        all_data = self.get_daily_ranking(date)
        filtered_data = [
            data for data in all_data 
            if data.turnover >= min_turnover
        ]
        
        logger.info(f"✅ 按成交额筛选: >={min_turnover}万元, 筛选出{len(filtered_data)}只股票")
        return filtered_data
    
    def search_stocks_by_seat(self, seat_name: str, days: int = 7) -> List[LongHuBangData]:
        """
        搜索特定席位参与的股票
        
        Args:
            seat_name: 席位名称(支持模糊匹配)
            days: 搜索最近几天
            
        Returns:
            包含该席位的龙虎榜数据
        """
        historical_data = self.get_historical_rankings(days)
        matched_stocks = []
        
        for stock_data in historical_data:
            # 检查买方席位
            for seat in stock_data.buy_seats:
                if seat_name in seat.seat_name:
                    matched_stocks.append(stock_data)
                    break
            else:
                # 检查卖方席位
                for seat in stock_data.sell_seats:
                    if seat_name in seat.seat_name:
                        matched_stocks.append(stock_data)
                        break
        
        logger.info(f"✅ 席位搜索: {seat_name}, 最近{days}天找到{len(matched_stocks)}只相关股票")
        return matched_stocks
    
    def get_statistics(self, date: str = None) -> Dict[str, Any]:
        """
        获取龙虎榜统计信息
        
        Args:
            date: 日期
            
        Returns:
            统计信息字典
        """
        ranking_data = self.get_daily_ranking(date)
        if not ranking_data:
            return {}
        
        # 计算统计指标
        total_stocks = len(ranking_data)
        total_turnover = sum(data.turnover for data in ranking_data)
        avg_change_pct = sum(data.change_pct for data in ranking_data) / total_stocks
        
        # 涨跌分布
        up_stocks = len([data for data in ranking_data if data.change_pct > 0])
        down_stocks = total_stocks - up_stocks
        
        # 成交额分布
        large_turnover_stocks = len([data for data in ranking_data if data.turnover > 50000])  # 5亿以上
        
        statistics = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_stocks': total_stocks,
            'total_turnover': total_turnover,
            'avg_change_pct': avg_change_pct,
            'up_stocks': up_stocks,
            'down_stocks': down_stocks,
            'up_ratio': up_stocks / total_stocks if total_stocks > 0 else 0,
            'large_turnover_stocks': large_turnover_stocks,
            'large_turnover_ratio': large_turnover_stocks / total_stocks if total_stocks > 0 else 0
        }
        
        logger.info(f"✅ 龙虎榜统计: {date}, 共{total_stocks}只股票, 总成交额{total_turnover:.0f}万元")
        return statistics
    


# 全局实例
_longhubang_provider = None

def get_longhubang_provider() -> LongHuBangProvider:
    """获取龙虎榜提供器单例"""
    global _longhubang_provider
    if _longhubang_provider is None:
        _longhubang_provider = LongHuBangProvider()
    return _longhubang_provider


# 便捷函数
def get_today_longhubang(ranking_type: RankingType = RankingType.DAILY) -> List[LongHuBangData]:
    """获取今日龙虎榜"""
    provider = get_longhubang_provider()
    return provider.get_daily_ranking(ranking_type=ranking_type)


def get_longhubang_by_change(min_change: float = 5.0, max_change: float = 20.0) -> List[LongHuBangData]:
    """按涨跌幅获取龙虎榜"""
    provider = get_longhubang_provider()
    return provider.get_stocks_by_change_pct(min_change, max_change)


def search_seat_activity(seat_name: str, days: int = 7) -> List[LongHuBangData]:
    """搜索席位活动"""
    provider = get_longhubang_provider()
    return provider.search_stocks_by_seat(seat_name, days)


if __name__ == "__main__":
    # 测试代码
    provider = get_longhubang_provider()
    
    # 获取今日龙虎榜
    today_data = provider.get_daily_ranking()
    print(f"今日龙虎榜: {len(today_data)}只股票")
    
    # 获取涨停板
    limit_up_data = provider.get_limit_up_stocks()
    print(f"今日涨停板: {len(limit_up_data)}只股票")
    
    # 获取统计信息
    stats = provider.get_statistics()
    print(f"统计信息: {stats}")