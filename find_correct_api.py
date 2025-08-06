#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找到东方财富研报数据的正确API
"""

import requests
import json

def test_real_report_api(stock_code: str):
    """测试真实的研报API"""
    
    # 东方财富研报API端点
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 使用研报摘要报表
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
        print(f"\n测试股票: {stock_code}")
        print(f"API URL: {api_url}")
        print(f"参数: {params}")
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"响应状态: {response.status_code}")
        print(f"响应结构: {list(data.keys())}")
        
        if 'result' in data and data['result'] is not None:
            result = data['result']
            print(f"结果结构: {list(result.keys())}")
            
            if 'data' in result and result['data']:
                reports = result['data']
                print(f"找到 {len(reports)} 条记录")
                
                if reports:
                    print("\n第一条记录:")
                    report = reports[0]
                    for key, value in report.items():
                        print(f"  {key}: {value}")
                        
                    return reports
            else:
                print("结果中无data字段或data为空")
                print(f"完整结果: {result}")
        else:
            print("无result字段或result为空")
            print(f"完整响应: {data}")
        
        return []
        
    except Exception as e:
        print(f"获取{stock_code}数据失败: {e}")
        return []

def test_alternative_apis(stock_code: str):
    """测试其他可能的API"""
    
    apis = [
        {
            'name': '研报摘要',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'params': {
                'reportName': 'RPT_WEB_ZZ',
                'filter': f'(SECURITY_CODE="{stock_code}")',
            }
        },
        {
            'name': '机构研报',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'params': {
                'reportName': 'RPT_ORGANIZATION_RESEARCH',
                'filter': f'(SECURITY_CODE="{stock_code}")',
            }
        },
        {
            'name': '研报评级',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'params': {
                'reportName': 'RPT_LICO_FN_CPD',
                'filter': f'(SECURITY_CODE="{stock_code}")',
            }
        },
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    for api in apis:
        print(f"\n--- 测试 {api['name']} ---")
        
        params = {
            'sortColumns': 'PUBLISH_DATE',
            'sortTypes': '-1',
            'pageSize': '10',
            'pageNumber': '1',
            'columns': 'ALL',
            'client': 'WEB',
        }
        params.update(api['params'])
        
        try:
            response = requests.get(api['url'], params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result') and data['result'].get('data'):
                reports = data['result']['data']
                print(f"✓ {api['name']}: 找到 {len(reports)} 条记录")
                
                # 显示可用字段
                if reports:
                    fields = list(reports[0].keys())
                    print(f"  可用字段: {fields}")
                    
                    # 显示第一条记录
                    report = reports[0]
                    print("  第一条记录:")
                    for key in ['TITLE', 'RESEARCH_TITLE', 'ORG_NAME', 'PUBLISH_DATE', 'EM_RATING_NAME']:
                        if key in report:
                            print(f"    {key}: {report[key]}")
                
                return reports
            else:
                print(f"✗ {api['name']}: 无数据")
                
        except Exception as e:
            print(f"✗ {api['name']}: 错误 - {e}")
    
    return []

if __name__ == "__main__":
    print("东方财富研报API查找")
    print("=" * 50)
    
    test_codes = ["002602", "000001", "600036"]
    
    for code in test_codes:
        print(f"\n{'='*50}")
        print(f"测试股票: {code}")
        
        reports = test_alternative_apis(code)
        if reports:
            print(f"\n成功获取 {len(reports)} 条研报记录")
            break