#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查AI模型配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_api_keys():
    """检查环境变量中的API密钥"""
    api_keys = {
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"), 
        "KIMI_API_KEY": os.getenv("KIMI_API_KEY"),
        "GLM_API_KEY": os.getenv("GLM_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }
    
    print("API Keys Status:")
    print("=" * 40)
    
    configured_count = 0
    for key, value in api_keys.items():
        if value and value != f"your_{key.lower()}_here":
            print(f"OK {key}: CONFIGURED")
            configured_count += 1
        else:
            print(f"NO {key}: NOT_CONFIGURED")
    
    print(f"\nTotal configured: {configured_count}/{len(api_keys)}")
    return configured_count

def check_llm_models():
    """检查LLM模型"""
    try:
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        print("\nLLM Manager Status:")
        print("=" * 40)
        
        llm_manager = get_llm_manager()
        all_models = llm_manager.get_available_models()
        enabled_models = llm_manager.get_enabled_models()
        
        print(f"Total models: {len(all_models)}")
        print(f"Enabled models: {len(enabled_models)}")
        
        # 显示已启用的模型
        print("\nEnabled Models:")
        for model_key, model_info in enabled_models.items():
            provider = model_info.get('provider', 'unknown')
            name = model_info.get('display_name', model_info.get('model_name', 'N/A'))
            print(f"  {provider}: {name}")
        
        return len(enabled_models)
        
    except Exception as e:
        print(f"LLM Manager Error: {e}")
        return 0

def main():
    """主函数"""
    print("AI Model Configuration Check")
    print("=" * 50)
    
    # 检查API密钥
    configured_keys = check_api_keys()
    
    # 检查LLM模型
    enabled_models = check_llm_models()
    
    print("\nConclusion:")
    print("=" * 40)
    
    if enabled_models > 1:
        print("SUCCESS: Multiple AI models available")
        print("If stock selector shows only OpenAI, it's a UI issue")
    else:
        print("ISSUE: Only few models enabled") 
        print("Check API key configuration")
    
    print(f"API Keys: {configured_keys}/8 configured")
    print(f"AI Models: {enabled_models} enabled")

if __name__ == "__main__":
    main()