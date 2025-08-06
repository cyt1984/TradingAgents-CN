#!/usr/bin/env python3
"""
最终测试688110股票数据
"""

import sys
import os
import requests

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_real_price(symbol):
    """获取真实股票价格"""
    
    # 处理科创板股票
    if symbol.startswith('688'):
        market = 'sh'
    else:
        market = 'sh' if symbol.startswith(('6', '5')) else 'sz'
    
    try:
        # 腾讯财经API
        url = f"http://qt.gtimg.cn/q={market}{symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.text.strip()
            if data and '~' in data:
                parts = data.split('~')
                if len(parts) > 3:
                    name = parts[1]
                    price = float(parts[3])
                    return {
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "source": "腾讯财经",
                        "success": True
                    }
    except Exception as e:
        pass
    
    try:
        # 新浪财经API
        url = f"http://hq.sinajs.cn/list={market}{symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.text.strip()
            if data and ',' in data:
                parts = data.split(',')
                if len(parts) > 3:
                    name = parts[0].split('="')[1] if '="' in parts[0] else symbol
                    price = float(parts[3])
                    return {
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "source": "新浪财经",
                        "success": True
                    }
    except Exception as e:
        pass
    
    return {
        "symbol": symbol,
        "success": False,
        "error": "无法获取数据"
    }

def test_688110():
    """测试688110"""
    print("=" * 50)
    print("测试688110股票数据")
    print("=" * 50)
    
    result = get_real_price('688110')
    
    if result['success']:
        print(f"股票代码: {result['symbol']}")
        print(f"股票名称: {result['name']}")
        print(f"当前价格: {result['price']}")
        print(f"数据源: {result['source']}")
        
        # 验证
        expected = 57.40
        actual = result['price']
        
        print(f"\n价格验证:")
        print(f"实际价格: {actual}")
        print(f"预期价格: {expected}")
        
        if abs(actual - expected) < 1:
            print("价格验证通过")
        else:
            print("价格存在较大差异")
            
    else:
        print("获取数据失败")
    
    return result

if __name__ == "__main__":
    test_688110()