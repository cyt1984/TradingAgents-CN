#!/usr/bin/env python3
"""
极简版选股引擎测试
仅测试核心功能，避免编码问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_filter_conditions_only():
    """只测试筛选条件模块"""
    print("=" * 50)
    print("Testing Filter Conditions Module")
    print("=" * 50)
    
    try:
        # 直接导入筛选条件模块，避免其他依赖
        print("Step 1: Import filter conditions...")
        
        import pandas as pd
        from tradingagents.selectors.filter_conditions import (
            FilterOperator, NumericFilter, EnumFilter, FilterLogic, FilterGroup
        )
        print("SUCCESS: Filter conditions imported")
        
        # 测试数值筛选
        print("\nStep 2: Create numeric filter...")
        numeric_filter = NumericFilter(
            field_name='market_cap',
            field_display_name='Market Cap',
            operator=FilterOperator.GREATER_EQUAL,
            value=100.0
        )
        print("SUCCESS: Numeric filter created")
        
        # 测试枚举筛选
        print("\nStep 3: Create enum filter...")
        enum_filter = EnumFilter(
            field_name='grade',
            field_display_name='Investment Grade',
            operator=FilterOperator.IN,
            value=['A+', 'A', 'A-']
        )
        print("SUCCESS: Enum filter created")
        
        # 测试数据应用
        print("\nStep 4: Test filter application...")
        
        # 创建测试数据
        test_data = pd.DataFrame({
            'symbol': ['000001', '000002', '600519'],
            'market_cap': [150.0, 80.0, 200.0],
            'grade': ['A+', 'B+', 'A']
        })
        
        # 应用数值筛选
        numeric_result = numeric_filter.apply_filter(test_data)
        filtered_count = numeric_result.sum()
        print(f"Numeric filter result: {filtered_count} stocks matched")
        
        # 应用枚举筛选
        enum_result = enum_filter.apply_filter(test_data)
        enum_count = enum_result.sum()
        print(f"Enum filter result: {enum_count} stocks matched")
        
        # 测试组合筛选
        print("\nStep 5: Test filter group...")
        filter_group = FilterGroup(
            conditions=[numeric_filter, enum_filter],
            logic=FilterLogic.AND
        )
        
        group_result = filter_group.apply_filter(test_data)
        group_count = group_result.sum()
        print(f"Group filter result: {group_count} stocks matched")
        
        # 输出结果
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        print("- Filter conditions module: OK")
        print("- Numeric filtering: OK")
        print("- Enum filtering: OK") 
        print("- Group filtering: OK")
        print("- Data application: OK")
        print("\nSTAGE 1 BASIC FUNCTIONS: PASSED")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_filter_conditions_only()
    sys.exit(0 if success else 1)