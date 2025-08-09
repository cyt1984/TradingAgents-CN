#!/usr/bin/env python3
"""
简化版AI专家系统测试
避免编码和依赖问题，专注于核心功能验证
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """测试基础导入"""
    print("测试基础导入...")
    
    try:
        from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee
        print("✓ AIExpertCommittee 导入成功")
        return True
    except Exception as e:
        print(f"✗ AIExpertCommittee 导入失败: {e}")
        return False

def test_ai_strategy_manager():
    """测试AI策略管理器"""
    print("测试AI策略管理器...")
    
    try:
        from tradingagents.selectors.ai_strategies.ai_strategy_manager import AIStrategyManager
        manager = AIStrategyManager()
        print("✓ AI策略管理器初始化成功")
        
        # 检查AI引擎状态
        summary = manager.get_performance_summary()
        print(f"✓ AI引擎状态: {summary.get('engine_availability', {})}")
        return True
    except Exception as e:
        print(f"✗ AI策略管理器测试失败: {e}")
        return False

def test_expert_committee_structure():
    """测试专家委员会结构"""
    print("测试专家委员会结构...")
    
    try:
        from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee
        
        # 创建测试实例
        committee = AIExpertCommittee()
        
        # 检查专家列表
        experts = committee.experts
        print(f"✓ 专家数量: {len(experts)}")
        
        for expert_name, expert in experts.items():
            print(f"  - {expert_name}: {expert.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ 专家委员会结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("AI专家系统核心功能验证")
    print("=" * 50)
    
    tests = [
        ("基础导入测试", test_basic_imports),
        ("AI策略管理器测试", test_ai_strategy_manager),
        ("专家委员会结构测试", test_expert_committee_structure),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有核心功能测试通过！")
    elif passed >= len(results) * 0.5:
        print("👍 部分功能可用，需要优化")
    else:
        print("⚠️ 系统存在较多问题")

if __name__ == "__main__":
    main()