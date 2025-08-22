#!/usr/bin/env python3
"""
AKShare数据源工具
提供AKShare数据获取的统一接口
"""

import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import warnings
from datetime import datetime, timedelta
import time
import concurrent.futures
import threading
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('akshare')
warnings.filterwarnings('ignore')

class AKShareProvider:
    """AKShare数据提供器"""

    def __init__(self):
        """初始化AKShare提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True

            # 设置更长的超时时间
            self._configure_timeout()

            logger.info(f"✅ AKShare初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            logger.error(f"❌ AKShare未安装")

    def _configure_timeout(self):
        """配置AKShare的超时设置"""
        try:
            import requests
            import socket

            # 设置更长的超时时间
            socket.setdefaulttimeout(60)  # 60秒超时

            # 如果AKShare使用requests，设置默认超时
            if hasattr(requests, 'adapters'):
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                # 创建重试策略
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )

                # 设置适配器
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session = requests.Session()
                session.mount("http://", adapter)
                session.mount("https://", adapter)

                logger.info(f"🔧 AKShare超时配置完成: 60秒超时，3次重试")

        except Exception as e:
            logger.error(f"⚠️ AKShare超时配置失败: {e}")
            logger.info(f"🔧 使用默认超时设置")
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        if not self.connected:
            return None
        
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                symbol = symbol
            else:
                symbol = symbol.replace('.SZ', '').replace('.SS', '')
            
            # 获取数据
            data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20240101",
                end_date=end_date.replace('-', '') if end_date else "20241231",
                adjust=""
            )
            
            return data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取股票数据失败: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not self.connected:
            return {}
        
        try:
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            stock_info = stock_list[stock_list['code'] == symbol]
            
            if not stock_info.empty:
                return {
                    'symbol': symbol,
                    'name': stock_info.iloc[0]['name'],
                    'source': 'akshare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}
                
        except Exception as e:
            logger.error(f"❌ AKShare获取股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

    def get_hk_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取港股历史数据

        Args:
            symbol: 港股代码 (如: 00700 或 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 港股历史数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接")
            return None

        try:
            # 标准化港股代码 - AKShare使用5位数字格式
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股数据: {hk_symbol} ({start_date} 到 {end_date})")

            # 格式化日期为AKShare需要的格式
            start_date_formatted = start_date.replace('-', '') if start_date else "20240101"
            end_date_formatted = end_date.replace('-', '') if end_date else "20241231"

            # 使用AKShare获取港股历史数据（带超时保护）
            import threading

            result = [None]
            exception = [None]

            def fetch_hist_data():
                try:
                    result[0] = self.ak.stock_hk_hist(
                        symbol=hk_symbol,
                        period="daily",
                        start_date=start_date_formatted,
                        end_date=end_date_formatted,
                        adjust=""
                    )
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_hist_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股历史数据获取超时（60秒）: {symbol}")
                raise Exception(f"AKShare港股历史数据获取超时（60秒）: {symbol}")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                data = result[0]

            if not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Symbol'] = symbol  # 保持原始格式

                # 重命名列以保持一致性
                column_mapping = {
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data = data.rename(columns={old_col: new_col})

                logger.info(f"✅ AKShare港股数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare港股数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取港股数据失败: {e}")
            return None

    def get_hk_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股基本信息

        Args:
            symbol: 港股代码

        Returns:
            Dict: 港股基本信息
        """
        if not self.connected:
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_unavailable'
            }

        try:
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股信息: {hk_symbol}")

            # 尝试获取港股实时行情数据来获取基本信息
            # 使用线程超时包装（兼容Windows）
            import threading
            import time


            result = [None]
            exception = [None]

            def fetch_data():
                try:
                    result[0] = self.ak.stock_hk_spot_em()
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股信息获取超时（60秒），使用备用方案")
                raise Exception("AKShare港股信息获取超时（60秒）")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                spot_data = result[0]

            # 查找对应的股票信息
            if not spot_data.empty:
                # 查找匹配的股票
                matching_stocks = spot_data[spot_data['代码'].str.contains(hk_symbol[:5], na=False)]

                if not matching_stocks.empty:
                    stock_info = matching_stocks.iloc[0]
                    return {
                        'symbol': symbol,
                        'name': stock_info.get('名称', f'港股{symbol}'),
                        'currency': 'HKD',
                        'exchange': 'HKG',
                        'latest_price': stock_info.get('最新价', None),
                        'source': 'akshare'
                    }

            # 如果没有找到，返回基本信息
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare'
            }

        except Exception as e:
            logger.error(f"❌ AKShare获取港股信息失败: {e}")
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_error',
                'error': str(e)
            }

    def _normalize_hk_symbol_for_akshare(self, symbol: str) -> str:
        """
        标准化港股代码为AKShare格式

        Args:
            symbol: 原始港股代码 (如: 0700.HK 或 700)

        Returns:
            str: AKShare格式的港股代码 (如: 00700)
        """
        if not symbol:
            return symbol

        # 移除.HK后缀
        clean_symbol = symbol.replace('.HK', '').replace('.hk', '')

        # 确保是5位数字格式
        if clean_symbol.isdigit():
            return clean_symbol.zfill(5)

        return clean_symbol

    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票财务数据
        
        Args:
            symbol: 股票代码 (6位数字)
            
        Returns:
            Dict: 包含主要财务指标的财务数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取{symbol}财务数据")
            return {}
        
        try:
            logger.info(f"🔍 开始获取{symbol}的AKShare财务数据")
            
            financial_data = {}
            
            # 1. 优先获取主要财务指标
            try:
                logger.debug(f"📊 尝试获取{symbol}主要财务指标...")
                main_indicators = self.ak.stock_financial_abstract(symbol=symbol)
                if main_indicators is not None and not main_indicators.empty:
                    financial_data['main_indicators'] = main_indicators
                    logger.info(f"✅ 成功获取{symbol}主要财务指标: {len(main_indicators)}条记录")
                    logger.debug(f"主要财务指标列名: {list(main_indicators.columns)}")
                else:
                    logger.warning(f"⚠️ {symbol}主要财务指标为空")
            except Exception as e:
                logger.warning(f"❌ 获取{symbol}主要财务指标失败: {e}")
            
            # 2. 尝试获取资产负债表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}资产负债表...")
                balance_sheet = self.ak.stock_balance_sheet_by_report_em(symbol=symbol)
                if balance_sheet is not None and not balance_sheet.empty:
                    financial_data['balance_sheet'] = balance_sheet
                    logger.debug(f"✅ 成功获取{symbol}资产负债表: {len(balance_sheet)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}资产负债表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}资产负债表失败: {e}")
            
            # 3. 尝试获取利润表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}利润表...")
                income_statement = self.ak.stock_profit_sheet_by_report_em(symbol=symbol)
                if income_statement is not None and not income_statement.empty:
                    financial_data['income_statement'] = income_statement
                    logger.debug(f"✅ 成功获取{symbol}利润表: {len(income_statement)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}利润表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}利润表失败: {e}")
            
            # 4. 尝试获取现金流量表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}现金流量表...")
                cash_flow = self.ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
                if cash_flow is not None and not cash_flow.empty:
                    financial_data['cash_flow'] = cash_flow
                    logger.debug(f"✅ 成功获取{symbol}现金流量表: {len(cash_flow)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}现金流量表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}现金流量表失败: {e}")
            
            # 记录最终结果
            if financial_data:
                logger.info(f"✅ AKShare财务数据获取完成: {symbol}, 包含{len(financial_data)}个数据集")
                for key, value in financial_data.items():
                    if hasattr(value, '__len__'):
                        logger.info(f"  - {key}: {len(value)}条记录")
            else:
                logger.warning(f"⚠️ 未能获取{symbol}的任何AKShare财务数据")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取{symbol}财务数据失败: {e}")
            return {}

    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """
        获取A股股票列表
        
        Returns:
            DataFrame: 包含所有A股股票信息
        """
        if not self.connected:
            return None
        
        try:
            logger.info("🔍 开始获取A股股票列表...")
            
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            
            if stock_list is not None and not stock_list.empty:
                # 添加标准化的字段
                stock_list['symbol'] = stock_list['code']
                stock_list['name'] = stock_list['name']
                stock_list['market'] = stock_list['code'].apply(self._get_market_from_code)
                
                logger.info(f"✅ 获取A股股票列表成功，共 {len(stock_list)} 只股票")
                return stock_list
            else:
                logger.warning("⚠️ 未能获取股票列表")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取股票列表失败: {e}")
            return None

    def _get_market_from_code(self, code: str) -> str:
        """根据股票代码判断市场"""
        if code.startswith(('000', '001', '002', '003', '300')):
            return 'SZ'  # 深圳
        elif code.startswith(('600', '601', '603', '605', '688', '689')):
            return 'SH'  # 上海
        else:
            return 'SZ'  # 默认深圳

    def batch_get_stock_data(self, symbols: List[str], start_date: str = None, 
                           end_date: str = None, max_workers: int = 20,  # 激进优化：提升到20并发
                           delay: float = 0.1) -> Dict[str, pd.DataFrame]:  # 缩短延迟
        """
        批量获取股票历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)  
            max_workers: 最大并发线程数
            delay: 请求间隔时间（秒）
            
        Returns:
            {symbol: DataFrame} 字典
        """
        if not self.connected:
            logger.error("❌ AKShare未连接")
            return {}
        
        if not symbols:
            logger.warning("⚠️ 股票代码列表为空")
            return {}
        
        results = {}
        total = len(symbols)
        processed = 0
        failed = 0
        
        logger.info(f"🚀 开始批量获取 {total} 只股票的AKShare数据...")
        logger.info(f"📊 配置: 并发数={max_workers}, 延迟={delay}秒, 日期范围={start_date}到{end_date}")
        
        def fetch_single_stock(symbol: str) -> Tuple[str, Optional[pd.DataFrame]]:
            """获取单个股票数据"""
            try:
                # 请求间隔
                time.sleep(delay)
                
                data = self.get_stock_data(symbol, start_date, end_date)
                return symbol, data
                
            except Exception as e:
                logger.error(f"❌ 批量获取 {symbol} 失败: {e}")
                return symbol, None
        
        # 使用线程池批量处理
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
                        logger.info(f"📈 进度: {current}/{total} ({progress:.1f}%) - 成功:{processed} 失败:{failed}")
                        
                except Exception as e:
                    logger.error(f"❌ 处理 {symbol} 结果时失败: {e}")
                    failed += 1
        
        success_rate = processed / total * 100 if total > 0 else 0
        logger.info(f"✅ AKShare批量获取完成: 总数:{total} 成功:{processed} 失败:{failed} 成功率:{success_rate:.1f}%")
        
        return results

    def batch_get_financial_data(self, symbols: List[str], max_workers: int = 10,  # 激进优化：提升到10并发
                               delay: float = 0.5) -> Dict[str, Dict[str, Any]]:  # 缩短延迟
        """
        批量获取财务数据
        
        Args:
            symbols: 股票代码列表
            max_workers: 最大并发数（财务数据请求较重，建议较小值）
            delay: 请求间隔（秒）
            
        Returns:
            {symbol: financial_data} 字典
        """
        if not self.connected:
            logger.error("❌ AKShare未连接")
            return {}
        
        results = {}
        total = len(symbols)
        processed = 0
        failed = 0
        
        logger.info(f"🚀 开始批量获取 {total} 只股票的财务数据...")
        
        def fetch_single_financial(symbol: str) -> Tuple[str, Dict[str, Any]]:
            """获取单个股票财务数据"""
            try:
                time.sleep(delay)  # 财务数据请求间隔较长
                financial_data = self.get_financial_data(symbol)
                return symbol, financial_data
            except Exception as e:
                logger.error(f"❌ 批量获取 {symbol} 财务数据失败: {e}")
                return symbol, {}
        
        # 使用较小的线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(fetch_single_financial, symbol): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_result, financial_data = future.result()
                    if financial_data:
                        results[symbol_result] = financial_data
                        processed += 1
                    else:
                        failed += 1
                    
                    current = processed + failed
                    if current % 20 == 0 or current == total:
                        progress = current / total * 100
                        logger.info(f"📈 财务数据进度: {current}/{total} ({progress:.1f}%) - 成功:{processed} 失败:{failed}")
                        
                except Exception as e:
                    logger.error(f"❌ 处理 {symbol} 财务数据结果时失败: {e}")
                    failed += 1
        
        success_rate = processed / total * 100 if total > 0 else 0
        logger.info(f"✅ AKShare财务数据批量获取完成: 成功率:{success_rate:.1f}%")
        
        return results

    def batch_download_all_stocks(self, start_date: str = None, end_date: str = None,
                                save_to_file: bool = True, file_path: str = None) -> Dict[str, Any]:
        """
        批量下载所有A股历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            save_to_file: 是否保存到文件
            file_path: 保存路径
            
        Returns:
            下载统计和数据
        """
        # 1. 获取股票列表
        stock_list = self.get_stock_list()
        if stock_list is None or stock_list.empty:
            logger.error("❌ 无法获取股票列表")
            return {}
        
        symbols = stock_list['code'].tolist()
        logger.info(f"🎯 准备批量下载 {len(symbols)} 只A股数据")
        
        # 2. 批量下载数据（使用激进并发优化）
        stock_data = self.batch_get_stock_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            max_workers=25,  # 激进优化：智能选股专用高并发
            delay=0.05       # 更短的延迟
        )
        
        # 3. 批量获取基本信息（可选）
        logger.info("📋 批量获取股票基本信息...")
        
        # 4. 统计信息
        stats = {
            'total_stocks': len(symbols),
            'successful_downloads': len(stock_data),
            'failed_downloads': len(symbols) - len(stock_data),
            'success_rate': len(stock_data) / len(symbols) * 100 if symbols else 0,
            'stock_list': stock_list,
            'download_summary': {}
        }
        
        # 5. 生成下载摘要
        for symbol, df in stock_data.items():
            if df is not None and not df.empty:
                stats['download_summary'][symbol] = {
                    'records': len(df),
                    'date_range': f"{df.index.min()} - {df.index.max()}" if not df.empty else "无数据",
                    'data_size': df.memory_usage(deep=True).sum()
                }
        
        logger.info(f"🎉 AKShare批量下载完成: 成功率 {stats['success_rate']:.1f}%")
        
        # 6. 保存到文件（可选）
        if save_to_file and stock_data:
            try:
                if not file_path:
                    file_path = f"akshare_batch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                
                import pickle
                with open(file_path, 'wb') as f:
                    pickle.dump({
                        'stats': stats,
                        'data': stock_data,
                        'download_time': datetime.now().isoformat()
                    }, f)
                
                logger.info(f"💾 数据已保存到: {file_path}")
                stats['saved_file'] = file_path
                
            except Exception as e:
                logger.error(f"❌ 保存数据失败: {e}")
        
        return {
            'stats': stats,
            'data': stock_data
        }

    def smart_batch_update(self, symbols: List[str], existing_data: Dict[str, pd.DataFrame] = None,
                         start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        智能批量更新 - 只获取缺失的数据
        
        Args:
            symbols: 股票代码列表
            existing_data: 现有数据 {symbol: DataFrame}
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            更新后的完整数据
        """
        if existing_data is None:
            existing_data = {}
        
        # 分析需要更新的股票
        need_full_download = []  # 需要完整下载
        need_incremental = []    # 需要增量更新
        up_to_date = []         # 已是最新
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for symbol in symbols:
            if symbol not in existing_data:
                need_full_download.append(symbol)
            else:
                df = existing_data[symbol]
                if df.empty:
                    need_full_download.append(symbol)
                else:
                    # 检查最新日期
                    if hasattr(df.index, 'max'):
                        latest_date = df.index.max().strftime('%Y-%m-%d')
                    else:
                        latest_date = df['date'].max() if 'date' in df.columns else start_date
                    
                    if latest_date < current_date:
                        need_incremental.append((symbol, latest_date))
                    else:
                        up_to_date.append(symbol)
        
        logger.info(f"📊 数据更新分析: 完整下载:{len(need_full_download)} 增量更新:{len(need_incremental)} 最新:{len(up_to_date)}")
        
        results = existing_data.copy()
        
        # 1. 完整下载
        if need_full_download:
            logger.info(f"🔄 完整下载 {len(need_full_download)} 只股票...")
            full_data = self.batch_get_stock_data(need_full_download, start_date, end_date)
            results.update(full_data)
        
        # 2. 增量更新
        if need_incremental:
            logger.info(f"⚡ 增量更新 {len(need_incremental)} 只股票...")
            for symbol, last_date in need_incremental:
                # 从最后日期的下一天开始
                next_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                new_data = self.get_stock_data(symbol, next_date, end_date)
                
                if new_data is not None and not new_data.empty:
                    # 合并数据
                    if symbol in results:
                        results[symbol] = pd.concat([results[symbol], new_data]).drop_duplicates()
                    else:
                        results[symbol] = new_data
        
        logger.info(f"✅ 智能批量更新完成，总计 {len(results)} 只股票有数据")
        return results

def get_akshare_provider() -> AKShareProvider:
    """获取AKShare提供器实例"""
    return AKShareProvider()


# 便捷函数
def get_hk_stock_data_akshare(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    使用AKShare获取港股数据的便捷函数

    Args:
        symbol: 港股代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的港股数据
    """
    try:
        provider = get_akshare_provider()
        data = provider.get_hk_stock_data(symbol, start_date, end_date)

        if data is not None and not data.empty:
            return format_hk_stock_data_akshare(symbol, data, start_date, end_date)
        else:
            return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    except Exception as e:
        return f"❌ AKShare港股数据获取失败: {e}"


def get_hk_stock_info_akshare(symbol: str) -> Dict[str, Any]:
    """
    使用AKShare获取港股信息的便捷函数

    Args:
        symbol: 港股代码

    Returns:
        Dict: 港股信息
    """
    try:
        provider = get_akshare_provider()
        return provider.get_hk_stock_info(symbol)
    except Exception as e:
        return {
            'symbol': symbol,
            'name': f'港股{symbol}',
            'currency': 'HKD',
            'exchange': 'HKG',
            'source': 'akshare_error',
            'error': str(e)
        }


def format_hk_stock_data_akshare(symbol: str, data: pd.DataFrame, start_date: str, end_date: str) -> str:
    """
    格式化AKShare港股数据为文本格式

    Args:
        symbol: 股票代码
        data: 股票数据DataFrame
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    try:
        # 获取股票基本信息（允许失败）
        stock_name = f'港股{symbol}'  # 默认名称
        try:
            provider = get_akshare_provider()
            stock_info = provider.get_hk_stock_info(symbol)
            stock_name = stock_info.get('name', f'港股{symbol}')
            logger.info(f"✅ 港股信息获取成功: {stock_name}")
        except Exception as info_error:
            logger.error(f"⚠️ 港股信息获取失败，使用默认信息: {info_error}")
            # 继续处理，使用默认信息

        # 计算统计信息
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100

        avg_volume = data['Volume'].mean() if 'Volume' in data.columns else 0
        max_price = data['High'].max()
        min_price = data['Low'].min()

        # 格式化输出
        formatted_text = f"""
🇭🇰 港股数据报告 (AKShare)
================

股票信息:
- 代码: {symbol}
- 名称: {stock_name}
- 货币: 港币 (HKD)
- 交易所: 香港交易所 (HKG)

价格信息:
- 最新价格: HK${latest_price:.2f}
- 期间涨跌: HK${price_change:+.2f} ({price_change_pct:+.2f}%)
- 期间最高: HK${max_price:.2f}
- 期间最低: HK${min_price:.2f}

交易信息:
- 数据期间: {start_date} 至 {end_date}
- 交易天数: {len(data)}天
- 平均成交量: {avg_volume:,.0f}股

最近5个交易日:
"""

        # 添加最近5天的数据
        recent_data = data.tail(5)
        for _, row in recent_data.iterrows():
            date = row['Date'].strftime('%Y-%m-%d') if 'Date' in row else row.name.strftime('%Y-%m-%d')
            volume = row.get('Volume', 0)
            formatted_text += f"- {date}: 开盘HK${row['Open']:.2f}, 收盘HK${row['Close']:.2f}, 成交量{volume:,.0f}\n"

        formatted_text += f"\n数据来源: AKShare (港股)\n"

        return formatted_text

    except Exception as e:
        logger.error(f"❌ 格式化AKShare港股数据失败: {e}")
        return f"❌ AKShare港股数据格式化失败: {symbol}"


def get_stock_news_em(symbol: str) -> pd.DataFrame:
    """
    使用AKShare获取东方财富个股新闻

    Args:
        symbol: 股票代码，如 "600000" 或 "300059"

    Returns:
        pd.DataFrame: 包含新闻标题、内容、日期和链接的DataFrame
    """
    start_time = datetime.now()
    logger.info(f"[东方财富新闻] 开始获取股票 {symbol} 的东方财富新闻数据")
    
    try:
        provider = get_akshare_provider()
        if not provider.connected:
            logger.error(f"[东方财富新闻] ❌ AKShare未连接，无法获取东方财富新闻")
            return pd.DataFrame()

        logger.info(f"[东方财富新闻] 📰 准备调用AKShare API获取个股新闻: {symbol}")

        # 使用线程超时包装（兼容Windows）
        import threading
        import time

        result = [None]
        exception = [None]

        def fetch_news():
            try:
                logger.debug(f"[东方财富新闻] 线程开始执行 stock_news_em API调用: {symbol}")
                thread_start = time.time()
                result[0] = provider.ak.stock_news_em(symbol=symbol)
                thread_end = time.time()
                logger.debug(f"[东方财富新闻] 线程执行完成，耗时: {thread_end - thread_start:.2f}秒")
            except Exception as e:
                logger.error(f"[东方财富新闻] 线程执行异常: {e}")
                exception[0] = e

        # 启动线程
        thread = threading.Thread(target=fetch_news)
        thread.daemon = True
        logger.debug(f"[东方财富新闻] 启动线程获取新闻数据")
        thread.start()

        # 等待30秒
        logger.debug(f"[东方财富新闻] 等待线程完成，最长等待30秒")
        thread.join(timeout=30)

        if thread.is_alive():
            # 超时了
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"[东方财富新闻] ⚠️ 获取超时（30秒）: {symbol}，总耗时: {elapsed_time:.2f}秒")
            raise Exception(f"东方财富个股新闻获取超时（30秒）: {symbol}")
        elif exception[0]:
            # 有异常
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"[东方财富新闻] ❌ API调用异常: {exception[0]}，总耗时: {elapsed_time:.2f}秒")
            raise exception[0]
        else:
            # 成功
            news_df = result[0]

        if news_df is not None and not news_df.empty:
            news_count = len(news_df)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # 记录一些新闻标题示例
            sample_titles = [row.get('标题', '无标题') for _, row in news_df.head(3).iterrows()]
            logger.info(f"[东方财富新闻] 新闻标题示例: {', '.join(sample_titles)}")
            
            logger.info(f"[东方财富新闻] ✅ 获取成功: {symbol}, 共{news_count}条记录，耗时: {elapsed_time:.2f}秒")
            return news_df
        else:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"[东方财富新闻] ⚠️ 数据为空: {symbol}，API返回成功但无数据，耗时: {elapsed_time:.2f}秒")
            return pd.DataFrame()

    except Exception as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"[东方财富新闻] ❌ 获取失败: {symbol}, 错误: {e}, 耗时: {elapsed_time:.2f}秒")
        return pd.DataFrame()
