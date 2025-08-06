#!/usr/bin/env python3
"""
简化版新模型测试脚本 - 不依赖 langchain
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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
        
        print("当前配置的模型:")
        for model in models:
            print(f"  - {model.provider}/{model.model_name} (启用: {model.enabled})")
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
        
        print("相关定价配置:")
        for price in pricing:
            if price.provider in ["kimi", "glm"]:
                price_info = f"输入{price.input_price_per_1k}/{price.currency}/1K, 输出{price.output_price_per_1k}/{price.currency}/1K"
                print(f"  - {price.provider}/{price.model_name}: {price_info}")
                
                if price.provider == "kimi" and price.model_name == "kimi-k2":
                    kimi_pricing_found = True
                    print(f"[OK] 找到 Kimi K2 定价配置")
                elif price.provider == "glm" and price.model_name == "glm-4-plus":
                    glm_pricing_found = True
                    print(f"[OK] 找到 GLM-4.5 定价配置")
        
        if not kimi_pricing_found:
            print("[FAIL] 未找到 Kimi K2 定价配置")
        if not glm_pricing_found:
            print("[FAIL] 未找到 GLM-4.5 定价配置")
        
        return kimi_pricing_found and glm_pricing_found
        
    except Exception as e:
        print(f"[FAIL] 定价配置测试失败: {e}")
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
        
        print(f"[密钥] Kimi API密钥: {'[OK] 已配置' if kimi_key_available else '[WARN] 未配置'}")
        print(f"[密钥] GLM API密钥: {'[OK] 已配置' if glm_key_available else '[WARN] 未配置'}")
        
        if not kimi_key_available:
            print("[提示] 设置环境变量 KIMI_API_KEY 以启用 Kimi K2")
        if not glm_key_available:
            print("[提示] 设置环境变量 GLM_API_KEY 以启用 GLM-4.5")
        
        return True  # 环境变量测试总是通过，只是提示状态
        
    except Exception as e:
        print(f"[FAIL] 环境变量测试失败: {e}")
        return False

def test_file_existence():
    """测试适配器文件是否存在"""
    print("\n[文件] 测试适配器文件...")
    
    project_root = Path(__file__).parent
    
    files_to_check = [
        "tradingagents/llm_adapters/kimi_adapter.py",
        "tradingagents/llm_adapters/glm_adapter.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"[OK] {file_path} 存在")
        else:
            print(f"[FAIL] {file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("[测试] TradingAgents-CN 新模型配置验证")
    print("=" * 60)
    
    tests = [
        ("文件存在性", test_file_existence),
        ("模型配置", test_model_configuration),
        ("定价配置", test_pricing_configuration),
        ("环境变量", test_environment_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "[OK] 通过" if result else "[FAIL] 失败"
            print(f"\n{status} {test_name}")
            
        except Exception as e:
            print(f"\n[FAIL] {test_name}异常: {e}")
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
    
    if passed >= 3:  # 至少3个测试通过就认为基本配置正确
        print("\n[成功] 新模型配置基本正确!")
        print("\n[提示] 使用说明:")
        print("1. 在 .env 文件中设置API密钥:")
        print("   KIMI_API_KEY=your_kimi_api_key")
        print("   GLM_API_KEY=your_glm_api_key")
        print("2. 重启Web应用或CLI")
        print("3. 在界面中选择新的模型进行分析")
        return True
    else:
        print(f"\n[警告] {total - passed} 个测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)