#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试东方财富研报API端点
使用正确的东方财富研报数据获取方式
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# 测试股票列表
test_stocks = [
    "002602",  # 世纪华通
    "000001",  # 平安银行
    "600036",  # 招商银行
    "000858",  # 五粮液
    "300750",  # 宁德时代
]

def test_eastmoney_report_api(stock_code: str) -> Dict[str, Any]:
    """测试东方财富研报API"""
    
    # 东方财富研报API端点
    api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    # 格式化股票代码
    if stock_code.startswith(('000', '002', '003', '300', '301')):
        formatted_code = f"{stock_code}.SZ"
    elif stock_code.startswith(('600', '601', '603', '605', '688', '689')):
        formatted_code = f"{stock_code}.SH"
    else:
        formatted_code = f"{stock_code}.SH"
    
    print(f"\n测试股票: {stock_code} ({formatted_code})")
    
    # API参数
    params = {
        'sortColumns': 'NOTICE_DATE',
        'sortTypes': '-1',
        'pageSize': '10',
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
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析研报数据
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
                    'summary': report.get('CONTENT', '')[:100] + '...' if report.get('CONTENT', '') else '',
                    'stock_code': report.get('SECURITY_CODE', ''),
                    'stock_name': report.get('SECURITY_NAME', '')
                })
        
        return {
            'stock_code': stock_code,
            'success': len(reports) > 0,
            'report_count': len(reports),
            'reports': reports[:3],  # 返回前3条
            'raw_data_exists': bool(data.get('result', {}).get('data')),
            'api_url': response.url
        }
        
    except Exception as e:
        return {
            'stock_code': stock_code,
            'success': False,
            'error': str(e),
            'report_count': 0,
            'reports': []
        }

def test_direct_page(stock_code: str) -> Dict[str, Any]:
    """测试直接访问研报页面"""
    
    page_url = f"https://data.eastmoney.com/report/singlestock.jshtml?stockcode={stock_code}"
    
    print(f"测试页面: {page_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 检查页面是否包含研报数据
        content = response.text
        has_reports = 'RESEARCH_TITLE' in content or '研报' in content
        
        return {
            'stock_code': stock_code,
            'success': has_reports,
            'page_found': True,
            'has_data': has_reports,
            'content_length': len(content),
            'page_url': page_url
        }
        
    except Exception as e:
        return {
            'stock_code': stock_code,
            'success': False,
            'page_found': False,
            'error': str(e)
        }

def main():
    """主测试函数"""
    print("开始测试东方财富研报API...")
    print("=" * 60)
    
    total_reports = 0
    successful_stocks = 0
    
    for stock in test_stocks:
        # 测试API
        api_result = test_eastmoney_report_api(stock)
        page_result = test_direct_page(stock)
        
        print(f"\n{stock} 测试结果:")
        print(f"  API接口: {'成功' if api_result['success'] else '失败'}")
        print(f"  研报数量: {api_result['report_count']}")
        
        if api_result['success'] and api_result['reports']:
            print(f"  最新研报: {api_result['reports'][0]['title'][:50]}...")
            print(f"  发布机构: {api_result['reports'][0]['institution']}")
            
            successful_stocks += 1
            total_reports += api_result['report_count']
        
        print(f"  页面访问: {'有数据' if page_result['success'] else '无数据'}")
        
        # 短暂延时避免请求过快
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  测试股票数: {len(test_stocks)}")
    print(f"  成功获取研报: {successful_stocks}")
    print(f"  总研报数量: {total_reports}")
    print(f"  成功率: {successful_stocks/len(test_stocks)*100:.1f}%")
    
    return {
        'total_stocks': len(test_stocks),
        'successful_stocks': successful_stocks,
        'total_reports': total_reports,
        'success_rate': successful_stocks / len(test_stocks)
    }

if __name__ == "__main__":
    result = main()