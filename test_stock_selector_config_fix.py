#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能选股的侧边栏配置修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_state_integration():
    """测试session state集成"""
    print("测试智能选股与侧边栏配置集成...")
    print("=" * 60)
    
    try:
        # 模拟session state
        import streamlit as st
        
        # 检查是否在Streamlit环境中
        try:
            st.session_state.test = True
            print("1. ✅ Streamlit环境检测成功")
        except:
            print("1. ⚠️ 非Streamlit环境，模拟session state")
            # 创建模拟的session state
            class MockSessionState:
                def __init__(self):
                    self.data = {}
                
                def get(self, key, default=None):
                    return self.data.get(key, default)
                
                def __setitem__(self, key, value):
                    self.data[key] = value
                
                def __getitem__(self, key):
                    return self.data[key]
                    
            st.session_state = MockSessionState()
        
        # 模拟侧边栏配置
        st.session_state['llm_provider'] = 'dashscope'
        st.session_state['llm_model'] = 'qwen-plus-latest'
        
        print("2. ✅ Session state配置模拟完成")
        print(f"   供应商: {st.session_state.get('llm_provider')}")
        print(f"   模型: {st.session_state.get('llm_model')}")
        
        # 测试动态LLM管理器
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        llm_manager = get_llm_manager()
        
        print("3. ✅ 动态LLM管理器初始化成功")
        
        # 测试模型映射逻辑
        llm_provider = st.session_state.get('llm_provider')
        llm_model = st.session_state.get('llm_model')
        
        model_mapping = {
            ("dashscope", "qwen-turbo"): "dashscope_qwen_turbo",
            ("dashscope", "qwen-plus-latest"): "dashscope_qwen_plus", 
            ("dashscope", "qwen-max"): "dashscope_qwen_max",
            ("deepseek", "deepseek-chat"): "deepseek_chat",
        }
        
        model_key = None
        for (provider, model), key in model_mapping.items():
            if provider == llm_provider and model == llm_model:
                model_key = key
                break
        
        if model_key:
            print(f"4. ✅ 模型映射成功: {llm_provider} + {llm_model} -> {model_key}")
            
            # 测试模型设置
            success = llm_manager.set_current_model(model_key)
            if success:
                print("5. ✅ 模型设置成功")
                
                # 验证当前模型
                current_config = llm_manager.get_current_config()
                if current_config:
                    print(f"6. ✅ 当前模型验证成功:")
                    print(f"   供应商: {current_config.provider}")
                    print(f"   模型名: {current_config.model_name}")
                    print(f"   显示名: {current_config.display_name}")
                else:
                    print("6. ❌ 当前模型验证失败")
                    return False
            else:
                print(f"5. ❌ 模型设置失败: {model_key}")
                return False
        else:
            print(f"4. ❌ 模型映射失败: {llm_provider} + {llm_model}")
            return False
        
        # 测试智能选股集成
        print("\n测试智能选股集成...")
        try:
            from tradingagents.selectors.stock_selector import get_stock_selector
            selector = get_stock_selector()
            print("7. ✅ 智能选股初始化成功")
            
            # 测试AI模型信息获取
            current_model_info = selector.get_current_ai_model_info()
            if current_model_info:
                print("8. ✅ AI模型信息获取成功:")
                print(f"   供应商: {current_model_info.get('provider')}")
                print(f"   模型名: {current_model_info.get('model_name')}")
                print(f"   显示名: {current_model_info.get('display_name')}")
            else:
                print("8. ⚠️ AI模型信息为空，可能需要初始化")
            
            # 测试可用模型列表
            available_models = selector.get_available_ai_models()
            if available_models:
                print(f"9. ✅ 可用模型获取成功: {len(available_models)} 个模型")
                
                # 按供应商统计
                providers = {}
                for model_key, model_info in available_models.items():
                    provider = model_info.get('provider', 'unknown')
                    if provider not in providers:
                        providers[provider] = 0
                    providers[provider] += 1
                
                print("   供应商分布:")
                for provider, count in providers.items():
                    print(f"     {provider}: {count} 个模型")
            else:
                print("9. ❌ 可用模型列表为空")
                return False
                
        except Exception as e:
            print(f"智能选股集成测试失败: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("\n修复要点:")
        print("  • 智能选股页面现在从session state读取侧边栏配置")
        print("  • 支持多个供应商的模型映射和切换")
        print("  • 与股票分析使用相同的AI模型管理系统")
        print("  • 实现了侧边栏配置的实时同步")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_state_integration()
    print(f"\n测试结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)