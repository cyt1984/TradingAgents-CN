#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接获取东方财富研报数据
"""

import requests
import json

def get_eastmoney_reports(stock_code: str, limit: int = 10):
    """获取东方财富研报数据"""
    
    # 东方财富研报API端点
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
                
                if title and title.strip():
                    reports.append({
                        'title': title,
                        'institution': institution,
                        'publish_date': publish_date,
                        'rating': rating,
                        'target_price': target_price,
                        'stock_code': str(report.get('SECURITY_CODE', '')),
                        'stock_name': str(report.get('SECURITY_NAME_ABBR', ''))
                    })
        
        return reports
        
    except Exception as e:
        print(f"Error getting reports for {stock_code}: {e}")
        return []

def main():
    """测试主函数"""
    
    # 测试股票
    test_stocks = ["002602", "000001", "600036", "000858"]
    
    print("EastMoney Report API Test")
    print("=" * 50)
    
    total_reports = 0
    
    for stock in test_stocks:
        print(f"\nTesting {stock}:")
        
        reports = get_eastmoney_reports(stock, limit=5)
        
        if reports:
            print(f"  Found {len(reports)} reports:")
            for i, report in enumerate(reports, 1):
                print(f"    {i}. {report['title']}")
                print(f"       Institution: {report['institution']}")
                print(f"       Date: {report['publish_date']}")
                print(f"       Rating: {report['rating']}")
                print(f"       Target Price: {report['target_price']}")
            
            total_reports += len(reports)
        else:
            print("  No reports found")
    
    print(f"\nTotal reports found: {total_reports}")

if __name__ == "__main__":
    main()