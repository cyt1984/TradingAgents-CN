#!/usr/bin/env python3
"""
东方财富API集成测试
测试新实现的东方财富研报HTTP API接口
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.research_report_utils import EastMoneyResearchProvider
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('test_eastmoney')

def test_eastmoney_api():
    """测试东方财富API"""
    logger.info("🚀 开始测试东方财富API集成...")
    
    # 创建东方财富提供器
    provider = EastMoneyResearchProvider()
    
    # 测试股票列表
    test_stocks = [
        ("000001", "平安银行"),
        ("600036", "招商银行"), 
        ("000858", "五粮液"),
        ("688215", "科创板股票"),
        ("002027", "分众传媒")
    ]
    
    total_reports = 0
    successful_stocks = 0
    
    for ticker, name in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 测试股票: {ticker} ({name})")
        
        try:
            start_time = time.time()
            
            # 获取研报数据
            reports = provider.get_reports(ticker, limit=5)
            
            elapsed_time = time.time() - start_time
            
            if reports:
                successful_stocks += 1
                total_reports += len(reports)
                
                logger.info(f"✅ 成功获取 {len(reports)} 条研报，耗时: {elapsed_time:.2f}秒")
                
                # 显示前2条研报详情
                for i, report in enumerate(reports[:2], 1):
                    logger.info(f"  {i}. 【{report.source}】{report.institution}: {report.title}")
                    logger.info(f"     评级: {report.rating}, 目标价: {report.target_price}, 可信度: {report.confidence_level:.2f}")
                    if report.key_points:
                        logger.info(f"     关键观点: {', '.join(report.key_points[:2])}")
                    logger.info(f"     发布日期: {report.publish_date}")
                
            else:
                logger.warning(f"⚠️ 未获取到研报数据: {ticker}")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {ticker}, 错误: {e}")
        
        # 短暂延时避免频率限制
        time.sleep(2)
    
    # 输出测试总结
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 东方财富API测试总结:")
    logger.info(f"✅ 成功测试: {successful_stocks}/{len(test_stocks)} 支股票")
    logger.info(f"📈 总研报数: {total_reports} 条")
    
    success_rate = successful_stocks / len(test_stocks) if test_stocks else 0
    
    if success_rate >= 0.6:
        logger.info("🎉 东方财富API集成测试成功！")
        return True
    else:
        logger.warning("⚠️ 东方财富API集成需要进一步优化")
        return False

def test_api_params():
    """测试API参数构建"""
    logger.info("🔧 测试API参数构建...")
    
    provider = EastMoneyResearchProvider()
    
    # 测试股票代码格式化
    test_cases = [
        ("000001", "000001.SZ"),
        ("600036", "600036.SH"),
        ("688215", "688215.SH"),
        ("000001.SZ", "000001.SZ"),
        ("600036.SH", "600036.SH"),
    ]
    
    for input_ticker, expected in test_cases:
        result = provider._format_ticker(input_ticker)
        status = "✅" if result == expected else "❌"
        logger.info(f"  {status} {input_ticker} -> {result} (期望: {expected})")
    
    # 测试API参数构建
    params = provider._build_api_params("000001.SZ", 10)
    logger.info(f"📋 API参数示例:")
    for key, value in params.items():
        if key != 'callback':  # callback太长，不显示
            logger.info(f"  {key}: {value}")

def main():
    """主测试函数"""
    logger.info(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 测试API参数构建
        test_api_params()
        
        # 2. 测试实际API调用
        success = test_eastmoney_api()
        
        logger.info(f"⏰ 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 测试过程异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)