#!/usr/bin/env python3
"""
选股系统快速测试脚本
验证选股功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_stock_selector():
    """测试选股系统基本功能"""
    print("🧪 选股系统快速测试")
    print("=" * 50)
    
    try:
        print("📦 正在导入选股模块...")
        from tradingagents.selectors.stock_selector import get_stock_selector
        print("✅ 模块导入成功")
        
        print("🚀 正在初始化选股引擎...")
        selector = get_stock_selector()
        print("✅ 选股引擎初始化成功")
        
        print("📋 测试可用字段获取...")
        fields = selector.get_available_fields()
        print(f"✅ 获取到 {len(fields)} 个筛选字段")
        
        print("🎯 执行简单选股测试 (限制5只股票)...")
        # 执行一个简单的选股测试
        result = selector.quick_select(
            min_score=0,           # 不限制评分
            min_market_cap=0,      # 不限制市值  
            max_pe_ratio=1000,     # 不限制市盈率
            limit=5                # 只返回5只股票用于测试
        )
        
        print(f"✅ 选股测试完成!")
        print(f"  - 执行时间: {result.execution_time:.2f}秒")
        print(f"  - 候选总数: {result.total_candidates}")
        print(f"  - 筛选结果: {result.filtered_count}")
        
        if result.symbols:
            print(f"  - 测试股票: {result.symbols[:3]}...")  # 显示前3只
            print("🎉 选股功能测试通过!")
            return True
        else:
            print("⚠️ 未获取到股票数据，可能需要检查:")
            print("  - 网络连接")
            print("  - API配置") 
            print("  - 数据源状态")
            return False
            
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("💡 请检查项目依赖是否完整安装")
        return False
        
    except Exception as e:
        print(f"❌ 选股测试失败: {e}")
        print("💡 这可能是正常的，选股功能需要:")
        print("  - 有效的API密钥配置") 
        print("  - 稳定的网络连接")
        print("  - 数据源服务可用")
        return False

def test_components():
    """测试各个组件"""
    print("\n🔧 组件测试")
    print("=" * 50)
    
    components = [
        ("数据管理器", "tradingagents.dataflows.enhanced_data_manager", "EnhancedDataManager"),
        ("评分系统", "tradingagents.analytics.comprehensive_scoring_system", "get_comprehensive_scoring_system"), 
        ("融合引擎", "tradingagents.analytics.data_fusion_engine", "get_fusion_engine"),
        ("Tushare提供者", "tradingagents.dataflows.tushare_utils", "get_tushare_provider")
    ]
    
    success_count = 0
    for name, module_name, class_name in components:
        try:
            print(f"📦 测试{name}...")
            module = __import__(module_name, fromlist=[class_name])
            component_class = getattr(module, class_name)
            if callable(component_class):
                component_class()  # 尝试实例化
            print(f"✅ {name}测试通过")
            success_count += 1
        except Exception as e:
            print(f"⚠️ {name}测试失败: {e}")
    
    print(f"\n📊 组件测试结果: {success_count}/{len(components)} 通过")
    return success_count == len(components)

def main():
    """主函数"""
    print("🌟 TradingAgents-CN 选股系统测试")
    print("当前测试不需要API密钥，主要验证代码完整性")
    print()
    
    # 测试1: 基本选股功能
    selector_ok = test_stock_selector()
    
    # 测试2: 各个组件
    components_ok = test_components()
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"  选股功能: {'✅ 通过' if selector_ok else '❌ 失败'}")
    print(f"  组件完整性: {'✅ 通过' if components_ok else '❌ 失败'}")
    
    if selector_ok and components_ok:
        print("\n🎉 系统测试全部通过!")
        print("💡 建议接下来:")
        print("  1. 配置API密钥 (见 .env.example)")  
        print("  2. 启动Web界面: python start_web.py")
        print("  3. 运行选股演示: python quick_stock_selector_demo.py")
    else:
        print("\n⚠️ 部分测试失败，但这是正常的")
        print("💡 完整功能需要:")
        print("  - 配置数据源API密钥")
        print("  - 网络连接畅通")
        print("  - 相关服务可用")
    
    print("=" * 50)

if __name__ == "__main__":
    main()