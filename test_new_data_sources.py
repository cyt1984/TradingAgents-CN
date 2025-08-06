#!/usr/bin/env python3
"""
新数据源测试脚本
测试东方财富、腾讯、新浪、雪球、股吧等新增数据源的功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
from tradingagents.dataflows.eastmoney_utils import get_eastmoney_stock_info, get_eastmoney_news
from tradingagents.dataflows.tencent_utils import get_tencent_stock_info, get_tencent_multiple_stocks
from tradingagents.dataflows.sina_utils import get_sina_stock_info, get_sina_stock_news
from tradingagents.dataflows.xueqiu_utils import get_xueqiu_discussions, get_xueqiu_sentiment
from tradingagents.dataflows.eastmoney_guba_utils import get_guba_discussions, get_guba_sentiment_analysis

import json
import time


def test_individual_sources():
    """测试各个数据源的单独功能"""
    test_symbol = '000001'  # 平安银行
    
    print("🚀 开始测试各个数据源...")
    print("=" * 60)
    
    # 测试东方财富
    print("\n📊 测试东方财富数据源...")
    try:
        eastmoney_info = get_eastmoney_stock_info(test_symbol)
        if eastmoney_info:
            print(f"✅ 东方财富股票信息: {eastmoney_info['name']} - {eastmoney_info['current_price']}")
        else:
            print("❌ 东方财富股票信息获取失败")
        
        eastmoney_news = get_eastmoney_news(test_symbol, 5)
        print(f"✅ 东方财富新闻数量: {len(eastmoney_news)}")
        
    except Exception as e:
        print(f"❌ 东方财富测试失败: {e}")
    
    # 测试腾讯财经
    print("\n📊 测试腾讯财经数据源...")
    try:
        tencent_info = get_tencent_stock_info(test_symbol)
        if tencent_info:
            print(f"✅ 腾讯财经股票信息: {tencent_info['name']} - {tencent_info['current_price']}")
        else:
            print("❌ 腾讯财经股票信息获取失败")
        
        # 测试批量获取
        tencent_multiple = get_tencent_multiple_stocks([test_symbol, '000002'])
        print(f"✅ 腾讯财经批量获取: {len(tencent_multiple)} 只股票")
        
    except Exception as e:
        print(f"❌ 腾讯财经测试失败: {e}")
    
    # 测试新浪财经
    print("\n📊 测试新浪财经数据源...")
    try:
        sina_info = get_sina_stock_info(test_symbol)
        if sina_info:
            print(f"✅ 新浪财经股票信息: {sina_info['name']} - {sina_info['current_price']}")
        else:
            print("❌ 新浪财经股票信息获取失败")
        
        sina_news = get_sina_stock_news(test_symbol, 3)
        print(f"✅ 新浪财经新闻数量: {len(sina_news)}")
        
    except Exception as e:
        print(f"❌ 新浪财经测试失败: {e}")
    
    # 测试雪球
    print("\n📊 测试雪球数据源...")
    try:
        xueqiu_discussions = get_xueqiu_discussions(test_symbol, 5)
        print(f"✅ 雪球讨论数量: {len(xueqiu_discussions)}")
        
        xueqiu_sentiment = get_xueqiu_sentiment(test_symbol)
        if xueqiu_sentiment:
            print(f"✅ 雪球情绪评分: {xueqiu_sentiment.get('sentiment_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 雪球测试失败: {e}")
    
    # 测试东方财富股吧
    print("\n📊 测试东方财富股吧数据源...")
    try:
        guba_discussions = get_guba_discussions(test_symbol, 5)
        print(f"✅ 股吧讨论数量: {len(guba_discussions)}")
        
        guba_sentiment = get_guba_sentiment_analysis(test_symbol)
        if guba_sentiment:
            print(f"✅ 股吧情绪评分: {guba_sentiment.get('sentiment_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 股吧测试失败: {e}")


def test_enhanced_manager():
    """测试增强数据源管理器"""
    test_symbol = '000001'
    
    print("\n\n🚀 测试增强数据源管理器...")
    print("=" * 60)
    
    try:
        manager = get_enhanced_data_manager()
        
        # 测试综合股票信息
        print("\n📊 测试综合股票信息...")
        comprehensive_info = manager.get_comprehensive_stock_info(test_symbol)
        if comprehensive_info:
            print(f"✅ 综合股票信息:")
            print(f"   股票代码: {comprehensive_info.get('symbol', 'N/A')}")
            print(f"   股票名称: {comprehensive_info.get('name', 'N/A')}")
            print(f"   当前价格: {comprehensive_info.get('current_price', 'N/A')}")
            print(f"   数据源: {comprehensive_info.get('sources', [])}")
        
        # 测试综合新闻
        print("\n📰 测试综合新闻...")
        comprehensive_news = manager.get_comprehensive_news(test_symbol, 10)
        print(f"✅ 综合新闻数量: {len(comprehensive_news)}")
        
        if comprehensive_news:
            print("   前3条新闻标题:")
            for i, news in enumerate(comprehensive_news[:3]):
                print(f"   {i+1}. {news.get('title', 'N/A')} [{news.get('data_source', 'unknown')}]")
        
        # 测试综合情绪分析
        print("\n😊 测试综合情绪分析...")
        comprehensive_sentiment = manager.get_comprehensive_sentiment(test_symbol)
        if comprehensive_sentiment:
            print(f"✅ 综合情绪分析:")
            print(f"   整体情绪评分: {comprehensive_sentiment.get('overall_sentiment', 0):.2f}")
            print(f"   置信度: {comprehensive_sentiment.get('confidence', 0):.2f}")
            print(f"   数据源: {comprehensive_sentiment.get('sources', [])}")
        
        # 测试社交讨论
        print("\n💬 测试社交讨论...")
        social_discussions = manager.get_social_discussions(test_symbol, 10)
        print(f"✅ 社交讨论数量: {len(social_discussions)}")
        
        if social_discussions:
            print("   热门讨论:")
            for i, discussion in enumerate(social_discussions[:3]):
                print(f"   {i+1}. {discussion.get('title', 'N/A')[:50]}... [{discussion.get('data_source', 'unknown')}]")
        
        # 测试市场总览
        print("\n📈 测试市场总览...")
        market_overview = manager.get_market_overview()
        if market_overview:
            print(f"✅ 市场总览:")
            print(f"   指数数量: {len(market_overview.get('indices', {}))}")
            print(f"   热门股票: {len(market_overview.get('hot_stocks', []))}")
        
        # 测试数据源状态
        print("\n🔍 数据源状态检查...")
        provider_status = manager.get_provider_status()
        print("✅ 数据源状态:")
        for source, status in provider_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {source}: {'可用' if status else '不可用'}")
        
        # 综合测试
        print("\n🧪 综合功能测试...")
        test_results = manager.test_all_providers(test_symbol)
        print("✅ 数据源测试结果:")
        for source, result in test_results.items():
            status = result.get('status', 'unknown')
            status_icon = "✅" if status == 'success' else "⚠️" if status == 'no_data' else "❌"
            print(f"   {status_icon} {source}: {status}")
        
    except Exception as e:
        print(f"❌ 增强数据源管理器测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_performance():
    """测试性能"""
    test_symbol = '000001'
    
    print("\n\n⚡ 性能测试...")
    print("=" * 60)
    
    try:
        manager = get_enhanced_data_manager()
        
        # 测试响应时间
        start_time = time.time()
        comprehensive_info = manager.get_comprehensive_stock_info(test_symbol)
        stock_time = time.time() - start_time
        
        start_time = time.time()
        comprehensive_news = manager.get_comprehensive_news(test_symbol, 20)
        news_time = time.time() - start_time
        
        start_time = time.time()
        comprehensive_sentiment = manager.get_comprehensive_sentiment(test_symbol)
        sentiment_time = time.time() - start_time
        
        print(f"✅ 性能测试结果:")
        print(f"   股票信息获取: {stock_time:.2f}秒")
        print(f"   新闻获取: {news_time:.2f}秒")
        print(f"   情绪分析: {sentiment_time:.2f}秒")
        print(f"   总耗时: {stock_time + news_time + sentiment_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")


def generate_sample_report():
    """生成样本报告"""
    test_symbol = '000001'
    
    print("\n\n📋 生成样本分析报告...")
    print("=" * 60)
    
    try:
        manager = get_enhanced_data_manager()
        
        # 获取所有数据
        stock_info = manager.get_comprehensive_stock_info(test_symbol)
        news_data = manager.get_comprehensive_news(test_symbol, 10)
        sentiment_data = manager.get_comprehensive_sentiment(test_symbol)
        discussions = manager.get_social_discussions(test_symbol, 10)
        
        report = {
            'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': test_symbol,
            'stock_info': stock_info,
            'news_count': len(news_data),
            'top_news': [news.get('title', '') for news in news_data[:5]],
            'sentiment_score': sentiment_data.get('overall_sentiment', 0),
            'sentiment_confidence': sentiment_data.get('confidence', 0),
            'discussions_count': len(discussions),
            'hot_discussions': [disc.get('title', '')[:50] for disc in discussions[:5]]
        }
        
        print("✅ 样本分析报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ 生成样本报告失败: {e}")


def main():
    """主函数"""
    print("🎯 TradingAgents-CN 新数据源功能测试")
    print("=" * 80)
    
    # 单独测试各个数据源
    test_individual_sources()
    
    # 测试增强数据源管理器
    test_enhanced_manager()
    
    # 性能测试
    test_performance()
    
    # 生成样本报告
    generate_sample_report()
    
    print("\n\n🎉 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()