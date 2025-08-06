#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际的研报API
"""

import requests
import json

def test_org_survey_api(stock_code: str = "002602"):
    """测试机构调研API - 这个包含研报信息"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    params = {
        'reportName': 'RPT_ORG_SURVEY',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="{stock_code}")',
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
        
        print(f"{stock_code} - 机构调研API:")
        print(f"成功: {data.get('success')}")
        print(f"消息: {data.get('message')}")
        
        if data.get('result', {}).get('data'):
            reports = data['result']['data']
            print(f"找到 {len(reports)} 条机构调研记录")
            
            for i, report in enumerate(reports[:5], 1):
                print(f"\n{i}. 调研日期: {report.get('NOTICE_DATE')}")
                print(f"   机构: {report.get('ORG_NAME')}")
                print(f"   调研时间: {report.get('RECEIVE_TIME_EXPLAIN')}")
                print(f"   调研对象: {report.get('RECEIVE_OBJECT')}")
                print(f"   内容: {report.get('CONTENT', '')[:100]}...")
            
            return reports
        
        return []
        
    except Exception as e:
        print(f"机构调研API错误: {e}")
        return []

def test_analyst_rating_api():
    """测试投资评级API"""
    
    # 尝试找到投资评级的正确API
    test_apis = [
        {
            'name': 'RPT_STOCK_MARKETING',
            'sortColumns': 'TRADE_DATE'
        },
        {
            'name': 'RPT_STOCK_RESEARCHDETAILS',
            'sortColumns': 'PUBLISH_DATE'
        },
        {
            'name': 'RPT_STOCK_FORECAST',
            'sortColumns': 'FORECAST_DATE'
        },
        {
            'name': 'RPT_STOCK_TARGETPRICE',
            'sortColumns': 'PUBLISH_DATE'
        }
    ]
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    stock_code = "002602"
    
    for api in test_apis:
        print(f"\n测试 {api['name']}:")
        
        params = {
            'reportName': api['name'],
            'columns': 'ALL',
            'filter': f'(SECURITY_CODE="{stock_code}")',
            'pageNumber': 1,
            'pageSize': 5,
            'sortTypes': -1,
            'sortColumns': api['sortColumns'],
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
                count = len(data['result']['data'])
                print(f"  找到 {count} 条记录")
                
                # 打印第一条记录
                first_item = data['result']['data'][0]
                print(f"  字段: {list(first_item.keys())}")
                
                # 显示有价值的信息
                for key, value in first_item.items():
                    if value and str(value).strip():
                        print(f"    {key}: {value}")
                        
        except Exception as e:
            print(f"  错误: {e}")

def test_comprehensive_data():
    """测试综合数据获取"""
    
    stock_codes = ["002602", "000001", "600036", "000858", "688585"]
    
    print("综合API测试")
    print("=" * 50)
    
    # 1. 价值分析数据
    print("\n1. 价值分析数据:")
    for code in stock_codes:
        try:
            api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
            
            params = {
                'reportName': 'RPT_VALUEANALYSIS_DET',
                'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR,CLOSE_PRICE,TOTAL_MARKET_CAP,PE_TTM,PB_MRQ,TRADE_DATE',
                'filter': f'(SECURITY_CODE="{code}")',
                'pageNumber': 1,
                'pageSize': 1,
                'sortTypes': -1,
                'sortColumns': 'TRADE_DATE',
                'client': 'WEB',
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://data.eastmoney.com/',
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('result', {}).get('data'):
                item = data['result']['data'][0]
                print(f"{code}: {item.get('CLOSE_PRICE')}元, 市值{item.get('TOTAL_MARKET_CAP')}, PE{item.get('PE_TTM')}")
            else:
                print(f"{code}: 无数据")
                
        except Exception as e:
            print(f"{code}: 错误 - {e}")
    
    # 2. 机构调研数据
    print("\n2. 机构调研数据:")
    for code in stock_codes:
        try:
            params = {
                'reportName': 'RPT_ORG_SURVEY',
                'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR,ORG_NAME,NOTICE_DATE,RECEIVE_TIME_EXPLAIN',
                'filter': f'(SECURITY_CODE="{code}")',
                'pageNumber': 1,
                'pageSize': 3,
                'sortTypes': -1,
                'sortColumns': 'NOTICE_DATE',
                'client': 'WEB',
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('result', {}).get('data'):
                reports = data['result']['data']
                print(f"{code}: {len(reports)} 条调研记录")
            else:
                print(f"{code}: 无调研记录")
                
        except Exception as e:
            print(f"{code}: 错误 - {e}")

if __name__ == "__main__":
    print("测试实际工作的API")
    print("=" * 50)
    
    print("1. 测试机构调研API:")
    test_org_survey_api()
    
    print("\n2. 测试投资评级API:")
    test_analyst_rating_api()
    
    print("\n3. 综合数据测试:")
    test_comprehensive_data()