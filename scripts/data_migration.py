#!/usr/bin/env python3
"""
数据迁移工具
将现有的缓存数据迁移到新的持久化存储系统
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.persistent_storage import get_persistent_manager
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager
from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager

logger = get_logger('data_migration')


class DataMigrationTool:
    """数据迁移工具类"""
    
    def __init__(self):
        self.persistent_manager = get_persistent_manager()
        self.historical_manager = get_historical_manager()
        self.stock_master_manager = get_stock_master_manager()
        self.enhanced_data_manager = EnhancedDataManager()
        
        # 缓存目录路径
        self.cache_dirs = {
            'data_cache': project_root / 'tradingagents' / 'dataflows' / 'data_cache',
            'cache': project_root / 'cache',
            'redis_cache': project_root / 'data' / 'cache'
        }
        
    def discover_cache_files(self) -> Dict[str, List[Path]]:
        """发现所有缓存文件"""
        cache_files = {}
        
        for cache_name, cache_dir in self.cache_dirs.items():
            if cache_dir.exists():
                files = list(cache_dir.rglob("*.csv")) + \
                       list(cache_dir.rglob("*.json")) + \
                       list(cache_dir.rglob("*.pkl")) + \
                       list(cache_dir.rglob("*.parquet"))
                
                cache_files[cache_name] = files
                logger.info(f"📁 发现 {cache_name}: {len(files)} 个文件")
        
        return cache_files
    
    def extract_symbols_from_filename(self, filename: str) -> List[str]:
        """从文件名中提取股票代码"""
        symbols = []
        
        # 常见的股票代码模式
        patterns = [
            r'(\d{6})',  # 6位数字 (A股)
            r'(\d{4}\.HK)',  # 港股
            r'(\w+)-',  # 美股模式
            r'([A-Z]{1,5})',  # 美股代码
        ]
        
        import re
        
        # 尝试匹配6位数字
        matches = re.findall(r'\d{6}', filename)
        symbols.extend(matches)
        
        # 尝试匹配港股
        matches = re.findall(r'\d{4}\.HK', filename)
        symbols.extend(matches)
        
        # 尝试匹配美股
        matches = re.findall(r'([A-Z]{1,5})[^a-zA-Z0-9]', filename.upper())
        symbols.extend(matches)
        
        return list(set(symbols))  # 去重
    
    def migrate_stock_list(self) -> int:
        """迁移股票列表数据"""
        logger.info("🔄 开始迁移股票列表数据...")
        
        migrated_count = 0
        cache_files = self.discover_cache_files()
        
        stock_data = []
        
        # 从各个缓存目录收集股票信息
        for cache_name, files in cache_files.items():
            for file_path in files:
                try:
                    symbols = self.extract_symbols_from_filename(file_path.name)
                    
                    for symbol in symbols:
                        # 获取股票详细信息
                        stock_info = self._get_stock_info_from_cache(symbol, file_path)
                        if stock_info:
                            stock_data.append(stock_info)
                        else:
                            # 创建基础信息
                            stock_data.append({
                                'symbol': symbol,
                                'name': f'股票{symbol}',
                                'market': self._guess_market(symbol),
                                'source': 'migration'
                            })
                
                except Exception as e:
                    logger.error(f"❌ 处理文件失败: {file_path} - {e}")
        
        if stock_data:
            # 去重
            unique_stocks = {}
            for stock in stock_data:
                symbol = stock['symbol']
                if symbol not in unique_stocks:
                    unique_stocks[symbol] = stock
            
            stock_list = list(unique_stocks.values())
            self.stock_master_manager.save_stock_list(stock_list)
            migrated_count = len(stock_list)
            logger.info(f"✅ 迁移股票列表完成: {migrated_count} 只股票")
        
        return migrated_count
    
    def _get_stock_info_from_cache(self, symbol: str, file_path: Path) -> Optional[Dict[str, Any]]:
        """从缓存文件中提取股票信息"""
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path, nrows=1)
                if 'name' in df.columns:
                    return {
                        'symbol': symbol,
                        'name': df['name'].iloc[0] if not pd.isna(df['name'].iloc[0]) else f'股票{symbol}'
                    }
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return data[0]
        except Exception:
            pass
        
        return None
    
    def _guess_market(self, symbol: str) -> str:
        """猜测股票所属市场"""
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('6', '5')):
                return 'A股'
            elif symbol.startswith(('0', '3', '2')):
                return 'A股'
        elif symbol.endswith('.HK'):
            return '港股'
        elif symbol.isalpha() and len(symbol) <= 5:
            return '美股'
        
        return '未知'
    
    def migrate_historical_data(self) -> int:
        """迁移历史价格数据"""
        logger.info("🔄 开始迁移历史价格数据...")
        
        migrated_count = 0
        cache_files = self.discover_cache_files()
        
        for cache_name, files in cache_files.items():
            for file_path in files:
                try:
                    # 提取股票代码
                    symbols = self.extract_symbols_from_filename(file_path.name)
                    
                    for symbol in symbols:
                        # 尝试加载价格数据
                        price_data = self._load_price_data(file_path, symbol)
                        if price_data is not None and not price_data.empty:
                            # 确定数据频率
                            frequency = self._detect_frequency(price_data)
                            
                            # 保存到持久化存储
                            self.historical_manager.save_historical_data(
                                symbol, price_data, frequency
                            )
                            migrated_count += 1
                            logger.info(f"✅ 迁移历史数据: {symbol} ({frequency})")
                
                except Exception as e:
                    logger.error(f"❌ 迁移历史数据失败: {file_path} - {e}")
        
        logger.info(f"✅ 迁移历史数据完成: {migrated_count} 个文件")
        return migrated_count
    
    def _load_price_data(self, file_path: Path, symbol: str) -> Optional[pd.DataFrame]:
        """加载价格数据"""
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
                if 'date' in df.columns or 'Date' in df.columns:
                    return df
            elif file_path.suffix == '.json':
                df = pd.read_json(file_path)
                if 'date' in df.columns or 'Date' in df.columns:
                    return df
            elif file_path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
                if 'date' in df.columns or 'Date' in df.columns:
                    return df
        except Exception as e:
            logger.debug(f"无法加载价格数据: {file_path} - {e}")
        
        return None
    
    def _detect_frequency(self, df: pd.DataFrame) -> str:
        """检测数据频率"""
        try:
            date_col = 'date' if 'date' in df.columns else 'Date'
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            
            # 计算日期间隔
            intervals = df[date_col].diff().dt.days.dropna()
            avg_interval = intervals.mean()
            
            if avg_interval <= 2:
                return 'daily'
            elif avg_interval <= 8:
                return 'weekly'
            else:
                return 'monthly'
        except Exception:
            return 'daily'
    
    def migrate_financial_data(self) -> int:
        """迁移财务数据"""
        logger.info("🔄 开始迁移财务数据...")
        
        migrated_count = 0
        cache_files = self.discover_cache_files()
        
        for cache_name, files in cache_files.items():
            for file_path in files:
                if 'financial' in str(file_path).lower() or 'fundamental' in str(file_path).lower():
                    try:
                        symbols = self.extract_symbols_from_filename(file_path.name)
                        
                        for symbol in symbols:
                            financial_data = self._load_financial_data(file_path)
                            if financial_data is not None and not financial_data.empty:
                                # 确定报告类型
                                report_type = 'quarterly' if 'quarter' in str(file_path).lower() else 'annual'
                                
                                self.persistent_manager.save_financial_data(
                                    symbol, financial_data, report_type
                                )
                                migrated_count += 1
                                logger.info(f"✅ 迁移财务数据: {symbol} ({report_type})")
                    
                    except Exception as e:
                        logger.error(f"❌ 迁移财务数据失败: {file_path} - {e}")
        
        logger.info(f"✅ 迁移财务数据完成: {migrated_count} 个文件")
        return migrated_count
    
    def _load_financial_data(self, file_path: Path) -> Optional[pd.DataFrame]:
        """加载财务数据"""
        try:
            if file_path.suffix == '.csv':
                return pd.read_csv(file_path)
            elif file_path.suffix == '.json':
                return pd.read_json(file_path)
            elif file_path.suffix == '.parquet':
                return pd.read_parquet(file_path)
        except Exception as e:
            logger.debug(f"无法加载财务数据: {file_path} - {e}")
        
        return None
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """生成迁移报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_directories': {},
            'migration_summary': {},
            'errors': []
        }
        
        # 统计源目录
        cache_files = self.discover_cache_files()
        for cache_name, files in cache_files.items():
            total_size = sum(f.stat().st_size for f in files if f.exists())
            report['source_directories'][cache_name] = {
                'file_count': len(files),
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
        
        # 统计迁移后的数据
        report['migration_summary'] = {
            'stock_list_count': self.stock_master_manager.get_market_summary().get('total_stocks', 0),
            'historical_daily': self.historical_manager.get_data_summary('daily')['total_symbols'],
            'historical_weekly': self.historical_manager.get_data_summary('weekly')['total_symbols'],
            'historical_monthly': self.historical_manager.get_data_summary('monthly')['total_symbols']
        }
        
        return report
    
    def run_full_migration(self) -> Dict[str, int]:
        """运行完整迁移"""
        logger.info("🚀 开始完整数据迁移...")
        
        results = {
            'stock_list': 0,
            'historical': 0,
            'financial': 0,
            'errors': 0
        }
        
        try:
            results['stock_list'] = self.migrate_stock_list()
            results['historical'] = self.migrate_historical_data()
            results['financial'] = self.migrate_financial_data()
            
            # 生成报告
            report = self.generate_migration_report()
            report_path = Path("./data/persistent") / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 迁移完成，报告已保存: {report_path}")
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            results['errors'] += 1
        
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradingAgents 数据迁移工具")
    parser.add_argument('--type', choices=['full', 'stocks', 'historical', 'financial'], 
                       default='full', help='迁移类型')
    parser.add_argument('--source', default='./cache', help='源目录')
    parser.add_argument('--report', action='store_true', help='只生成报告')
    
    args = parser.parse_args()
    
    try:
        migration_tool = DataMigrationTool()
        
        if args.report:
            report = migration_tool.generate_migration_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return
        
        if args.type == 'full':
            results = migration_tool.run_full_migration()
        elif args.type == 'stocks':
            results = {'stock_list': migration_tool.migrate_stock_list()}
        elif args.type == 'historical':
            results = {'historical': migration_tool.migrate_historical_data()}
        elif args.type == 'financial':
            results = {'financial': migration_tool.migrate_financial_data()}
        
        print("🎉 迁移结果:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    
    except KeyboardInterrupt:
        print("\n🛑 迁移被用户中断")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()