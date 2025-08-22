#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试股票002602股价数据问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_stock_data():
    """测试股票数据获取"""
    print("调试股票002602数据问题...")
    print("=" * 50)
    
    symbol = "002602"
    
    try:
        # 1. 测试数据源管理器
        print(f"\n1. 测试数据源管理器获取{symbol}数据...")
        from tradingagents.dataflows.data_source_manager import get_data_source_manager
        
        manager = get_data_source_manager()
        print(f"当前数据源: {manager.get_current_source().value}")
        print(f"可用数据源: {[s.value for s in manager.available_sources]}")
        
        # 获取最近30天数据
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        print(f"获取数据期间: {start_date} 到 {end_date}")
        
        data = manager.get_stock_data(symbol, start_date, end_date)
        print(f"返回数据长度: {len(data) if data else 0} 字符")
        
        if data:
            lines = data.split('\n')
            print(f"数据行数: {len(lines)}")
            print(f"\n前15行数据:")
            for i, line in enumerate(lines[:15]):
                print(f"  {i+1}: {line}")
            
            # 查找股价相关信息
            price_keywords = ['价格', '收盘', '¥', '元']
            price_lines = []
            for line in lines:
                if any(keyword in line for keyword in price_keywords):
                    price_lines.append(line)
            
            if price_lines:
                print(f"\n股价相关信息:")
                for line in price_lines:
                    print(f"  {line}")
        
        # 2. 测试直接Tushare适配器
        print(f"\n2. 测试Tushare适配器获取{symbol}数据...")
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        adapter = get_tushare_adapter()
        df_data = adapter.get_stock_data(symbol, start_date, end_date)
        
        if df_data is not None and not df_data.empty:
            print(f"DataFrame数据形状: {df_data.shape}")
            print(f"列名: {list(df_data.columns)}")
            
            # 显示最新几天的数据
            print(f"\n最新3天数据:")
            recent_data = df_data.tail(3)
            for idx, row in recent_data.iterrows():
                print(f"  日期: {row.get('date', 'N/A')}")
                print(f"  开盘: {row.get('open', 'N/A')}")
                print(f"  收盘: {row.get('close', 'N/A')}")
                print(f"  最高: {row.get('high', 'N/A')}")
                print(f"  最低: {row.get('low', 'N/A')}")
                print(f"  成交量: {row.get('volume', 'N/A')}")
                print("  ---")
            
            # 检查价格列
            if 'close' in df_data.columns:
                latest_price = df_data['close'].iloc[-1]
                print(f"\n最新收盘价: {latest_price}")
            
        else:
            print("未获取到DataFrame数据")
        
        # 3. 测试股票信息
        print(f"\n3. 测试股票{symbol}基本信息...")
        stock_info = manager.get_stock_info(symbol)
        print(f"股票信息: {stock_info}")
            
    except Exception as e:
        import traceback
        print(f"测试失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    test_stock_data()