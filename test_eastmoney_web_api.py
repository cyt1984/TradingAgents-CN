#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富网页版API
"""

import requests
import re
import json

def get_reports_from_web(stock_code: str):
    """从网页获取研报数据"""
    
    # 东方财富研报页面
    url = f"https://data.eastmoney.com/report/singlestock.jshtml?stockcode={stock_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        
        # 查找JSON数据
        pattern = r'var\s+data\s*=\s*({.*?});'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            print(f"{stock_code} 找到网页数据")
            return data
        else:
            # 尝试查找其他格式的数据
            pattern2 = r'({"result".*?})'
            match2 = re.search(pattern2, content, re.DOTALL)
            if match2:
                try:
                    data = json.loads(match2.group(1))
                    print(f"{stock_code} 找到JSON数据")
                    return data
                except:
                    pass
        
        print(f"{stock_code} 未找到数据")
        return None
        
    except Exception as e:
        print(f"获取{stock_code}网页数据失败: {e}")
        return None

def test_direct_json_api():
    """测试直接JSON API"""
    
    # 东方财富直接研报API
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 测试002602
    params = {
        'reportName': 'RPT_WEB_ZZ',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="002602")',
        'pageNumber': 1,
        'pageSize': 20,
        'sortTypes': -1,
        'sortColumns': 'PUBLISH_DATE',
        'source': 'WEB',
        'client': 'WEB',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print("API响应状态:", response.status_code)
        print("响应URL:", response.url)
        print("响应结构:", list(data.keys()))
        
        if 'result' in data and data['result']:
            result = data['result']
            print("结果结构:", list(result.keys()))
            
            if 'data' in result and result['data']:
                reports = result['data']
                print(f"找到 {len(reports)} 条记录")
                
                if reports:
                    print("\n第一条记录:")
                    report = reports[0]
                    for key in ['TITLE', 'RESEARCH_TITLE', 'ORG_NAME', 'PUBLISH_DATE', 'EM_RATING_NAME', 'TARGET_PRICE']:
                        if key in report:
                            print(f"  {key}: {report[key]}")
                
                return reports
        
        print("无数据或数据格式不符")
        return []
        
    except Exception as e:
        print(f"API调用失败: {e}")
        return []

def main():
    """主测试"""
    
    print("东方财富研报测试")
    print("=" * 50)
    
    # 测试直接API
    reports = test_direct_json_api()
    
    if reports:
        print(f"\n成功获取到 {len(reports)} 条研报")
    else:
        print("\n未获取到研报数据")
    
    # 测试网页
    print("\n测试网页获取...")
    data = get_reports_from_web("002602")
    if data:
        print("网页数据获取成功")
    else:
        print("网页数据获取失败")

if __name__ == "__main__":
    main()