#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找到东方财富研报数据的正确API端点
"""

import requests
import json

def test_report_api(stock_code: str):
    """测试研报API"""
    
    # 东方财富研报API - 使用正确的reportName
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试不同的报表名称
    report_names = [
        'RPT_LICO_FN_CPD',     # 机构评级
        'RPT_WEB_ZZ',          # 研报摘要
        'RPT_ORGANIZATION_RESEARCH',  # 机构研报
        'RPT_WEB_RESEARCH',    # 研报数据
    ]
    
    for report_name in report_names:
        print(f"\n测试报表名称: {report_name}")
        
        params = {
            'sortColumns': 'NOTICE_DATE',
            'sortTypes': '-1',
            'pageSize': '10',
            'pageNumber': '1',
            'reportName': report_name,
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
            
            if 'result' in data and 'data' in data['result']:
                reports = data['result']['data']
                print(f"  {report_name}: 找到 {len(reports)} 条记录")
                
                if reports and 'RESEARCH_TITLE' in str(reports[0]):
                    print(f"  ✓ {report_name}: 包含研报标题")
                    return report_name, reports
                elif reports and 'TITLE' in str(reports[0]):
                    print(f"  ✓ {report_name}: 包含标题字段")
                    return report_name, reports
                else:
                    print(f"  ✗ {report_name}: 无研报相关字段")
                    if reports:
                        print(f"    可用字段: {list(reports[0].keys())}")
            else:
                print(f"  ✗ {report_name}: 无数据")
                
        except Exception as e:
            print(f"  ✗ {report_name}: 错误 - {e}")
    
    return None, []

def test_individual_report_api(stock_code: str):
    """测试个股研报API"""
    
    # 使用东方财富个股研报API
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 正确的研报API参数
    params = {
        'sortColumns': 'PUBLISH_DATE',
        'sortTypes': '-1',
        'pageSize': '10',
        'pageNumber': '1',
        'reportName': 'RPT_WEB_ZZ',
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
        
        print(f"\n=== {stock_code} 研报API响应 ===")
        
        if 'result' in data and 'data' in data['result']:
            reports = data['result']['data']
            print(f"找到 {len(reports)} 条研报")
            
            for i, report in enumerate(reports[:3], 1):
                print(f"\n研报 {i}:")
                for key, value in report.items():
                    if value and str(value).strip():
                        print(f"  {key}: {value}")
        else:
            print("无研报数据")
            if data:
                print("响应结构:", data.keys())
        
        return data
        
    except Exception as e:
        print(f"获取{stock_code}研报失败: {e}")
        return None

if __name__ == "__main__":
    print("东方财富研报API查找测试")
    print("=" * 50)
    
    # 测试002602
    test_individual_report_api("002602")
    
    print("\n" + "=" * 50)
    
    # 测试000001
    test_individual_report_api("000001")