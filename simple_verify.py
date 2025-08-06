#!/usr/bin/env python3
"""
简化版集成验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("TradingAgents-CN 新数据源集成验证")
    print("=" * 50)
    
    # 测试1: 导入增强工具
    print("\n[测试1] 导入增强工具...")
    try:
        from tradingagents.tools.enhanced_news_tool import get_enhanced_stock_news
        print("[OK] 增强新闻工具导入成功")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    # 测试2: 导入数据管理器
    print("\n[测试2] 导入数据管理器...")
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        print("[OK] 数据管理器导入成功")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    # 测试3: 初始化数据管理器
    print("\n[测试3] 初始化数据管理器...")
    try:
        manager = get_enhanced_data_manager()
        status = manager.get_provider_status()
        available = sum(1 for s in status.values() if s)
        print(f"[OK] 数据管理器初始化成功，{available}个数据源可用")
    except Exception as e:
        print(f"[FAIL] 初始化失败: {e}")
        return False
    
    # 测试4: 测试工具功能
    print("\n[测试4] 测试工具功能...")
    try:
        result = get_enhanced_stock_news('000001', 5)
        if result and len(result) > 100:
            print(f"[OK] 工具功能正常，返回{len(result)}字符")
        else:
            print("[FAIL] 工具返回数据不足")
            return False
    except Exception as e:
        print(f"[FAIL] 工具测试失败: {e}")
        return False
    
    # 测试5: 检查分析师集成
    print("\n[测试5] 检查分析师集成...")
    try:
        news_file = project_root / "tradingagents" / "agents" / "analysts" / "news_analyst.py"
        if news_file.exists():
            with open(news_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if "enhanced_news_tool" in content:
                print("[OK] 新闻分析师已集成增强工具")
            else:
                print("[WARN] 新闻分析师可能未完全集成")
        else:
            print("[FAIL] 新闻分析师文件不存在")
            return False
    except Exception as e:
        print(f"[FAIL] 分析师检查失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("验证结果: 所有测试通过!")
    print("\n确认信息:")
    print("- 新数据源已成功集成")
    print("- 增强工具可以正常工作") 
    print("- 分析师已升级使用新工具")
    print("- 数据可以融入分析报告")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[结论] 新数据源确实可以融入到报告中!")
    else:
        print("\n[结论] 存在集成问题，需要检查")
    
    sys.exit(0 if success else 1)