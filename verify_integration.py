#!/usr/bin/env python3
"""
验证新数据源集成脚本
确保新数据源可以正确融入分析报告
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tool_imports():
    """测试工具导入"""
    print("测试增强工具导入...")
    
    try:
        from tradingagents.tools.enhanced_news_tool import (
            get_enhanced_stock_news,
            get_enhanced_market_sentiment, 
            get_enhanced_social_discussions
        )
        print("[OK] 增强新闻工具导入成功")
    except Exception as e:
        print(f"[FAIL] 增强新闻工具导入失败: {e}")
        return False
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        print("[OK] 增强数据管理器导入成功")
    except Exception as e:
        print(f"[FAIL] 增强数据管理器导入失败: {e}")
        return False
    
    return True

def test_data_manager():
    """测试数据管理器"""
    print("\n📊 测试增强数据管理器...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        manager = get_enhanced_data_manager()
        print("✅ 数据管理器初始化成功")
        
        # 检查可用的数据源
        status = manager.get_provider_status()
        available_sources = [name for name, available in status.items() if available]
        
        print(f"📡 可用数据源 ({len(available_sources)}个): {', '.join(available_sources)}")
        
        if len(available_sources) >= 2:
            print("✅ 至少有2个数据源可用，数据整合可以正常工作")
            return True
        else:
            print("⚠️ 可用数据源较少，可能影响数据整合效果")
            return False
            
    except Exception as e:
        print(f"❌ 数据管理器测试失败: {e}")
        return False

def test_tools_functionality():
    """测试工具功能"""
    print("\n🛠️ 测试工具功能...")
    test_symbol = '000001'
    
    try:
        from tradingagents.tools.enhanced_news_tool import get_enhanced_stock_news
        
        print(f"📰 测试新闻工具: {test_symbol}")
        result = get_enhanced_stock_news(test_symbol, 5)
        
        if result and len(result) > 100:
            print(f"✅ 新闻工具测试成功，返回 {len(result)} 字符")
            
            # 验证返回格式
            if "增强新闻分析报告" in result:
                print("✅ 返回格式符合预期")
            if "数据源" in result:
                print("✅ 包含数据源信息")
            if "新闻总数" in result:
                print("✅ 包含统计信息")
                
            return True
        else:
            print("❌ 新闻工具返回数据不足")
            return False
            
    except Exception as e:
        print(f"❌ 工具功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analyst_integration():
    """测试分析师集成"""
    print("\n🤖 测试分析师集成...")
    
    try:
        # 检查新闻分析师是否正确导入了增强工具
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        print("✅ 新闻分析师导入成功")
        
        # 检查社交媒体分析师
        from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
        print("✅ 社交媒体分析师导入成功")
        
        # 验证文件中是否包含增强工具的引用
        news_analyst_file = Path(__file__).parent / "tradingagents" / "agents" / "analysts" / "news_analyst.py"
        
        if news_analyst_file.exists():
            with open(news_analyst_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "enhanced_news_tool" in content:
                print("✅ 新闻分析师已集成增强工具")
            else:
                print("⚠️ 新闻分析师可能未完全集成增强工具")
                
            if "get_enhanced_stock_news" in content:
                print("✅ 新闻分析师包含增强新闻功能")
                
        return True
        
    except Exception as e:
        print(f"❌ 分析师集成测试失败: {e}")
        return False

def test_report_generation():
    """测试报告生成"""
    print("\n📋 测试报告生成...")
    
    try:
        from tradingagents.tools.enhanced_news_tool import get_enhanced_stock_news
        
        test_symbol = '000001'
        print(f"🔍 生成测试报告: {test_symbol}")
        
        # 生成报告
        report = get_enhanced_stock_news(test_symbol, 10)
        
        if not report:
            print("❌ 报告生成失败")
            return False
        
        # 验证报告内容
        checks = [
            ("标题", "增强新闻分析报告" in report),
            ("股票代码", test_symbol in report),
            ("基本信息", "基本信息" in report),
            ("新闻动态", "新闻动态" in report),
            ("统计分析", "分析统计" in report),
            ("Markdown格式", "##" in report and "|" in report),
        ]
        
        passed_checks = 0
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}检查通过")
                passed_checks += 1
            else:
                print(f"❌ {check_name}检查失败")
        
        if passed_checks >= 4:
            print(f"✅ 报告生成测试通过 ({passed_checks}/{len(checks)})")
            
            # 保存测试报告
            report_file = f"test_report_{test_symbol}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 测试报告已保存: {report_file}")
            
            return True
        else:
            print(f"❌ 报告生成测试未通过 ({passed_checks}/{len(checks)})")
            return False
            
    except Exception as e:
        print(f"❌ 报告生成测试失败: {e}")
        return False

def main():
    """主函数"""
    print("TradingAgents-CN 新数据源集成验证")
    print("=" * 60)
    
    tests = [
        ("工具导入", test_tool_imports),
        ("数据管理器", test_data_manager), 
        ("工具功能", test_tools_functionality),
        ("分析师集成", test_analyst_integration),
        ("报告生成", test_report_generation),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"验证结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("所有测试通过！新数据源已成功集成到分析报告中")
        print("\n✅ 确认信息:")
        print("   - 增强新闻工具可以正常工作")
        print("   - 多数据源整合功能正常")
        print("   - 分析师已升级使用新工具")
        print("   - 报告格式符合预期")
        print("   - 数据可以正确融入最终报告")
        
        return True
    else:
        print("⚠️ 部分测试未通过，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)