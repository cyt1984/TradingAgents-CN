#!/usr/bin/env python3
"""
A股选股功能快速测试
验证Tushare配置后的A股选股能力
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tushare_connection():
    """测试Tushare连接"""
    print("🔍 测试Tushare API连接...")
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        provider = get_tushare_provider()
        print("✅ Tushare提供者初始化成功")
        
        # 测试获取股票列表
        print("📋 获取A股股票列表...")
        stock_list = provider.get_stock_list()
        
        if not stock_list.empty:
            print(f"✅ 成功获取 {len(stock_list)} 只A股股票")
            print(f"📊 示例股票: {stock_list['ts_code'].head(3).tolist()}")
            return True
        else:
            print("❌ 获取股票列表为空")
            return False
            
    except Exception as e:
        print(f"❌ Tushare连接测试失败: {e}")
        return False

def test_a_stock_selection():
    """测试A股选股功能"""
    print("\n🎯 测试A股智能选股...")
    
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        
        # 初始化选股引擎
        selector = get_stock_selector()
        print("✅ 选股引擎初始化成功")
        
        # 执行简单的A股选股
        print("🚀 执行A股快速选股测试...")
        result = selector.quick_select(
            min_score=0,           # 不限制评分，确保有结果
            min_market_cap=0,      # 不限制市值
            max_pe_ratio=1000,     # 不限制市盈率
            grades=None,           # 不限制等级
            limit=10               # 限制10只股票用于测试
        )
        
        print(f"✅ A股选股测试完成!")
        print(f"  ⏱️ 执行时间: {result.execution_time:.2f}秒")
        print(f"  📊 候选总数: {result.total_candidates}")
        print(f"  🎯 筛选结果: {result.filtered_count}")
        
        if result.symbols:
            print(f"  🏆 选出的A股: {result.symbols[:5]}")  # 显示前5只
            return True
        else:
            print("  ⚠️ 未选出A股，可能需要调整筛选条件")
            return False
            
    except Exception as e:
        print(f"❌ A股选股测试失败: {e}")
        return False

def test_specific_a_stocks():
    """测试特定A股的评分功能"""
    print("\n📈 测试A股评分功能...")
    
    # 测试一些知名A股
    test_stocks = ['000001.SZ', '000002.SZ', '600036.SH', '600519.SH']
    
    try:
        from tradingagents.analytics.comprehensive_scoring_system import get_comprehensive_scoring_system
        from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
        
        scoring_system = get_comprehensive_scoring_system()
        data_manager = EnhancedDataManager()
        
        print("✅ 评分系统和数据管理器初始化成功")
        
        for stock in test_stocks[:2]:  # 只测试前2只，避免API限制
            try:
                print(f"\n📊 分析股票: {stock}")
                
                # 获取股票数据
                stock_data = data_manager.get_latest_price_data(stock)
                
                if stock_data:
                    print(f"  📈 价格: {stock_data.get('price', 'N/A')}")
                    
                    # 计算评分
                    score = scoring_system.calculate_comprehensive_score(stock, stock_data)
                    print(f"  🎯 综合评分: {score.overall_score:.1f}")
                    print(f"  🏆 投资等级: {score.grade}")
                else:
                    print(f"  ⚠️ 未获取到 {stock} 的数据")
                    
            except Exception as e:
                print(f"  ❌ {stock} 分析失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ A股评分测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🇨🇳 A股选股功能测试")
    print("验证Tushare token配置后的选股能力")
    print("=" * 50)
    
    # 测试1: Tushare连接
    tushare_ok = test_tushare_connection()
    
    # 测试2: A股选股
    selector_ok = test_a_stock_selection()
    
    # 测试3: A股评分
    scoring_ok = test_specific_a_stocks()
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"  Tushare连接: {'✅ 成功' if tushare_ok else '❌ 失败'}")
    print(f"  A股选股功能: {'✅ 成功' if selector_ok else '❌ 失败'}")
    print(f"  A股评分功能: {'✅ 成功' if scoring_ok else '❌ 失败'}")
    
    if tushare_ok and selector_ok:
        print("\n🎉 A股选股功能测试通过!")
        print("💡 现在可以在Web界面使用A股选股了:")
        print("  1. 运行: python start_web.py")
        print("  2. 访问: http://localhost:8501")
        print("  3. 选择: 🎯 智能选股")
        print("  4. 开始选择优质A股!")
    else:
        print("\n⚠️ 部分功能测试失败")
        if not tushare_ok:
            print("🔧 Tushare问题解决方案:")
            print("  - 检查token是否正确")
            print("  - 检查网络连接") 
            print("  - 访问 https://tushare.pro/ 确认账户状态")
    
    print("=" * 50)

if __name__ == "__main__":
    main()