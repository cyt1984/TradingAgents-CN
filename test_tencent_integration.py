#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯数据集成效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tencent_integration():
    """测试腾讯数据集成"""
    try:
        # 测试腾讯数据源
        print("=== 测试腾讯实时行情 ===")
        from tradingagents.dataflows.tencent_utils import get_tencent_stock_info
        
        result = get_tencent_stock_info('000001')
        if result:
            print("腾讯000001获取成功:")
            print(f"   股票名称: {result.get('name', '未知')}")
            print(f"   当前价格: ¥{result.get('current_price', 0):.2f}")
            print(f"   涨跌幅: {result.get('change_pct', 0):+.2f}%")
            print(f"   成交量: {result.get('volume', 0):,}")
        else:
            print("腾讯000001获取失败")
            
        # 测试增强数据管理器
        print("\n=== 测试增强数据管理器 ===")
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        manager = get_enhanced_data_manager()
        comprehensive = manager.get_comprehensive_stock_info('000001')
        
        if comprehensive:
            print("综合数据获取成功:")
            print(f"   股票代码: {comprehensive.get('symbol')}")
            print(f"   数据源: {comprehensive.get('sources', [])}")
            print(f"   质量评分: {comprehensive.get('data_quality_score', 0):.2f}")
            print(f"   主数据源: {comprehensive.get('primary_source')}")
            
            if 'current_price' in comprehensive:
                print(f"   当前价格: ¥{comprehensive.get('current_price', 0):.2f}")
        else:
            print("综合数据获取失败")
            
        # 测试K线数据
        print("\n=== 测试腾讯K线数据 ===")
        from tradingagents.dataflows.tencent_utils import get_tencent_kline
        
        kline_data = get_tencent_kline('000001', period='day', count=5)
        if kline_data is not None and not kline_data.empty:
            print("K线数据获取成功:")
            print(f"   数据条数: {len(kline_data)}")
            print(f"   最新数据:")
            latest = kline_data.iloc[-1]
            print(f"   日期: {latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else latest.name}")
            print(f"   收盘: ¥{latest.get('close', 0):.2f}")
            print(f"   成交量: {latest.get('volume', 0):,}")
        else:
            print("K线数据获取失败")
            
        print("\n=== 阶段1测试完成 ===")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_tencent_integration()