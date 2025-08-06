#!/usr/bin/env python3
"""
股票数据调试脚本 - 验证688110的实际数据
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_stock_data(symbol='688110'):
    """调试股票数据获取"""
    print(f"=" * 60)
    print(f"调试股票 {symbol} 数据获取")
    print(f"=" * 60)
    
    try:
        # 测试各个数据源
        from tradingagents.dataflows.eastmoney_utils import get_eastmoney_provider
        from tradingagents.dataflows.tencent_utils import get_tencent_provider
        from tradingagents.dataflows.sina_utils import get_sina_provider
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        print(f"\n[1] 直接测试各数据源:")
        
        # 东方财富
        try:
            eastmoney = get_eastmoney_provider()
            data = eastmoney.get_stock_info(symbol)
            if data:
                print(f"  东方财富: {data.get('name', 'N/A')} ¥{data.get('current_price', 0)}")
                print(f"  详细信息: {data}")
            else:
                print(f"  东方财富: 无数据")
        except Exception as e:
            print(f"  东方财富错误: {e}")
        
        # 腾讯财经
        try:
            tencent = get_tencent_provider()
            data = tencent.get_stock_info(symbol)
            if data:
                print(f"  腾讯财经: {data.get('name', 'N/A')} ¥{data.get('current_price', 0)}")
                print(f"  详细信息: {data}")
            else:
                print(f"  腾讯财经: 无数据")
        except Exception as e:
            print(f"  腾讯财经错误: {e}")
        
        # 新浪财经
        try:
            sina = get_sina_provider()
            data = sina.get_stock_info(symbol)
            if data:
                print(f"  新浪财经: {data.get('name', 'N/A')} ¥{data.get('current_price', 0)}")
                print(f"  详细信息: {data}")
            else:
                print(f"  新浪财经: 无数据")
        except Exception as e:
            print(f"  新浪财经错误: {e}")
        
        # 增强数据管理器
        print(f"\n[2] 增强数据管理器结果:")
        manager = get_enhanced_data_manager()
        comprehensive = manager.get_comprehensive_stock_info(symbol)
        if comprehensive:
            print(f"  综合数据: {comprehensive.get('name', 'N/A')} ¥{comprehensive.get('current_price', 0)}")
            print(f"  数据源: {comprehensive.get('sources', [])}")
            print(f"  原始数据: {json.dumps(comprehensive, ensure_ascii=False, indent=2)}")
        
        # 检查股票代码是否正确
        print(f"\n[3] 股票代码验证:")
        print(f"  输入代码: {symbol}")
        print(f"  预期市场: 科创板(688开头)")
        
        # 测试不同格式
        test_codes = [symbol, f"sh{symbol}", f"{symbol}.SS"]
        for code in test_codes:
            print(f"\n[4] 测试代码格式: {code}")
            try:
                tencent = get_tencent_provider()
                data = tencent.get_stock_info(code)
                if data:
                    print(f"  腾讯财经({code}): ¥{data.get('current_price', 0)}")
                
                sina = get_sina_provider()
                data = sina.get_stock_info(code)
                if data:
                    print(f"  新浪财经({code}): ¥{data.get('current_price', 0)}")
                    
            except Exception as e:
                print(f"  错误({code}): {e}")
        
    except Exception as e:
        print(f"调试错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_stock_data('688110')