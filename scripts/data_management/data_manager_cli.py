#!/usr/bin/env python3
"""
数据管理CLI工具
用于管理本地持久化存储的股票数据
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.persistent_storage import get_persistent_manager
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager

logger = get_logger('data_manager_cli')

class DataManagerCLI:
    """数据管理CLI工具类"""
    
    def __init__(self):
        self.persistent_manager = get_persistent_manager()
        self.historical_manager = get_historical_manager()
        self.stock_master_manager = get_stock_master_manager()
    
    def show_status(self):
        """显示数据存储状态"""
        print("📊 数据存储状态报告")
        print("=" * 50)
        
        # 股票基础信息状态
        stock_summary = self.stock_master_manager.get_market_summary()
        print(f"📈 股票基础信息:")
        print(f"   总股票数: {stock_summary.get('total_stocks', 0)}")
        print(f"   最后更新: {stock_summary.get('last_updated', '未知')}")
        print(f"   市场分布: {stock_summary.get('markets', {})}")
        
        # 历史数据状态
        for freq in ["daily", "weekly", "monthly"]:
            summary = self.historical_manager.get_data_summary(freq)
            print(f"📊 {freq.upper()}历史数据:")
            print(f"   股票数: {summary.get('total_symbols', 0)}")
            print(f"   记录数: {summary.get('total_records', 0)}")
            print(f"   最早日期: {summary.get('earliest_date', '未知')}")
            print(f"   最新日期: {summary.get('latest_date', '未知')}")
        
        # 存储空间统计
        data_dir = Path("./data/persistent")
        if data_dir.exists():
            total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            print(f"💾 存储空间: {total_size / 1024 / 1024:.2f} MB")
    
    def list_stocks(self, market: Optional[str] = None, limit: int = 50):
        """列出股票信息"""
        stocks = self.stock_master_manager.load_stock_list(market)
        if stocks is None or stocks.empty:
            print("⚠️ 没有找到股票信息")
            return
        
        print(f"📋 股票列表 ({len(stocks)} 只股票)")
        print("-" * 80)
        
        display_cols = ['symbol', 'name', 'industry', 'market', 'list_date']
        available_cols = [col for col in display_cols if col in stocks.columns]
        
        display_df = stocks[available_cols].head(limit)
        print(display_df.to_string(index=False))
    
    def search_stocks(self, keyword: str, field: str = "name"):
        """搜索股票"""
        results = self.stock_master_manager.search_stocks(keyword, field)
        if results.empty:
            print(f"🔍 没有找到包含 '{keyword}' 的股票")
            return
        
        print(f"🔍 搜索结果: 找到 {len(results)} 只股票")
        print("-" * 80)
        
        display_cols = ['symbol', 'name', 'industry', 'market']
        available_cols = [col for col in display_cols if col in results.columns]
        
        print(results[available_cols].to_string(index=False))
    
    def check_data_availability(self, symbol: str, frequency: str = "daily"):
        """检查数据可用性"""
        availability = self.historical_manager.get_data_availability(symbol, frequency)
        
        print(f"📈 {symbol} 数据可用性 ({frequency})")
        print("-" * 30)
        
        if availability["available"]:
            print(f"✅ 数据可用")
            print(f"   日期范围: {availability['start_date']} 至 {availability['end_date']}")
            print(f"   记录数量: {availability['record_count']}")
            print(f"   最后更新: {availability['last_updated']}")
        else:
            print("❌ 数据不可用")
    
    def export_stock_list(self, market: Optional[str] = None, 
                         format: str = "csv", output_path: Optional[str] = None):
        """导出股票列表"""
        output_file = self.stock_master_manager.export_stock_list(
            market=market, format=format, output_path=output_path
        )
        
        if output_file:
            print(f"✅ 股票列表已导出到: {output_file}")
        else:
            print("❌ 导出失败")
    
    def validate_data(self, symbol: str, frequency: str = "daily"):
        """验证数据完整性"""
        result = self.historical_manager.verify_data_integrity(symbol, frequency)
        
        print(f"🔍 {symbol} 数据验证报告 ({frequency})")
        print("-" * 30)
        print(f"验证结果: {result['integrity_check']}")
        
        if result['issues']:
            print("发现的问题:")
            for issue in result['issues']:
                print(f"  - {issue}")
        else:
            print("✅ 数据完整性验证通过")
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        print(f"🧹 清理 {days} 天前的数据...")
        
        # 清理元数据文件
        metadata_files = list(Path("./data/persistent").rglob("*_metadata.json"))
        cleaned_count = 0
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = pd.json.loads(f.read())
                    
                updated_at = pd.to_datetime(metadata.get('updated_at', ''))
                if updated_at < cutoff_date:
                    # 删除对应的parquet文件
                    parquet_file = metadata_file.with_suffix('.parquet')
                    if parquet_file.exists():
                        parquet_file.unlink()
                    metadata_file.unlink()
                    cleaned_count += 1
                    
            except Exception as e:
                logger.warning(f"清理失败: {metadata_file} - {e}")
        
        print(f"✅ 清理完成，删除了 {cleaned_count} 个旧数据文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradingAgents 数据管理工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='显示数据存储状态')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出股票信息')
    list_parser.add_argument('--market', help='市场类型 (A股/美股/港股)')
    list_parser.add_argument('--limit', type=int, default=50, help='显示数量限制')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索股票')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--field', default='name', 
                              choices=['name', 'symbol', 'industry'], 
                              help='搜索字段')
    
    # 检查命令
    check_parser = subparsers.add_parser('check', help='检查数据可用性')
    check_parser.add_argument('symbol', help='股票代码')
    check_parser.add_argument('--frequency', default='daily', 
                             choices=['daily', 'weekly', 'monthly'],
                             help='数据频率')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出股票列表')
    export_parser.add_argument('--market', help='市场类型')
    export_parser.add_argument('--format', default='csv', 
                              choices=['csv', 'xlsx', 'json'],
                              help='导出格式')
    export_parser.add_argument('--output', help='输出文件路径')
    
    # 验证命令
    validate_parser = subparsers.add_parser('validate', help='验证数据完整性')
    validate_parser.add_argument('symbol', help='股票代码')
    validate_parser.add_argument('--frequency', default='daily',
                                choices=['daily', 'weekly', 'monthly'],
                                help='数据频率')
    
    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧数据')
    cleanup_parser.add_argument('--days', type=int, default=30,
                               help='清理多少天前的数据')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = DataManagerCLI()
        
        if args.command == 'status':
            cli.show_status()
        elif args.command == 'list':
            cli.list_stocks(args.market, args.limit)
        elif args.command == 'search':
            cli.search_stocks(args.keyword, args.field)
        elif args.command == 'check':
            cli.check_data_availability(args.symbol, args.frequency)
        elif args.command == 'export':
            cli.export_stock_list(args.market, args.format, args.output)
        elif args.command == 'validate':
            cli.validate_data(args.symbol, args.frequency)
        elif args.command == 'cleanup':
            cli.cleanup_old_data(args.days)
            
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    main()