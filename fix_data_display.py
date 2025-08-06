#!/usr/bin/env python3
"""
修复股票数据显示问题
"""

import sys
import os
import requests
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_real_time_price(symbol):
    """获取实时股票价格"""
    
    # 科创板股票代码处理
    if symbol.startswith('688'):
        market_prefix = 'sh'  # 科创板在上交所
    else:
        market_prefix = 'sh' if symbol.startswith(('6', '5')) else 'sz'
    
    full_code = f"{market_prefix}{symbol}"
    
    try:
        # 使用腾讯财经API（最稳定）
        url = f"http://qt.gtimg.cn/q={full_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.text.strip()
            if data and '~' in data:
                parts = data.split('~')
                if len(parts) > 32:
                    return {
                        "symbol": symbol,
                        "name": parts[1],
                        "current_price": float(parts[3]),
                        "change": float(parts[31]),
                        "change_pct": float(parts[32]),
                        "volume": int(parts[36]) if len(parts) > 36 else 0,
                        "source": "腾讯财经",
                        "status": "success"
                    }
    except Exception as e:
        print(f"腾讯财经API错误: {e}")
    
    try:
        # 使用新浪财经API作为备选
        url = f"http://hq.sinajs.cn/list={full_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.text.strip()
            if data and ',' in data:
                parts = data.split(',')
                if len(parts) > 30:
                    name = parts[0].split('="')[1] if '="' in parts[0] else symbol
                    return {
                        "symbol": symbol,
                        "name": name,
                        "current_price": float(parts[3]),
                        "change": float(parts[3]) - float(parts[2]),
                        "change_pct": ((float(parts[3]) - float(parts[2])) / float(parts[2])) * 100,
                        "volume": int(parts[8]) if len(parts) > 8 else 0,
                        "source": "新浪财经",
                        "status": "success"
                    }
    except Exception as e:
        print(f"新浪财经API错误: {e}")
    
    return {
        "symbol": symbol,
        "status": "failed",
        "error": "无法获取数据"
    }

def test_688110():
    """测试688110股票数据"""
    print("=" * 60)
    print("测试688110股票数据（东芯股份）")
    print("=" * 60)
    
    result = get_real_time_price('688110')
    
    if result['status'] == 'success':
        print("\n[数据获取成功]")
        print("股票代码: {}".format(result['symbol']))
        print("股票名称: {}".format(result['name']))
        print("当前价格: ¥{:.2f}".format(result['current_price']))
        print("涨跌额: ¥{:.2f}".format(result['change']))
        print("涨跌幅: {:.2f}%".format(result['change_pct']))
        print("成交量: {:,}".format(result['volume']))
        print("数据源: {}".format(result['source']))
        
        # 验证价格
        expected_price = 57.40
        actual_price = result['current_price']
        
        if abs(actual_price - expected_price) < 1:  # 允许1元误差
            print("\n[价格验证通过]")
            print("实际价格: ¥{:.2f}".format(actual_price))
            print("预期价格: ¥{:.2f}".format(expected_price))
        else:
            print("\n[价格差异较大]")
            print("实际价格: ¥{:.2f}".format(actual_price))
            print("预期价格: ¥{:.2f}".format(expected_price))
            
    else:
        print("\n[获取失败]: {}".format(result['error']))
    
    return result

if __name__ == "__main__":
    test_688110()