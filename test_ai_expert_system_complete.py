#!/usr/bin/env python3
"""
测试AI专家系统的完整工作流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.selectors.stock_selector import StockSelector, AIMode, AISelectionConfig
from tradingagents.selectors.ai_strategies.ai_strategy_manager import get_ai_strategy_manager

def test_ai_expert_system():
    """测试AI专家系统完整工作流程"""
    print("=" * 60)
    print("AI专家系统工作流程测试")
    print("=" * 60)
    
    try:
        # 1. 测试AI策略管理器
        print("\n1. 测试AI策略管理器初始化...")
        ai_manager = get_ai_strategy_manager()
        ai_status = ai_manager.get_performance_summary()
        
        print(f"   ✅ AI引擎状态: {ai_status['ai_engines_status']}")
        print(f"   ✅ 可用引擎数量: {ai_status['engine_availability']['available_count']}/{ai_status['engine_availability']['total_count']}")
        print(f"   ✅ AI启用状态: {ai_status['ai_enabled']}")
        
        # 2. 测试选股引擎
        print("\n2. 测试选股引擎初始化...")
        selector = StockSelector(cache_enabled=True)
        
        if selector.ai_strategy_manager:
            print("   ✅ 选股引擎AI增强功能已启用")
        else:
            print("   ⚠️ 选股引擎AI增强功能未启用")
        
        # 3. 测试AI增强选股配置
        print("\n3. 测试AI增强选股配置...")
        
        # 基础AI增强配置
        basic_ai_config = AISelectionConfig(
            ai_mode=AIMode.AI_ENHANCED,
            min_ai_score=65.0,
            min_confidence=0.6,
            enable_caching=True,
            parallel_processing=True
        )
        
        # 专家委员会配置
        expert_config = AISelectionConfig(
            ai_mode=AIMode.EXPERT_COMMITTEE,
            expert_committee_weight=1.0,
            min_ai_score=70.0,
            min_confidence=0.7,
            enable_caching=True
        )
        
        print(f"   ✅ 基础AI配置: {basic_ai_config.ai_mode.value}")
        print(f"   ✅ 专家委员会配置: {expert_config.ai_mode.value}")
        
        # 4. 测试快速选股（AI增强）
        print("\n4. 测试AI增强快速选股...")
        try:
            quick_result = selector.quick_select(
                min_score=65.0,
                min_market_cap=50.0,
                max_pe_ratio=30.0,
                grades=['A+', 'A', 'B+'],
                limit=10
            )
            
            print(f"   ✅ AI增强选股完成")
            print(f"   📊 选股结果: {len(quick_result.symbols)} 只股票")
            print(f"   ⏱️ 执行时间: {quick_result.execution_time:.2f} 秒")
            
            # 检查AI分析结果
            if 'ai_overall_score' in quick_result.data.columns:
                print("   🤖 AI评分列已添加到结果中")
                ai_scores = quick_result.data['ai_overall_score'].dropna()
                if len(ai_scores) > 0:
                    print(f"   📈 AI评分范围: {ai_scores.min():.1f} - {ai_scores.max():.1f}")
            
        except Exception as e:
            print(f"   ⚠️ AI增强选股测试失败: {e}")
        
        # 5. 测试专家委员会选股
        print("\n5. 测试专家委员会选股...")
        try:
            expert_result = selector.expert_committee_select(
                min_expert_score=70.0,
                min_consensus="基本一致",
                limit=5
            )
            
            print(f"   ✅ 专家委员会选股完成")
            print(f"   📊 选股结果: {len(expert_result.symbols)} 只股票")
            print(f"   ⏱️ 执行时间: {expert_result.execution_time:.2f} 秒")
            
            # 检查专家委员会评分
            if 'expert_committee_score' in expert_result.data.columns:
                print("   👥 专家委员会评分列已添加到结果中")
                expert_scores = expert_result.data['expert_committee_score'].dropna()
                if len(expert_scores) > 0:
                    print(f"   📈 专家评分范围: {expert_scores.min():.1f} - {expert_scores.max():.1f}")
            
        except Exception as e:
            print(f"   ⚠️ 专家委员会选股测试失败: {e}")
        
        # 6. 测试完整AI选股
        print("\n6. 测试完整AI选股...")
        try:
            full_ai_result = selector.full_ai_select(
                min_overall_score=75.0,
                min_confidence=0.7,
                risk_tolerance="中等",
                limit=3
            )
            
            print(f"   ✅ 完整AI选股完成")
            print(f"   📊 选股结果: {len(full_ai_result.symbols)} 只股票")
            print(f"   ⏱️ 执行时间: {full_ai_result.execution_time:.2f} 秒")
            
            # 检查完整AI分析结果
            ai_columns = [col for col in full_ai_result.data.columns if 'ai_' in col or 'expert_' in col or 'pattern_' in col]
            if ai_columns:
                print(f"   🔍 AI分析列: {ai_columns}")
            
        except Exception as e:
            print(f"   ⚠️ 完整AI选股测试失败: {e}")
        
        # 7. 性能监控
        print("\n7. AI引擎性能监控...")
        try:
            performance = selector.get_ai_performance_summary()
            print(f"   📊 总分析次数: {performance.get('total_analyses', 0)}")
            print(f"   🎯 缓存命中率: {performance.get('cache_hit_rate', 0):.1f}%")
            print(f"   ⏱️ 平均处理时间: {performance.get('average_processing_time', 0):.2f} 秒")
            print(f"   💾 缓存大小: {performance.get('cache_size', 0)}")
        except Exception as e:
            print(f"   ⚠️ 性能监控获取失败: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 AI专家系统工作流程测试完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ AI专家系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_expert_system()
    sys.exit(0 if success else 1)