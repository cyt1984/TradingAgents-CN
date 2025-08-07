#!/usr/bin/env python3
"""
新浪财经增强功能测试
测试新浪财经新闻API集成、深度行情数据和情感分析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
from tradingagents.dataflows.sina_utils import get_sina_provider
from tradingagents.analytics.sentiment_analyzer import SentimentAnalyzer
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('test')

def test_sina_news_enhancement():
    """测试新浪财经新闻增强功能"""
    logger.info("🧪 开始测试新浪财经新闻增强功能...")
    
    try:
        sina_provider = get_sina_provider()
        symbol = '000001'  # 平安银行
        
        # 测试增强的新闻获取功能
        news = sina_provider.get_stock_news(symbol, limit=10)
        
        if news:
            logger.info(f"✅ 成功获取新闻 {len(news)} 条")
            
            # 显示前3条新闻
            for i, item in enumerate(news[:3], 1):
                logger.info(f"   [{i}] {item.get('title', 'N/A')}")
                logger.info(f"       来源: {item.get('source', 'N/A')}")
                logger.info(f"       相关性: {item.get('relevance_score', 'N/A')}")
                logger.info(f"       类型: {item.get('news_type', 'N/A')}")
        else:
            logger.warning("⚠️ 未获取到新闻数据")
            
        return len(news) > 0
        
    except Exception as e:
        logger.error(f"❌ 新浪财经新闻测试失败: {e}")
        return False

def test_sina_deep_market_data():
    """测试新浪财经深度行情数据"""
    logger.info("🧪 开始测试新浪财经深度行情数据...")
    
    try:
        sina_provider = get_sina_provider()
        symbol = '000001'  # 平安银行
        
        # 测试深度行情数据
        deep_data = sina_provider.get_deep_market_data(symbol)
        
        if deep_data:
            logger.info(f"✅ 成功获取深度行情数据")
            logger.info(f"   股票代码: {deep_data.get('symbol', 'N/A')}")
            
            # 基础信息
            basic_info = deep_data.get('basic_info', {})
            if basic_info:
                logger.info(f"   股票名称: {basic_info.get('name', 'N/A')}")
                logger.info(f"   当前价格: ¥{basic_info.get('current_price', 0):.2f}")
                logger.info(f"   涨跌幅: {basic_info.get('change_pct', 0):.2f}%")
            
            # 深度报价
            depth_quotes = deep_data.get('depth_quotes', {})
            if depth_quotes:
                logger.info(f"   买卖价差: ¥{depth_quotes.get('spread', 0):.3f}")
                logger.info(f"   总买量: {depth_quotes.get('total_buy_volume', 0):,}")
            
            # 市场指标
            market_metrics = deep_data.get('market_metrics', {})
            if market_metrics:
                logger.info(f"   振幅: {market_metrics.get('amplitude', 0):.2f}%")
                logger.info(f"   相对位置: {market_metrics.get('relative_position', 0):.1%}")
        else:
            logger.warning("⚠️ 未获取到深度行情数据")
            
        return bool(deep_data)
        
    except Exception as e:
        logger.error(f"❌ 深度行情数据测试失败: {e}")
        return False

def test_sentiment_analysis():
    """测试情感分析功能"""
    logger.info("🧪 开始测试情感分析功能...")
    
    try:
        sentiment_analyzer = SentimentAnalyzer()
        symbol = '000001'  # 平安银行
        
        # 测试情感分析
        sentiment_result = sentiment_analyzer.analyze_sentiment(symbol)
        
        if sentiment_result and 'error' not in sentiment_result:
            logger.info(f"✅ 情感分析完成")
            
            # 总体情感
            overall = sentiment_result.get('overall_sentiment', {})
            logger.info(f"   总体情感: {overall.get('sentiment_label', 'N/A')}")
            logger.info(f"   情感得分: {overall.get('sentiment_score', 0):.2f}")
            logger.info(f"   置信度: {overall.get('confidence', 0):.1%}")
            
            # 新闻情感
            news_sentiment = sentiment_result.get('news_sentiment', {})
            logger.info(f"   新闻数量: {news_sentiment.get('news_count', 0)}")
            logger.info(f"   新闻情感: {news_sentiment.get('sentiment_label', 'N/A')}")
            logger.info(f"   数据源: {news_sentiment.get('data_source', 'N/A')}")
            
            # 情感预警
            alerts = sentiment_result.get('alerts', [])
            if alerts:
                logger.info(f"   情感预警: {len(alerts)} 条")
                for alert in alerts:
                    logger.info(f"     - {alert.get('message', 'N/A')} ({alert.get('level', 'N/A')})")
        else:
            logger.warning(f"⚠️ 情感分析失败: {sentiment_result.get('error', '未知错误')}")
            
        return sentiment_result and 'error' not in sentiment_result
        
    except Exception as e:
        logger.error(f"❌ 情感分析测试失败: {e}")
        return False

def test_multi_source_integration():
    """测试多源数据融合"""
    logger.info("🧪 开始测试多源数据融合...")
    
    try:
        data_manager = get_enhanced_data_manager()
        symbol = '000001'  # 平安银行
        
        # 测试综合股票信息
        comprehensive_data = data_manager.get_comprehensive_stock_info(symbol)
        
        if comprehensive_data:
            logger.info(f"✅ 多源数据融合成功")
            logger.info(f"   股票代码: {comprehensive_data.get('symbol', 'N/A')}")
            logger.info(f"   主数据源: {comprehensive_data.get('primary_source', 'N/A')}")
            logger.info(f"   数据源列表: {comprehensive_data.get('sources', [])}")
            logger.info(f"   数据质量评分: {comprehensive_data.get('data_quality_score', 0):.2f}")
            
            if 'current_price' in comprehensive_data:
                logger.info(f"   当前价格: ¥{comprehensive_data['current_price']:.2f}")
            
            if 'change_pct' in comprehensive_data:
                logger.info(f"   涨跌幅: {comprehensive_data['change_pct']:.2f}%")
        else:
            logger.warning("⚠️ 多源数据融合失败")
        
        # 测试综合新闻
        comprehensive_news = data_manager.get_comprehensive_news(symbol, limit=5)
        
        if comprehensive_news:
            logger.info(f"✅ 综合新闻获取成功: {len(comprehensive_news)} 条")
        else:
            logger.warning("⚠️ 综合新闻获取失败")
        
        return bool(comprehensive_data) and bool(comprehensive_news)
        
    except Exception as e:
        logger.error(f"❌ 多源数据融合测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始执行新浪财经增强功能完整测试...")
    
    test_results = {}
    
    # 执行各项测试
    tests = [
        ("新浪财经新闻增强", test_sina_news_enhancement),
        ("新浪财经深度行情", test_sina_deep_market_data),
        ("情感分析功能", test_sentiment_analysis),
        ("多源数据融合", test_multi_source_integration)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"开始测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            test_results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"{test_name}: ❌ 异常 - {e}")
    
    # 汇总测试结果
    logger.info(f"\n{'='*50}")
    logger.info("📊 测试结果汇总")
    logger.info(f"{'='*50}")
    
    passed_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n总体结果: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有测试均通过！新浪财经增强功能集成成功！")
        return True
    else:
        logger.warning(f"⚠️ 有 {total_count - passed_count} 项测试未通过")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)