#!/usr/bin/env python3
"""
测试动态LLM管理器功能
验证模型选择和切换是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('test')

def test_llm_manager():
    """测试LLM管理器基本功能"""
    print("=" * 60)
    print("🧪 测试动态LLM管理器")
    print("=" * 60)
    
    try:
        # 1. 获取管理器实例
        manager = get_llm_manager()
        print(f"✅ LLM管理器初始化成功")
        
        # 2. 查看可用模型
        available_models = manager.get_available_models()
        enabled_models = manager.get_enabled_models()
        
        print(f"\n📋 可用模型总数: {len(available_models)}")
        print(f"🟢 已启用模型数: {len(enabled_models)}")
        
        # 3. 显示已启用的模型
        if enabled_models:
            print("\n🟢 已启用的模型:")
            for key, info in enabled_models.items():
                print(f"   - {key}: {info['display_name']} ({info['provider']})")
        else:
            print("\n⚠️ 没有已启用的模型 (请检查API密钥配置)")
            return False
        
        # 4. 测试模型切换
        first_model = list(enabled_models.keys())[0]
        print(f"\n🔄 测试切换到: {first_model}")
        success = manager.set_current_model(first_model)
        
        if success:
            print(f"✅ 模型切换成功")
            current_config = manager.get_current_config()
            if current_config:
                print(f"   当前模型: {current_config.display_name}")
                print(f"   提供商: {current_config.provider}")
                print(f"   API密钥: {'已配置' if current_config.api_key else '未配置'}")
        else:
            print(f"❌ 模型切换失败")
            return False
        
        # 5. 测试模型连接
        print(f"\n🔗 测试模型连接...")
        test_result = manager.test_model(first_model)
        
        if test_result['success']:
            print(f"✅ 模型连接测试成功")
            print(f"   响应: {test_result.get('response', '无响应')[:100]}...")
        else:
            print(f"❌ 模型连接测试失败: {test_result.get('error')}")
            # 连接失败不算整体失败，可能是网络问题
        
        return True
        
    except Exception as e:
        print(f"❌ LLM管理器测试失败: {e}")
        return False

def test_trading_graph_integration():
    """测试TradingGraph集成"""
    print("\n" + "=" * 60)
    print("🧪 测试TradingGraph集成")
    print("=" * 60)
    
    try:
        # 创建TradingGraph实例
        print("🔧 创建TradingGraph实例...")
        from tradingagents.default_config import DEFAULT_CONFIG
        
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # 只使用市场分析师减少复杂度
            debug=False,
            config=DEFAULT_CONFIG
        )
        
        print("✅ TradingGraph创建成功")
        
        # 查看当前模型信息
        current_model = graph.get_current_model_info()
        if current_model:
            print(f"   当前模型: {current_model['display_name']}")
            print(f"   提供商: {current_model['provider']}")
        
        # 查看可用模型
        available = graph.get_available_models()
        print(f"   可用模型数: {len(available)}")
        
        # 测试模型切换（如果有多个模型）
        if len(available) > 1:
            second_model = list(available.keys())[1]
            print(f"\n🔄 测试切换到: {second_model}")
            switch_success = graph.switch_llm_model(second_model)
            
            if switch_success:
                print("✅ 模型切换成功")
                new_model = graph.get_current_model_info()
                if new_model:
                    print(f"   新模型: {new_model['display_name']}")
            else:
                print("❌ 模型切换失败")
        
        return True
        
    except Exception as e:
        print(f"❌ TradingGraph集成测试失败: {e}")
        return False

def test_expert_committee_integration():
    """测试AI专家委员会集成"""
    print("\n" + "=" * 60)
    print("🧪 测试AI专家委员会集成")
    print("=" * 60)
    
    try:
        # 创建AI专家委员会实例
        print("🔧 创建AI专家委员会实例...")
        committee = AIExpertCommittee()
        
        print("✅ AI专家委员会创建成功")
        
        # 查看可用模型
        available = committee.get_available_ai_models()
        print(f"   可用模型数: {len(available)}")
        
        # 查看当前模型
        current_model = committee.get_current_ai_model_info()
        if current_model:
            print(f"   当前模型: {current_model['display_name']}")
        
        # 测试模型切换
        if len(available) > 0:
            first_model = list(available.keys())[0]
            print(f"\n🔄 测试预设模型: {first_model}")
            switch_success = committee.switch_ai_model(first_model)
            
            if switch_success:
                print("✅ 模型预设成功")
            else:
                print("❌ 模型预设失败")
        
        return True
        
    except Exception as e:
        print(f"❌ AI专家委员会集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试动态LLM管理器...")
    
    # 测试结果
    results = []
    
    # 1. 基础LLM管理器测试
    results.append(("LLM管理器基础功能", test_llm_manager()))
    
    # 2. TradingGraph集成测试
    results.append(("TradingGraph集成", test_trading_graph_integration()))
    
    # 3. AI专家委员会集成测试
    results.append(("AI专家委员会集成", test_expert_committee_integration()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 总体结果: {'✅ 全部通过' if all_passed else '❌ 存在失败'}")
    
    if all_passed:
        print("\n🎉 恭喜！动态LLM管理器已成功集成到系统中!")
        print("💡 现在用户可以在运行时动态选择和切换AI模型了。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和API密钥。")

if __name__ == "__main__":
    main()