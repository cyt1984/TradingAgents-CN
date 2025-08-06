#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索实际工作的东方财富API
"""

import requests
import json

def test_working_api_detailed():
    """测试价值分析API的详细数据"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试价值分析数据
    params = {
        'reportName': 'RPT_VALUEANALYSIS_DET',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 10,
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
        
        print("价值分析API详细数据:")
        if data.get('result', {}).get('data'):
            for item in data['result']['data']:
                print(f"股票: {item.get('SECURITY_NAME_ABBR')} ({item.get('SECURITY_CODE')})")
                print(f"日期: {item.get('TRADE_DATE')}")
                print(f"收盘价: {item.get('CLOSE_PRICE')}")
                print(f"市值: {item.get('TOTAL_MARKET_CAP')}")
                print(f"PE: {item.get('PE_TTM')}")
                print(f"PB: {item.get('PB_MRQ')}")
                print("-" * 40)
        
        return data
        
    except Exception as e:
        print(f"API错误: {e}")
        return None

def test_financial_data_correct():
    """测试正确的财务报表API"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 使用正确的排序列
    params = {
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 10,
        'sortTypes': -1,
        'sortColumns': 'REPORTDATE',
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
        print(f"成功: {data.get('success')}")
        print(f"消息: {data.get('message')}")
        
        if data.get('result', {}).get('data'):
            print(f"找到 {len(data['result']['data'])} 条财务记录")
            for item in data['result']['data'][:3]:
                print(f"报告期: {item.get('REPORTDATE')}")
                print(f"净利润: {item.get('PARENTNETPROFIT')}")
                print(f"营业收入: {item.get('TOTALOPERATEREVE')}")
                print("-" * 40)
        
        return data
        
    except Exception as e:
        print(f"财务报表API错误: {e}")
        return None

def find_actual_research_api():
    """通过网页实际分析找到研报API"""
    
    # 让我们直接访问东方财富的研报页面，看看实际调用了什么API
    
    # 1. 先尝试一些通过分析网页发现的API
    
    test_apis = [
        {
            'name': '研报列表',
            'reportName': 'RPT_RESUL_RESEARCH',
            'sortColumns': 'PUBLISH_DATE'
        },
        {
            'name': '研报摘要',
            'reportName': 'RPT_RESUL_RESEARCHLIS',
            'sortColumns': 'PUBLISH_DATE'
        },
        {
            'name': '机构研报',
            'reportName': 'RPT_ORG_SURVEY',
            'sortColumns': 'NOTICE_DATE'
        },
        {
            'name': '投资评级',
            'reportName': 'RPT_STOCK_INVESTVALUE',
            'sortColumns': 'TRADE_DATE'
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
        print("-" * 30)
        
        params = {
            'reportName': api['reportName'],
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
                
                # 打印第一条记录的关键信息
                first_item = data['result']['data'][0]
                print(f"  字段: {list(first_item.keys())}")
                
        except Exception as e:
            print(f"  错误: {e}")

def test_web_scraping_approach():
    """使用网页抓取的方式获取研报数据"""
    
    import re
    
    # 直接访问研报页面
    url = f"https://data.eastmoney.com/report/singlestock.jshtml?stockcode=002602"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        
        print("网页内容长度:", len(content))
        
        # 查找可能的API调用
        api_patterns = [
            r'https://datacenter-web\.eastmoney\.com[^"\']*reportName[^"\']*',
            r'https://emappdata\.eastmoney\.com[^"\']*report[^"\']*',
            r'https://reportapi\.eastmoney\.com[^"\']*',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"找到API调用: {matches}")
        
        # 查找JSON数据
        json_patterns = [
            r'var\s+data\s*=\s*({.*?});',
            r'var\s+result\s*=\s*({.*?});',
            r'"data"\s*:\s*({.*?})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    print("找到JSON数据:", type(data))
                    if isinstance(data, dict):
                        print("可用键:", list(data.keys()))
                except:
                    continue
        
        return content
        
    except Exception as e:
        print(f"网页抓取错误: {e}")
        return None

if __name__ == "__main__":
    print("探索实际工作的东方财富API")
    print("=" * 50)
    
    print("1. 测试价值分析API:")
    test_working_api_detailed()
    
    print("\n2. 测试财务报表API:")
    test_financial_data_correct()
    
    print("\n3. 测试可能的研报API:")
    find_actual_research_api()
    
    print("\n4. 测试网页抓取:")
    test_web_scraping_approach()