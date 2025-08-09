#!/usr/bin/env python3
"""
历史数据管理器
专门处理历史价格数据的永久存储和高效查询
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

from tradingagents.utils.logging_manager import get_logger
from .persistent_storage import get_persistent_manager

logger = get_logger('historical_data')


class HistoricalDataManager:
    """历史数据管理器"""
    
    def __init__(self, data_dir: str = "./data/historical"):
        """
        初始化历史数据管理器
        
        Args:
            data_dir: 历史数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.persistent_manager = get_persistent_manager()
        self._lock = threading.Lock()
        
        # SQLite数据库用于索引和快速查询
        self.db_path = self.data_dir / "historical_index.db"
        self._init_database()
        
        logger.info("📈 历史数据管理器初始化完成")
        logger.info(f"🗄️ 数据库路径: {self.db_path}")
    
    def _init_database(self):
        """初始化SQLite数据库"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stock_data_index (
                    symbol TEXT PRIMARY KEY,
                    frequency TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    record_count INTEGER,
                    file_path TEXT,
                    last_updated TEXT,
                    checksum TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS data_gaps (
                    symbol TEXT,
                    frequency TEXT,
                    gap_start TEXT,
                    gap_end TEXT,
                    PRIMARY KEY (symbol, frequency, gap_start, gap_end)
                )
            ''')
            
            conn.commit()
    
    def save_historical_data(self, symbol: str, data: pd.DataFrame, 
                           frequency: str = "daily", overwrite: bool = False) -> bool:
        """
        保存历史价格数据
        
        Args:
            symbol: 股票代码
            data: 价格数据DataFrame
            frequency: 数据频率 (daily, weekly, monthly)
            overwrite: 是否覆盖现有数据
        
        Returns:
            是否保存成功
        """
        if data.empty or 'date' not in data.columns:
            logger.warning(f"⚠️ 无效数据格式: {symbol}")
            return False
        
        try:
            # 确保数据按日期排序
            data = data.sort_values('date')
            data['date'] = pd.to_datetime(data['date'])
            
            # 检查现有数据
            existing_data = self.load_historical_data(symbol, frequency)
            if existing_data is not None and not overwrite:
                # 合并数据，避免重复
                combined_data = pd.concat([existing_data, data])
                combined_data = combined_data.drop_duplicates(subset=['date'], keep='last')
                combined_data = combined_data.sort_values('date')
                data = combined_data
            
            # 保存到持久化存储
            self.persistent_manager.save_historical_prices(symbol, data, frequency)
            
            # 更新数据库索引
            self._update_data_index(symbol, frequency, data)
            
            logger.info(f"✅ 保存历史数据: {symbol} ({frequency}) - {len(data)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存历史数据失败: {symbol} - {e}")
            return False
    
    def load_historical_data(self, symbol: str, frequency: str = "daily",
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        加载历史价格数据
        
        Args:
            symbol: 股票代码
            frequency: 数据频率
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            价格数据DataFrame或None
        """
        try:
            return self.persistent_manager.load_historical_prices(
                symbol, frequency, start_date, end_date
            )
        except Exception as e:
            logger.error(f"❌ 加载历史数据失败: {symbol} - {e}")
            return None
    
    def _update_data_index(self, symbol: str, frequency: str, data: pd.DataFrame):
        """更新数据索引"""
        if data.empty or 'date' not in data.columns:
            return
        
        start_date = data['date'].min().strftime('%Y-%m-%d')
        end_date = data['date'].max().strftime('%Y-%m-%d')
        record_count = len(data)
        
        file_path = str(self.persistent_manager._get_file_path("historical", symbol, frequency))
        checksum = self.persistent_manager._calculate_checksum(data)
        
        metadata = {
            "columns": list(data.columns),
            "data_types": str(data.dtypes.to_dict())
        }
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO stock_data_index 
                (symbol, frequency, start_date, end_date, record_count, 
                 file_path, last_updated, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, frequency, start_date, end_date, record_count,
                file_path, datetime.now().isoformat(), checksum,
                json.dumps(metadata)
            ))
            conn.commit()
    
    def get_data_availability(self, symbol: str, frequency: str = "daily") -> Dict[str, Any]:
        """获取数据可用性信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT start_date, end_date, record_count, last_updated
                FROM stock_data_index
                WHERE symbol = ? AND frequency = ?
            ''', (symbol, frequency))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "available": True,
                    "start_date": result[0],
                    "end_date": result[1],
                    "record_count": result[2],
                    "last_updated": result[3]
                }
            else:
                return {
                    "available": False,
                    "start_date": None,
                    "end_date": None,
                    "record_count": 0,
                    "last_updated": None
                }
    
    def get_missing_date_ranges(self, symbol: str, frequency: str = "daily",
                              start_date: str = None, end_date: str = None) -> List[Dict[str, str]]:
        """获取缺失的日期范围"""
        availability = self.get_data_availability(symbol, frequency)
        
        if not availability["available"]:
            return [{"start": start_date or "2000-01-01", "end": end_date or datetime.now().strftime('%Y-%m-%d')}]
        
        data_start = pd.to_datetime(availability["start_date"])
        data_end = pd.to_datetime(availability["end_date"])
        
        target_start = pd.to_datetime(start_date) if start_date else data_start
        target_end = pd.to_datetime(end_date) if end_date else pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
        
        missing_ranges = []
        
        if target_start < data_start:
            missing_ranges.append({
                "start": target_start.strftime('%Y-%m-%d'),
                "end": (data_start - timedelta(days=1)).strftime('%Y-%m-%d')
            })
        
        if target_end > data_end:
            missing_ranges.append({
                "start": (data_end + timedelta(days=1)).strftime('%Y-%m-%d'),
                "end": target_end.strftime('%Y-%m-%d')
            })
        
        return missing_ranges
    
    def list_available_symbols(self, frequency: str = "daily") -> List[str]:
        """获取可用的股票代码列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT DISTINCT symbol FROM stock_data_index
                WHERE frequency = ?
            ''', (frequency,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_data_summary(self, frequency: str = "daily") -> Dict[str, Any]:
        """获取数据摘要信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(DISTINCT symbol), SUM(record_count),
                       MIN(start_date), MAX(end_date)
                FROM stock_data_index
                WHERE frequency = ?
            ''', (frequency,))
            
            result = cursor.fetchone()
            
            return {
                "total_symbols": result[0] or 0,
                "total_records": result[1] or 0,
                "earliest_date": result[2],
                "latest_date": result[3],
                "frequency": frequency
            }
    
    def verify_data_integrity(self, symbol: str, frequency: str = "daily") -> Dict[str, Any]:
        """验证数据完整性"""
        result = {
            "symbol": symbol,
            "frequency": frequency,
            "integrity_check": "failed",
            "issues": []
        }
        
        try:
            # 从索引获取文件信息
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT file_path, checksum, record_count, start_date, end_date
                    FROM stock_data_index
                    WHERE symbol = ? AND frequency = ?
                ''', (symbol, frequency))
                
                index_info = cursor.fetchone()
                
                if not index_info:
                    result["issues"].append("数据索引不存在")
                    return result
            
            file_path = Path(index_info[0])
            expected_checksum = index_info[1]
            expected_count = index_info[2]
            
            # 检查文件是否存在
            if not file_path.exists():
                result["issues"].append("数据文件不存在")
                return result
            
            # 加载数据并验证
            data = self.load_historical_data(symbol, frequency)
            if data is None or data.empty:
                result["issues"].append("数据为空或无法加载")
                return result
            
            # 验证记录数量
            actual_count = len(data)
            if actual_count != expected_count:
                result["issues"].append(f"记录数量不匹配: 期望{expected_count}, 实际{actual_count}")
            
            # 验证日期范围
            actual_start = data['date'].min().strftime('%Y-%m-%d')
            actual_end = data['date'].max().strftime('%Y-%m-%d')
            
            if actual_start != index_info[3] or actual_end != index_info[4]:
                result["issues"].append("日期范围不匹配")
            
            # 验证数据连续性
            expected_days = (pd.to_datetime(actual_end) - pd.to_datetime(actual_start)).days + 1
            if frequency == "daily" and actual_count != expected_days:
                result["issues"].append(f"数据不连续: 期望{expected_days}天, 实际{actual_count}条记录")
            
            if not result["issues"]:
                result["integrity_check"] = "passed"
            
        except Exception as e:
            result["issues"].append(f"验证错误: {str(e)}")
        
        return result
    
    def bulk_save_data(self, data_dict: Dict[str, pd.DataFrame], 
                      frequency: str = "daily", max_workers: int = 4) -> Dict[str, bool]:
        """批量保存数据"""
        results = {}
        
        def save_single(symbol_data):
            symbol, data = symbol_data
            return symbol, self.save_historical_data(symbol, data, frequency)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(save_single, (symbol, data)): symbol
                for symbol, data in data_dict.items()
            }
            
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    symbol, success = future.result()
                    results[symbol] = success
                except Exception as e:
                    logger.error(f"❌ 批量保存失败: {symbol} - {e}")
                    results[symbol] = False
        
        return results
    
    def export_data(self, symbol: str, frequency: str = "daily", 
                   format: str = "csv", output_path: Optional[str] = None) -> bool:
        """导出数据"""
        data = self.load_historical_data(symbol, frequency)
        if data is None or data.empty:
            logger.warning(f"⚠️ 无数据可导出: {symbol}")
            return False
        
        if output_path is None:
            output_path = self.data_dir / "exports" / f"{symbol}_{frequency}.{format}"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format.lower() == "csv":
                data.to_csv(output_path, index=False, encoding='utf-8')
            elif format.lower() == "json":
                data.to_json(output_path, orient='records', indent=2, force_ascii=False)
            elif format.lower() == "excel":
                data.to_excel(output_path, index=False)
            else:
                logger.error(f"❌ 不支持的导出格式: {format}")
                return False
            
            logger.info(f"✅ 导出数据: {symbol} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导出数据失败: {symbol} - {e}")
            return False


# 全局实例
_historical_manager = None


def get_historical_manager(data_dir: str = "./data/historical") -> HistoricalDataManager:
    """获取全局历史数据管理器实例"""
    global _historical_manager
    if _historical_manager is None:
        _historical_manager = HistoricalDataManager(data_dir)
    return _historical_manager