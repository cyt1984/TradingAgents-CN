#!/usr/bin/env python3
"""
批量并行数据更新管理器
实现智能活跃度分类驱动的批量并行更新系统
"""

import asyncio
import concurrent.futures
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading
from dataclasses import dataclass
import json

import pandas as pd

from tradingagents.utils.logging_manager import get_logger
from tradingagents.analytics.stock_activity_classifier import get_activity_classifier
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager

logger = get_logger('batch_update')


@dataclass
class UpdateTask:
    """更新任务数据类"""
    symbol: str
    classification: str
    priority: int
    last_update: Optional[datetime]
    estimated_duration: float
    update_frequency: str


class BatchUpdateManager:
    """批量并行数据更新管理器"""
    
    def __init__(self, max_workers: int = 10):
        """初始化批量更新管理器"""
        self.classifier = get_activity_classifier()
        self.historical_manager = get_historical_manager()
        self.data_manager = get_enhanced_data_manager()
        
        self.max_workers = max_workers
        self.update_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 更新频率配置（小时）
        self.update_intervals = {
            'active': 24,      # 活跃股票：每天
            'normal': 168,     # 普通股票：每周
            'inactive': 720    # 冷门股票：每月
        }
        
        # 优先级权重
        self.priority_weights = {
            'active': 100,
            'normal': 50,
            'inactive': 10
        }
        
        logger.info(f"🚀 批量更新管理器初始化完成，最大并行数：{max_workers}")
    
    def should_update(self, symbol: str, classification: str) -> bool:
        """判断是否需要更新"""
        try:
            availability = self.historical_manager.get_data_availability(symbol, "daily")
            
            if not availability['available']:
                return True
            
            last_update = datetime.fromisoformat(availability['last_updated'])
            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
            
            required_interval = self.update_intervals.get(classification, 168)
            
            return hours_since_update >= required_interval
            
        except Exception as e:
            logger.debug(f"判断{symbol}是否需要更新失败: {e}")
            return True
    
    def create_update_tasks(self, symbols: List[str]) -> List[UpdateTask]:
        """创建更新任务列表"""
        logger.info(f"📋 为{len(symbols)}只股票创建更新任务...")
        
        # 批量分类股票
        classifications = self.classifier.classify_stocks(symbols)
        
        tasks = []
        
        for classification, symbols_list in classifications.items():
            for symbol in symbols_list:
                if self.should_update(symbol, classification):
                    # 获取更新预估时间
                    estimated_time = self._estimate_update_time(symbol)
                    
                    # 获取最后更新时间
                    availability = self.historical_manager.get_data_availability(symbol, "daily")
                    last_update = None
                    if availability['available']:
                        last_update = datetime.fromisoformat(availability['last_updated'])
                    
                    task = UpdateTask(
                        symbol=symbol,
                        classification=classification,
                        priority=self.priority_weights.get(classification, 50),
                        last_update=last_update,
                        estimated_duration=estimated_time,
                        update_frequency=self.update_intervals.get(classification, 168)
                    )
                    tasks.append(task)
        
        # 按优先级排序
        tasks.sort(key=lambda x: (-x.priority, x.estimated_duration))
        
        logger.info(f"📊 创建更新任务：{len(tasks)}个，跳过{len(symbols) - len(tasks)}个")
        return tasks
    
    def _estimate_update_time(self, symbol: str) -> float:
        """估算单个股票更新时间"""
        # 基于历史经验估算
        try:
            # 检查现有数据量
            availability = self.historical_manager.get_data_availability(symbol, "daily")
            
            if not availability['available']:
                return 5.0  # 全量更新约5秒
            
            # 计算缺失天数
            missing_ranges = self.historical_manager.get_missing_date_ranges(
                symbol, "daily", 
                start_date=availability['end_date'],
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if not missing_ranges:
                return 0.5  # 只需检查，0.5秒
            
            # 估算缺失天数
            total_missing_days = 0
            for range_info in missing_ranges:
                start = datetime.strptime(range_info['start'], '%Y-%m-%d')
                end = datetime.strptime(range_info['end'], '%Y-%m-%d')
                total_missing_days += (end - start).days + 1
            
            # 每缺失一天约0.5秒
            return max(0.5, min(5.0, total_missing_days * 0.5))
            
        except Exception:
            return 2.0  # 默认2秒
    
    def update_single_stock(self, symbol: str, classification: str) -> bool:
        """更新单个股票数据"""
        try:
            logger.info(f"🔄 更新{symbol}({classification})...")
            
            # 确定更新范围
            availability = self.historical_manager.get_data_availability(symbol, "daily")
            
            if availability['available']:
                start_date = (datetime.strptime(availability['end_date'], '%Y-%m-%d') + 
                             timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取最新数据
            new_data = self.data_manager.get_historical_data(
                symbol, start_date, end_date, "daily"
            )
            
            if new_data is not None and not new_data.empty:
                # 保存到本地存储
                success = self.historical_manager.save_historical_data(
                    symbol, new_data, "daily"
                )
                
                if success:
                    logger.info(f"✅ {symbol}更新完成：{len(new_data)}条记录")
                    return True
                else:
                    logger.error(f"❌ {symbol}保存失败")
                    return False
            else:
                logger.info(f"ℹ️ {symbol}无新数据需要更新")
                return True
                
        except Exception as e:
            logger.error(f"❌ 更新{symbol}失败: {e}")
            return False
    
    def update_batch_parallel(self, tasks: List[UpdateTask]) -> Dict[str, int]:
        """并行批量更新"""
        logger.info(f"🚀 开始并行更新{len(tasks)}个任务...")
        
        stats = {
            'total': len(tasks),
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 按批次处理
        batch_size = min(self.max_workers, len(tasks))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.update_single_stock, task.symbol, task.classification): task
                for task in tasks
            }
            
            # 处理结果
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                except Exception as e:
                    logger.error(f"❌ {task.symbol}处理异常: {e}")
                    stats['failed'] += 1
        
        logger.info(f"📊 批量更新完成：成功{stats['successful']}个，失败{stats['failed']}个")
        return stats
    
    def smart_batch_update(self, symbols: List[str], force_update: bool = False) -> Dict[str, Any]:
        """
        智能批量更新主函数
        
        Args:
            symbols: 股票代码列表
            force_update: 是否强制更新所有股票
            
        Returns:
            更新统计结果
        """
        start_time = time.time()
        logger.info(f"🎯 开始智能批量更新，共{len(symbols)}只股票...")
        
        # 创建更新任务
        if force_update:
            # 强制更新所有股票
            tasks = []
            for symbol in symbols:
                task = UpdateTask(
                    symbol=symbol,
                    classification='normal',  # 默认分类
                    priority=50,
                    last_update=None,
                    estimated_duration=2.0,
                    update_frequency=168
                )
                tasks.append(task)
        else:
            # 智能选择需要更新的股票
            tasks = self.create_update_tasks(symbols)
        
        if not tasks:
            logger.info("ℹ️ 没有需要更新的股票")
            return {
                'total_symbols': len(symbols),
                'updated_symbols': 0,
                'skipped_symbols': len(symbols),
                'successful': 0,
                'failed': 0,
                'duration': 0
            }
        
        # 执行并行更新
        stats = self.update_batch_parallel(tasks)
        
        # 计算分类统计
        classifications = self.classifier.classify_stocks([task.symbol for task in tasks])
        
        duration = time.time() - start_time
        result = {
            'total_symbols': len(symbols),
            'updated_symbols': len(tasks),
            'skipped_symbols': len(symbols) - len(tasks),
            'successful': stats['successful'],
            'failed': stats['failed'],
            'duration': round(duration, 2),
            'classifications': {
                'active': len(classifications.get('active', [])),
                'normal': len(classifications.get('normal', [])),
                'inactive': len(classifications.get('inactive', []))
            },
            'throughput': round(len(tasks) / duration, 2) if duration > 0 else 0
        }
        
        logger.info(f"🎉 智能批量更新完成：{result}")
        return result
    
    def estimate_update_time(self, symbols: List[str]) -> Dict[str, float]:
        """预估更新时间"""
        tasks = self.create_update_tasks(symbols)
        
        total_time = sum(task.estimated_duration for task in tasks)
        
        # 考虑并行效率
        parallel_time = total_time / min(self.max_workers, len(tasks)) if tasks else 0
        
        return {
            'total_tasks': len(tasks),
            'total_estimate': round(total_time, 2),
            'parallel_estimate': round(parallel_time, 2),
            'max_workers': self.max_workers
        }


# 全局实例
_batch_manager = None


def get_batch_update_manager(max_workers: int = 10) -> BatchUpdateManager:
    """获取批量更新管理器实例"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchUpdateManager(max_workers)
    return _batch_manager


def batch_update_stocks(symbols: List[str], force_update: bool = False, max_workers: int = 10) -> Dict[str, Any]:
    """便捷函数：批量更新股票"""
    manager = get_batch_update_manager(max_workers)
    return manager.smart_batch_update(symbols, force_update)


def estimate_batch_time(symbols: List[str], max_workers: int = 10) -> Dict[str, float]:
    """便捷函数：预估更新时间"""
    manager = get_batch_update_manager(max_workers)
    return manager.estimate_update_time(symbols)