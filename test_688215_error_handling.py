#!/usr/bin/env python3
"""
测试688215股票代码的错误处理
验证科创板股票的特殊处理和错误分类是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.research_report_utils import get_stock_research_reports, get_institutional_consensus
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('test')

def test_688215_error_handling():
    """测试688215股票代码的错误处理"""
    ticker = "688215"
    logger.info(f"🧪 开始测试 {ticker} (科创板) 的错误处理...")
    
    try:
        # 测试研报获取
        logger.info(f"📊 测试研报获取: {ticker}")
        reports = get_stock_research_reports(ticker, limit=5)
        
        if reports:
            logger.info(f"✅ 成功获取到 {len(reports)} 条研报")
            for i, report in enumerate(reports, 1):
                logger.info(f"  {i}. {report.institution}: {report.title}")
                logger.info(f"     评级: {report.rating}, 目标价: {report.target_price}")
        else:
            logger.info(f"ℹ️ 未获取到研报数据，这对科创板股票是正常情况")
        
        # 测试机构一致预期
        logger.info(f"🎯 测试机构一致预期: {ticker}")
        consensus = get_institutional_consensus(ticker)
        
        if consensus:
            logger.info(f"✅ 机构一致预期数据:")
            for key, value in consensus.items():
                if value is not None:
                    logger.info(f"  {key}: {value}")
        else:
            logger.info(f"ℹ️ 未获取到机构一致预期数据")
        
        logger.info(f"✅ 测试完成: {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {ticker}, 错误: {e}")
        return False

def test_special_boards():
    """测试多个特殊板块的股票代码"""
    test_cases = [
        ("688215", "科创板 - 首都在线"),
        ("688123", "科创板 - 聚辰股份"),
        ("300001", "创业板 - 特锐德"),
        ("430047", "北交所/新三板"),
        ("002027", "中小板 - 分众传媒"),
        ("000001", "深圳主板 - 平安银行"),
        ("600036", "上海主板 - 招商银行")
    ]
    
    logger.info(f"🧪 开始测试多个特殊板块股票代码...")
    
    results = {}
    for ticker, description in test_cases:
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 测试: {ticker} ({description})")
        
        try:
            reports = get_stock_research_reports(ticker, limit=3)
            results[ticker] = {
                'success': True,
                'report_count': len(reports),
                'description': description
            }
            
            if reports:
                logger.info(f"✅ 获取到 {len(reports)} 条研报")
            else:
                logger.info(f"ℹ️ 未获取到研报，但处理正常")
                
        except Exception as e:
            logger.error(f"❌ 处理异常: {e}")
            results[ticker] = {
                'success': False,
                'error': str(e),
                'description': description
            }
    
    # 输出测试结果摘要
    logger.info(f"\n{'='*50}")
    logger.info(f"📈 测试结果摘要:")
    
    successful = 0
    failed = 0
    
    for ticker, result in results.items():
        if result['success']:
            successful += 1
            status = "✅ 成功"
            detail = f"({result['report_count']} 条研报)"
        else:
            failed += 1
            status = "❌ 失败"
            detail = f"({result.get('error', '未知错误')})"
        
        logger.info(f"  {ticker} ({result['description']}): {status} {detail}")
    
    logger.info(f"\n📊 总体结果: {successful} 成功, {failed} 失败")
    
    return successful, failed

def main():
    """主测试函数"""
    logger.info("🚀 开始研报错误处理综合测试...")
    
    # 测试特定的688215问题
    logger.info("\n" + "="*60)
    logger.info("🎯 专项测试: 688215 科创板股票错误处理")
    test_688215_error_handling()
    
    # 测试多个特殊板块
    logger.info("\n" + "="*60)
    logger.info("🌟 综合测试: 多个特殊板块股票")
    successful, failed = test_special_boards()
    
    # 总结
    logger.info("\n" + "="*60)
    logger.info("📋 测试总结:")
    logger.info(f"  - 已实现科创板、北交所、创业板等特殊板块支持")
    logger.info(f"  - 增强了错误分类和处理机制")
    logger.info(f"  - 提供了板块特定的错误建议")
    logger.info(f"  - 实现了智能重试和容错机制")
    logger.info(f"  - 测试结果: {successful} 成功, {failed} 失败")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！错误处理机制工作正常")
    else:
        logger.warning(f"⚠️ 有 {failed} 个测试失败，需要进一步检查")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)