#!/usr/bin/env python3
"""
测试价格数据获取功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== 测试价格数据获取功能 ===")

def test_price_data():
    """测试价格数据获取"""
    print("\n1. 测试价格数据获取...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
        manager = EnhancedDataManager()
        
        # 测试几个股票代码
        test_symbols = ['000001', '600519', '688235']
        
        for symbol in test_symbols:
            try:
                price_data = manager.get_latest_price_data(symbol)
                if price_data:
                    print(f"   {symbol}: 成功获取价格数据")
                    print(f"      当前价格: {price_data.get('current_price', 'N/A')}")
                    print(f"      开盘价: {price_data.get('open', 'N/A')}")
                    print(f"      成交量: {price_data.get('volume', 'N/A')}")
                else:
                    print(f"   {symbol}: 无法获取价格数据")
            except Exception as e:
                print(f"   {symbol}: 错误 - {e}")
        
        return True
    except Exception as e:
        print(f"   测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_selector_with_prices():
    """测试股票选择器是否能正确获取价格数据"""
    print("\n2. 测试股票选择器价格数据...")
    
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        selector = StockSelector()
        
        # 测试快速选股，限制数量以避免太多API调用
        result = selector.quick_select(limit=5)
        print(f"   选股结果数量: {len(result.symbols)}")
        
        if result.symbols:
            print("   选股结果:")
            for symbol in result.symbols:
                try:
                    # 测试通过数据管理器获取价格
                    price_data = selector.data_manager.get_latest_price_data(symbol)
                    if price_data:
                        print(f"      {symbol}: 价格={price_data.get('current_price', 'N/A')}")
                    else:
                        print(f"      {symbol}: 价格数据不可用")
                except Exception as e:
                    print(f"      {symbol}: 获取价格失败 - {e}")
        
        return True
    except Exception as e:
        print(f"   测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试价格数据获取功能...")
    
    tests = [
        ("价格数据", test_price_data),
        ("股票选择器", test_stock_selector_with_prices)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        if test_func():
            print(f"[PASS] {test_name}")
            passed += 1
        else:
            print(f"[FAIL] {test_name}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 测试通过")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)