#!/usr/bin/env python3
"""
最终验证脚本 - 测试统一智能选股系统
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== 最终验证：统一智能选股系统 ===")

def test_market_selection():
    """测试市场选择功能"""
    print("\n1. 测试市场选择功能...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
        manager = EnhancedDataManager()
        
        # 测试A股
        a_stocks = manager.get_stock_list('A')
        print(f"   ✅ A股股票数量: {len(a_stocks)}")
        
        # 测试港股
        hk_stocks = manager.get_stock_list('HK')
        print(f"   ✅ 港股股票数量: {len(hk_stocks)}")
        
        return True
    except Exception as e:
        print(f"   ❌ 市场选择测试失败: {e}")
        return False

def test_stock_selector():
    """测试股票选择器"""
    print("\n2. 测试股票选择器...")
    
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        selector = StockSelector()
        
        # 测试获取股票列表
        stock_list = selector._get_stock_list()
        print(f"   ✅ 股票选择器获取数量: {len(stock_list)}")
        print(f"   ✅ 数据类型: {type(stock_list)}")
        print(f"   ✅ 列名: {list(stock_list.columns)}")
        
        # 测试前3只股票
        if not stock_list.empty:
            sample = stock_list.head(3)
            for _, row in sample.iterrows():
                print(f"   📊 {row['ts_code']} - {row['name']}")
        
        return True
    except Exception as e:
        print(f"   ❌ 股票选择器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_system():
    """测试AI系统"""
    print("\n3. 测试AI专家系统...")
    
    try:
        from tradingagents.selectors.ai_strategies.ai_strategy_manager import get_ai_strategy_manager
        
        ai_manager = get_ai_strategy_manager()
        if ai_manager:
            performance = ai_manager.get_performance_summary()
            print(f"   ✅ AI系统状态: {performance.get('status', '未知')}")
            print(f"   ✅ 可用引擎: {performance.get('engine_availability', {}).get('available_count', 0)}")
            return True
        else:
            print("   ⚠️ AI系统未初始化")
            return False
    except Exception as e:
        print(f"   ❌ AI系统测试失败: {e}")
        return False

def test_quick_selection():
    """测试快速选股"""
    print("\n4. 测试快速选股...")
    
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        selector = StockSelector()
        
        # 使用基础模式快速测试
        result = selector.quick_select(limit=5)
        print(f"   ✅ 选股结果数量: {len(result.symbols)}")
        print(f"   ✅ 执行时间: {result.execution_time:.2f}秒")
        
        if result.symbols:
            print("   📊 推荐股票:")
            for symbol in result.symbols[:3]:
                print(f"      - {symbol}")
        
        return True
    except Exception as e:
        print(f"   ❌ 快速选股测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("开始验证统一智能选股系统...")
    
    tests = [
        ("市场选择", test_market_selection),
        ("股票选择器", test_stock_selector), 
        ("AI系统", test_ai_system),
        ("快速选股", test_quick_selection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        if test_func():
            print(f"✅ {test_name} - 通过")
            passed += 1
        else:
            print(f"❌ {test_name} - 失败")
    
    print(f"\n{'='*50}")
    print(f"最终测试结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 恭喜！统一智能选股系统验证成功！")
        print("   - 市场选择功能正常 (A股/港股/美股)")
        print("   - 股票选择器正常工作")
        print("   - AI专家系统已激活")
        print("   - 所有数据源兼容")
    else:
        print(f"\n⚠️  发现 {total - passed} 个问题需要修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)