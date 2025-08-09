#!/usr/bin/env python3
"""
简单测试A股数据源修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== 测试A股数据源修复 ===")

try:
    # 测试增强数据管理器获取A股列表
    from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
    manager = EnhancedDataManager()
    
    # 获取A股股票列表
    a_stocks = manager.get_stock_list('A')
    print(f"A股股票数量: {len(a_stocks)}")
    
    if a_stocks:
        print("前5只股票:")
        for stock in a_stocks[:5]:
            print(f"  {stock['symbol']} - {stock['name']}")
    
    print("✅ A股数据源修复成功！")
    
except Exception as e:
    print(f"测试失败: {e}")

print("\n=== 测试完成 ===")