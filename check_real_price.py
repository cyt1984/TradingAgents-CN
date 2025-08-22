#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查002602真实股价
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_real_price():
    """检查真实股价"""
    print("检查股票002602真实股价...")
    print("=" * 50)
    
    symbol = "002602"
    
    try:
        # 1. 检查AKShare实时数据
        print("1. 检查AKShare实时数据...")
        import akshare as ak
        
        # 获取A股实时数据
        real_data = ak.stock_zh_a_spot_em()
        stock_real = real_data[real_data['代码'] == symbol]
        
        if not stock_real.empty:
            print("AKShare实时数据:")
            row = stock_real.iloc[0]
            print(f"  股票代码: {row['代码']}")
            print(f"  股票名称: {row['名称']}")
            print(f"  最新价: {row['最新价']}")
            print(f"  涨跌幅: {row['涨跌幅']}%")
            print(f"  涨跌额: {row['涨跌额']}")
            print(f"  成交量: {row['成交量']}")
            print(f"  成交额: {row['成交额']}")
            print(f"  今开: {row['今开']}")
            print(f"  昨收: {row['昨收']}")
            print(f"  最高: {row['最高']}")
            print(f"  最低: {row['最低']}")
        else:
            print("未找到002602的实时数据")
        
        # 2. 检查历史数据
        print("\n2. 检查AKShare历史数据...")
        hist_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20250815", end_date="20250818", adjust="")
        
        if not hist_data.empty:
            print("AKShare历史数据(最近3天):")
            print(hist_data.tail(3).to_string())
        else:
            print("未找到历史数据")
            
        # 3. 检查Tushare数据（如果可用）
        print("\n3. 检查Tushare数据...")
        try:
            import tushare as ts
            token = '你的tushare_token_here'  # 这里需要实际的token
            ts.set_token(token)
            pro = ts.pro_api()
            
            # 转换股票代码格式
            ts_code = "002602.SZ"
            df = pro.daily(ts_code=ts_code, start_date='20250815', end_date='20250818')
            
            if not df.empty:
                print("Tushare历史数据:")
                print(df.to_string())
            else:
                print("Tushare未找到数据")
                
        except Exception as e:
            print(f"Tushare检查失败: {e}")
        
        # 4. 对比数据
        print("\n4. 数据对比分析...")
        if not stock_real.empty and not hist_data.empty:
            real_price = stock_real.iloc[0]['最新价']
            hist_latest = hist_data.iloc[-1]['收盘'] if '收盘' in hist_data.columns else hist_data.iloc[-1]['close']
            
            print(f"实时价格: {real_price}")
            print(f"历史最新收盘价: {hist_latest}")
            print(f"价格差异: {abs(real_price - hist_latest):.2f}")
            
            if abs(real_price - hist_latest) > 0.1:
                print("注意: 实时价格与历史数据存在差异")
            else:
                print("实时价格与历史数据基本一致")
            
    except Exception as e:
        import traceback
        print(f"检查失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    check_real_price()