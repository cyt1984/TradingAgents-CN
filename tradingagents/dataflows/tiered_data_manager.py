#!/usr/bin/env python3
"""
分层数据管理器 - 核心调度逻辑
实现"批量优先 + 实时补充"的智能数据获取策略
解决用户提出的速度问题：从"一个个获取"改为"批量下载+精准补充"
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import time
import threading
from pathlib import Path
import json

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('tiered_data')

# 导入各种数据源
from .baostock_utils import get_baostock_provider
from .akshare_utils import get_akshare_provider
from .tushare_adapter import get_tushare_adapter

# 导入实时数据源
from .eastmoney_utils import get_eastmoney_provider
from .tencent_utils import get_tencent_provider
from .sina_utils import get_sina_provider
from .xueqiu_utils import get_xueqiu_provider


class DataTier(Enum):
    """数据层级枚举"""
    BATCH = "batch"           # 批量数据源层
    REALTIME = "realtime"     # 实时数据源层
    CACHE = "cache"           # 缓存层


class DataType(Enum):
    """数据类型枚举"""
    HISTORICAL = "historical"  # 历史K线数据
    FINANCIAL = "financial"    # 财务数据
    NEWS = "news"             # 新闻数据
    REALTIME_PRICE = "realtime_price"  # 实时价格
    SOCIAL = "social"         # 社交媒体数据


@dataclass
class DataRequest:
    """数据请求结构"""
    symbols: List[str]
    data_type: DataType
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    priority: int = 5  # 1-10，数字越小优先级越高
    max_age_hours: int = 24  # 数据最大年龄（小时）
    batch_preferred: bool = True  # 是否优先使用批量数据源


@dataclass
class DataResponse:
    """数据响应结构"""
    data: Dict[str, pd.DataFrame]
    source_info: Dict[str, str]  # {symbol: source}
    stats: Dict[str, Any]
    cache_hits: int = 0
    batch_hits: int = 0
    realtime_hits: int = 0


class TieredDataManager:
    """分层数据管理器"""
    
    def __init__(self):
        """初始化分层数据管理器"""
        self.batch_providers = {}
        self.realtime_providers = {}
        self.provider_status = {}
        
        # 数据获取统计
        self.stats = {
            'batch_requests': 0,
            'realtime_requests': 0,
            'cache_hits': 0,
            'total_requests': 0,
            'performance_log': []
        }
        
        # 初始化所有数据源
        self._init_batch_providers()
        self._init_realtime_providers()
        
        logger.info("🏗️ 分层数据管理器初始化完成")
        logger.info(f"   批量数据源: {list(self.batch_providers.keys())}")
        logger.info(f"   实时数据源: {list(self.realtime_providers.keys())}")

    def _init_batch_providers(self):
        """初始化批量数据源"""
        logger.info("📦 初始化批量数据源...")
        
        # BaoStock - 完全免费的批量数据源
        try:
            baostock = get_baostock_provider()
            if baostock.connected:
                self.batch_providers['baostock'] = baostock
                self.provider_status['baostock'] = True
                logger.info("✅ BaoStock批量数据源就绪")
            else:
                self.provider_status['baostock'] = False
                logger.warning("⚠️ BaoStock连接失败")
        except Exception as e:
            logger.error(f"❌ BaoStock初始化失败: {e}")
            self.provider_status['baostock'] = False
        
        # AKShare - 免费批量数据源
        try:
            akshare = get_akshare_provider()
            if akshare.connected:
                self.batch_providers['akshare'] = akshare
                self.provider_status['akshare'] = True
                logger.info("✅ AKShare批量数据源就绪")
            else:
                self.provider_status['akshare'] = False
                logger.warning("⚠️ AKShare连接失败")
        except Exception as e:
            logger.error(f"❌ AKShare初始化失败: {e}")
            self.provider_status['akshare'] = False
        
        # Tushare - 付费但高质量的批量数据源
        try:
            if get_tushare_adapter:
                tushare = get_tushare_adapter()
                if hasattr(tushare, 'connected') and tushare.connected:
                    self.batch_providers['tushare'] = tushare
                    self.provider_status['tushare'] = True
                    logger.info("✅ Tushare批量数据源就绪")
                else:
                    self.provider_status['tushare'] = False
                    logger.info("ℹ️ Tushare未配置或连接失败")
        except Exception as e:
            logger.warning(f"⚠️ Tushare初始化失败: {e}")
            self.provider_status['tushare'] = False

    def _init_realtime_providers(self):
        """初始化实时数据源"""
        logger.info("⚡ 初始化实时数据源...")
        
        # 东方财富 - 实时数据
        try:
            eastmoney = get_eastmoney_provider()
            self.realtime_providers['eastmoney'] = eastmoney
            self.provider_status['eastmoney'] = True
            logger.info("✅ 东方财富实时数据源就绪")
        except Exception as e:
            logger.error(f"❌ 东方财富初始化失败: {e}")
            self.provider_status['eastmoney'] = False
        
        # 腾讯财经 - 实时数据
        try:
            tencent = get_tencent_provider()
            self.realtime_providers['tencent'] = tencent
            self.provider_status['tencent'] = True
            logger.info("✅ 腾讯财经实时数据源就绪")
        except Exception as e:
            logger.error(f"❌ 腾讯财经初始化失败: {e}")
            self.provider_status['tencent'] = False
        
        # 新浪财经 - 实时数据
        try:
            sina = get_sina_provider()
            self.realtime_providers['sina'] = sina
            self.provider_status['sina'] = True
            logger.info("✅ 新浪财经实时数据源就绪")
        except Exception as e:
            logger.error(f"❌ 新浪财经初始化失败: {e}")
            self.provider_status['sina'] = False
        
        # 雪球 - 社交和实时数据
        try:
            xueqiu = get_xueqiu_provider()
            self.realtime_providers['xueqiu'] = xueqiu
            self.provider_status['xueqiu'] = True
            logger.info("✅ 雪球实时数据源就绪")
        except Exception as e:
            logger.error(f"❌ 雪球初始化失败: {e}")
            self.provider_status['xueqiu'] = False

    def get_data(self, request: DataRequest) -> DataResponse:
        """
        智能获取数据 - 核心调度方法
        
        Args:
            request: 数据请求
            
        Returns:
            数据响应
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        logger.info(f"🎯 开始处理数据请求: {len(request.symbols)}只股票, 类型:{request.data_type.value}")
        
        # 初始化响应
        response = DataResponse(
            data={},
            source_info={},
            stats={}
        )
        
        try:
            # 1. 检查缓存（如果可用）
            cached_data = self._check_cache(request)
            if cached_data:
                response.data.update(cached_data)
                response.cache_hits = len(cached_data)
                logger.info(f"💾 缓存命中: {len(cached_data)}只股票")
            
            # 2. 确定需要获取的股票
            remaining_symbols = [s for s in request.symbols if s not in response.data]
            
            if not remaining_symbols:
                logger.info("✅ 所有数据都来自缓存")
                return response
            
            # 3. 分层数据获取策略
            if request.batch_preferred and request.data_type in [DataType.HISTORICAL, DataType.FINANCIAL]:
                # 优先使用批量数据源
                batch_data = self._get_batch_data(remaining_symbols, request)
                if batch_data:
                    response.data.update(batch_data['data'])
                    response.source_info.update(batch_data['source_info'])
                    response.batch_hits = len(batch_data['data'])
                    
                    # 更新剩余需要获取的股票
                    remaining_symbols = [s for s in remaining_symbols if s not in batch_data['data']]
            
            # 4. 实时数据源补充
            if remaining_symbols:
                realtime_data = self._get_realtime_data(remaining_symbols, request)
                if realtime_data:
                    response.data.update(realtime_data['data'])
                    response.source_info.update(realtime_data['source_info'])
                    response.realtime_hits = len(realtime_data['data'])
            
            # 5. 保存新获取的数据到缓存
            self._save_to_cache(response.data, request)
            
            # 6. 更新统计信息
            elapsed_time = time.time() - start_time
            response.stats = {
                'total_symbols': len(request.symbols),
                'successful': len(response.data),
                'failed': len(request.symbols) - len(response.data),
                'elapsed_time': elapsed_time,
                'cache_hits': response.cache_hits,
                'batch_hits': response.batch_hits,
                'realtime_hits': response.realtime_hits,
                'success_rate': len(response.data) / len(request.symbols) * 100 if request.symbols else 0
            }
            
            # 6. 记录性能日志
            self.stats['performance_log'].append({
                'timestamp': datetime.now().isoformat(),
                'symbols_count': len(request.symbols),
                'data_type': request.data_type.value,
                'elapsed_time': elapsed_time,
                'success_rate': response.stats['success_rate'],
                'strategy': 'batch' if response.batch_hits > response.realtime_hits else 'realtime'
            })
            
            logger.info(f"✅ 数据获取完成: 成功{response.stats['successful']}/{response.stats['total_symbols']} "
                       f"({response.stats['success_rate']:.1f}%), 耗时{elapsed_time:.2f}秒")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 数据获取失败: {e}")
            response.stats = {'error': str(e)}
            return response

    def _check_cache(self, request: DataRequest) -> Optional[Dict[str, pd.DataFrame]]:
        """检查缓存数据"""
        try:
            # 导入现有的缓存管理器
            from tradingagents.dataflows.cache_manager import get_cache
            from tradingagents.dataflows.historical_data_manager import get_historical_manager
            
            cached_data = {}
            cache_manager = get_cache()
            historical_manager = get_historical_manager()
            
            for symbol in request.symbols:
                # 1. 先检查内存缓存 - 使用多种缓存键尝试
                cache_keys = [
                    f"stock_data_{symbol}_{request.start_date}_{request.end_date}",  # 精确匹配
                    f"stock_data_{symbol}_recent",  # 最近数据（不依赖具体日期）
                    f"stock_data_{symbol}_daily"  # 日线数据通用缓存
                ]
                
                cached_df = None
                for cache_key in cache_keys:
                    cached_df = cache_manager.get(cache_key)
                    if cached_df is not None and not cached_df.empty:
                        # 检查数据是否包含所需的日期范围
                        if hasattr(cached_df, 'index') and len(cached_df.index) > 0:
                            try:
                                # 检查数据的日期范围是否满足需求
                                data_start = cached_df.index[0].date() if hasattr(cached_df.index[0], 'date') else cached_df.index[0]
                                data_end = cached_df.index[-1].date() if hasattr(cached_df.index[-1], 'date') else cached_df.index[-1]
                                
                                from datetime import datetime
                                req_start = datetime.strptime(request.start_date, '%Y-%m-%d').date() if request.start_date else None
                                req_end = datetime.strptime(request.end_date, '%Y-%m-%d').date() if request.end_date else None
                                
                                # 检查缓存数据是否覆盖所需范围
                                if req_start and req_end:
                                    if data_start <= req_start and data_end >= req_end:
                                        # 过滤出所需的日期范围
                                        filtered_df = cached_df[(cached_df.index >= request.start_date) & (cached_df.index <= request.end_date)]
                                        if not filtered_df.empty:
                                            cached_data[symbol] = filtered_df
                                            logger.debug(f"✅ 内存缓存命中(范围过滤): {symbol} (key: {cache_key})")
                                            break
                                elif req_end is None or data_end >= req_end:
                                    # 如果没有结束日期限制，或数据足够新
                                    cached_data[symbol] = cached_df
                                    logger.debug(f"✅ 内存缓存命中(最新数据): {symbol} (key: {cache_key})")
                                    break
                            except Exception as e:
                                logger.debug(f"缓存数据日期检查失败 {symbol}: {e}")
                                continue
                        else:
                            cached_data[symbol] = cached_df
                            logger.debug(f"✅ 内存缓存命中(无索引): {symbol} (key: {cache_key})")
                            break
                
                if symbol in cached_data:
                    continue
                else:
                    logger.debug(f"❌ 内存缓存完全未命中: {symbol}")
                
                # 2. 检查历史数据管理器（持久化存储）
                if request.data_type == DataType.HISTORICAL:
                    try:
                        stored_data = historical_manager.get_data(
                            symbol=symbol,
                            start_date=request.start_date,
                            end_date=request.end_date
                        )
                        
                        if stored_data is not None and not stored_data.empty:
                            # 检查数据是否足够新
                            latest_date = stored_data.index[-1] if hasattr(stored_data, 'index') else None
                            if latest_date:
                                # 如果数据在指定时间范围内，使用缓存
                                current_date = datetime.now().date()
                                data_date = latest_date.date() if hasattr(latest_date, 'date') else latest_date
                                
                                # 激进缓存策略：如果数据不超过3天，认为是新鲜的（智能选股性能优化）
                                if (current_date - data_date).days <= 3:
                                    cached_data[symbol] = stored_data
                                    logger.debug(f"✅ 持久化缓存命中: {symbol} (数据日期: {data_date}, 年龄: {(current_date - data_date).days}天)")
                                    
                                    # 同时更新内存缓存
                                    cache_manager.set(cache_key, stored_data, expire_minutes=60)
                                else:
                                    logger.debug(f"❌ 持久化缓存过期: {symbol} (数据日期: {data_date}, 年龄: {(current_date - data_date).days}天)")
                                    
                    except Exception as e:
                        logger.debug(f"检查 {symbol} 历史缓存失败: {e}")
                        continue
            
            if cached_data:
                logger.info(f"💾 缓存命中: {len(cached_data)} 只股票，跳过重复获取")
                
            return cached_data if cached_data else None
            
        except Exception as e:
            logger.warning(f"⚠️ 缓存检查失败: {e}")
            return None

    def _save_to_cache(self, data: Dict[str, pd.DataFrame], request: DataRequest):
        """保存数据到缓存"""
        try:
            # 导入缓存管理器
            from tradingagents.dataflows.cache_manager import get_cache
            from tradingagents.dataflows.historical_data_manager import get_historical_manager
            
            cache_manager = get_cache()
            historical_manager = get_historical_manager()
            
            for symbol, df in data.items():
                if df is not None and not df.empty:
                    # 1. 保存到内存缓存（短期缓存）- 使用多种缓存键
                    cache_keys = [
                        f"stock_data_{symbol}_{request.start_date}_{request.end_date}",  # 精确匹配
                        f"stock_data_{symbol}_recent",  # 最近数据
                        f"stock_data_{symbol}_daily"  # 日线数据通用
                    ]
                    
                    for cache_key in cache_keys:
                        cache_manager.set(cache_key, df, expire_minutes=480)  # 激进缓存：延长到8小时
                    
                    # 2. 保存到历史数据管理器（持久化存储）
                    if request.data_type == DataType.HISTORICAL:
                        try:
                            historical_manager.save_data(
                                symbol=symbol,
                                data=df,
                                data_type='daily'  # 默认日线数据
                            )
                        except Exception as e:
                            logger.debug(f"保存 {symbol} 到历史数据库失败: {e}")
            
            if data:
                logger.info(f"💾 已保存 {len(data)} 只股票数据到缓存")
                
        except Exception as e:
            logger.warning(f"⚠️ 保存数据到缓存失败: {e}")

    def _get_batch_data(self, symbols: List[str], request: DataRequest) -> Optional[Dict[str, Any]]:
        """
        从批量数据源获取数据
        
        Args:
            symbols: 股票代码列表
            request: 数据请求
            
        Returns:
            批量数据结果
        """
        logger.info(f"📦 使用批量数据源获取 {len(symbols)} 只股票数据...")
        
        # 批量数据源优先级：BaoStock -> AKShare -> Tushare
        batch_order = ['baostock', 'akshare', 'tushare']
        
        for source in batch_order:
            if source not in self.batch_providers or not self.provider_status.get(source, False):
                continue
            
            try:
                provider = self.batch_providers[source]
                logger.info(f"🔄 尝试使用 {source} 批量获取数据...")
                
                if request.data_type == DataType.HISTORICAL:
                    # 获取历史K线数据
                    if source == 'baostock':
                        data = provider.batch_get_stock_data(
                            symbols=symbols,
                            start_date=request.start_date,
                            end_date=request.end_date,
                            batch_size=100,
                            delay=0.05
                        )
                    elif source == 'akshare':
                        data = provider.batch_get_stock_data(
                            symbols=symbols,
                            start_date=request.start_date,
                            end_date=request.end_date,
                            max_workers=8,
                            delay=0.1
                        )
                    elif source == 'tushare':
                        # Tushare批量获取逻辑
                        data = self._get_tushare_batch_data(provider, symbols, request)
                    else:
                        continue
                
                elif request.data_type == DataType.FINANCIAL:
                    # 获取财务数据
                    if hasattr(provider, 'batch_get_financial_data'):
                        data = provider.batch_get_financial_data(symbols)
                    else:
                        continue
                else:
                    continue
                
                if data and len(data) > 0:
                    # 成功获取数据
                    self.stats['batch_requests'] += 1
                    source_info = {symbol: source for symbol in data.keys()}
                    
                    logger.info(f"✅ {source} 批量获取成功: {len(data)}/{len(symbols)} 只股票")
                    
                    return {
                        'data': data,
                        'source_info': source_info,
                        'source': source
                    }
                else:
                    logger.warning(f"⚠️ {source} 批量获取失败或无数据")
                    
            except Exception as e:
                logger.error(f"❌ {source} 批量获取异常: {e}")
                continue
        
        logger.warning("⚠️ 所有批量数据源都失败")
        return None

    def _get_realtime_data(self, symbols: List[str], request: DataRequest) -> Optional[Dict[str, Any]]:
        """
        从实时数据源获取数据
        
        Args:
            symbols: 股票代码列表
            request: 数据请求
            
        Returns:
            实时数据结果
        """
        logger.info(f"⚡ 使用实时数据源补充获取 {len(symbols)} 只股票数据...")
        
        # 实时数据源优先级：东方财富 -> 腾讯 -> 新浪 -> 雪球
        realtime_order = ['eastmoney', 'tencent', 'sina', 'xueqiu']
        
        data = {}
        source_info = {}
        remaining_symbols = symbols.copy()
        
        for source in realtime_order:
            if not remaining_symbols:
                break
                
            if source not in self.realtime_providers or not self.provider_status.get(source, False):
                continue
            
            try:
                provider = self.realtime_providers[source]
                logger.info(f"🔄 尝试使用 {source} 获取 {len(remaining_symbols)} 只股票...")
                
                # 逐个获取（实时数据源通常不支持批量）
                successful_symbols = []
                for symbol in remaining_symbols:
                    try:
                        if request.data_type == DataType.HISTORICAL:
                            result = provider.get_stock_data(symbol, request.start_date, request.end_date)
                        elif request.data_type == DataType.REALTIME_PRICE:
                            result = provider.get_real_time_data(symbol)
                        elif request.data_type == DataType.NEWS:
                            result = provider.get_news_data(symbol)
                        else:
                            continue
                        
                        if result is not None and not (hasattr(result, 'empty') and result.empty):
                            data[symbol] = result
                            source_info[symbol] = source
                            successful_symbols.append(symbol)
                            
                    except Exception as e:
                        logger.debug(f"❌ {source} 获取 {symbol} 失败: {e}")
                        continue
                
                # 更新剩余需要获取的股票
                remaining_symbols = [s for s in remaining_symbols if s not in successful_symbols]
                
                if successful_symbols:
                    logger.info(f"✅ {source} 获取成功: {len(successful_symbols)} 只股票")
                
            except Exception as e:
                logger.error(f"❌ {source} 获取异常: {e}")
                continue
        
        if data:
            self.stats['realtime_requests'] += 1
            return {
                'data': data,
                'source_info': source_info
            }
        else:
            logger.warning("⚠️ 所有实时数据源都失败")
            return None

    def _get_tushare_batch_data(self, provider, symbols: List[str], request: DataRequest) -> Dict[str, pd.DataFrame]:
        """获取Tushare批量数据"""
        # TODO: 实现Tushare批量获取逻辑
        # 这里需要根据具体的Tushare适配器API实现
        return {}

    def get_stock_list_batch(self) -> Optional[pd.DataFrame]:
        """
        批量获取股票列表
        
        Returns:
            股票列表DataFrame
        """
        logger.info("📋 批量获取股票列表...")
        
        # 优先使用批量数据源获取股票列表
        for source in ['akshare', 'baostock']:
            if source in self.batch_providers and self.provider_status.get(source, False):
                try:
                    provider = self.batch_providers[source]
                    stock_list = provider.get_stock_list()
                    
                    if stock_list is not None and not stock_list.empty:
                        logger.info(f"✅ 从 {source} 获取股票列表成功: {len(stock_list)} 只股票")
                        return stock_list
                        
                except Exception as e:
                    logger.error(f"❌ 从 {source} 获取股票列表失败: {e}")
                    continue
        
        logger.error("❌ 无法从任何批量数据源获取股票列表")
        return None

    def batch_download_all(self, start_date: str = None, end_date: str = None, 
                          data_types: List[DataType] = None) -> Dict[str, Any]:
        """
        批量下载所有股票数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            data_types: 要下载的数据类型列表
            
        Returns:
            下载结果统计
        """
        if data_types is None:
            data_types = [DataType.HISTORICAL]
        
        logger.info(f"🚀 开始批量下载所有股票数据: {[dt.value for dt in data_types]}")
        
        # 1. 获取股票列表
        stock_list = self.get_stock_list_batch()
        if stock_list is None or stock_list.empty:
            return {'error': '无法获取股票列表'}
        
        symbols = stock_list['code'].tolist() if 'code' in stock_list.columns else stock_list['symbol'].tolist()
        
        # 2. 分批下载不同类型的数据
        results = {}
        total_start_time = time.time()
        
        for data_type in data_types:
            logger.info(f"📊 下载 {data_type.value} 数据...")
            
            request = DataRequest(
                symbols=symbols,
                data_type=data_type,
                start_date=start_date,
                end_date=end_date,
                batch_preferred=True
            )
            
            response = self.get_data(request)
            results[data_type.value] = response
        
        # 3. 生成总体统计
        total_elapsed = time.time() - total_start_time
        total_stats = {
            'total_symbols': len(symbols),
            'data_types': [dt.value for dt in data_types],
            'total_elapsed_time': total_elapsed,
            'results': {dt.value: resp.stats for dt, resp in zip(data_types, results.values())},
            'overall_success_rate': sum(resp.stats.get('success_rate', 0) for resp in results.values()) / len(data_types)
        }
        
        logger.info(f"🎉 批量下载完成: 总耗时{total_elapsed:.2f}秒, 平均成功率{total_stats['overall_success_rate']:.1f}%")
        
        return {
            'stats': total_stats,
            'results': results
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            'total_requests': self.stats['total_requests'],
            'batch_requests': self.stats['batch_requests'],
            'realtime_requests': self.stats['realtime_requests'],
            'cache_hits': self.stats['cache_hits'],
            'provider_status': self.provider_status.copy(),
            'recent_performance': self.stats['performance_log'][-10:] if self.stats['performance_log'] else []
        }


