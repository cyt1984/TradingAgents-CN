#!/usr/bin/env python3
"""
简单测试688110的股票数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接测试API调用
import requests

def test_simple():
    print("测试688110股票数据...")
    
    # 测试新浪财经API
    try:
        url = f"http://hq.sinajs.cn/list=sh688110"
        response = requests.get(url, timeout=5)
        print(f"新浪财经原始数据: {response.text}")
        
        if response.text:
            data = response.text.strip()
            parts = data.split(',')
            if len(parts) > 3:
                name = parts[0].split('="')[1]
                price = float(parts[3])
                print(f"新浪财经: {name} ¥{price}")
    except Exception as e:
        print(f"新浪财经错误: {e}")
    
    # 测试腾讯财经API
    try:
        url = f"http://qt.gtimg.cn/q=sh688110"
        response = requests.get(url, timeout=5)
        print(f"腾讯财经原始数据: {response.text}")
        
        if response.text:
            data = response.text.strip()
            parts = data.split('~')
            if len(parts) > 3:
                name = parts[1]
                price = float(parts[3])
                print(f"腾讯财经: {name} ¥{price}")
    except Exception as e:
        print(f"腾讯财经错误: {e}")

if __name__ == "__main__":
    test_simple()