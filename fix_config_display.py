#!/usr/bin/env python3
"""
修复配置显示问题
强制刷新环境变量和配置状态
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_config():
    """修复配置显示"""
    print("修复配置显示问题")
    print("=" * 50)
    
    # 强制重新加载.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"[OK] 重新加载.env文件: {env_file}")
        load_dotenv(env_file, override=True)
    
    # 检查关键环境变量
    key_vars = {
        "KIMI_API_KEY": "Kimi K2",
        "GLM_API_KEY": "GLM-4.5",
        "DASHSCOPE_API_KEY": "阿里百炼"
    }
    
    print("\n当前环境变量状态:")
    print("-" * 30)
    
    for var, name in key_vars.items():
        value = os.getenv(var)
        if value and not value.startswith("your_") and value != "":
            print(f"[OK] {name}: 已配置")
        else:
            print(f"[FAIL] {name}: 未配置")
    
    # 测试配置管理器
    try:
        from tradingagents.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        print("\n配置管理器状态:")
        print("-" * 30)
        
        env_status = config_manager.get_env_config_status()
        
        for provider in ["kimi", "glm", "dashscope"]:
            if provider in env_status["api_keys"]:
                status = "[OK] 已配置" if env_status["api_keys"][provider] else "[FAIL] 未配置"
                print(f"{provider}: {status}")
        
        return True
        
    except Exception as e:
        print(f"配置管理器错误: {e}")
        return False

def main():
    success = fix_config()
    
    if success:
        print(f"\n{'='*50}")
        print("配置检查完成！")
        print("\n如果Kimi和GLM显示为已配置：")
        print("1. 刷新浏览器页面 (F5)")
        print("2. 或重启Web应用")
        print("3. 在侧边栏应该能看到新模型选项")
    else:
        print("配置检查失败")
        
    return success

if __name__ == "__main__":
    main()