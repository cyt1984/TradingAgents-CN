#!/usr/bin/env python3
"""
BaoStock数据源工具
提供BaoStock数据获取的统一接口，支持批量下载历史数据
BaoStock是完全免费的股票数据源，特别适合批量历史数据下载
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import warnings
from datetime import datetime, timedelta
import time
import concurrent.futures  # 添加并发支持

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('baostock')
warnings.filterwarnings('ignore')


class BaoStockProvider:
    """BaoStock数据提供器"""

    def __init__(self):
        """初始化BaoStock提供器"""
        try:
            import baostock as bs
            self.bs = bs
            self.connected = False
            self._login()
            logger.info(f"✅ BaoStock初始化成功，版本: {bs.__version__}")
        except ImportError:
            self.bs = None
            self.connected = False
            logger.error(f"❌ BaoStock未安装，请运行: pip install baostock")

    def _login(self):
        """登录BaoStock"""
        if not self.bs:
            return False
        
        try:
            # BaoStock登录
            lg = self.bs.login()
            if lg.error_code == '0':
                self.connected = True
                logger.info(f"🔐 BaoStock登录成功: {lg.error_msg}")
                return True
            else:
                self.connected = False
                logger.error(f"❌ BaoStock登录失败: {lg.error_msg}")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"❌ BaoStock登录异常: {e}")
            return False

    def _logout(self):
        """登出BaoStock"""
        if self.bs and self.connected:
            try:
                self.bs.logout()
                self.connected = False
                logger.info("🔓 BaoStock登出成功")
            except Exception as e:
                logger.warning(f"⚠️ BaoStock登出失败: {e}")

    def __del__(self):
        """析构函数，确保登出"""
        self._logout()

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码格式为BaoStock格式
        
        Args:
            symbol: 股票代码（如 000001 或 000001.SZ）
            
        Returns:
            BaoStock格式的股票代码（如 sz.000001）
        """
        if not symbol:
            return ""
        
        # 移除可能的后缀
        clean_symbol = symbol.replace('.SZ', '').replace('.SS', '').replace('.SH', '')
        
        # 确保是6位数字
        if len(clean_symbol) == 6 and clean_symbol.isdigit():
            # 根据代码判断交易所
            if clean_symbol.startswith(('000', '001', '002', '003', '300')):
                return f"sz.{clean_symbol}"  # 深圳
            elif clean_symbol.startswith(('600', '601', '603', '605', '688')):
                return f"sh.{clean_symbol}"  # 上海
            else:
                # 默认深圳
                return f"sz.{clean_symbol}"
        else:
            logger.warning(f"⚠️ 无效的股票代码格式: {symbol}")
            return symbol

    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """
        获取所有股票列表
        
        Returns:
            包含所有股票信息的DataFrame
        """
        if not self.connected:
            if not self._login():
                return None
        
        try:
            logger.info("🔍 开始获取股票列表...")
            
            # 尝试多个日期，从当前日期往前推
            for days_back in range(5):
                try_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                # 获取沪深A股列表
                rs = self.bs.query_all_stock(day=try_date)
                
                if rs.error_code != '0':
                    logger.warning(f"⚠️ 日期 {try_date} 查询失败: {rs.error_msg}")
                    continue
                
                stock_list = []
                while (rs.error_code == '0') & rs.next():
                    row_data = rs.get_row_data()
                    stock_list.append(row_data)
                
                if stock_list:
                    # 转换为DataFrame
                    columns = rs.fields  # 使用实际返回的字段名
                    df = pd.DataFrame(stock_list, columns=columns)
                    
                    # 过滤A股股票
                    a_stock_df = df[df['type'] == '1'].copy()  # type=1表示股票
                    
                    logger.info(f"✅ 获取股票列表成功，日期: {try_date}，共 {len(a_stock_df)} 只A股")
                    return a_stock_df
                else:
                    logger.warning(f"⚠️ 日期 {try_date} 未获取到数据")
            
            # 如果所有日期都失败，尝试使用沪深股票代码列表
            logger.info("🔄 尝试备用方法获取股票列表...")
            
            # 备用方法：使用预定义的股票代码范围
            stock_codes = []
            
            # 深圳股票代码范围
            for prefix in ['000', '001', '002', '003', '300']:
                for i in range(1000):
                    code = f"sz.{prefix}{i:03d}"
                    stock_codes.append([code, f"股票{prefix}{i:03d}", "", "", "1", "1"])
            
            # 上海股票代码范围  
            for prefix in ['600', '601', '603', '605', '688']:
                for i in range(1000):
                    code = f"sh.{prefix}{i:03d}"
                    stock_codes.append([code, f"股票{prefix}{i:03d}", "", "", "1", "1"])
            
            if stock_codes:
                columns = ['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status']
                df = pd.DataFrame(stock_codes, columns=columns)
                logger.info(f"✅ 使用备用方法生成股票列表，共 {len(df)} 个代码")
                return df
            
            logger.error("❌ 所有方法都无法获取股票列表")
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取股票列表失败: {e}")
            return None

    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None,
                      frequency: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: 数据频率 ("daily", "weekly", "monthly")
            
        Returns:
            股票历史数据DataFrame
        """
        if not self.connected:
            if not self._login():
                return None
        
        try:
            # 转换股票代码
            bs_symbol = self._convert_symbol(symbol)
            
            # 设置默认日期
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # 设置频率参数
            frequency_map = {
                "daily": "d",
                "weekly": "w", 
                "monthly": "m"
            }
            freq = frequency_map.get(frequency, "d")
            
            logger.info(f"📊 获取 {symbol} 历史数据: {start_date} 到 {end_date}")
            
            # 查询历史K线数据
            rs = self.bs.query_history_k_data_plus(
                bs_symbol,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start_date,
                end_date=end_date,
                frequency=freq,
                adjustflag="3"  # 不复权
            )
            
            # 获取数据
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"⚠️ {symbol} 无历史数据")
                return None
            
            # 转换为DataFrame
            columns = ['date', 'code', 'open', 'high', 'low', 'close', 'preclose', 
                      'volume', 'amount', 'adjustflag', 'turn', 'tradestatus', 'pctChg', 'isST']
            df = pd.DataFrame(data_list, columns=columns)
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"✅ {symbol} 数据获取成功，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取 {symbol} 数据失败: {e}")
            return None

    def batch_get_stock_data(self, symbols: List[str], start_date: str = None, 
                           end_date: str = None, frequency: str = "daily",
                           batch_size: int = 100, delay: float = 0.05,
                           max_workers: int = 15) -> Dict[str, pd.DataFrame]:  # 新增并发参数
        """
        批量获取股票历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            batch_size: 批次大小
            delay: 请求间隔（秒）
            
        Returns:
            {symbol: DataFrame} 字典
        """
        if not self.connected:
            if not self._login():
                return {}
        
        results = {}
        total = len(symbols)
        processed = 0
        failed = 0
        
        logger.info(f"🚀 开始批量获取 {total} 只股票数据...")
        
        def fetch_single_stock(symbol):
            """获取单个股票数据的内部函数"""
            try:
                # 小延迟防止过于频繁的请求
                time.sleep(delay)
                df = self.get_stock_data(symbol, start_date, end_date, frequency)
                return symbol, df
            except Exception as e:
                logger.error(f"❌ 批量获取 {symbol} 失败: {e}")
                return symbol, None
        
        # 使用线程池进行并发处理（BaoStock性能优化）
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(fetch_single_stock, symbol): symbol 
                for symbol in symbols
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_result, data = future.result()
                    if data is not None and not data.empty:
                        results[symbol_result] = data
                        processed += 1
                    else:
                        failed += 1
                    
                    # 进度报告
                    current = processed + failed
                    if current % 50 == 0 or current == total:
                        progress = current / total * 100
                        logger.info(f"📈 BaoStock进度: {current}/{total} ({progress:.1f}%) - 成功:{processed} 失败:{failed}")
                        
                except Exception as e:
                    logger.error(f"❌ 处理 {symbol} 结果时失败: {e}")
                    failed += 1
        
        success_rate = processed / total * 100 if total > 0 else 0
        logger.info(f"✅ BaoStock批量获取完成: 总数:{total} 成功:{processed} 失败:{failed} 成功率:{success_rate:.1f}%")
        
        return results

    def get_financial_data(self, symbol: str, year: int = None, quarter: int = None) -> Optional[pd.DataFrame]:
        """
        获取财务数据
        
        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)
            
        Returns:
            财务数据DataFrame
        """
        if not self.connected:
            if not self._login():
                return None
        
        try:
            bs_symbol = self._convert_symbol(symbol)
            
            if not year:
                year = datetime.now().year
            if not quarter:
                quarter = 4  # 默认年报
            
            logger.info(f"📋 获取 {symbol} 财务数据: {year}年Q{quarter}")
            
            # 查询季频盈利能力数据
            rs = self.bs.query_profit_data(code=bs_symbol, year=year, quarter=quarter)
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"⚠️ {symbol} 无财务数据")
                return None
            
            # 获取字段名
            fields = rs.fields
            df = pd.DataFrame(data_list, columns=fields)
            
            logger.info(f"✅ {symbol} 财务数据获取成功")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取 {symbol} 财务数据失败: {e}")
            return None

    def get_industry_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票行业信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            行业信息字典
        """
        if not self.connected:
            if not self._login():
                return None
        
        try:
            bs_symbol = self._convert_symbol(symbol)
            
            # 查询行业分类
            rs = self.bs.query_stock_industry(code=bs_symbol)
            
            industry_data = []
            while (rs.error_code == '0') & rs.next():
                industry_data.append(rs.get_row_data())
            
            if not industry_data:
                return None
            
            # 转换为字典格式
            fields = rs.fields
            if industry_data:
                row = industry_data[0]  # 取第一条记录
                return dict(zip(fields, row))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取 {symbol} 行业信息失败: {e}")
            return None

    def batch_download_all_stocks(self, start_date: str = None, end_date: str = None,
                                frequency: str = "daily", save_path: str = None) -> Dict[str, Any]:
        """
        批量下载所有A股历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期  
            frequency: 数据频率
            save_path: 保存路径
            
        Returns:
            下载统计信息
        """
        # 获取股票列表
        stock_list = self.get_stock_list()
        if stock_list is None or stock_list.empty:
            logger.error("❌ 无法获取股票列表")
            return {}
        
        # 提取股票代码
        symbols = [code.split('.')[1] for code in stock_list['code'].tolist() if '.' in code]
        
        logger.info(f"🎯 准备批量下载 {len(symbols)} 只股票数据")
        
        # 批量下载
        results = self.batch_get_stock_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            batch_size=100,
            delay=0.05  # 5毫秒间隔
        )
        
        # 统计信息
        stats = {
            'total_stocks': len(symbols),
            'successful_downloads': len(results),
            'failed_downloads': len(symbols) - len(results),
            'success_rate': len(results) / len(symbols) * 100 if symbols else 0,
            'data_summary': {}
        }
        
        # 数据摘要
        for symbol, df in results.items():
            stats['data_summary'][symbol] = {
                'records': len(df),
                'date_range': f"{df['date'].min()} - {df['date'].max()}" if not df.empty else "无数据"
            }
        
        logger.info(f"🎉 批量下载完成: 成功率 {stats['success_rate']:.1f}%")
        
        return {'stats': stats, 'data': results}


def get_baostock_provider() -> BaoStockProvider:
    """获取BaoStock数据提供器实例"""
    return BaoStockProvider()


# 示例使用
if __name__ == "__main__":
    # 创建提供器
    provider = get_baostock_provider()
    
    if provider.connected:
        # 获取股票列表
        stocks = provider.get_stock_list()
        print(f"股票总数: {len(stocks) if stocks is not None else 0}")
        
        # 获取单只股票数据
        data = provider.get_stock_data("000001", start_date="2024-01-01")
        if data is not None:
            print(f"平安银行数据: {len(data)} 条记录")
            print(data.head())
        
        # 批量获取示例
        symbols = ["000001", "000002", "600000"]
        batch_data = provider.batch_get_stock_data(symbols, start_date="2024-01-01")
        print(f"批量获取结果: {len(batch_data)} 只股票")