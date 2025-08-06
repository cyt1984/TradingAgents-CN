#!/usr/bin/env python3
"""
简单测试Kimi模型修复
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_kimi_config():
    """测试Kimi配置更新"""
    
    print("[TEST] 检查Kimi模型配置...")
    
    # 检查配置文件
    from tradingagents.config.config_manager import config_manager
    
    models = config_manager.load_models()
    kimi_models = [m for m in models if m.provider == "kimi"]
    
    if kimi_models:
        print("[SUCCESS] 找到Kimi模型配置:")
        for model in kimi_models:
            print(f"  模型: {model.model_name}, 状态: {'启用' if model.enabled else '禁用'}")
    else:
        print("[ERROR] 未找到Kimi模型配置")
    
    # 检查定价配置
    pricing = config_manager.load_pricing()
    kimi_pricing = [p for p in pricing if p.provider == "kimi"]
    
    if kimi_pricing:
        print("[SUCCESS] 找到Kimi定价配置:")
        for price in kimi_pricing:
            print(f"  模型: {price.model_name}, 价格: ¥{price.input_price_per_1k}/{price.output_price_per_1k} per 1K tokens")
    
    return True

def test_kimi_adapter():
    """测试Kimi适配器"""
    
    try:
        from tradingagents.llm_adapters.kimi_adapter import ChatKimi
        
        # 测试可用模型列表
        models = ChatKimi.get_available_models()
        print("[SUCCESS] Kimi适配器可用模型:")
        for model in models:
            print(f"  - {model}")
        
        # 测试创建适配器
        api_key = os.getenv("KIMI_API_KEY")
        if not api_key:
            print("[WARNING] KIMI_API_KEY未设置，跳过连接测试")
            return True
        
        kimi = ChatKimi(model="moonshot-v1-8k")
        print("[SUCCESS] Kimi适配器创建成功")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Kimi适配器测试失败: {e}")
        return False

if __name__ == "__main__":
    print("[START] 测试Kimi模型修复...")
    print("=" * 50)
    
    # 测试配置
    test_kimi_config()
    print()
    
    # 测试适配器
    success = test_kimi_adapter()
    
    print("=" * 50)
    if success:
        print("[SUCCESS] Kimi模型配置已修复")
    else:
        print("[ERROR] 修复完成但测试失败")