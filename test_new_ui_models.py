#!/usr/bin/env python3
"""
测试Web界面新模型配置
验证Kimi K2和GLM-4.5是否正确加载到界面中
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_loading():
    """测试配置加载"""
    print("[测试] 配置文件加载测试")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # 测试模型配置
        models = config_manager.load_models()
        print(f"[OK] 加载了 {len(models)} 个模型配置")
        
        # 检查新模型
        kimi_models = [m for m in models if m.provider == "kimi"]
        glm_models = [m for m in models if m.provider == "glm"]
        
        print(f"[检查] Kimi模型数量: {len(kimi_models)}")
        for model in kimi_models:
            print(f"  - {model.provider}: {model.model_name}")
            
        print(f"[检查] GLM模型数量: {len(glm_models)}")
        for model in glm_models:
            print(f"  - {model.provider}: {model.model_name}")
            
        return len(kimi_models) > 0 and len(glm_models) > 0
        
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False

def test_sidebar_providers():
    """测试侧边栏提供商列表"""
    print("\n[测试] 侧边栏提供商测试")
    print("=" * 50)
    
    try:
        # 直接测试侧边栏代码
        sidebar_file = project_root / "web" / "components" / "sidebar.py"
        with open(sidebar_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查新提供商是否在选项中
        has_kimi = '"kimi"' in content and "Kimi K2" in content
        has_glm = '"glm"' in content and "GLM-4.5" in content
        
        print(f"[检查] 侧边栏包含Kimi: {has_kimi}")
        print(f"[检查] 侧边栏包含GLM: {has_glm}")
        
        return has_kimi and has_glm
        
    except Exception as e:
        print(f"[FAIL] 侧边栏测试失败: {e}")
        return False

def test_analysis_runner():
    """测试分析运行器支持"""
    print("\n[测试] 分析运行器支持测试")
    print("=" * 50)
    
    try:
        runner_file = project_root / "web" / "utils" / "analysis_runner.py"
        with open(runner_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查新提供商的配置逻辑
        has_kimi_config = 'llm_provider == "kimi"' in content
        has_glm_config = 'llm_provider == "glm"' in content
        has_kimi_url = "api.moonshot.cn" in content
        has_glm_url = "open.bigmodel.cn" in content
        
        print(f"[检查] 分析器支持Kimi配置: {has_kimi_config}")
        print(f"[检查] 分析器支持GLM配置: {has_glm_config}")
        print(f"[检查] Kimi API端点配置: {has_kimi_url}")
        print(f"[检查] GLM API端点配置: {has_glm_url}")
        
        return all([has_kimi_config, has_glm_config, has_kimi_url, has_glm_url])
        
    except Exception as e:
        print(f"[FAIL] 分析运行器测试失败: {e}")
        return False

def test_adapter_imports():
    """测试适配器导入"""
    print("\n[测试] 模型适配器导入测试")
    print("=" * 50)
    
    # 测试Kimi适配器
    try:
        from tradingagents.llm_adapters.kimi_adapter import ChatKimi, create_kimi_adapter
        print("[OK] Kimi适配器导入成功")
        kimi_ok = True
    except Exception as e:
        print(f"[FAIL] Kimi适配器导入失败: {e}")
        kimi_ok = False
        
    # 测试GLM适配器
    try:
        from tradingagents.llm_adapters.glm_adapter import ChatGLM, create_glm_adapter
        print("[OK] GLM适配器导入成功")
        glm_ok = True
    except Exception as e:
        print(f"[FAIL] GLM适配器导入失败: {e}")
        glm_ok = False
        
    return kimi_ok and glm_ok

def main():
    """主测试函数"""
    print("TradingAgents-CN 新模型UI集成测试")
    print("=" * 60)
    
    tests = [
        ("配置文件加载", test_config_loading),
        ("侧边栏提供商", test_sidebar_providers), 
        ("分析运行器支持", test_analysis_runner),
        ("适配器导入", test_adapter_imports)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n[OK] {test_name} 测试通过")
                passed_tests += 1
            else:
                print(f"\n[FAIL] {test_name} 测试失败")
        except Exception as e:
            print(f"\n[ERROR] {test_name} 测试异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"测试结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("所有测试通过！新模型已成功集成到Web界面中")
        print("\n确认信息:")
        print("   - Kimi K2和GLM-4.5模型配置已添加")
        print("   - Web界面侧边栏可以选择新模型")
        print("   - 分析运行器支持新模型执行")
        print("   - 模型适配器可以正常导入")
        print("\n使用方法:")
        print("1. 启动Web应用: python start_web.py")
        print("2. 在侧边栏选择 '🌙 Kimi K2' 或 '🧠 GLM-4.5'")
        print("3. 配置对应的API密钥")
        print("4. 正常进行股票分析")
        return True
    else:
        print("部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)