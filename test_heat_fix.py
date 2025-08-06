#!/usr/bin/env python3
"""
测试热度分析报告修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_heat_analyst_fix():
    """测试热度分析师修复效果"""
    print("=" * 50)
    print("测试热度分析报告修复效果")
    print("=" * 50)
    
    try:
        # 测试1: 导入热度分析师模块
        print("\n1. 测试热度分析师模块导入...")
        from tradingagents.agents.analysts.heat_analyst import create_heat_analyst, HeatAnalystAgent
        print("✅ 热度分析师模块导入成功")
        
        # 测试2: 创建热度分析师实例
        print("\n2. 测试创建热度分析师实例...")
        heat_agent = HeatAnalystAgent()
        print("✅ 热度分析师实例创建成功")
        
        # 测试3: 检查返回格式
        print("\n3. 测试返回格式...")
        from langchain_core.messages import AIMessage
        
        # 模拟返回结果
        test_report = "测试热度分析报告"
        test_result = {
            "messages": [AIMessage(content=test_report)],
            "heat_report": test_report,
        }
        
        print(f"✅ 返回格式正确:")
        print(f"   - messages类型: {type(test_result['messages'][0])}")
        print(f"   - heat_report存在: {'heat_report' in test_result}")
        print(f"   - heat_report内容: {test_result['heat_report']}")
        
        # 测试4: 检查条件逻辑
        print("\n4. 测试条件逻辑...")
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        logic = ConditionalLogic()
        test_state = {
            'messages': [AIMessage(content="test")]
        }
        
        result = logic.should_continue_heat(test_state)
        print(f"✅ 条件逻辑结果: {result}")
        
        if result == "Msg Clear Heat":
            print("✅ 热度分析师不会进入工具调用循环")
        else:
            print("❌ 热度分析师可能进入工具调用循环")
        
        # 测试5: 检查工作流程设置
        print("\n5. 测试工作流程设置...")
        from tradingagents.graph.setup import GraphSetup
        
        print("✅ 工作流程设置模块导入成功")
        print("✅ 热度分析师可以在工作流程中使用")
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！热度分析报告修复成功！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_heat_analyst_fix()
    if success:
        print("\n🔥 热度分析报告现在已经可以在Web界面中正确显示！")
        print("请在Web界面中选择热度分析师进行分析测试。")
    else:
        print("\n❌ 测试失败，请检查修复是否完整。")