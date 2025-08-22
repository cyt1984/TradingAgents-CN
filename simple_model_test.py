#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的AI模型测试
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
            print(f"✅ {key}: CONFIGURED")
            configured_count += 1
        else:
            print(f"❌ {key}: NOT_CONFIGURED")
    
    print(f"\nTotal configured: {configured_count}/{len(api_keys)}")
    return api_keys

def check_llm_manager():
    """检查LLM管理器"""
    try:
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        print("\nLLM Manager Status:")
        print("=" * 40)
        
        llm_manager = get_llm_manager()
        all_models = llm_manager.get_available_models()
        enabled_models = llm_manager.get_enabled_models()
        
        print(f"Total models: {len(all_models)}")
        print(f"Enabled models: {len(enabled_models)}")
        
        # 按供应商统计
        provider_stats = {}
        for model_info in all_models.values():
            provider = model_info.get('provider', 'unknown')
            enabled = model_info.get('enabled', False)
            
            if provider not in provider_stats:
                provider_stats[provider] = {'total': 0, 'enabled': 0}
            
            provider_stats[provider]['total'] += 1
            if enabled:
                provider_stats[provider]['enabled'] += 1
        
        print("\nBy Provider:")
        for provider, stats in provider_stats.items():
            print(f"  {provider}: {stats['enabled']}/{stats['total']} enabled")
        
        return enabled_models
        
    except Exception as e:
        print(f"LLM Manager Error: {e}")
        return {}

def main():
    """主函数"""
    print("AI Model Configuration Test")
    print("=" * 50)
    
    # 检查API密钥
    api_keys = check_api_keys()
    
    # 检查LLM管理器
    enabled_models = check_llm_manager()
    
    print("\nConclusion:")
    print("=" * 40)
    
    if len(enabled_models) > 1:
        print("✅ Multiple AI models are available")
        print("🔍 If stock selector only shows OpenAI, it's a display issue")
    else:
        print("⚠️ Only few models enabled")
        print("💡 Check API key configuration")

if __name__ == "__main__":
    main()