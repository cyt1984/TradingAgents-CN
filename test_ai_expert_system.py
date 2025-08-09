#!/usr/bin/env python3
"""
AI专家系统完整工作流程测试
验证AI增强选股系统的各个组件是否正常工作
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.selectors.stock_selector import get_stock_selector, SelectionCriteria
from tradingagents.selectors.ai_strategies.ai_strategy_manager import AIMode, AISelectionConfig
from tradingagents.selectors.ai_debug_tools import get_ai_debug_tools

logger = get_logger('test')


def test_ai_system_initialization():
    """测试AI系统初始化"""
    print("🔧 测试1: AI系统初始化")
    print("-" * 50)
    
    try:
        # 初始化选股引擎
        selector = get_stock_selector()
        print("✅ 选股引擎初始化成功")
        
        # 获取AI状态
        ai_status = selector.get_ai_performance_summary()
        print(f"AI引擎状态: {ai_status.get('ai_enabled', False)}")
        
        engines_status = ai_status.get('ai_engines_status', {})
        for engine_name, status in engines_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {engine_name}")
        
        availability = ai_status.get('engine_availability', {})
        available_count = availability.get('available_count', 0)
        total_count = availability.get('total_count', 4)
        print(f"AI引擎可用性: {available_count}/{total_count} ({availability.get('availability_rate', 0):.1f}%)")
        
        return True
    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        return False


def test_basic_stock_selection():
    """测试基础选股功能"""
    print("\n📊 测试2: 基础选股功能")
    print("-" * 50)
    
    try:
        selector = get_stock_selector()
        
        # 测试快速选股
        start_time = time.time()
        result = selector.quick_select(
            min_score=60,
            min_market_cap=10.0,
            max_pe_ratio=50.0,
            grades=['A+', 'A', 'A-', 'B+', 'B'],
            limit=10
        )
        end_time = time.time()
        
        print(f"快速选股结果:")
        print(f"  候选股票: {result.total_candidates}")
        print(f"  筛选结果: {result.filtered_count}")
        print(f"  成功率: {result.summary.get('success_rate', 0):.1f}%")
        print(f"  执行时间: {end_time - start_time:.2f}秒")
        print(f"  股票列表: {result.symbols[:5]}" + ("..." if len(result.symbols) > 5 else ""))
        
        return len(result.symbols) > 0
    except Exception as e:
        print(f"❌ 基础选股测试失败: {e}")
        return False


def test_ai_enhanced_selection():
    """测试AI增强选股"""
    print("\n🤖 测试3: AI增强选股")
    print("-" * 50)
    
    try:
        selector = get_stock_selector()
        
        # 检查AI是否可用
        ai_status = selector.get_ai_performance_summary()
        if not ai_status.get('ai_enabled', False):
            print("⚠️ AI功能不可用，跳过AI增强测试")
            return True
        
        # 测试AI增强选股
        start_time = time.time()
        result = selector.ai_enhanced_select(
            min_ai_score=60,
            min_confidence=0.4,
            max_risk_level="中高风险",
            limit=5
        )
        end_time = time.time()
        
        print(f"AI增强选股结果:")
        print(f"  候选股票: {result.total_candidates}")
        print(f"  筛选结果: {result.filtered_count}")
        print(f"  执行时间: {end_time - start_time:.2f}秒")
        print(f"  股票列表: {result.symbols}")
        
        # 检查AI分析数据
        if not result.data.empty:
            ai_columns = ['ai_overall_score', 'ai_confidence', 'ai_recommendation', 'ai_risk_assessment']
            available_ai_columns = [col for col in ai_columns if col in result.data.columns]
            print(f"  AI分析列: {available_ai_columns}")
            
            if 'ai_overall_score' in result.data.columns:
                ai_scores = result.data['ai_overall_score'].dropna()
                if not ai_scores.empty:
                    print(f"  AI平均评分: {ai_scores.mean():.1f}")
                    print(f"  AI最高评分: {ai_scores.max():.1f}")
        
        return len(result.symbols) > 0
    except Exception as e:
        print(f"❌ AI增强选股测试失败: {e}")
        return False


def test_expert_committee():
    """测试专家委员会选股"""
    print("\n👥 测试4: 专家委员会选股")
    print("-" * 50)
    
    try:
        selector = get_stock_selector()
        
        # 检查专家委员会是否可用
        ai_status = selector.get_ai_performance_summary()
        engines_status = ai_status.get('ai_engines_status', {})
        
        if not engines_status.get('expert_committee', False):
            print("⚠️ 专家委员会不可用，跳过测试")
            return True
        
        # 测试专家委员会选股
        start_time = time.time()
        result = selector.expert_committee_select(
            min_expert_score=70,
            min_consensus="存在分歧",
            limit=3
        )
        end_time = time.time()
        
        print(f"专家委员会选股结果:")
        print(f"  候选股票: {result.total_candidates}")
        print(f"  筛选结果: {result.filtered_count}")
        print(f"  执行时间: {end_time - start_time:.2f}秒")
        print(f"  股票列表: {result.symbols}")
        
        # 检查专家委员会特定数据
        if not result.data.empty and 'expert_committee_score' in result.data.columns:
            expert_scores = result.data['expert_committee_score'].dropna()
            if not expert_scores.empty:
                print(f"  专家委员会平均评分: {expert_scores.mean():.1f}")
        
        return True
    except Exception as e:
        print(f"❌ 专家委员会测试失败: {e}")
        return False


def test_ai_debugging_tools():
    """测试AI调试工具"""
    print("\n🔧 测试5: AI调试工具")
    print("-" * 50)
    
    try:
        debug_tools = get_ai_debug_tools()
        
        # 运行系统检查
        print("执行AI系统检查...")
        check_result = debug_tools.run_full_system_check()
        
        overall_status = check_result.get('overall_status', 'unknown')
        print(f"系统总体状态: {overall_status}")
        
        recommendations = check_result.get('recommendations', [])
        if recommendations:
            print("系统建议:")
            for i, rec in enumerate(recommendations[:3], 1):  # 显示前3个建议
                print(f"  {i}. {rec}")
        
        # 测试缓存清理
        print("执行缓存清理...")
        clear_result = debug_tools.clear_ai_caches()
        cleared_caches = clear_result.get('cleared_caches', [])
        print(f"已清理缓存: {cleared_caches}")
        
        return True
    except Exception as e:
        print(f"❌ 调试工具测试失败: {e}")
        return False


def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 AI专家系统综合测试开始")
    print("=" * 60)
    print(f"测试时间: {datetime.now()}")
    print("=" * 60)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("AI系统初始化", test_ai_system_initialization),
        ("基础选股功能", test_basic_stock_selection),
        ("AI增强选股", test_ai_enhanced_selection),
        ("专家委员会", test_expert_committee),
        ("AI调试工具", test_ai_debugging_tools)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 显示测试总结
    print("\n" + "=" * 60)
    print("🎯 测试总结")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    success_rate = passed_tests / len(test_results) * 100
    print(f"\n📊 总体测试结果: {passed_tests}/{len(test_results)} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 AI专家系统运行状态优秀！")
    elif success_rate >= 60:
        print("👍 AI专家系统基本正常，部分功能需要优化")
    else:
        print("⚠️ AI专家系统存在较多问题，需要进一步检查")
    
    return success_rate >= 60


if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        sys.exit(1)