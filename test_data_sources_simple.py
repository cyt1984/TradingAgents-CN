#!/usr/bin/env python3
"""
简化版数据源测试脚本
测试核心数据源功能，避免依赖问题
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置编码
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_basic_data_sources():
    """测试基础数据源"""
    print("=" * 50)
    print("数据源测试开始")
    print("=" * 50)
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {},
        'summary': {}
    }
    
    # 测试东方财富
    print("\n[东方财富数据源测试]")
    try:
        from tradingagents.dataflows.eastmoney_utils import get_eastmoney_provider
        provider = get_eastmoney_provider()
        
        # 测试股票信息
        stock_info = provider.get_stock_info('000001')
        if stock_info:
            print(f"  成功: {stock_info.get('name', '未知')} - ￥{stock_info.get('current_price', 0)}")
            results['tests']['eastmoney'] = {
                'status': 'success',
                'name': stock_info.get('name'),
                'price': stock_info.get('current_price', 0),
                'change_pct': stock_info.get('change_pct', 0)
            }
        else:
            print("  失败: 无数据返回")
            results['tests']['eastmoney'] = {'status': 'failed', 'error': 'no_data'}
            
    except Exception as e:
        print(f"  错误: {str(e)}")
        results['tests']['eastmoney'] = {'status': 'error', 'error': str(e)}
    
    # 测试腾讯财经
    print("\n[腾讯财经数据源测试]")
    try:
        from tradingagents.dataflows.tencent_utils import get_tencent_provider
        provider = get_tencent_provider()
        
        stock_info = provider.get_stock_info('000001')
        if stock_info:
            print(f"  成功: {stock_info.get('name', '未知')} - ￥{stock_info.get('current_price', 0)}")
            results['tests']['tencent'] = {
                'status': 'success',
                'name': stock_info.get('name'),
                'price': stock_info.get('current_price', 0),
                'change_pct': stock_info.get('change_pct', 0)
            }
        else:
            print("  失败: 无数据返回")
            results['tests']['tencent'] = {'status': 'failed', 'error': 'no_data'}
            
    except Exception as e:
        print(f"  错误: {str(e)}")
        results['tests']['tencent'] = {'status': 'error', 'error': str(e)}
    
    # 测试新浪财经
    print("\n[新浪财经数据源测试]")
    try:
        from tradingagents.dataflows.sina_utils import get_sina_provider
        provider = get_sina_provider()
        
        stock_info = provider.get_stock_info('000001')
        if stock_info:
            print(f"  成功: {stock_info.get('name', '未知')} - ￥{stock_info.get('current_price', 0)}")
            results['tests']['sina'] = {
                'status': 'success',
                'name': stock_info.get('name'),
                'price': stock_info.get('current_price', 0),
                'change_pct': stock_info.get('change_pct', 0)
            }
        else:
            print("  失败: 无数据返回")
            results['tests']['sina'] = {'status': 'failed', 'error': 'no_data'}
            
    except Exception as e:
        print(f"  错误: {str(e)}")
        results['tests']['sina'] = {'status': 'error', 'error': str(e)}
    
    # 测试增量数据管理器
    print("\n[增强数据管理器测试]")
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        manager = get_enhanced_data_manager()
        
        # 测试综合股票信息
        comprehensive_data = manager.get_comprehensive_stock_info('000001')
        if comprehensive_data and comprehensive_data.get('sources'):
            print(f"  成功: 综合数据来自 {comprehensive_data.get('sources', [])}")
            print(f"  数据源数: {len(comprehensive_data.get('sources', []))}")
            results['tests']['enhanced_manager'] = {
                'status': 'success',
                'sources': comprehensive_data.get('sources', []),
                'quality_score': comprehensive_data.get('data_quality_score', 0)
            }
        else:
            print("  失败: 无综合数据")
            results['tests']['enhanced_manager'] = {'status': 'failed', 'error': 'no_data'}
            
    except Exception as e:
        print(f"  错误: {str(e)}")
        results['tests']['enhanced_manager'] = {'status': 'error', 'error': str(e)}
    
    # 生成总结报告
    print("\n" + "=" * 50)
    print("测试总结报告")
    print("=" * 50)
    
    successful_tests = [k for k, v in results['tests'].items() if v.get('status') == 'success']
    failed_tests = [k for k, v in results['tests'].items() if v.get('status') != 'success']
    
    results['summary'] = {
        'total_tests': len(results['tests']),
        'successful_tests': len(successful_tests),
        'failed_tests': len(failed_tests),
        'success_rate': len(successful_tests) / len(results['tests']) if results['tests'] else 0
    }
    
    print(f"测试时间: {results['timestamp']}")
    print(f"总测试数: {results['summary']['total_tests']}")
    print(f"成功测试: {results['summary']['successful_tests']}")
    print(f"失败测试: {results['summary']['failed_tests']}")
    print(f"成功率: {results['summary']['success_rate']:.1%}")
    
    print(f"\n详细结果:")
    for source, test_result in results['tests'].items():
        status = test_result.get('status', 'unknown')
        icon = "✅" if status == 'success' else "❌"
        print(f"{icon} {source}: {status}")
        
        if status == 'success' and 'price' in test_result:
            print(f"   价格: ￥{test_result['price']:.2f} ({test_result.get('change_pct', 0):+.2f}%)")
    
    # 保存结果
    try:
        with open('data_source_test_simple.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: data_source_test_simple.json")
    except Exception as e:
        print(f"保存结果失败: {str(e)}")
    
    # 给出建议
    print("\n" + "=" * 50)
    print("建议:")
    
    if results['summary']['success_rate'] >= 0.8:
        print("✅ 数据源工作正常，可以开始使用多数据源功能")
    elif results['summary']['success_rate'] >= 0.5:
        print("⚠️ 部分数据源有问题，建议检查网络连接")
    else:
        print("❌ 数据源问题严重，建议检查配置和网络")
    
    print("=" * 50)
    
    return results


if __name__ == "__main__":
    print("开始数据源测试...")
    results = test_basic_data_sources()
    print("测试完成！")