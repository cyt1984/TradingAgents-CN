#!/usr/bin/env python3
"""
测试StockSelector类型修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== 测试StockSelector类型修复 ===")

try:
    # 测试股票选择器
    from tradingagents.selectors.stock_selector import StockSelector
    selector = StockSelector()
    
    # 测试获取股票列表
    stock_list = selector._get_stock_list()
    print(f"股票列表类型: {type(stock_list)}")
    
    if not stock_list.empty:
        print(f"成功获取股票数量: {len(stock_list)}")
        print(f"列名: {list(stock_list.columns)}")
        print("前3只股票:")
        for i, row in stock_list.head(3).iterrows():
            print(f"  {row.get('ts_code', row.get('symbol', 'N/A'))} - {row.get('name', 'N/A')}")
    else:
        print("警告: 股票列表为空")
        
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")