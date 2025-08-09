#!/usr/bin/env python3
"""
快速选股系统演示
展示如何使用TradingAgents-CN的选股功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_quick_select():
    """演示快速选股功能"""
    print("🚀 TradingAgents-CN 快速选股演示")
    print("=" * 60)
    
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        
        print("📊 正在初始化选股引擎...")
        selector = get_stock_selector()
        
        print("🔍 开始快速选股...")
        print("  - 最小综合评分: 70分")
        print("  - 最小市值: 50亿元")
        print("  - 最大市盈率: 30倍")
        print("  - 投资等级: A+, A级")
        print("  - 结果数量: 前20只股票")
        
        # 执行快速选股
        result = selector.quick_select(
            min_score=70.0,        # 最小综合评分70分
            min_market_cap=50.0,   # 最小市值50亿
            max_pe_ratio=30.0,     # 最大市盈率30倍  
            grades=['A+', 'A'],    # 投资等级A+和A级
            limit=20               # 返回前20只股票
        )
        
        print(f"\n✅ 选股完成! 耗时: {result.execution_time:.2f}秒")
        print(f"📋 候选股票总数: {result.total_candidates}")
        print(f"🎯 筛选后数量: {result.filtered_count}")
        print(f"📈 成功率: {result.summary['success_rate']:.1f}%")
        
        if result.symbols:
            print(f"\n🏆 选出的优质股票 (前10只):")
            for i, symbol in enumerate(result.symbols[:10], 1):
                print(f"  {i:2d}. {symbol}")
            
            # 显示详细统计
            if 'statistics' in result.summary:
                stats = result.summary['statistics']
                if 'overall_score' in stats:
                    score_stats = stats['overall_score']
                    print(f"\n📊 综合评分统计:")
                    print(f"  平均分: {score_stats['mean']:.1f}")
                    print(f"  最高分: {score_stats['max']:.1f}")
                    print(f"  最低分: {score_stats['min']:.1f}")
        else:
            print("\n⚠️ 未找到符合条件的股票")
            print("建议适当放宽筛选条件")
            
    except Exception as e:
        print(f"❌ 选股失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 确认API配置正确")
        print("3. 稍后重试")

def demo_custom_filter():
    """演示自定义筛选功能"""
    print("\n" + "=" * 60)
    print("🎯 自定义筛选演示")
    print("=" * 60)
    
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector, SelectionCriteria
        from tradingagents.selectors.filter_conditions import FilterOperator
        
        selector = get_stock_selector()
        
        # 创建自定义筛选条件
        filters = [
            # 综合评分大于等于75分
            selector.create_numeric_filter('overall_score', FilterOperator.GREATER_EQUAL, 75),
            # 市值大于100亿
            selector.create_numeric_filter('market_cap', FilterOperator.GREATER_EQUAL, 100),
            # 只要A+级股票
            selector.create_enum_filter('grade', FilterOperator.IN, ['A+'])
        ]
        
        criteria = SelectionCriteria(
            filters=filters,
            sort_by='overall_score',  # 按综合评分排序
            sort_ascending=False,     # 降序排列
            limit=10,                 # 限制10只
            include_scores=True,      # 包含评分数据
            include_basic_info=True   # 包含基本信息
        )
        
        print("🔍 开始自定义选股...")
        print("  筛选条件: 综合评分≥75分 + 市值≥100亿 + A+级")
        
        result = selector.select_stocks(criteria)
        
        print(f"\n✅ 自定义选股完成! 耗时: {result.execution_time:.2f}秒")
        print(f"🎯 筛选结果: {result.filtered_count}只股票")
        
        if result.symbols:
            print(f"\n🌟 A+级优质股票:")
            for i, symbol in enumerate(result.symbols, 1):
                print(f"  {i:2d}. {symbol}")
        else:
            print("\n📝 建议: A+级条件较严格，可尝试:")
            print("  - 降低评分要求 (如65分)")
            print("  - 包含A级股票")
            print("  - 减少市值要求")
            
    except Exception as e:
        print(f"❌ 自定义选股失败: {e}")

def demo_available_fields():
    """演示可用的筛选字段"""
    print("\n" + "=" * 60)  
    print("📋 可用筛选字段列表")
    print("=" * 60)
    
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        
        selector = get_stock_selector()
        fields = selector.get_available_fields()
        
        print("📊 数值类型字段:")
        numeric_fields = [k for k, v in fields.items() if v.get('type') == 'numeric']
        for field in numeric_fields[:10]:  # 显示前10个
            info = fields[field]
            print(f"  • {info.get('name', field)}: {info.get('description', '无描述')}")
        
        print(f"\n🏷️ 枚举类型字段:")
        enum_fields = [k for k, v in fields.items() if v.get('type') == 'enum']
        for field in enum_fields[:5]:  # 显示前5个
            info = fields[field]
            print(f"  • {info.get('name', field)}: {info.get('description', '无描述')}")
            if 'allowed_values' in info:
                values = info['allowed_values'][:5]  # 显示前5个值
                print(f"    可选值: {values}")
                
        print(f"\n💡 总共可用字段: {len(fields)}个")
        
    except Exception as e:
        print(f"❌ 获取字段信息失败: {e}")

def main():
    """主函数"""
    print("🌟 TradingAgents-CN 选股系统演示")
    print("请确保已正确配置API密钥和依赖")
    print()
    
    # 演示1: 快速选股
    demo_quick_select()
    
    # 演示2: 自定义筛选
    demo_custom_filter()
    
    # 演示3: 可用字段
    demo_available_fields()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("💡 提示: 访问Web界面获得更好的交互体验")
    print("   启动命令: python start_web.py")
    print("   访问地址: http://localhost:8501")
    print("=" * 60)

if __name__ == "__main__":
    main()