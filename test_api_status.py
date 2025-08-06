#!/usr/bin/env python3
"""
测试API密钥状态
检查环境变量中的API密钥配置情况
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """测试环境变量加载"""
    print("API密钥状态检查")
    print("=" * 50)
    
    # 加载.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"[OK] 找到.env文件: {env_file}")
        load_dotenv(env_file, override=True)
    else:
        print(f"[FAIL] 未找到.env文件: {env_file}")
        return False
    
    # 检查各个API密钥
    api_keys = {
        "DASHSCOPE_API_KEY": "阿里百炼",
        "DEEPSEEK_API_KEY": "DeepSeek V3", 
        "KIMI_API_KEY": "Kimi K2 (月之暗面)",
        "GLM_API_KEY": "GLM-4.5 (智谱AI)",
        "GOOGLE_API_KEY": "Google AI",
        "OPENAI_API_KEY": "OpenAI",
        "TUSHARE_TOKEN": "Tushare",
        "FINNHUB_API_KEY": "FinnHub"
    }
    
    print("\n检查结果:")
    print("-" * 50)
    
    for env_var, name in api_keys.items():
        value = os.getenv(env_var)
        if value and value != f"your_{env_var.lower()}_here" and not value.startswith("your_"):
            status = "[OK] 已配置"
            print(f"- {name}: {status}")
        else:
            status = "[FAIL] 未配置"
            print(f"- {name}: {status}")
    
    return True

def test_config_manager():
    """测试配置管理器"""
    print("\n配置管理器测试")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # 获取环境状态
        env_status = config_manager.get_env_config_status()
        
        print("配置管理器检测到的API密钥状态:")
        print("-" * 40)
        
        for provider, configured in env_status["api_keys"].items():
            status = "[OK] 已配置" if configured else "[FAIL] 未配置"
            print(f"- {provider}: {status}")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] 配置管理器测试失败: {e}")
        return False

def main():
    """主函数"""
    success1 = test_env_loading()
    success2 = test_config_manager()
    
    if success1 and success2:
        print(f"\n{'='*50}")
        print("测试完成！如果Kimi和GLM显示为已配置，")
        print("重新启动Web应用后应该能在界面上看到正确状态。")
        return True
    else:
        print(f"\n{'='*50}")
        print("测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)