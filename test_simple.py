#!/usr/bin/env python3
"""
简单测试A股数据源修复 - 无Unicode版本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== Testing A-share Data Source Fix ===")

try:
    # 测试增强数据管理器获取A股列表
    from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
    manager = EnhancedDataManager()
    
    # 获取A股股票列表
    a_stocks = manager.get_stock_list('A')
    print(f"A-share stock count: {len(a_stocks)}")
    
    if a_stocks:
        print("First 3 stocks:")
        for stock in a_stocks[:3]:
            print(f"  {stock['symbol']} - {stock['name']}")
    
    print("SUCCESS: A-share data source fix verified!")
    
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing Stock Selector ===")

try:
    # 测试股票选择器
    from tradingagents.selectors.stock_selector import StockSelector
    selector = StockSelector()
    
    # 测试获取股票列表
    stock_list = selector._get_stock_list()
    if not stock_list.empty:
        print(f"Stock selector count: {len(stock_list)}")
        print(f"Columns: {list(stock_list.columns)}")
        print("Sample data:")
        for i, row in stock_list.head(3).iterrows():
            print(f"  {row.to_dict()}")
    else:
        print("Warning: Stock selector returned empty list")
        
except Exception as e:
    print(f"Stock selector test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")