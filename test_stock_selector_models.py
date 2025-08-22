#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能选股的AI模型获取
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_stock_selector_models():
    """测试智能选股模块的AI模型获取"""
    print("Testing Stock Selector AI Models")
    print("=" * 50)
    
    try:
        # 1. 直接测试LLM管理器
        print("1. Testing LLM Manager directly:")
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        llm_manager = get_llm_manager()
        enabled_models = llm_manager.get_enabled_models()
        print(f"   LLM Manager enabled models: {len(enabled_models)}")
        
        for model_key, model_info in enabled_models.items():
            provider = model_info.get('provider', 'unknown')
            name = model_info.get('display_name', model_info.get('model_name', 'N/A'))
            print(f"     {provider}: {name}")
        
        # 2. 测试股票选择器
        print("\n2. Testing Stock Selector:")
        from tradingagents.selectors.stock_selector import get_stock_selector
        
        selector = get_stock_selector()
        print("   Stock Selector initialized")
        
        # 检查AI策略管理器状态
        if selector.ai_strategy_manager:
            print("   AI Strategy Manager: AVAILABLE")
            
            # 测试AI策略管理器的模型获取
            ai_models = selector.ai_strategy_manager.get_available_ai_models()
            print(f"   AI Strategy Manager models: {len(ai_models)}")
            
            for model_key, model_info in ai_models.items():
                provider = model_info.get('provider', 'unknown')
                name = model_info.get('display_name', model_info.get('model_name', 'N/A'))
                print(f"     {provider}: {name}")
                
        else:
            print("   AI Strategy Manager: NOT_AVAILABLE")
        
        # 3. 测试选股器的模型获取方法
        print("\n3. Testing Selector get_available_ai_models():")
        selector_models = selector.get_available_ai_models()
        print(f"   Selector available models: {len(selector_models)}")
        
        for model_key, model_info in selector_models.items():
            provider = model_info.get('provider', 'unknown')
            name = model_info.get('display_name', model_info.get('model_name', 'N/A'))
            enabled = model_info.get('enabled', False)
            has_key = model_info.get('has_api_key', False)
            print(f"     {provider}: {name} (enabled: {enabled}, has_key: {has_key})")
        
        # 4. 测试当前模型信息
        print("\n4. Testing current model info:")
        current_model = selector.get_current_ai_model_info()
        if current_model:
            print(f"   Current model: {current_model.get('display_name', 'N/A')}")
            print(f"   Provider: {current_model.get('provider', 'N/A')}")
        else:
            print("   Current model: NOT_SET")
        
        print("\n" + "=" * 50)
        print("CONCLUSION:")
        
        if len(selector_models) > 1:
            providers = set(model_info.get('provider') for model_info in selector_models.values())
            print(f"SUCCESS: {len(selector_models)} models from {len(providers)} providers")
            print("Stock Selector should show multiple providers")
            if len(providers) == 1:
                print("WARNING: All models from same provider - check API keys")
        else:
            print("ISSUE: Limited models available")
            print("Check AI Strategy Manager and LLM configuration")
        
        return len(selector_models)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    model_count = test_stock_selector_models()
    print(f"\nFinal result: {model_count} models available")
    sys.exit(0 if model_count > 1 else 1)