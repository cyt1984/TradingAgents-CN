#!/usr/bin/env python3
"""
快速测试新数据源的使用方法
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_individual_sources():
    """测试各个数据源"""
    print("🔍 测试各个数据源...")
    
    # 测试东方财富
    try:
        from tradingagents.dataflows.eastmoney_utils import get_eastmoney_stock_info, get_eastmoney_news
        
        print("\n📊 东方财富 - 股票信息:")
        stock_info = get_eastmoney_stock_info('000001')
        if stock_info:
            print(f"  股票名称: {stock_info.get('name', 'N/A')}")
            print(f"  当前价格: {stock_info.get('current_price', 'N/A')}")
            print(f"  涨跌幅: {stock_info.get('change_pct', 0):.2f}%")
        
        print("\n📰 东方财富 - 新闻:")
        news = get_eastmoney_news('000001', 3)
        for i, item in enumerate(news[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 东方财富测试失败: {e}")

def test_enhanced_manager():
    """测试增强数据管理器"""
    print("\n🚀 测试增强数据管理器...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        manager = get_enhanced_data_manager()
        
        # 获取综合股票信息
        print("\n📊 综合股票信息:")
        stock_info = manager.get_comprehensive_stock_info('000001')
        if stock_info:
            print(f"  股票代码: {stock_info.get('symbol', 'N/A')}")
            print(f"  股票名称: {stock_info.get('name', 'N/A')}")
            print(f"  当前价格: {stock_info.get('current_price', 'N/A')}")
            print(f"  数据来源: {', '.join(stock_info.get('sources', []))}")
        
        # 获取综合新闻
        print("\n📰 综合新闻:")
        news = manager.get_comprehensive_news('000001', 5)
        print(f"  获取到 {len(news)} 条新闻")
        for i, item in enumerate(news[:3], 1):
            source = item.get('data_source', item.get('source', '未知'))
            print(f"  {i}. [{source}] {item.get('title', 'N/A')}")
        
        # 获取市场情绪
        print("\n😊 市场情绪分析:")
        sentiment = manager.get_comprehensive_sentiment('000001')
        if sentiment:
            score = sentiment.get('overall_sentiment', 0)
            confidence = sentiment.get('confidence', 0)
            sources = ', '.join(sentiment.get('sources', []))
            print(f"  整体情绪: {score:.3f}")
            print(f"  置信度: {confidence:.2f}")
            print(f"  数据来源: {sources}")
        
    except Exception as e:
        print(f"❌ 增强数据管理器测试失败: {e}")

def test_enhanced_tools():
    """测试增强工具"""
    print("\n🛠️ 测试增强分析工具...")
    
    try:
        from tradingagents.tools.enhanced_news_tool import (
            get_enhanced_stock_news,
            get_enhanced_market_sentiment
        )
        
        # 测试增强新闻工具
        print("\n📰 增强新闻工具:")
        news_report = get_enhanced_stock_news('000001', 10)
        print(f"  报告长度: {len(news_report)} 字符")
        print("  报告预览:")
        print("  " + news_report[:300].replace('\n', '\n  ') + "...")
        
        # 测试情绪分析工具
        print("\n😊 情绪分析工具:")
        sentiment_report = get_enhanced_market_sentiment('000001')
        print(f"  报告长度: {len(sentiment_report)} 字符")
        print("  报告预览:")
        print("  " + sentiment_report[:300].replace('\n', '\n  ') + "...")
        
    except Exception as e:
        print(f"❌ 增强工具测试失败: {e}")

def main():
    """主函数"""
    print("🎯 TradingAgents-CN 新数据源快速测试")
    print("=" * 50)
    
    # 测试各个数据源
    test_individual_sources()
    
    # 测试增强数据管理器
    test_enhanced_manager()
    
    # 测试增强工具
    test_enhanced_tools()
    
    print("\n" + "=" * 50)
    print("✅ 快速测试完成！")
    print("\n💡 使用建议:")
    print("1. 直接使用现有的Web界面或CLI，新数据源已自动集成")
    print("2. 分析A股时会自动使用多个数据源获取更丰富的信息")
    print("3. 如需自定义开发，可以调用增强数据管理器的API")

if __name__ == "__main__":
    main()