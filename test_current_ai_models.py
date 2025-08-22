#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试当前可用的AI模型
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_available_ai_models():
    """测试当前可用的AI模型"""
    print("检查当前可用的AI模型...")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        # 获取LLM管理器
        llm_manager = get_llm_manager()
        
        # 获取所有模型（包括未启用的）
        all_models = llm_manager.get_available_models()
        print(f"所有配置的模型数量: {len(all_models)}")
        
        # 获取已启用的模型
        enabled_models = llm_manager.get_enabled_models()
        print(f"已启用的模型数量: {len(enabled_models)}")
        print()
        
        # 按供应商分组显示
        providers = {}
        for model_key, model_info in all_models.items():
            provider = model_info.get('provider', 'unknown')
            if provider not in providers:
                providers[provider] = []
            providers[provider].append((model_key, model_info))
        
        # 显示各供应商的模型
        for provider, models in providers.items():
            print(f"📱 {provider.upper()} 供应商:")
            
            for model_key, model_info in models:
                display_name = model_info.get('display_name', model_info.get('model_name', 'N/A'))
                enabled = model_info.get('enabled', False)
                has_key = model_info.get('has_api_key', False)
                
                # 状态指示
                if enabled and has_key:
                    status = "可用"
                    icon = "✅"
                elif has_key:
                    status = "有密钥但未启用"
                    icon = "🔧"
                else:
                    status = "未配置API密钥"
                    icon = "❌"
                
                print(f"  {icon} {display_name} ({model_info.get('model_name', 'N/A')}) - {status}")
                
                if model_info.get('description'):
                    print(f"     描述: {model_info.get('description')}")
            print()
        
        # 显示当前使用的模型
        current_config = llm_manager.get_current_config()
        if current_config:
            print(f"🎯 当前使用的模型:")
            print(f"   供应商: {current_config.provider}")
            print(f"   模型名: {current_config.model_name}")
            print(f"   显示名: {current_config.display_name}")
        else:
            print("⚠️ 当前未设置默认模型")
        
        print("\n" + "=" * 60)
        print("结论:")
        if len(enabled_models) > 1:
            print(f"  ✅ 系统已配置 {len(enabled_models)} 个可用模型")
            print("  🔍 如果智能选股界面只显示OpenAI模型，可能是Web界面显示问题")
        else:
            print(f"  ⚠️ 只有 {len(enabled_models)} 个可用模型")
            print("  💡 请检查其他供应商的API密钥配置")
        
        return True
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_available_ai_models()
    sys.exit(0 if success else 1)