# 单例模式
_tiered_manager_instance = None

def get_tiered_data_manager() -> TieredDataManager:
    """获取分层数据管理器单例"""
    global _tiered_manager_instance
    if _tiered_manager_instance is None:
        _tiered_manager_instance = TieredDataManager()
    return _tiered_manager_instance


# 便捷函数
def smart_get_stock_data(symbols: Union[str, List[str]], start_date: str = None, 
                        end_date: str = None, batch_preferred: bool = True) -> Dict[str, pd.DataFrame]:
    """
    智能获取股票历史数据
    
    Args:
        symbols: 股票代码或股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        batch_preferred: 是否优先使用批量数据源
        
    Returns:
        {symbol: DataFrame} 数据字典
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    
    manager = get_tiered_data_manager()
    request = DataRequest(
        symbols=symbols,
        data_type=DataType.HISTORICAL,
        start_date=start_date,
        end_date=end_date,
        batch_preferred=batch_preferred
    )
    
    response = manager.get_data(request)
    return response.data


def smart_batch_download(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    智能批量下载所有股票数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        下载结果
    """
    manager = get_tiered_data_manager()
    return manager.batch_download_all(start_date, end_date)


if __name__ == "__main__":
    # 测试分层数据管理器
    manager = get_tiered_data_manager()
    
    # 测试获取单只股票数据
    data = smart_get_stock_data("000001", start_date="2024-01-01", end_date="2024-01-10")
    print(f"获取结果: {len(data)} 只股票")
    
    # 测试批量获取
    symbols = ["000001", "000002", "600000"]
    batch_data = smart_get_stock_data(symbols, start_date="2024-01-01", end_date="2024-01-10")
    print(f"批量获取结果: {len(batch_data)} 只股票")
    
    # 性能统计
    stats = manager.get_performance_stats()
    print(f"性能统计: {stats}")