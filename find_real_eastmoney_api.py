#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找实际的东方财富研报API
"""

import requests
import json
import time

def test_financial_reports_api():
    """测试财务报表API - 这个应该能工作"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试财务报表数据（之前测试过的）
    params = {
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 20,
        'sortTypes': -1,
        'sortColumns': 'REPORT_DATE',
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
        
        print("财务报表API响应:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        return data
        
    except Exception as e:
        print(f"财务报表API错误: {e}")
        return None

def test_stock_basic_info():
    """测试股票基本信息API"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试股票基本信息
    params = {
        'reportName': 'RPT_VALUEANALYSIS_DET',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 20,
        'sortTypes': -1,
        'sortColumns': 'TRADE_DATE',
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
        
        print("股票信息API响应:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        return data
        
    except Exception as e:
        print(f"股票信息API错误: {e}")
        return None

def test_announcement_api():
    """测试公告API"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    params = {
        'reportName': 'RPT_LICO_FN_NOTICE',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 20,
        'sortTypes': -1,
        'sortColumns': 'NOTICE_DATE',
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
        
        print("公告API响应:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        return data
        
    except Exception as e:
        print(f"公告API错误: {e}")
        return None

def test_known_working_apis():
    """测试已知能工作的API"""
    
    test_cases = [
        {
            'name': '财务报表',
            'reportName': 'RPT_LICO_FN_CPD',
            'sortColumns': 'REPORT_DATE'
        },
        {
            'name': '公告',
            'reportName': 'RPT_LICO_FN_NOTICE',
            'sortColumns': 'NOTICE_DATE'
        },
        {
            'name': '价值分析',
            'reportName': 'RPT_VALUEANALYSIS_DET',
            'sortColumns': 'TRADE_DATE'
        },
        {
            'name': '公司资料',
            'reportName': 'RPT_F10_MAIN_ORGPROFILE',
            'sortColumns': 'ORG_CODE'
        }
    ]
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    stock_code = "002602"
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']}:")
        print("-" * 30)
        
        params = {
            'reportName': test_case['reportName'],
            'columns': 'ALL',
            'filter': f'(SECURITY_CODE="{stock_code}")',
            'pageNumber': 1,
            'pageSize': 5,
            'sortTypes': -1,
            'sortColumns': test_case['sortColumns'],
            'client': 'WEB',
        }
        
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            success = data.get('success', False)
            message = data.get('message', '')
            total = data.get('result', {}).get('pages', 0) if data.get('result') else 0
            count = len(data.get('result', {}).get('data', [])) if data.get('result') else 0
            
            print(f"  成功: {success}")
            print(f"  消息: {message}")
            print(f"  总记录: {total}")
            print(f"  当前数据: {count}")
            
            if count > 0 and data.get('result', {}).get('data'):
                print("  找到数据!")
                # 打印第一条数据的字段
                first_item = data['result']['data'][0]
                print(f"  字段: {list(first_item.keys())}")
                
        except Exception as e:
            print(f"  错误: {e}")

def find_research_reports_api():
    """尝试找到研报相关的API"""
    
    # 尝试一些可能的研报API
    possible_apis = [
        'RPT_WEB_RESEARCH',
        'RPT_STOCK_RESEARCH',
        'RPT_ORG_RESEARCH',
        'RPT_ANALYST_REPORT',
        'RPT_INVESTMENT_REPORT',
        'RPT_SECURITIES_REPORT',
        'RPT_BROKERAGE_REPORT',
        'RPT_STOCK_REPORT',
        'RPT_RESEARCH_REPORT',
    ]
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    stock_code = "002602"
    
    for report_name in possible_apis:
        print(f"\n测试 {report_name}:")
        
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
            
            print(f"  成功: {success}")
            print(f"  消息: {message}")
            
            if success and data.get('result', {}).get('data'):
                print(f"  找到研报数据!")
                count = len(data['result']['data'])
                print(f"  记录数: {count}")
                
        except Exception as e:
            print(f"  错误: {e}")

if __name__ == "__main__":
    print("查找实际的东方财富API")
    print("=" * 50)
    
    print("1. 测试已知能工作的API:")
    test_known_working_apis()
    
    print("\n2. 测试可能的研报API:")
    find_research_reports_api()