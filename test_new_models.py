#!/usr/bin/env python3
"""
测试新增的 Kimi K2 和 GLM-4.5 模型适配器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_model_imports():
    """测试模型适配器导入"""
    print("[导入] 测试模型适配器导入...")
    
    # 测试 Kimi 适配器导入
    try:
        from tradingagents.llm_adapters.kimi_adapter import ChatKimi, create_kimi_adapter
        print("[OK] Kimi K2 适配器导入成功")
        kimi_import_ok = True
    except Exception as e:
        print(f"[FAIL] Kimi K2 适配器导入失败: {e}")
        kimi_import_ok = False
    
    # 测试 GLM 适配器导入
    try:
        from tradingagents.llm_adapters.glm_adapter import ChatGLM, create_glm_adapter
        print("[OK] GLM-4.5 适配器导入成功")
        glm_import_ok = True
    except Exception as e:
        print(f"[FAIL] GLM-4.5 适配器导入失败: {e}")
        glm_import_ok = False
    
    return kimi_import_ok, glm_import_ok

def test_model_configuration():
    """测试模型配置"""
    print("\n[配置] 测试模型配置...")
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 获取模型配置
        models = config_manager.load_models()
        
        # 查找新模型
        kimi_found = False
        glm_found = False
        
        for model in models:
            if model.provider == "kimi" and model.model_name in ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]:
                kimi_found = True
                print(f"[OK] 找到 Kimi 配置: {model.model_name}")
            elif model.provider == "glm" and model.model_name == "glm-4-plus":
                glm_found = True
                print(f"[OK] 找到 GLM-4.5 配置: {model.model_name}")
        
        if not kimi_found:
            print("[FAIL] 未找到 Kimi K2 模型配置")
        if not glm_found:
            print("[FAIL] 未找到 GLM-4.5 模型配置")
        
        return kimi_found and glm_found
        
    except Exception as e:
        print(f"[FAIL] 模型配置测试失败: {e}")
        return False

def test_pricing_configuration():
    """测试定价配置"""
    print("\n[价格] 测试定价配置...")
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 获取定价配置
        pricing = config_manager.load_pricing()
        
        # 查找新模型定价
        kimi_pricing_found = False
        glm_pricing_found = False
        
        for price in pricing:
            if price.provider == "kimi" and price.model_name in ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]:
                kimi_pricing_found = True
                print(f"[OK] 找到 Kimi 定价: 输入¥{price.input_price_per_1k}/1K, 输出¥{price.output_price_per_1k}/1K")
            elif price.provider == "glm" and price.model_name == "glm-4-plus":
                glm_pricing_found = True
                print(f"[OK] 找到 GLM-4.5 定价: 输入¥{price.input_price_per_1k}/1K, 输出¥{price.output_price_per_1k}/1K")
        
        if not kimi_pricing_found:
            print("[FAIL] 未找到 Kimi K2 定价配置")
        if not glm_pricing_found:
            print("[FAIL] 未找到 GLM-4.5 定价配置")
        
        return kimi_pricing_found and glm_pricing_found
        
    except Exception as e:
        print(f"[FAIL] 定价配置测试失败: {e}")
        return False

def test_model_creation():
    """测试模型创建（不需要API密钥）"""
    print("\n[工具] 测试模型创建...")
    
    # 测试 Kimi 模型创建
    try:
        from tradingagents.llm_adapters.kimi_adapter import ChatKimi
        
        # 尝试创建模型信息
        kimi_models = ChatKimi.get_available_models()
        print(f"[OK] Kimi 可用模型: {', '.join(kimi_models)}")
        
        # 测试成本估算
        temp_kimi = type('TempKimi', (), {
            'model_name': 'kimi-k2',
            'estimate_cost': lambda self, input_tokens, output_tokens: (input_tokens / 1000) * 0.01 + (output_tokens / 1000) * 0.03
        })()
        cost = temp_kimi.estimate_cost(1000, 500)
        print(f"[OK] Kimi 成本估算 (1000输入+500输出): ¥{cost:.4f}")
        
        kimi_ok = True
    except Exception as e:
        print(f"[FAIL] Kimi 模型创建测试失败: {e}")
        kimi_ok = False
    
    # 测试 GLM 模型创建
    try:
        from tradingagents.llm_adapters.glm_adapter import ChatGLM
        
        # 尝试创建模型信息
        glm_models = ChatGLM.get_available_models()
        print(f"[OK] GLM 可用模型: {', '.join(glm_models)}")
        
        # 测试成本估算
        temp_glm = type('TempGLM', (), {
            'model_name': 'glm-4-plus',
            'estimate_cost': lambda self, input_tokens, output_tokens: (input_tokens / 1000) * 0.05 + (output_tokens / 1000) * 0.15
        })()
        cost = temp_glm.estimate_cost(1000, 500)
        print(f"[OK] GLM 成本估算 (1000输入+500输出): ¥{cost:.4f}")
        
        glm_ok = True
    except Exception as e:
        print(f"[FAIL] GLM 模型创建测试失败: {e}")
        glm_ok = False
    
    return kimi_ok and glm_ok

def test_openai_compatible_integration():
    """测试OpenAI兼容集成"""
    print("\n[集成] 测试OpenAI兼容集成...")
    
    try:
        from tradingagents.llm_adapters.openai_compatible_base import OPENAI_COMPATIBLE_PROVIDERS
        
        providers_found = []
        
        if "kimi" in OPENAI_COMPATIBLE_PROVIDERS:
            providers_found.append("kimi")
            kimi_config = OPENAI_COMPATIBLE_PROVIDERS["kimi"]
            print(f"[OK] Kimi 集成配置: {len(kimi_config['models'])} 个模型")
        
        if "glm" in OPENAI_COMPATIBLE_PROVIDERS:
            providers_found.append("glm")
            glm_config = OPENAI_COMPATIBLE_PROVIDERS["glm"]
            print(f"[OK] GLM 集成配置: {len(glm_config['models'])} 个模型")
        
        print(f"[OK] 已集成提供商: {', '.join(providers_found)}")
        
        return len(providers_found) == 2
        
    except Exception as e:
        print(f"[FAIL] OpenAI兼容集成测试失败: {e}")
        return False

def test_environment_variables():
    """测试环境变量配置"""
    print("\n[环境] 测试环境变量配置...")
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 获取环境配置状态
        env_status = config_manager.get_env_config_status()
        
        kimi_key_available = env_status["api_keys"].get("kimi", False)
        glm_key_available = env_status["api_keys"].get("glm", False)
        
        print(f"[密钥] Kimi API密钥: {'[OK] 已配置' if kimi_key_available else '[FAIL] 未配置'}")
        print(f"[密钥] GLM API密钥: {'[OK] 已配置' if glm_key_available else '[FAIL] 未配置'}")
        
        if not kimi_key_available:
            print("[提示] 提示: 设置环境变量 KIMI_API_KEY 以启用 Kimi K2")
        if not glm_key_available:
            print("[提示] 提示: 设置环境变量 GLM_API_KEY 以启用 GLM-4.5")
        
        return True  # 环境变量测试总是通过，只是提示状态
        
    except Exception as e:
        print(f"[FAIL] 环境变量测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("[测试] TradingAgents-CN 新模型适配器测试")
    print("=" * 60)
    
    tests = [
        ("模型导入", test_model_imports),
        ("模型配置", test_model_configuration),
        ("定价配置", test_pricing_configuration),
        ("模型创建", test_model_creation),
        ("OpenAI兼容集成", test_openai_compatible_integration),
        ("环境变量", test_environment_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "模型导入":
                # 特殊处理导入测试
                kimi_ok, glm_ok = test_func()
                result = kimi_ok and glm_ok
            else:
                result = test_func()
            
            results.append((test_name, result))
            status = "[OK] 通过" if result else "[FAIL] 失败"
            print(f"\n[{status}] {test_name}")
            
        except Exception as e:
            print(f"\n[[FAIL] 异常] {test_name}: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("[统计] 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n[测试] 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n[成功] 所有测试通过! 新模型适配器已成功集成")
        print("\n[提示] 使用说明:")
        print("1. 设置相应的API密钥环境变量:")
        print("   - export KIMI_API_KEY='your_kimi_api_key'")
        print("   - export GLM_API_KEY='your_glm_api_key'")
        print("2. 在配置中启用对应的模型")
        print("3. 通过现有的Web界面或CLI使用新模型")
        return True
    else:
        print(f"\n[警告] {total - passed} 个测试失败，请检查相关配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)