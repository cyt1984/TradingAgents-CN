#!/usr/bin/env python3
"""
本地数据持久化存储系统
提供永久性的股票数据本地存储功能
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pickle
import gzip
import hashlib
from dataclasses import dataclass

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('persistent_storage')


@dataclass
class DataVersion:
    """数据版本信息"""
    version: str
    created_at: datetime
    updated_at: datetime
    checksum: str
    data_size: int


class PersistentDataManager:
    """持久化数据管理器"""
    
    def __init__(self, data_dir: str = "./data/persistent"):
        """
        初始化持久化数据管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self._ensure_directories()
        
        # 数据分类存储路径
        self.stocks_dir = self.data_dir / "stocks"
        self.historical_dir = self.data_dir / "historical"
        self.financial_dir = self.data_dir / "financial"
        self.macro_dir = self.data_dir / "macro"
        self.technical_dir = self.data_dir / "technical"
        self.news_dir = self.data_dir / "news"
        
        logger.info("🗂️ 持久化数据管理器初始化完成")
        logger.info(f"📁 数据目录: {self.data_dir}")
    
    def _ensure_directories(self):
        """确保所有目录存在"""
        directories = [
            self.data_dir,
            self.data_dir / "stocks",
            self.data_dir / "historical" / "daily",
            self.data_dir / "historical" / "weekly",
            self.data_dir / "historical" / "monthly",
            self.data_dir / "financial" / "quarterly",
            self.data_dir / "financial" / "annual",
            self.data_dir / "macro" / "indices",
            self.data_dir / "macro" / "economic",
            self.data_dir / "technical" / "indicators",
            self.data_dir / "news" / "announcements",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, category: str, symbol: str, data_type: str, 
                      date_range: Optional[str] = None) -> Path:
        """获取文件存储路径"""
        base_dir = self.data_dir / category
        
        if category == "stocks":
            return base_dir / f"{symbol}_{data_type}.parquet"
        elif category == "historical":
            return base_dir / data_type / f"{symbol}.parquet"
        elif category == "financial":
            return base_dir / data_type / f"{symbol}.parquet"
        else:
            return base_dir / f"{symbol}_{data_type}.parquet"
    
    def _calculate_checksum(self, data: pd.DataFrame) -> str:
        """计算数据校验和"""
        if data.empty:
            return ""
        data_str = data.to_string()
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def save_stock_master(self, stock_data: pd.DataFrame):
        """保存股票基础信息"""
        file_path = self.data_dir / "stocks" / "master_data.parquet"
        stock_data.to_parquet(file_path, compression='snappy')
        
        # 保存元数据
        metadata = {
            "updated_at": datetime.now().isoformat(),
            "record_count": len(stock_data),
            "checksum": self._calculate_checksum(stock_data)
        }
        
        metadata_path = self.data_dir / "stocks" / "master_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 保存股票基础信息: {len(stock_data)} 条记录")
    
    def load_stock_master(self) -> Optional[pd.DataFrame]:
        """加载股票基础信息"""
        file_path = self.data_dir / "stocks" / "master_data.parquet"
        if file_path.exists():
            return pd.read_parquet(file_path)
        return None
    
    def save_historical_prices(self, symbol: str, data: pd.DataFrame, 
                             frequency: str = "daily"):
        """保存历史价格数据"""
        if data.empty:
            return
            
        file_path = self._get_file_path("historical", symbol, frequency)
        
        # 确保数据按日期排序
        if 'date' in data.columns:
            data = data.sort_values('date')
        
        # 保存数据
        data.to_parquet(file_path, compression='snappy')
        
        # 保存元数据
        metadata = {
            "symbol": symbol,
            "frequency": frequency,
            "updated_at": datetime.now().isoformat(),
            "date_range": {
                "start": data['date'].min() if 'date' in data.columns else None,
                "end": data['date'].max() if 'date' in data.columns else None
            },
            "record_count": len(data),
            "checksum": self._calculate_checksum(data)
        }
        
        metadata_path = file_path.parent / f"{symbol}_{frequency}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 保存历史价格数据: {symbol} ({frequency}) - {len(data)} 条记录")
    
    def load_historical_prices(self, symbol: str, frequency: str = "daily",
                             start_date: Optional[str] = None, 
                             end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """加载历史价格数据"""
        file_path = self._get_file_path("historical", symbol, frequency)
        
        if not file_path.exists():
            return None
        
        try:
            data = pd.read_parquet(file_path)
            
            if 'date' in data.columns and (start_date or end_date):
                data['date'] = pd.to_datetime(data['date'])
                
                if start_date:
                    data = data[data['date'] >= pd.to_datetime(start_date)]
                if end_date:
                    data = data[data['date'] <= pd.to_datetime(end_date)]
            
            return data
        except Exception as e:
            logger.error(f"❌ 加载历史价格数据失败: {symbol} - {e}")
            return None
    
    def save_financial_data(self, symbol: str, data: pd.DataFrame, 
                          report_type: str = "quarterly"):
        """保存财务数据"""
        if data.empty:
            return
            
        file_path = self._get_file_path("financial", symbol, report_type)
        data.to_parquet(file_path, compression='snappy')
        
        metadata = {
            "symbol": symbol,
            "report_type": report_type,
            "updated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "checksum": self._calculate_checksum(data)
        }
        
        metadata_path = file_path.parent / f"{symbol}_{report_type}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 保存财务数据: {symbol} ({report_type}) - {len(data)} 条记录")
    
    def load_financial_data(self, symbol: str, 
                          report_type: str = "quarterly") -> Optional[pd.DataFrame]:
        """加载财务数据"""
        file_path = self._get_file_path("financial", symbol, report_type)
        
        if not file_path.exists():
            return None
        
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.error(f"❌ 加载财务数据失败: {symbol} - {e}")
            return None
    
    def get_available_symbols(self, category: str = "historical", 
                            frequency: str = "daily") -> List[str]:
        """获取可用的股票代码列表"""
        if category == "historical":
            directory = self.historical_dir / frequency
        elif category == "financial":
            directory = self.financial_dir / frequency
        else:
            directory = self.data_dir / category
        
        if not directory.exists():
            return []
        
        files = directory.glob("*.parquet")
        return [f.stem for f in files]
    
    def get_data_status(self, symbol: str, category: str, 
                       data_type: str) -> Dict[str, Any]:
        """获取数据状态信息"""
        file_path = self._get_file_path(category, symbol, data_type)
        metadata_path = file_path.parent / f"{symbol}_{data_type}_metadata.json"
        
        status = {
            "exists": file_path.exists(),
            "file_path": str(file_path),
            "file_size": 0,
            "last_updated": None,
            "record_count": 0,
            "date_range": None
        }
        
        if file_path.exists():
            status["file_size"] = file_path.stat().st_size
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        status.update(metadata)
                except Exception as e:
                    logger.warning(f"⚠️ 读取元数据失败: {e}")
        
        return status
    
    def cleanup_old_metadata(self):
        """清理旧的元数据文件"""
        for category_dir in [self.historical_dir, self.financial_dir]:
            for freq_dir in category_dir.iterdir():
                if freq_dir.is_dir():
                    for metadata_file in freq_dir.glob("*_metadata.json"):
                        symbol = metadata_file.stem.replace("_daily_metadata", "").replace("_quarterly_metadata", "").replace("_annual_metadata", "")
                        data_file = freq_dir / f"{symbol}.parquet"
                        
                        if not data_file.exists():
                            metadata_file.unlink()
                            logger.info(f"🧹 清理孤立元数据: {metadata_file}")


# 全局实例
_persistent_manager = None


def get_persistent_manager(data_dir: str = "./data/persistent") -> PersistentDataManager:
    """获取全局持久化数据管理器实例"""
    global _persistent_manager
    if _persistent_manager is None:
        _persistent_manager = PersistentDataManager(data_dir)
    return _persistent_manager