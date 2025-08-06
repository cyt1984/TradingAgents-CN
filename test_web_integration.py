#!/usr/bin/env python3
"""
Web界面集成测试
测试Web数据接口和增强数据管理器的集成
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_web_integration():
    """测试Web界面集成"""
    print("=" * 60)
    print("Web界面集成测试")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {},
        'summary': {}
    }
    
    # 测试1: Web数据接口
    print("\n[1] 测试Web数据接口")
    try:
        from tradingagents.dataflows.web_data_interface import get_web_data_interface
        web_interface = get_web_data_interface()
        
        # 获取股票展示数据
        display_data = web_interface.get_stock_display_data('000001')
        
        if display_data.get('status') == 'success':
            print(f"  ✅ 成功获取展示数据")
            print(f"  📊 股票: {display_data.get('name')} ({display_data.get('symbol')})")
            print(f"  💰 价格: {display_data.get('price_display')}")
            print(f"  📈 涨跌幅: {display_data.get('change_pct_display')}")
            print(f"  📊 质量: {display_data.get('quality_grade')} (评分: {display_data.get('data_quality_score')})")
            print(f"  🔄 数据源: {display_data.get('sources_display')}")
            
            results['tests']['web_interface'] = {
                'status': 'success',
                'symbol': display_data.get('symbol'),
                'name': display_data.get('name'),
                'price': display_data.get('current_price'),
                'change_pct': display_data.get('change_pct'),
                'quality_score': display_data.get('data_quality_score'),
                'quality_grade': display_data.get('quality_grade'),
                'data_sources': display_data.get('data_sources')
            }
        else:
            print(f"  ❌ 获取失败: {display_data.get('error')}")
            results['tests']['web_interface'] = {'status': 'failed', 'error': display_data.get('error')}
            
    except Exception as e:
        print(f"  ❌ Web接口错误: {str(e)}")
        results['tests']['web_interface'] = {'status': 'error', 'error': str(e)}
    
    # 测试2: 增强股票数据
    print("\n[2] 测试增强股票数据")
    try:
        enhanced_data = web_interface.get_enhanced_stock_data('000001', include_news=True, include_sentiment=True)
        
        if 'error' not in enhanced_data:
            stock_info = enhanced_data.get('stock_info', {})
            news_count = len(enhanced_data.get('news_data', []))
            sentiment_score = enhanced_data.get('sentiment_data', {}).get('overall_sentiment', 0)
            social_count = len(enhanced_data.get('social_discussions', []))
            
            print(f"  ✅ 成功获取增强数据")
            print(f"  📊 股票信息: {stock_info.get('name')}")
            print(f"  📰 新闻数量: {news_count}")
            print(f"  😊 情绪评分: {sentiment_score:.2f}")
            print(f"  💬 社交讨论: {social_count}")
            print(f"  📊 数据汇总: {enhanced_data.get('summary', {})}")
            
            results['tests']['enhanced_data'] = {
                'status': 'success',
                'news_count': news_count,
                'sentiment_score': sentiment_score,
                'social_count': social_count,
                'data_sources': stock_info.get('data_sources', [])
            }
        else:
            print(f"  ❌ 增强数据获取失败: {enhanced_data.get('error')}")
            results['tests']['enhanced_data'] = {'status': 'failed', 'error': enhanced_data.get('error')}
            
    except Exception as e:
        print(f"  ❌ 增强数据错误: {str(e)}")
        results['tests']['enhanced_data'] = {'status': 'error', 'error': str(e)}
    
    # 测试3: 数据源状态
    print("\n[3] 测试数据源状态")
    try:
        sources_status = web_interface.get_data_sources_status()
        
        if sources_status:
            print(f"  📊 总数据源: {sources_status.get('total_sources', 0)}")
            print(f"  ✅ 可用数据源: {sources_status.get('total_active', 0)}")
            print("\n  各数据源状态:")
            
            for source, info in sources_status.get('sources_status', {}).items():
                status = "✅ 可用" if info.get('is_active') else "❌ 不可用"
                priority = info.get('priority', 99)
                print(f"    {info.get('name', source)}: {status} (优先级: {priority})")
            
            results['tests']['sources_status'] = {
                'status': 'success',
                'total_sources': sources_status.get('total_sources', 0),
                'active_sources': sources_status.get('total_active', 0),
                'sources': sources_status.get('sources_status', {})
            }
        else:
            print("  ❌ 无法获取数据源状态")
            results['tests']['sources_status'] = {'status': 'failed'}
            
    except Exception as e:
        print(f"  ❌ 数据源状态错误: {str(e)}")
        results['tests']['sources_status'] = {'status': 'error', 'error': str(e)}
    
    # 测试4: 多股票支持
    print("\n[4] 测试多股票支持")
    test_symbols = ['000001', '600000', '300001', 'AAPL', 'TSLA']
    multi_results = {}
    
    try:
        for symbol in test_symbols:
            try:
                data = web_interface.get_stock_display_data(symbol)
                if data.get('status') == 'success':
                    multi_results[symbol] = {
                        'status': 'success',
                        'name': data.get('name'),
                        'price': data.get('current_price'),
                        'change_pct': data.get('change_pct'),
                        'quality_score': data.get('data_quality_score'),
                        'data_sources': data.get('data_sources')
                    }
                    print(f"  ✅ {symbol}: {data.get('name')} ¥{data.get('current_price')} ({data.get('change_pct_display')})")
                else:
                    multi_results[symbol] = {'status': 'failed', 'error': data.get('error')}
                    print(f"  ❌ {symbol}: {data.get('error')}")
            except Exception as e:
                multi_results[symbol] = {'status': 'error', 'error': str(e)}
                print(f"  ❌ {symbol}: {str(e)}")
                
        results['tests']['multi_symbols'] = multi_results
        
    except Exception as e:
        print(f"  ❌ 多股票测试错误: {str(e)}")
        results['tests']['multi_symbols'] = {'status': 'error', 'error': str(e)}
    
    # 生成总结
    print("\n" + "=" * 60)
    print("集成测试总结报告")
    print("=" * 60)
    
    successful_tests = [k for k, v in results['tests'].items() 
                       if isinstance(v, dict) and v.get('status') == 'success']
    
    results['summary'] = {
        'total_tests': len(results['tests']),
        'successful_tests': len(successful_tests),
        'success_rate': len(successful_tests) / len(results['tests']) if results['tests'] else 0
    }
    
    print(f"测试时间: {results['timestamp']}")
    print(f"总测试数: {results['summary']['total_tests']}")
    print(f"成功测试: {results['summary']['successful_tests']}")
    print(f"成功率: {results['summary']['success_rate']:.1%}")
    
    # 分析多股票测试结果
    if 'multi_symbols' in results['tests'] and isinstance(results['tests']['multi_symbols'], dict):
        multi_results = results['tests']['multi_symbols']
        successful_symbols = [s for s, data in multi_results.items() 
                            if isinstance(data, dict) and data.get('status') == 'success']
        
        print(f"\n多股票测试:")
        print(f"  测试股票: {len(multi_results)}")
        print(f"  成功获取: {len(successful_symbols)}")
        print(f"  成功率: {len(successful_symbols)/len(multi_results):.1%}")
        
        if successful_symbols:
            print("\n  成功股票:")
            for symbol in successful_symbols[:3]:  # 只显示前3个
                data = multi_results[symbol]
                print(f"    {symbol}: {data.get('name')} ¥{data.get('price')}")
    
    # 保存结果
    try:
        with open('web_integration_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: web_integration_test_results.json")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")
    
    return results

if __name__ == "__main__":
    print("开始Web界面集成测试...")
    results = test_web_integration()
    print("\n测试完成！")
    
    if results['summary']['success_rate'] >= 0.8:
        print("✅ 系统集成成功，可以正常使用")
    else:
        print("⚠️ 系统存在问题，建议检查配置")