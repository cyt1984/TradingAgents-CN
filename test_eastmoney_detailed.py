#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试东方财富研报API，获取实际研报数据
"""

import requests
import json
import time
from datetime import datetime

def get_eastmoney_reports(stock_code: str, limit: int = 10) -> list:
    """获取东方财富研报数据"""
    
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    params = {
        'sortColumns': 'NOTICE_DATE',
        'sortTypes': '-1',
        'pageSize': str(limit),
        'pageNumber': '1',
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': f'(SECURITY_CODE="{stock_code}")',
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
        
        reports = []
        if 'result' in data and 'data' in data['result']:
            raw_reports = data['result']['data']
            for report in raw_reports:
                reports.append({
                    'title': report.get('RESEARCH_TITLE', ''),
                    'institution': report.get('ORG_NAME', ''),
                    'analyst': report.get('AUTHOR_NAME', ''),
                    'publish_date': report.get('NOTICE_DATE', ''),
                    'rating': report.get('EM_RATING_NAME', ''),
                    'target_price': report.get('TARGET_PRICE', 0),
                    'current_price': report.get('CLOSE_PRICE', 0),
                    'stock_code': report.get('SECURITY_CODE', ''),
                    'stock_name': report.get('SECURITY_NAME', '')
                })
        
        return reports
        
    except Exception as e:
        print(f"获取{stock_code}研报失败: {e}")
        return []

def main():
    """主测试函数"""
    
    test_stocks = [
        "002602",  # 世纪华通
        "000001",  # 平安银行
        "600036",  # 招商银行
        "000858",  # 五粮液
        "300750",  # 宁德时代
        "688585",  # 您提供的示例股票
    ]
    
    print("东方财富研报API详细测试")
    print("=" * 80)
    
    total_reports = 0
    
    for stock_code in test_stocks:
        print(f"\n股票代码: {stock_code}")
        print("-" * 40)
        
        reports = get_eastmoney_reports(stock_code, limit=5)
        
        if reports:
            print(f"成功获取 {len(reports)} 条研报:")
            for i, report in enumerate(reports[:3], 1):
                print(f"  {i}. {report['title']}")
                print(f"     机构: {report['institution']}")
                print(f"     分析师: {report['analyst']}")
                print(f"     评级: {report['rating']}")
                print(f"     目标价: {report['target_price']}")
                print(f"     发布日期: {report['publish_date']}")
                print()
            total_reports += len(reports)
        else:
            print("未获取到研报数据")
        
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 80)
    print(f"测试完成 - 总共获取到 {total_reports} 条研报")
    
    # 特别测试002602
    print(f"\n特别测试 - 002602世纪华通:")
    st_reports = get_eastmoney_reports("002602", limit=10)
    if st_reports:
        print(f"002602世纪华通获取到 {len(st_reports)} 条研报:")
        for report in st_reports[:5]:
            print(f"  - {report['title']} ({report['institution']}, {report['publish_date']})")
    else:
        print("002602未获取到研报")

if __name__ == "__main__":
    main()