#\!/usr/bin/env python3
# 测试A股数据源修复效果
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print('=== 测试A股数据源修复效果 ===')

def test_a_share_data_source():
    print('\n1. 测试A股数据源...')
    try:
        from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
        manager = EnhancedDataManager()
        stocks = manager.get_stock_list('A')
        print(f'   A股股票数量: {len(stocks)}')
        if stocks:
            print('   前3只股票:')
            for i, stock in enumerate(stocks[:3]):
                print(f'      {i+1}. {stock["symbol"]} - {stock["name"]}')
        return True
    except Exception as e:
        print(f'   错误: {e}')
        return False

def test_stock_selector():
    print('\n2. 测试股票选择器（无Tushare依赖）...')
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        selector = StockSelector()
        stock_list = selector._get_stock_list()
        print(f'   股票选择器获取数量: {len(stock_list)}')
        if not stock_list.empty:
            print(f'   数据类型: {type(stock_list)}')
            print(f'   列名: {list(stock_list.columns)}')
            print('   前3只股票:')
            for _, row in stock_list.head(3).iterrows():
                print(f'      {row["ts_code"]} - {row["name"]}')
        return True
    except Exception as e:
        print(f'   错误: {e}')
        return False

def main():
    print('开始验证A股数据源修复效果...')
    tests = [
        ('A股数据源', test_a_share_data_source),
        ('股票选择器', test_stock_selector)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f'\n{=*50}')
        if test_func():
            print(f'[PASS] {test_name}')
            passed += 1
        else:
            print(f'[FAIL] {test_name}')
    
    print(f'\n{=*50}')
    print(f'测试结果: {passed}/{total} 测试通过')
    return passed == total

if __name__ == __main__:
    success = main()
    sys.exit(0 if success else 1)
