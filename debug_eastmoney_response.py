#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试东方财富API响应，查看实际数据结构
"""

import requests
import json

def debug_api_response(stock_code: str):
    """调试API响应"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    params = {
        'sortColumns': 'NOTICE_DATE',
        'sortTypes': '-1',
        'pageSize': '5',
        'pageNumber': '1',
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="{stock_code}")',
        'client': 'WEB',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n=== {stock_code} 原始响应结构 ===")
        print("响应状态:", response.status_code)
        print("响应URL:", response.url)
        print("\n完整响应结构:")
        
        # 打印完整响应用于调试
        if 'result' in data and 'data' in data['result']:
            reports = data['result']['data']
            print(f"找到 {len(reports)} 条记录")
            
            if reports:
                print("\n第一条记录的所有字段:")
                first_report = reports[0]
                for key, value in first_report.items():
                    print(f"  {key}: {value}")
            else:
                print("数据为空")
        else:
            print("响应结构异常:", data.keys())
            print("响应内容:", json.dumps(data, ensure_ascii=False, indent=2))
            
        return data
        
    except Exception as e:
        print(f"获取{stock_code}数据失败: {e}")
        return None

if __name__ == "__main__":
    # 测试几个关键股票
    test_codes = ["002602", "000001", "600036"]
    
    print("东方财富API调试测试")
    print("=" * 50)
    
    for code in test_codes:
        debug_api_response(code)
        print("\n" + "=" * 50)
        time.sleep(1)