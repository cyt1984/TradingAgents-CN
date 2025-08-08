#!/usr/bin/env python3
"""
阶段1选股引擎集成测试
验证核心选股功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.selectors import (
    StockSelector, SelectionCriteria, 
    FilterOperator, NumericFilter, EnumFilter
)
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')

def test_basic_functionality():
    """测试基础功能"""
    print("=" * 60)
    print("🧪 阶段1选股引擎功能测试")
    print("=" * 60)
    
    try:
        # 1. 初始化选股引擎
        print("\n1️⃣ 初始化选股引擎...")
        selector = StockSelector(cache_enabled=True)
        print("✅ 选股引擎初始化成功")
        
        # 2. 测试可用字段
        print("\n2️⃣ 获取可用筛选字段...")
        fields = selector.get_available_fields()
        print(f"✅ 可用字段数量: {len(fields)}个")
        print("主要字段:", list(fields.keys())[:10])
        
        # 3. 测试筛选条件创建
        print("\n3️⃣ 创建筛选条件...")
        
        # 创建市值筛选条件
        market_cap_filter = selector.create_numeric_filter(
            'market_cap', FilterOperator.GREATER_EQUAL, 100.0
        )
        print("✅ 市值筛选条件创建成功")
        
        # 创建市盈率筛选条件
        pe_filter = selector.create_numeric_filter(
            'pe_ratio', FilterOperator.BETWEEN, (10.0, 25.0)
        )
        print("✅ 市盈率筛选条件创建成功")
        
        # 创建投资等级筛选条件
        grade_filter = selector.create_enum_filter(
            'grade', FilterOperator.IN, ['A+', 'A', 'A-']
        )
        print("✅ 投资等级筛选条件创建成功")
        
        # 4. 测试快速选股
        print("\n4️⃣ 执行快速选股...")
        result = selector.quick_select(
            min_score=60.0,
            min_market_cap=50.0,
            max_pe_ratio=30.0,
            limit=20
        )
        
        print(f"✅ 快速选股完成:")
        print(f"   - 候选股票: {result.total_candidates}只")
        print(f"   - 筛选结果: {result.filtered_count}只")
        print(f"   - 执行时间: {result.execution_time:.2f}秒")
        
        if result.symbols:
            print(f"   - 前5只股票: {result.symbols[:5]}")
        
        # 5. 测试自定义选股条件
        print("\n5️⃣ 执行自定义选股...")
        criteria = SelectionCriteria(
            filters=[market_cap_filter, pe_filter],
            sort_by='market_cap',
            sort_ascending=False,
            limit=10,
            include_scores=False,  # 暂时不包含评分以加快测试
            include_basic_info=True
        )
        
        result2 = selector.select_stocks(criteria)
        print(f"✅ 自定义选股完成:")
        print(f"   - 候选股票: {result2.total_candidates}只")
        print(f"   - 筛选结果: {result2.filtered_count}只")
        print(f"   - 执行时间: {result2.execution_time:.2f}秒")
        
        if result2.symbols:
            print(f"   - 选中股票: {result2.symbols}")
        
        # 6. 总结
        print("\n" + "=" * 60)
        print("📊 测试总结:")
        print("✅ 选股引擎初始化: 成功")
        print("✅ 筛选条件创建: 成功")
        print("✅ 快速选股功能: 成功")
        print("✅ 自定义选股功能: 成功")
        print("\n🎉 阶段1核心功能验证通过!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)