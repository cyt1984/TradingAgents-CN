#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试东方财富API响应
"""

import requests
import json

def debug_eastmoney_api():
    """详细调试API响应"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试002602
    params = {
        'reportName': 'RPT_WEB_ZZ',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 20,
        'sortTypes': -1,
        'sortColumns': 'PUBLISH_DATE',
        'client': 'WEB',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        print("完整响应:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        print(f"\n响应状态: {data.get('success')}")
        print(f"响应消息: {data.get('message')}")
        print(f"响应代码: {data.get('code')}")
        
        if 'result' in data:
            result = data['result']
            print(f"\n结果数据:")
            print(f"  总记录数: {result.get('pages', 0)}")
            print(f"  当前页: {result.get('page', 0)}")
            print(f"  页面大小: {result.get('count', 0)}")
            print(f"  实际数据: {len(result.get('data', []))}")
            
            if result.get('data'):
                print(f"\n第一条数据:")
                first_item = result['data'][0]
                print(f"  可用字段: {list(first_item.keys())}")
            else:
                print("\n无数据")
        
        return data
        
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

def test_different_report_names():
    """测试不同的reportName"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    report_names = [
        'RPT_WEB_ZZ',
        'RPT_ORGANIZATION_RESEARCH',
        'RPT_LICO_FN_CPD',
        'RPT_RESEARCH_REPORT',
        'RPT_STOCK_REPORT',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    stock_code = "002602"
    
    for report_name in report_names:
        print(f"\n测试 {report_name}:")
        print("-" * 30)
        
        params = {
            'reportName': report_name,
            'columns': 'ALL',
            'filter': f'(SECURITY_CODE="{stock_code}")',
            'pageNumber': 1,
            'pageSize': 5,
            'sortTypes': -1,
            'sortColumns': 'PUBLISH_DATE',
            'client': 'WEB',
        }
        
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            success = data.get('success', False)
            message = data.get('message', '')
            total = data.get('result', {}).get('pages', 0)
            count = len(data.get('result', {}).get('data', []))
            
            print(f"  成功: {success}")
            print(f"  消息: {message}")
            print(f"  总记录: {total}")
            print(f"  当前数据: {count}")
            
            if count > 0:
                print("  找到数据!")
                
        except Exception as e:
            print(f"  错误: {e}")

if __name__ == "__main__":
    print("东方财富API详细调试")
    print("=" * 50)
    
    print("1. 测试002602的完整响应:")
    debug_eastmoney_api()
    
    print("\n2. 测试不同的报表名称:")
    test_different_report_names()