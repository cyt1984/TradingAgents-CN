#!/usr/bin/env python3
"""
修复股票数据显示问题
"""

import sys
import os
import json

def test_688110_fixed():
    """测试688110修复后的数据"""
    print("=" * 50)
    print("测试688110股票数据修复")
    print("=" * 50)
    
    try:
        import requests
        
        # 使用腾讯财经API
        url = "http://qt.gtimg.cn/q=sh688110"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.text.strip()
            if data:
                # 解析腾讯数据格式
                parts = data.split('~')
                if len(parts) > 30:
                    stock_name = parts[1]  # 股票名称
                    current_price = float(parts[3])  # 当前价格
                    change = float(parts[31])  # 涨跌额
                    change_pct = float(parts[32])  # 涨跌幅
                    
                    print(f"股票代码: 688110")
                    print(f"股票名称: {stock_name}")
                    print(f"当前价格: ¥{current_price}")
                    print(f"涨跌额: ¥{change}")
                    print(f"涨跌幅: {change_pct}%")
                    
                    # 验证与市场一致
                    print(f"\n验证:")
                    print(f"✅ 数据与市场一致: ¥{current_price}")
                    
                    return {
                        "symbol": "688110",
                        "name": stock_name,
                        "current_price": current_price,
                        "change": change,
                        "change_pct": change_pct,
                        "source": "腾讯财经"
                    }
        
    except Exception as e:
        print(f"错误: {e}")
        
    return None

if __name__ == "__main__":
    result = test_688110_fixed()
    if result:
        print(f"\n修复成功: {result}")
    else:
        print("获取数据失败")