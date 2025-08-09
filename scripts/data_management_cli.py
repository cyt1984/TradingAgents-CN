#!/usr/bin/env python3
"""
数据管理CLI工具
用于管理本地持久化存储的股票数据
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.persistent_storage import get_persistent_manager
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager

logger = get_logger('data_management_cli')


class DataManagementCLI:
    """数据管理CLI工具类"""
    
    def __init__(self):
        self.persistent_manager = get_persistent_manager()
        self.historical_manager = get_historical_manager()
        self.stock_master_manager = get_stock_master_manager()
    
    def show_status(self):
        """显示数据状态"""
        print("📊 数据存储状态")
        print("=" * 50)
        
        # 股票基础信息状态
        stock_summary = self.stock_master_manager.get_market_summary()
        if stock_summary:
            print(f"📈 股票总数: {stock_summary.get('total_stocks', 0)}")
            print(f"🔄 最后更新: {stock_summary.get('last_updated', '未知')}")
            
            markets = stock_summary.get('markets', {})
            if markets:
                print("\n🏛️ 按市场分布:")
                for market, count in markets.items():
                    print(f"   {market}: {count} 只股票")
        
        # 历史数据状态
        for freq in ['daily', 'weekly', 'monthly']:
            summary = self.historical_manager.get_data_summary(freq)
            if summary['total_symbols'] > 0:
                print(f"\n📅 {freq.upper()}历史数据:")
                print(f"   股票数量: {summary['total_symbols']}")
                print(f"   总记录数: {summary['total_records']:,}")
                print(f"   数据范围: {summary['earliest_date']} - {summary['latest_date']}")
        
        # 存储空间统计
        data_dir = Path("./data/persistent")
        if data_dir.exists():
            total_size = 0
            file_count = 0
            
            for category_dir in data_dir.iterdir():
                if category_dir.is_dir():
                    for file in category_dir.rglob("*.parquet"):
                        total_size += file.stat().st_size
                        file_count += 1
            
            print(f"\n💾 存储统计:")
            print(f"   文件总数: {file_count}")
            print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
    
    def list_stocks(self, market: Optional[str] = None, limit: int = 50):
        """列出股票"""
        stock_list = self.stock_master_manager.load_stock_list(market)
        
        if stock_list is None or stock_list.empty:
            print("❌ 无股票数据")
            return
        
        print(f"📋 股票列表 ({len(stock_list)} 只股票)")
        print("=" * 80)
        
        display_df = stock_list[['symbol', 'name', 'industry', 'market']].head(limit)
        print(display_df.to_string(index=False))
        
        if len(stock_list) > limit:
            print(f"\n... 显示前 {limit} 条，共 {len(stock_list)} 只股票")
    
    def search_stocks(self, keyword: str, field: str = "name"):
        """搜索股票"""
        results = self.stock_master_manager.search_stocks(keyword, field)
        
        if results.empty:
            print(f"❌ 未找到包含 '{keyword}' 的股票")
            return
        
        print(f"🔍 搜索结果: '{keyword}' (字段: {field})")
        print("=" * 80)
        print(results[['symbol', 'name', 'industry', 'market']].to_string(index=False))
        print(f"\n找到 {len(results)} 只股票")
    
    def show_stock_info(self, symbol: str):
        """显示股票详细信息"""
        info = self.stock_master_manager.get_stock_info(symbol)
        
        if not info:
            print(f"❌ 未找到股票代码: {symbol}")
            return
        
        print(f"📈 股票详情: {symbol}")
        print("=" * 50)
        
        for key, value in info.items():
            if pd.notna(value) and value not in ['', None]:
                print(f"{key}: {value}")
    
    def check_data_integrity(self, symbol: str):
        """检查数据完整性"""
        print(f"🔍 检查数据完整性: {symbol}")
        print("=" * 50)
        
        # 检查股票基础信息
        stock_info = self.stock_master_manager.get_stock_info(symbol)
        if not stock_info:
            print(f"❌ 股票基础信息缺失: {symbol}")
            return
        
        print("✅ 股票基础信息存在")
        
        # 检查历史数据
        for freq in ['daily', 'weekly', 'monthly']:
            availability = self.historical_manager.get_data_availability(symbol, freq)
            if availability['available']:
                print(f"✅ {freq.upper()}历史数据: {availability['record_count']} 条记录")
                
                # 验证数据完整性
                integrity = self.historical_manager.verify_data_integrity(symbol, freq)
                if integrity['integrity_check'] == 'passed':
                    print(f"   ✅ {freq.upper()}数据完整性验证通过")
                else:
                    print(f"   ❌ {freq.upper()}数据完整性问题:")
                    for issue in integrity['issues']:
                        print(f"      - {issue}")
            else:
                print(f"⚠️ {freq.upper()}历史数据不存在")
    
    def cleanup_expired_data(self, days: int = 30):
        """清理过期数据"""
        print(f"🧹 清理 {days} 天前的过期数据...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        # 清理旧的元数据文件
        data_dir = Path("./data/persistent")
        if data_dir.exists():
            for metadata_file in data_dir.rglob("*_metadata.json"):
                try:
                    file_time = datetime.fromtimestamp(metadata_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        # 检查对应的数据文件是否存在
                        data_file = metadata_file.with_suffix('.parquet')
                        if not data_file.exists():
                            metadata_file.unlink()
                            cleaned_count += 1
                            print(f"✅ 清理孤立元数据: {metadata_file}")
                except Exception as e:
                    print(f"❌ 清理失败: {metadata_file} - {e}")
        
        print(f"🎉 清理完成，共清理 {cleaned_count} 个文件")
    
    def export_data(self, symbol: str, output_path: str, format: str = "csv"):
        """导出数据"""
        print(f"📤 导出数据: {symbol}")
        
        # 导出股票信息
        stock_info = self.stock_master_manager.get_stock_info(symbol)
        if stock_info:
            info_df = pd.DataFrame([stock_info])
            info_file = Path(output_path) / f"{symbol}_info.{format}"
            
            if format == "csv":
                info_df.to_csv(info_file, index=False, encoding='utf-8')
            elif format == "json":
                info_df.to_json(info_file, orient='records', force_ascii=False, indent=2)
            
            print(f"✅ 股票信息已导出: {info_file}")
        
        # 导出历史数据
        for freq in ['daily', 'weekly', 'monthly']:
            data = self.historical_manager.load_historical_data(symbol, freq)
            if data is not None and not data.empty:
                data_file = Path(output_path) / f"{symbol}_{freq}.{format}"
                
                if format == "csv":
                    data.to_csv(data_file, index=False, encoding='utf-8')
                elif format == "json":
                    data.to_json(data_file, orient='records', force_ascii=False, indent=2)
                
                print(f"✅ {freq.upper()}历史数据已导出: {data_file}")
    
    def migrate_from_cache(self, source_dir: str = "./cache"):
        """从缓存迁移数据到持久化存储"""
        print("🔄 从缓存迁移数据到持久化存储...")
        
        cache_dir = Path(source_dir)
        if not cache_dir.exists():
            print(f"❌ 缓存目录不存在: {source_dir}")
            return
        
        migrated_count = 0
        
        # 迁移股票列表数据
        stock_files = list(cache_dir.glob("*stocks*.csv")) + list(cache_dir.glob("*stocks*.json"))
        for stock_file in stock_files:
            try:
                if stock_file.suffix == '.csv':
                    df = pd.read_csv(stock_file)
                elif stock_file.suffix == '.json':
                    df = pd.read_json(stock_file)
                
                if 'symbol' in df.columns and 'name' in df.columns:
                    self.stock_master_manager.save_stock_list(df.to_dict('records'))
                    migrated_count += 1
                    print(f"✅ 迁移股票列表: {stock_file}")
            except Exception as e:
                print(f"❌ 迁移失败: {stock_file} - {e}")
        
        print(f"🎉 迁移完成，共迁移 {migrated_count} 个文件")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradingAgents 数据管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='显示数据状态')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出股票')
    list_parser.add_argument('--market', help='指定市场')
    list_parser.add_argument('--limit', type=int, default=50, help='显示数量限制')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索股票')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--field', default='name', choices=['name', 'symbol', 'industry'], help='搜索字段')
    
    # 详情命令
    info_parser = subparsers.add_parser('info', help='显示股票详情')
    info_parser.add_argument('symbol', help='股票代码')
    
    # 检查命令
    check_parser = subparsers.add_parser('check', help='检查数据完整性')
    check_parser.add_argument('symbol', help='股票代码')
    
    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理过期数据')
    cleanup_parser.add_argument('--days', type=int, default=30, help='清理天数')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('symbol', help='股票代码')
    export_parser.add_argument('--output', default='./exports', help='输出目录')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='导出格式')
    
    # 迁移命令
    migrate_parser = subparsers.add_parser('migrate', help='从缓存迁移数据')
    migrate_parser.add_argument('--source', default='./cache', help='源目录')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = DataManagementCLI()
        
        if args.command == 'status':
            cli.show_status()
        elif args.command == 'list':
            cli.list_stocks(args.market, args.limit)
        elif args.command == 'search':
            cli.search_stocks(args.keyword, args.field)
        elif args.command == 'info':
            cli.show_stock_info(args.symbol)
        elif args.command == 'check':
            cli.check_data_integrity(args.symbol)
        elif args.command == 'cleanup':
            cli.cleanup_expired_data(args.days)
        elif args.command == 'export':
            cli.export_data(args.symbol, args.output, args.format)
        elif args.command == 'migrate':
            cli.migrate_from_cache(args.source)
    
    except KeyboardInterrupt:
        print("\n🛑 操作被用户中断")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()