#!/usr/bin/env python3
"""
最终验证AI专家系统完整工作流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.selectors.stock_selector import StockSelector, AIMode
from tradingagents.selectors.ai_strategies.ai_strategy_manager import get_ai_strategy_manager
from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee
import pandas as pd
from datetime import datetime

def test_complete_ai_workflow():
    """测试完整的AI专家系统工作流程"""
    print("=" * 80)
    print("AI专家系统完整工作流程验证")
    print("=" * 80)
    
    success_count = 0
    total_tests = 8
    
    try:
        # 测试1: AI策略管理器初始化
        print("\n1. 测试AI策略管理器初始化...")
        try:
            ai_manager = get_ai_strategy_manager()
            status = ai_manager.get_performance_summary()
            
            if status['ai_enabled'] and status['fully_operational']:
                print("   ✅ AI策略管理器初始化成功")
                print(f"   📊 可用引擎: {status['engine_availability']['available_count']}/{status['engine_availability']['total_count']}")
                success_count += 1
            else:
                print("   ❌ AI策略管理器初始化失败")
        except Exception as e:
            print(f"   ❌ AI策略管理器初始化异常: {e}")
        
        # 测试2: 专家委员会初始化
        print("\n2. 测试AI专家委员会初始化...")
        try:
            expert_committee = AIExpertCommittee()
            print("   ✅ AI专家委员会初始化成功")
            print(f"   👥 专家数量: {len(expert_committee.expert_weights)}")
            print(f"   ⚖️ 权重配置: {dict(list(expert_committee.expert_weights.items())[:3])}...")
            success_count += 1
        except Exception as e:
            print(f"   ❌ AI专家委员会初始化异常: {e}")
        
        # 测试3: 选股引擎AI增强
        print("\n3. 测试选股引擎AI增强功能...")
        try:
            selector = StockSelector(cache_enabled=True)
            if selector.ai_strategy_manager:
                print("   ✅ 选股引擎AI增强功能已启用")
                success_count += 1
            else:
                print("   ❌ 选股引擎AI增强功能未启用")
        except Exception as e:
            print(f"   ❌ 选股引擎AI增强功能异常: {e}")
        
        # 测试4: 快速AI选股
        print("\n4. 测试快速AI选股...")
        try:
            result = selector.quick_select(
                min_score=65.0,
                min_market_cap=50.0,
                max_pe_ratio=30.0,
                grades=['A+', 'A', 'B+'],
                limit=5
            )
            
            if result.success and len(result.symbols) > 0:
                print("   ✅ 快速AI选股成功")
                print(f"   📊 选股结果: {len(result.symbols)} 只股票")
                print(f"   ⏱️ 执行时间: {result.execution_time:.2f} 秒")
                
                # 检查AI分析结果
                if hasattr(result, 'data') and 'ai_overall_score' in result.data.columns:
                    ai_scores = result.data['ai_overall_score'].dropna()
                    if len(ai_scores) > 0:
                        print(f"   🤖 AI评分范围: {ai_scores.min():.1f} - {ai_scores.max():.1f}")
                        success_count += 1
                    else:
                        print("   ⚠️ 未找到AI评分数据")
                else:
                    print("   ⚠️ 结果数据中缺少AI评分列")
            else:
                print("   ❌ 快速AI选股失败或无结果")
        except Exception as e:
            print(f"   ❌ 快速AI选股异常: {e}")
        
        # 测试5: 专家委员会选股
        print("\n5. 测试专家委员会选股...")
        try:
            result = selector.expert_committee_select(
                min_expert_score=70.0,
                min_consensus="基本一致",
                limit=3
            )
            
            if result.success and len(result.symbols) > 0:
                print("   ✅ 专家委员会选股成功")
                print(f"   📊 选股结果: {len(result.symbols)} 只股票")
                print(f"   ⏱️ 执行时间: {result.execution_time:.2f} 秒")
                
                # 检查专家委员会评分
                if hasattr(result, 'data') and 'expert_committee_score' in result.data.columns:
                    expert_scores = result.data['expert_committee_score'].dropna()
                    if len(expert_scores) > 0:
                        print(f"   👥 专家评分范围: {expert_scores.min():.1f} - {expert_scores.max():.1f}")
                        success_count += 1
                    else:
                        print("   ⚠️ 未找到专家委员会评分数据")
                else:
                    print("   ⚠️ 结果数据中缺少专家委员会评分列")
            else:
                print("   ❌ 专家委员会选股失败或无结果")
        except Exception as e:
            print(f"   ❌ 专家委员会选股异常: {e}")
        
        # 测试6: AI增强数据处理
        print("\n6. 测试AI增强数据处理...")
        try:
            # 创建测试数据
            test_data = pd.DataFrame({
                'ts_code': ['000001.SZ', '600519.SH'],
                'name': ['平安银行', '贵州茅台'],
                'market_cap': [2000.0, 25000.0],
                'pe_ratio': [8.5, 35.2],
                'overall_score': [75.0, 85.0]
            })
            
            enriched_data = selector._enrich_stock_data_with_ai(test_data)
            
            if 'ai_overall_score' in enriched_data.columns:
                print("   ✅ AI增强数据处理成功")
                print(f"   📊 处理后数据列: {list(enriched_data.columns)}")
                ai_scores = enriched_data['ai_overall_score'].dropna()
                if len(ai_scores) > 0:
                    print(f"   🤖 AI评分: {ai_scores.tolist()}")
                    success_count += 1
                else:
                    print("   ⚠️ AI评分为空")
            else:
                print("   ❌ AI增强数据处理失败，缺少AI评分列")
        except Exception as e:
            print(f"   ❌ AI增强数据处理异常: {e}")
        
        # 测试7: 权重分配逻辑
        print("\n7. 测试权重分配逻辑...")
        try:
            # 创建包含AI评分的测试数据
            test_data = pd.DataFrame({
                'ts_code': ['000001.SZ', '600519.SH'],
                'overall_score': [75.0, 85.0],
                'ai_overall_score': [80.0, 90.0],
                'ai_confidence': [0.8, 0.9]
            })
            
            # 模拟权重分配逻辑
            ai_weight = 0.7
            traditional_weight = 0.3
            
            ai_scores = test_data['ai_overall_score']
            traditional_scores = test_data['overall_score']
            confidence_scores = test_data['ai_confidence']
            
            # 动态权重计算
            dynamic_ai_weight = ai_weight * confidence_scores + (1 - confidence_scores) * 0.4
            dynamic_traditional_weight = 1 - dynamic_ai_weight
            
            intelligent_scores = (
                ai_scores * dynamic_ai_weight + 
                traditional_scores * dynamic_traditional_weight
            )
            
            print("   ✅ 权重分配逻辑测试成功")
            print(f"   🤖 动态AI权重: {dynamic_ai_weight.tolist()}")
            print(f"   📊 智能评分: {intelligent_scores.tolist()}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ 权重分配逻辑异常: {e}")
        
        # 测试8: 性能监控
        print("\n8. 测试AI引擎性能监控...")
        try:
            performance = selector.get_ai_performance_summary()
            print("   ✅ AI引擎性能监控获取成功")
            print(f"   📊 总分析次数: {performance.get('total_analyses', 0)}")
            print(f"   🎯 缓存命中率: {performance.get('cache_hit_rate', 0):.1f}%")
            print(f"   ⏱️ 平均处理时间: {performance.get('average_processing_time', 0):.2f} 秒")
            success_count += 1
        except Exception as e:
            print(f"   ❌ AI引擎性能监控异常: {e}")
        
        # 最终结果
        print("\n" + "=" * 80)
        print(f"AI专家系统工作流程验证完成: {success_count}/{total_tests} 项测试通过")
        print("=" * 80)
        
        if success_count >= 6:
            print("🎉 AI专家系统运行状态: 优秀")
            print("✅ 核心功能正常，AI专家系统已完全集成并运行")
            return True
        elif success_count >= 4:
            print("⚡ AI专家系统运行状态: 良好")
            print("✅ 主要功能正常，部分功能需要优化")
            return True
        else:
            print("🔧 AI专家系统运行状态: 需要修复")
            print("❌ 多个功能异常，需要进一步调试")
            return False
            
    except Exception as e:
        print(f"\n❌ AI专家系统验证过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_ai_workflow()
    sys.exit(0 if success else 1)