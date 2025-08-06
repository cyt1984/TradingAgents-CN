#!/usr/bin/env python3
"""
直接测试688110股票数据，绕过编码问题
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_688110_direct():
    """直接测试688110数据"""
    print("=" * 50)
    print("测试688110股票数据")
    print("=" * 50)
    
    # 禁用Unicode日志
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    try:
        # 直接测试各个数据源
        print("\n[1] 测试腾讯财经:")
        from tradingagents.dataflows.tencent_utils import get_tencent_provider
        tencent = get_tencent_provider()
        data = tencent.get_stock_info('688110')
        if data:
            print(f"  股票名称: {data.get('name')}")
            print(f"  当前价格: ¥{data.get('current_price')}")
            print(f"  涨跌幅: {data.get('change_pct')}%")
            print(f"  完整数据: {data}")
        
        print("\n[2] 测试新浪财经:")
        from tradingagents.dataflows.sina_utils import get_sina_provider
        sina = get_sina_provider()
        data = sina.get_stock_info('688110')
        if data:
            print(f"  股票名称: {data.get('name')}")
            print(f"  当前价格: ¥{data.get('current_price')}")
            print(f"  涨跌幅: {data.get('change_pct')}%")
            print(f"  完整数据: {data}")
        
        print("\n[3] 测试东方财富:")
        from tradingagents.dataflows.eastmoney_utils import get_eastmoney_provider
        eastmoney = get_eastmoney_provider()
        data = eastmoney.get_stock_info('688110')
        if data:
            print(f"  股票名称: {data.get('name')}")
            print(f"  当前价格: ¥{data.get('current_price')}")
            print(f"  涨跌幅: {data.get('change_pct')}%")
            print(f"  完整数据: {data}")
        
        print("\n[4] 测试增强数据管理器:")
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        manager = get_enhanced_data_manager()
        data = manager.get_comprehensive_stock_info('688110')
        if data:
            print(f"  股票名称: {data.get('name')}")
            print(f"  当前价格: ¥{data.get('current_price')}")
            print(f"  数据源: {data.get('sources')}")
            print(f"  质量评分: {data.get('data_quality_score')}")
            print(f"  完整数据: {data}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_688110_direct()