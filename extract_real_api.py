#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从实际网页提取东方财富研报API
"""

import requests
import re
import json

class EastMoneyReportExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_reports_from_direct_page(self, stock_code: str):
        """从研报页面获取数据"""
        
        # 使用实际提供的链接格式
        url = f"https://data.eastmoney.com/report/singlestock.jshtml?stockcode={stock_code}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # 查找实际的数据API调用
            # 查找包含研报数据的JSON
            patterns = [
                r'var\s+initdata\s*=\s*({.*?});',
                r'var\s+data\s*=\s*({.*?});',
                r'"data"\s*:\s*({.*?})',
                r'jsonpCallback\s*\(\s*({.*?})\s*\)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        # 清理JSON字符串
                        json_str = re.sub(r'\s+', ' ', match).strip()
                        data = json.loads(json_str)
                        
                        if 'result' in str(data) and 'data' in str(data):
                            print(f"Found JSON data for {stock_code}")
                            return data
                    except:
                        continue
            
            # 查找XHR请求URL
            xhr_patterns = [
                r'https://datacenter-web\.eastmoney\.com[^"\']*reportName[^"\']*',
                r'https://datacenter-web\.eastmoney\.com[^"\']*RPT_[^"\']*',
            ]
            
            for pattern in xhr_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"Found API URL: {matches[0]}")
                    return self.call_api_directly(matches[0])
            
            # 尝试分析页面结构
            print(f"Analyzing page structure for {stock_code}...")
            
            # 查找包含研报的部分
            report_section = re.search(r'<table[^>]*>.*?</table>', content, re.DOTALL)
            if report_section:
                print(f"Found table structure for {stock_code}")
                return {"html": report_section.group(0)}
            
            return None
            
        except Exception as e:
            print(f"Error accessing page for {stock_code}: {e}")
            return None
    
    def call_api_directly(self, api_url):
        """直接调用API"""
        try:
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API call error: {e}")
            return None
    
    def test_real_api(self, stock_code: str):
        """测试真实API"""
        
        # 基于实际网页分析的API
        api_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        
        # 使用研报摘要报表
        params = {
            'callback': 'jQuery112300000000000000000_1620000000000',
            'sortColumns': 'PUBLISH_DATE',
            'sortTypes': '-1',
            'pageSize': '20',
            'pageNumber': '1',
            'reportName': 'RPT_WEB_ZZ',
            'columns': 'ALL',
            'filter': f'(SECURITY_CODE="{stock_code}")',
            'client': 'WEB',
            '_': '1620000000000'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://data.eastmoney.com/',
            'Accept': 'text/javascript, application/javascript, */*',
        }
        
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"{stock_code} API Response:")
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            if 'result' in data and data['result']:
                result = data['result']
                if 'data' in result and result['data']:
                    reports = result['data']
                    print(f"Found {len(reports)} reports")
                    
                    # 显示前几条
                    for i, report in enumerate(reports[:3], 1):
                        title = report.get('TITLE', '')
                        org = report.get('ORG_NAME', '')
                        date = report.get('PUBLISH_DATE', '')
                        rating = report.get('EM_RATING_NAME', '')
                        
                        if title.strip():
                            print(f"  {i}. {title}")
                            print(f"     {org} - {date} - {rating}")
                    
                    return reports
            
            return []
            
        except Exception as e:
            print(f"API Error for {stock_code}: {e}")
            return []

def main():
    """主测试"""
    
    extractor = EastMoneyReportExtractor()
    
    test_stocks = ["002602", "000001", "600036", "688585"]
    
    print("东方财富研报提取测试")
    print("=" * 50)
    
    for stock_code in test_stocks:
        print(f"\n测试股票: {stock_code}")
        print("-" * 30)
        
        # 测试实际API
        reports = extractor.test_real_api(stock_code)
        
        if reports:
            print(f"成功获取 {len(reports)} 条研报")
        else:
            print("未获取到研报")

if __name__ == "__main__":
    main()