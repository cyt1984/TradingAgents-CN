#!/usr/bin/env python3
"""
最终测试脚本 - 验证多数据源系统功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_data_system():
    """测试增强数据系统"""
    print("=" * 50)
    print("增强数据系统测试")
    print("=" * 50)
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {},
        'summary': {}
    }
    
    # 测试1: 增强数据管理器
    print("\n[1] 测试增强数据管理器")
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        manager = get_enhanced_data_manager()
        
        # 获取股票数据
        data = manager.get_comprehensive_stock_info('000001')
        if data and data.get('sources'):
            print(f"  ✅ 成功获取数据: {data.get('name', '未知股票')}")
            print(f"  📊 数据源: {data.get('sources', [])}")
            print(f"  💰 价格: ¥{data.get('current_price', 0)}")
            print(f"  📈 质量评分: {data.get('data_quality_score', 0):.2f}")
            results['tests']['enhanced_manager'] = {
                'status': 'success',
                'sources': data.get('sources', []),
                'price': data.get('current_price', 0),
                'quality_score': data.get('data_quality_score', 0)
            }
        else:
            print("  ❌ 无法获取数据")
            results['tests']['enhanced_manager'] = {'status': 'failed'}
            
    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")
        results['tests']['enhanced_manager'] = {'status': 'error', 'error': str(e)}
    
    # 测试2: Web数据接口
    print("\n[2] 测试Web数据接口")
    try:
        from tradingagents.dataflows.web_data_interface import get_web_data_interface
        web_interface = get_web_data_interface()
        
        # 获取展示数据
        display_data = web_interface.get_stock_display_data('000001')
        if display_data.get('status') == 'success':
            print(f"  ✅ 成功获取展示数据: {display_data.get('name')}")
            print(f"  💰 价格: {display_data.get('price_display')}")
            print(f"  📊 质量等级: {display_data.get('quality_grade')}")
            print(f"  🔄 数据源: {display_data.get('sources_display')}")
            results['tests']['web_interface'] = {
                'status': 'success',
                'name': display_data.get('name'),
                'price': display_data.get('current_price'),
                'quality_grade': display_data.get('quality_grade')
            }
        else:
            print("  ❌ 无法获取展示数据")
            results['tests']['web_interface'] = {'status': 'failed'}
            
    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")
        results['tests']['web_interface'] = {'status': 'error', 'error': str(e)}
    
    # 测试3: 数据源状态
    print("\n[3] 测试数据源状态")
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        manager = get_enhanced_data_manager()
        
        status = manager.get_provider_status()
        print(f"  📊 总数据源: {len(status)}")
        
        active_sources = [k for k, v in status.items() if v]
        print(f"  ✅ 可用数据源: {len(active_sources)}")
        
        for source, is_active in status.items():
            print(f"     {source}: {'✅' if is_active else '❌'}")
            
        results['tests']['data_sources'] = {
            'status': 'success',
            'total': len(status),
            'active': len(active_sources),
            'sources': status
        }
        
    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")
        results['tests']['data_sources'] = {'status': 'error', 'error': str(e)}
    
    # 测试4: 多股票测试
    print("\n[4] 测试多股票支持")
    test_symbols = ['000001', '600000', '300001']
    symbol_results = {}
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        manager = get_enhanced_data_manager()
        
        for symbol in test_symbols:
            try:
                data = manager.get_comprehensive_stock_info(symbol)
                if data and data.get('sources'):
                    symbol_results[symbol] = {
                        'status': 'success',
                        'name': data.get('name'),
                        'price': data.get('current_price'),
                        'sources': data.get('sources')
                    }
                    print(f"  ✅ {symbol}: {data.get('name')} ¥{data.get('current_price')}")
                else:
                    symbol_results[symbol] = {'status': 'failed'}
                    print(f"  ❌ {symbol}: 获取失败")
            except Exception as e:
                symbol_results[symbol] = {'status': 'error', 'error': str(e)}
                print(f"  ❌ {symbol}: {str(e)}")
                
        results['tests']['multi_symbols'] = symbol_results
        
    except Exception as e:
        print(f"  ❌ 多股票测试错误: {str(e)}")
        results['tests']['multi_symbols'] = {'status': 'error', 'error': str(e)}
    
    # 生成总结
    print("\n" + "=" * 50)
    print("测试总结报告")
    print("=" * 50)
    
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
    
    # 保存结果
    try:
        with open('final_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: final_test_results.json")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")
    
    return results

if __name__ == "__main__":
    print("开始最终测试...")
    results = test_enhanced_data_system()
    print("\n测试完成！")
    
    if results['summary']['success_rate'] >= 0.8:
        print("✅ 系统运行正常，可以开始使用多数据源功能")
    else:
        print("⚠️ 系统存在问题，建议检查配置和网络连接")