#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的东方财富研报API
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.research_report_utils import EastMoneyResearchProvider

def test_updated_provider():
    """测试更新后的东方财富研报提供器"""
    
    provider = EastMoneyResearchProvider()
    
    test_stocks = ["002602", "000001", "600036", "000858", "688585"]
    
    print("测试更新后的东方财富研报API")
    print("=" * 50)
    
    total_reports = 0
    
    for stock in test_stocks:
        print(f"\n测试股票: {stock}")
        print("-" * 30)
        
        try:
            reports = provider.get_reports(stock, limit=5)
            
            if reports:
                print(f"成功获取 {len(reports)} 条调研报告")
                total_reports += len(reports)
                
                for i, report in enumerate(reports[:3], 1):
                    print(f"  {i}. {report.title}")
                    print(f"     机构: {report.institution}")
                    print(f"     日期: {report.publish_date}")
                    print(f"     摘要: {report.summary[:100]}...")
                    
            else:
                print("未获取到数据")
                
        except Exception as e:
            print(f"获取数据失败: {e}")
    
    print(f"\n总计获取到 {total_reports} 条调研报告")

if __name__ == "__main__":
    test_updated_provider()