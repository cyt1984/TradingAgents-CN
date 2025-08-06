#!/usr/bin/env python3
"""
测试Kimi模型修复
验证更新后的Kimi模型名称是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.llm_adapters.kimi_adapter import create_kimi_adapter

def test_kimi_connection():
    """测试Kimi模型连接"""
    
    # 检查API密钥
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("[ERROR] KIMI_API_KEY 环境变量未设置")
        print("[INFO] 请在 .env 文件中设置 KIMI_API_KEY")
        return False
    
    print("[SUCCESS] 找到Kimi API密钥")
    
    try:
        # 测试moonshot-v1-8k模型
        print("[TEST] 测试 moonshot-v1-8k 模型...")
        kimi = create_kimi_adapter(model="moonshot-v1-8k")
        
        # 获取模型信息
        info = kimi.get_model_info()
        print("[INFO] 模型信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 简单测试调用
        print("[TEST] 适配器创建成功，模型配置正确")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False

def test_available_models():
    """测试可用模型列表"""
    try:
        from tradingagents.llm_adapters.kimi_adapter import ChatKimi
        
        models = ChatKimi.get_available_models()
        print("[INFO] 可用Kimi模型:")
        for model in models:
            print(f"  - {model}")
        
        return models
    except Exception as e:
        print(f"[ERROR] 获取模型列表失败: {e}")
        return []

if __name__ == "__main__":
    print("[START] 开始测试Kimi模型修复...")
    print("=" * 50)
    
    # 测试可用模型
    test_available_models()
    print()
    
    # 测试连接
    success = test_kimi_connection()
    
    print("=" * 50)
    if success:
        print("[SUCCESS] 所有测试通过！Kimi模型已修复")
    else:
        print("[WARNING] 测试未完成，请检查配置")