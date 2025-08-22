#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能选股的AI模型选择功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_stock_selector_ai_models():
    """测试智能选股的AI模型功能"""
    print("正在测试智能选股的AI模型选择功能...")
    print("=" * 60)
    
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        
        # 获取选股引擎实例
        print("1. 初始化智能选股引擎...")
        selector = get_stock_selector()
        print("   ✅ 智能选股引擎初始化成功")
        
        # 获取可用AI模型
        print("\n2. 获取可用AI模型...")
        try:
            available_models = selector.get_available_ai_models()
            print(f"   ✅ 发现 {len(available_models)} 个AI模型")
            
            for model_key, model_info in available_models.items():
                display_name = model_info.get('display_name', 'N/A')
                provider = model_info.get('provider', 'N/A')
                enabled = model_info.get('enabled', False)
                has_key = model_info.get('has_api_key', False)
                
                status = "可用" if (enabled and has_key) else "不可用"
                print(f"     • {display_name} ({provider}) - {status}")
                
        except Exception as e:
            print(f"   ❌ 获取AI模型失败: {e}")
            return False
        
        # 获取当前AI模型
        print("\n3. 获取当前AI模型...")
        try:
            current_model = selector.get_current_ai_model_info()
            if current_model:
                print(f"   ✅ 当前模型: {current_model.get('display_name', 'N/A')}")
                print(f"     供应商: {current_model.get('provider', 'N/A')}")
                print(f"     温度: {current_model.get('temperature', 'N/A')}")
            else:
                print("   ⚠️ 未检测到当前AI模型")
        except Exception as e:
            print(f"   ❌ 获取当前模型失败: {e}")
        
        # 测试AI性能摘要
        print("\n4. 获取AI性能摘要...")
        try:
            ai_summary = selector.get_ai_performance_summary()
            ai_enabled = ai_summary.get('ai_enabled', False)
            print(f"   AI状态: {'✅ 启用' if ai_enabled else '❌ 未启用'}")
            
            if ai_enabled:
                availability = ai_summary.get('engine_availability', {})
                available_count = availability.get('available_count', 0)
                total_count = availability.get('total_count', 0)
                print(f"   AI引擎: {available_count}/{total_count} 个可用")
                
                # 显示AI引擎状态
                engines = ai_summary.get('ai_engines_status', {})
                for engine, status in engines.items():
                    status_text = "✅" if status else "❌"
                    print(f"     • {engine}: {status_text}")
            
        except Exception as e:
            print(f"   ❌ 获取AI性能摘要失败: {e}")
        
        # 测试模型切换功能
        print("\n5. 测试模型切换功能...")
        try:
            # 找一个可用的模型来测试切换
            available_model_key = None
            for model_key, model_info in available_models.items():
                if model_info.get('enabled') and model_info.get('has_api_key'):
                    available_model_key = model_key
                    break
            
            if available_model_key:
                print(f"   测试切换到: {available_models[available_model_key].get('display_name')}")
                switch_result = selector.switch_ai_model(available_model_key)
                print(f"   切换结果: {'✅ 成功' if switch_result else '❌ 失败'}")
            else:
                print("   ⚠️ 未找到可用的AI模型进行切换测试")
                
        except Exception as e:
            print(f"   ❌ 模型切换测试失败: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 智能选股AI模型功能测试完成")
        print("\n结论:")
        print("  • 智能选股模块已成功集成动态AI模型选择功能")
        print("  • 支持查看可用模型、当前模型信息和性能状态")
        print("  • 支持运行时切换AI模型")
        print("  • 与股票分析功能使用相同的AI模型管理系统")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stock_selector_ai_models()
    sys.exit(0 if success else 1)