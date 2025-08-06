#!/usr/bin/env python3
"""
数据源测试脚本
测试所有数据源的数据质量和可用性
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.web_data_interface import get_web_data_interface
from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager


def test_data_sources():
    """测试所有数据源"""
    print("=" * 60)
    print("📊 数据源测试开始")
    print("=" * 60)
    
    # 初始化接口
    web_interface = get_web_data_interface()
    data_manager = get_enhanced_data_manager()
    
    # 测试股票
    test_symbols = ['000001', '600000', '300001', 'AAPL', 'TSLA']
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sources_status': {},
        'symbol_tests': {},
        'summary': {}
    }
    
    # 测试数据源状态
    print("\n🔍 检查数据源状态...")
    sources_status = web_interface.get_data_sources_status()
    results['sources_status'] = sources_status
    
    print(f"📊 总数据源数: {sources_status['total_sources']}")
    print(f"✅ 可用数据源: {sources_status['total_active']}")
    
    for source, info in sources_status['sources_status'].items():
        status_icon = "✅" if info['is_active'] else "❌"
        print(f"{status_icon} {info['name']}: {info['status']}")
    
    # 测试具体股票数据
    print(f"\n📈 测试股票数据获取...")
    
    for symbol in test_symbols:
        print(f"\n🔍 测试股票: {symbol}")
        
        try:
            # 获取综合股票信息
            stock_data = web_interface.get_stock_display_data(symbol)
            
            if stock_data.get('status') == 'success':
                print(f"  ✅ 成功获取数据")
                print(f"  📊 股票名称: {stock_data['name']}")
                print(f"  💰 当前价格: {stock_data['price_display']}")
                print(f"  📈 涨跌幅: {stock_data['change_pct_display']}")
                print(f"  📊 数据质量: {stock_data['quality_grade']} ({stock_data['data_quality_score']:.2f})")
                print(f"  🔄 数据源: {stock_data['sources_display']}")
                
                results['symbol_tests'][symbol] = {
                    'status': 'success',
                    'name': stock_data['name'],
                    'price': stock_data['current_price'],
                    'change_pct': stock_data['change_pct'],
                    'data_quality_score': stock_data['data_quality_score'],
                    'sources': stock_data['data_sources'],
                    'primary_source': stock_data['primary_source']
                }
            else:
                print(f"  ❌ 获取失败: {stock_data.get('error', '未知错误')}")
                results['symbol_tests'][symbol] = {
                    'status': 'failed',
                    'error': stock_data.get('error', '未知错误')
                }
                
        except Exception as e:
            print(f"  ❌ 测试异常: {str(e)}")
            results['symbol_tests'][symbol] = {
                'status': 'error',
                'error': str(e)
            }
    
    # 测试增强功能
    print(f"\n🚀 测试增强功能...")
    
    # 测试新闻获取
    print(f"\n📰 测试新闻数据获取...")
    try:
        news_data = data_manager.get_comprehensive_news('000001', limit=5)
        print(f"  ✅ 成功获取新闻: {len(news_data)} 条")
        for i, news in enumerate(news_data[:3], 1):
            print(f"    {i}. {news.get('title', '')[:50]}...")
    except Exception as e:
        print(f"  ❌ 新闻获取失败: {str(e)}")
    
    # 测试情绪分析
    print(f"\n😊 测试情绪分析...")
    try:
        sentiment_data = data_manager.get_comprehensive_sentiment('000001')
        score = sentiment_data.get('overall_sentiment', 0)
        print(f"  ✅ 情绪评分: {score:.2f}")
        print(f"  ✅ 数据源: {sentiment_data.get('sources', [])}")
    except Exception as e:
        print(f"  ❌ 情绪分析失败: {str(e)}")
    
    # 测试社交讨论
    print(f"\n💬 测试社交讨论...")
    try:
        social_data = data_manager.get_social_discussions('000001', limit=5)
        print(f"  ✅ 成功获取讨论: {len(social_data)} 条")
    except Exception as e:
        print(f"  ❌ 社交讨论获取失败: {str(e)}")
    
    # 生成测试报告
    print(f"\n📊 生成测试报告...")
    
    successful_symbols = [s for s, data in results['symbol_tests'].items() if data.get('status') == 'success']
    failed_symbols = [s for s, data in results['symbol_tests'].items() if data.get('status') != 'success']
    
    results['summary'] = {
        'total_symbols': len(test_symbols),
        'successful_symbols': len(successful_symbols),
        'failed_symbols': len(failed_symbols),
        'success_rate': len(successful_symbols) / len(test_symbols) if test_symbols else 0,
        'active_sources': sources_status['total_active'],
        'total_sources': sources_status['total_sources']
    }
    
    print("\n" + "=" * 60)
    print("📋 测试总结报告")
    print("=" * 60)
    print(f"📊 测试时间: {results['timestamp']}")
    print(f"📈 测试股票数: {results['summary']['total_symbols']}")
    print(f"✅ 成功获取: {results['summary']['successful_symbols']}")
    print(f"❌ 获取失败: {results['summary']['failed_symbols']}")
    print(f"📊 成功率: {results['summary']['success_rate']:.1%}")
    print(f"🔄 可用数据源: {results['summary']['active_sources']}/{results['summary']['total_sources']}")
    
    # 按数据源统计
    source_counts = {}
    for symbol, data in results['symbol_tests'].items():
        if data.get('status') == 'success':
            sources = data.get('sources', [])
            for source in sources:
                source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\n📊 数据源使用情况:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  📊 {source}: {count} 次")
    
    # 保存测试结果到文件
    try:
        import json
        with open('data_source_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 测试结果已保存到: data_source_test_results.json")
    except Exception as e:
        print(f"⚠️ 保存测试结果失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 数据源测试完成")
    print("=" * 60)
    
    return results


def test_individual_sources():
    """单独测试每个数据源"""
    print("\n🔍 单独测试各数据源...")
    
    try:
        from tradingagents.dataflows.eastmoney_utils import get_eastmoney_provider
        from tradingagents.dataflows.tencent_utils import get_tencent_provider
        from tradingagents.dataflows.sina_utils import get_sina_provider
        
        # 测试东方财富
        print(f"\n📊 测试东方财富数据源...")
        try:
            provider = get_eastmoney_provider()
            data = provider.get_stock_info('000001')
            if data:
                print(f"  ✅ 东方财富: 成功获取 {data.get('name', '股票')} ¥{data.get('current_price', 0)}")
            else:
                print(f"  ❌ 东方财富: 无数据返回")
        except Exception as e:
            print(f"  ❌ 东方财富: {str(e)}")
        
        # 测试腾讯财经
        print(f"\n📊 测试腾讯财经数据源...")
        try:
            provider = get_tencent_provider()
            data = provider.get_stock_info('000001')
            if data:
                print(f"  ✅ 腾讯财经: 成功获取 {data.get('name', '股票')} ¥{data.get('current_price', 0)}")
            else:
                print(f"  ❌ 腾讯财经: 无数据返回")
        except Exception as e:
            print(f"  ❌ 腾讯财经: {str(e)}")
        
        # 测试新浪财经
        print(f"\n📊 测试新浪财经数据源...")
        try:
            provider = get_sina_provider()
            data = provider.get_stock_info('000001')
            if data:
                print(f"  ✅ 新浪财经: 成功获取 {data.get('name', '股票')} ¥{data.get('current_price', 0)}")
            else:
                print(f"  ❌ 新浪财经: 无数据返回")
        except Exception as e:
            print(f"  ❌ 新浪财经: {str(e)}")
            
    except Exception as e:
        print(f"❌ 单独测试失败: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始数据源测试...")
    
    # 运行综合测试
    results = test_data_sources()
    
    # 运行单独测试
    test_individual_sources()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
    
    # 如果成功率低于80%，给出建议
    if results['summary']['success_rate'] < 0.8:
        print("⚠️ 警告：数据获取成功率低于80%")
        print("💡 建议：")
        print("   1. 检查网络连接")
        print("   2. 验证API配置")
        print("   3. 查看详细日志")
    else:
        print("✅ 数据获取表现良好，可以正常使用")