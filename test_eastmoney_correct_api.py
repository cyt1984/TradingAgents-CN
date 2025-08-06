#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用正确的东方财富研报API
"""

import requests
import json
import time

def get_eastmoney_reports_correct(stock_code: str, limit: int = 10):
    """使用正确的东方财富研报API"""
    
    # 东方财富研报API端点 - 实际使用这个
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 使用研报摘要报表
    params = {
        'sortColumns': 'PUBLISH_DATE',
        'sortTypes': '-1',
        'pageSize': str(limit),
        'pageNumber': '1',
        'reportName': 'RPT_WEB_ZZ',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="{stock_code}")',
        'client': 'WEB',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        reports = []
        if data.get('result') and data['result'].get('data'):
            raw_reports = data['result']['data']
            
            for report in raw_reports:
                # 提取研报信息
                title = str(report.get('TITLE', ''))
                institution = str(report.get('ORG_NAME', ''))
                publish_date = str(report.get('PUBLISH_DATE', ''))
                rating = str(report.get('EM_RATING_NAME', ''))
                target_price = report.get('TARGET_PRICE', 0)
                
                reports.append({
                    'title': title,
                    'institution': institution,
                    'publish_date': publish_date,
                    'rating': rating,
                    'target_price': target_price,
                    'stock_code': str(report.get('SECURITY_CODE', '')),
                    'stock_name': str(report.get('SECURITY_NAME_ABBR', '')),
                    'summary': str(report.get('CONTENT', ''))[:200] + '...' if report.get('CONTENT', '') else ''
                })
        
        return reports
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_with_different_params(stock_code: str):
    """使用不同参数测试"""
    
    # 测试多个API端点
    apis = [
        {
            'name': '研报摘要',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'report_name': 'RPT_WEB_ZZ'
        },
        {
            'name': '机构研报',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'report_name': 'RPT_ORGANIZATION_RESEARCH'
        },
        {
            'name': '研报评级',
            'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
            'report_name': 'RPT_LICO_FN_CPD'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    all_reports = []
    
    for api in apis:
        try:
            params = {
                'sortColumns': 'PUBLISH_DATE',
                'sortTypes': '-1',
                'pageSize': '10',
                'pageNumber': '1',
                'reportName': api['report_name'],
                'columns': 'ALL',
                'filter': f'(SECURITY_CODE="{stock_code}")',
                'client': 'WEB',
            }
            
            response = requests.get(api['url'], params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result') and data['result'].get('data'):
                reports = data['result']['data']
                print(f"{api['name']}: Found {len(reports)} reports")
                
                # 显示第一条记录的关键字段
                if reports:
                    report = reports[0]
                    print(f"  Sample fields: {list(report.keys())[:10]}")
                    if 'TITLE' in report:
                        print(f"  Title: {report['TITLE']}")
                    if 'ORG_NAME' in report:
                        print(f"  Institution: {report['ORG_NAME']}")
                
                all_reports.extend(reports)
            else:
                print(f"{api['name']}: No data")
                
        except Exception as e:
            print(f"{api['name']}: Error - {e}")
    
    return all_reports

def main():
    """主测试函数"""
    
    test_stocks = [
        "002602",  # 世纪华通
        "000001",  # 平安银行
        "600036",  # 招商银行
        "000858",  # 五粮液
        "688585",  # 您提供的示例股票
    ]
    
    print("EastMoney Report API Test")
    print("=" * 60)
    
    total_reports = 0
    
    for stock_code in test_stocks:
        print(f"\nTesting {stock_code}:")
        print("-" * 30)
        
        # 使用多种API测试
        reports = test_with_different_params(stock_code)
        
        if reports:
            print(f"Total reports found: {len(reports)}")
            
            # 显示前3条
            for i, report in enumerate(reports[:3], 1):
                title = report.get('TITLE', '') or report.get('RESEARCH_TITLE', '')
                institution = report.get('ORG_NAME', '')
                date = report.get('PUBLISH_DATE', '')
                
                if title and title.strip():
                    print(f"  {i}. {title}")
                    print(f"     {institution} - {date}")
            
            total_reports += len(reports)
        else:
            print("No reports found")
        
        time.sleep(1)
    
    print(f"\nTotal reports across all stocks: {total_reports}")
    
    # 特别测试002602
    print(f"\nSpecial test for 002602:")
    st_reports = get_eastmoney_reports_correct("002602", limit=10)
    if st_reports:
        print(f"Found {len(st_reports)} reports for 002602")
        for report in st_reports[:3]:
            if report['title'].strip():
                print(f"  - {report['title']} ({report['institution']})")
    else:
        print("No reports found for 002602")

if __name__ == "__main__":
    main()