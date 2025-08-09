#!/usr/bin/env python3
"""
股票基础信息存储管理器
管理股票的基础信息、公司资料、行业分类等静态数据
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from tradingagents.utils.logging_manager import get_logger
from .persistent_storage import get_persistent_manager

logger = get_logger('stock_master')


class StockMasterManager:
    """股票基础信息管理器"""
    
    def __init__(self, data_dir: str = "./data/persistent"):
        """
        初始化股票基础信息管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.persistent_manager = get_persistent_manager(data_dir)
        
        # 定义基础信息字段
        self.master_columns = [
            'symbol', 'name', 'fullname', 'industry', 'sector',
            'market', 'exchange', 'list_date', 'delist_date',
            'total_shares', 'float_shares', 'area', 'province',
            'city', 'business_scope', 'chairman', 'manager',
            'reg_capital', 'employees', 'phone', 'website',
            'email', 'address', 'introduction', 'updated_at'
        ]
        
        logger.info("📋 股票基础信息管理器初始化完成")
    
    def save_stock_list(self, stock_list: List[Dict[str, Any]]):
        """
        保存股票列表
        
        Args:
            stock_list: 股票信息列表
        """
        if not stock_list:
            logger.warning("⚠️ 股票列表为空")
            return
        
        # 转换为DataFrame并标准化格式
        df = pd.DataFrame(stock_list)
        
        # 确保所有必需字段存在
        for col in ['symbol', 'name']:
            if col not in df.columns:
                logger.error(f"❌ 缺少必需字段: {col}")
                return
        
        # 标准化字段名称
        column_mapping = {
            'ts_code': 'symbol',
            'ts_name': 'name',
            'ts_fullname': 'fullname',
            'industry': 'industry',
            'sector': 'sector',
            'market': 'market',
            'exchange': 'exchange',
            'list_date': 'list_date',
            'delist_date': 'delist_date',
            'total_share': 'total_shares',
            'float_share': 'float_shares',
            'area': 'area',
            'province': 'province',
            'city': 'city',
            'chairman': 'chairman',
            'manager': 'manager',
            'reg_capital': 'reg_capital',
            'employees': 'employees',
            'phone': 'phone',
            'website': 'website',
            'email': 'email',
            'address': 'address',
            'introduction': 'introduction'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 确保所有标准字段存在
        for col in self.master_columns:
            if col not in df.columns:
                df[col] = None
        
        # 添加更新时间
        df['updated_at'] = datetime.now().isoformat()
        
        # 保存数据
        self.persistent_manager.save_stock_master(df)
        
        # 按市场分类保存
        self._save_by_market(df)
        
        logger.info(f"✅ 保存股票列表: {len(df)} 只股票")
    
    def _save_by_market(self, df: pd.DataFrame):
        """按市场分类保存"""
        markets = df['market'].unique() if 'market' in df.columns else ['unknown']
        
        for market in markets:
            if pd.isna(market):
                market = 'unknown'
                
            market_data = df[df['market'] == market] if market != 'unknown' else df
            
            if not market_data.empty:
                file_path = self.persistent_manager.data_dir / "stocks" / f"{market}_stocks.parquet"
                market_data.to_parquet(file_path, compression='snappy')
                
                logger.info(f"📊 保存{market}市场股票: {len(market_data)} 只")
    
    def load_stock_list(self, market: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        加载股票列表
        
        Args:
            market: 市场类型 (可选)
            
        Returns:
            DataFrame: 股票列表
        """
        if market:
            file_path = self.persistent_manager.data_dir / "stocks" / f"{market}_stocks.parquet"
            if file_path.exists():
                return pd.read_parquet(file_path)
        
        return self.persistent_manager.load_stock_master()
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票详细信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 股票详细信息
        """
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty:
            return None
        
        stock_info = stock_list[stock_list['symbol'] == symbol]
        
        if stock_info.empty:
            return None
        
        return stock_info.iloc[0].to_dict()
    
    def search_stocks(self, keyword: str, field: str = "name") -> pd.DataFrame:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            field: 搜索字段 (name/fullname/industry)
            
        Returns:
            DataFrame: 搜索结果
        """
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty:
            return pd.DataFrame()
        
        if field not in stock_list.columns:
            return pd.DataFrame()
        
        # 模糊搜索
        mask = stock_list[field].astype(str).str.contains(keyword, na=False, case=False)
        return stock_list[mask]
    
    def get_stocks_by_industry(self, industry: str) -> pd.DataFrame:
        """按行业获取股票列表"""
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty or 'industry' not in stock_list.columns:
            return pd.DataFrame()
        
        return stock_list[stock_list['industry'] == industry]
    
    def get_stocks_by_sector(self, sector: str) -> pd.DataFrame:
        """按板块获取股票列表"""
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty or 'sector' not in stock_list.columns:
            return pd.DataFrame()
        
        return stock_list[stock_list['sector'] == sector]
    
    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场汇总信息"""
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty:
            return {}
        
        summary = {
            "total_stocks": len(stock_list),
            "last_updated": None,
            "markets": {},
            "industries": {},
            "sectors": {}
        }
        
        # 获取最后更新时间
        metadata_path = self.persistent_manager.data_dir / "stocks" / "master_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    summary["last_updated"] = metadata.get("updated_at")
            except Exception:
                pass
        
        # 按市场统计
        if 'market' in stock_list.columns:
            summary["markets"] = stock_list['market'].value_counts().to_dict()
        
        # 按行业统计
        if 'industry' in stock_list.columns:
            summary["industries"] = stock_list['industry'].value_counts().to_dict()
        
        # 按板块统计
        if 'sector' in stock_list.columns:
            summary["sectors"] = stock_list['sector'].value_counts().to_dict()
        
        return summary
    
    def validate_stock_data(self) -> Dict[str, Any]:
        """验证股票数据完整性"""
        stock_list = self.load_stock_list()
        
        if stock_list is None or stock_list.empty:
            return {"valid": False, "error": "无数据"}
        
        validation_result = {
            "valid": True,
            "total_stocks": len(stock_list),
            "missing_symbols": 0,
            "missing_names": 0,
            "duplicate_symbols": 0,
            "issues": []
        }
        
        # 检查必需字段
        required_fields = ['symbol', 'name']
        for field in required_fields:
            if field not in stock_list.columns:
                validation_result["issues"].append(f"缺少字段: {field}")
                validation_result["valid"] = False
                continue
            
            missing_count = stock_list[field].isna().sum()
            if missing_count > 0:
                validation_result[f"missing_{field}s"] = missing_count
                validation_result["issues"].append(f"缺失{field}: {missing_count} 条")
        
        # 检查重复代码
        if 'symbol' in stock_list.columns:
            duplicate_symbols = stock_list[stock_list.duplicated(subset=['symbol'])]
            validation_result["duplicate_symbols"] = len(duplicate_symbols)
            if len(duplicate_symbols) > 0:
                validation_result["issues"].append(f"重复股票代码: {len(duplicate_symbols)} 个")
        
        return validation_result
    
    def export_stock_list(self, market: Optional[str] = None, 
                         format: str = "csv", output_path: Optional[str] = None) -> str:
        """
        导出股票列表
        
        Args:
            market: 市场类型
            format: 导出格式
            output_path: 输出路径
            
        Returns:
            导出文件路径
        """
        stock_list = self.load_stock_list(market)
        
        if stock_list is None or stock_list.empty:
            logger.warning("⚠️ 无数据可导出")
            return ""
        
        if output_path is None:
            filename = f"stocks_{market or 'all'}.{format}" if market else f"stocks_all.{format}"
            output_path = self.persistent_manager.data_dir / "exports" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path = Path(output_path)
        
        if format.lower() == "csv":
            stock_list.to_csv(output_path, index=False, encoding='utf-8')
        elif format.lower() == "xlsx":
            stock_list.to_excel(output_path, index=False)
        elif format.lower() == "json":
            stock_list.to_json(output_path, orient='records', force_ascii=False, indent=2)
        
        logger.info(f"📤 导出股票列表: {len(stock_list)} 只股票 - {output_path}")
        return str(output_path)


# 全局实例
_stock_master_manager = None


def get_stock_master_manager(data_dir: str = "./data/persistent") -> StockMasterManager:
    """获取全局股票基础信息管理器实例"""
    global _stock_master_manager
    if _stock_master_manager is None:
        _stock_master_manager = StockMasterManager(data_dir)
    return _stock_master_manager


def save_stock_list(stock_list: List[Dict[str, Any]]):
    """便捷函数：保存股票列表"""
    return get_stock_master_manager().save_stock_list(stock_list)


def load_stock_list(market: Optional[str] = None) -> Optional[pd.DataFrame]:
    """便捷函数：加载股票列表"""
    return get_stock_master_manager().load_stock_list(market)


def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取单只股票信息"""
    return get_stock_master_manager().get_stock_info(symbol)


def search_stocks(keyword: str, field: str = "name") -> pd.DataFrame:
    """便捷函数：搜索股票"""
    return get_stock_master_manager().search_stocks(keyword, field)


def get_market_summary() -> Dict[str, Any]:
    """便捷函数：获取市场汇总信息"""
    return get_stock_master_manager().get_market_summary()


if __name__ == "__main__":
    # 测试功能
    manager = get_stock_master_manager()
    
    # 创建测试数据
    test_data = [
        {
            "symbol": "000001",
            "name": "平安银行",
            "fullname": "平安银行股份有限公司",
            "industry": "银行",
            "sector": "金融",
            "market": "A股",
            "exchange": "SZSE",
            "list_date": "1991-04-03"
        },
        {
            "symbol": "600519",
            "name": "贵州茅台",
            "fullname": "贵州茅台酒股份有限公司",
            "industry": "酿酒",
            "sector": "消费",
            "market": "A股",
            "exchange": "SSE",
            "list_date": "2001-08-27"
        }
    ]
    
    # 保存测试数据
    save_stock_list(test_data)
    
    # 加载测试数据
    loaded_data = load_stock_list()
    if loaded_data is not None:
        print(f"测试成功: 保存并加载了 {len(loaded_data)} 只股票")
        print(get_market_summary())
        print(get_stock_info("000001"))
    else:
        print("测试失败: 无法加载数据")