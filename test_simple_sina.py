#!/usr/bin/env python3
"""
简化的新浪财经测试脚本
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_basic_imports():
    """测试基本模块导入"""
    print("[TEST] 测试基本模块导入...")
    
    try:
        # 测试新浪财经数据源
        from tradingagents.dataflows.sina_utils import get_sina_provider
        print("[OK] 新浪财经数据源导入成功")
        
        # 测试增强数据管理器
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        print("[OK] 增强数据管理器导入成功")
        
        return True
    except Exception as e:
        print(f"[ERROR] 模块导入失败: {e}")
        return False

def test_sina_basic_functionality():
    """测试新浪财经基本功能"""
    print("\n[TEST] 测试新浪财经基本功能...")
    
    try:
        from tradingagents.dataflows.sina_utils import get_sina_provider
        
        provider = get_sina_provider()
        symbol = '000001'
        
        # 测试基本股票信息获取
        stock_info = provider.get_stock_info(symbol)
        
        if stock_info:
            print("[OK] 新浪财经股票信息获取成功")
            print(f"   股票代码: {stock_info.get('symbol', 'N/A')}")
            print(f"   股票名称: {stock_info.get('name', 'N/A')}")
            print(f"   当前价格: {stock_info.get('current_price', 0):.2f}")
            print(f"   涨跌幅: {stock_info.get('change_pct', 0):.2f}%")
            return True
        else:
            print("[WARN] 未获取到股票信息")
            return False
            
    except Exception as e:
        print(f"[ERROR] 新浪财经基本功能测试失败: {e}")
        return False

def test_enhanced_data_manager():
    """测试增强数据管理器"""
    print("\n[TEST] 测试增强数据管理器...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        manager = get_enhanced_data_manager()
        symbol = '000001'
        
        # 测试综合数据获取
        comprehensive_data = manager.get_comprehensive_stock_info(symbol)
        
        if comprehensive_data:
            print("[OK] 综合股票数据获取成功")
            print(f"   股票代码: {comprehensive_data.get('symbol', 'N/A')}")
            print(f"   主数据源: {comprehensive_data.get('primary_source', 'N/A')}")
            print(f"   数据源数量: {len(comprehensive_data.get('sources', []))}")
            print(f"   数据质量评分: {comprehensive_data.get('data_quality_score', 0):.2f}")
            
            if 'current_price' in comprehensive_data:
                print(f"   当前价格: {comprehensive_data['current_price']:.2f}")
            
            return True
        else:
            print("[WARN] 未获取到综合数据")
            return False
            
    except Exception as e:
        print(f"[ERROR] 增强数据管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("[START] 开始简化版新浪财经功能测试...\n")
    
    tests = [
        ("基本模块导入", test_basic_imports),
        ("新浪财经基本功能", test_sina_basic_functionality),
        ("增强数据管理器", test_enhanced_data_manager)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"开始测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"[ERROR] 测试异常: {e}")
            results[test_name] = False
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("[SUMMARY] 测试结果汇总")
    print(f"{'='*50}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("[SUCCESS] 所有测试均通过！")
    else:
        print(f"[WARN] 有 {total - passed} 项测试失败")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)