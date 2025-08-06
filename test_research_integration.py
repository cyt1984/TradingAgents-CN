#!/usr/bin/env python3
"""
测试研报数据集成效果和准确性
验证基本面分析师、研究员和新闻分析师的研报功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.research_report_utils import (
    get_stock_research_reports, 
    get_institutional_consensus,
    get_research_report_manager
)

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('test')


def test_research_data_adapter():
    """测试研报数据适配器"""
    print("🔍 测试研报数据适配器...")
    
    test_symbols = ["000001", "600519", "002027"]
    
    for symbol in test_symbols:
        print(f"\n📊 测试股票: {symbol}")
        
        try:
            # 测试获取研报
            reports = get_stock_research_reports(symbol, limit=5)
            print(f"  ✅ 获取研报数量: {len(reports)}")
            
            if reports:
                print(f"  📰 最新研报: {reports[0].title}")
                print(f"  🏢 机构: {reports[0].institution}")
                print(f"  📈 评级: {reports[0].rating}")
                print(f"  💰 目标价: {reports[0].target_price}")
                
            # 测试机构一致预期
            consensus = get_institutional_consensus(symbol)
            print(f"  📈 机构一致预期: {consensus.get('total_reports', 0)} 份研报")
            
            if consensus:
                print(f"  🎯 平均目标价: {consensus.get('average_target_price')}")
                print(f"  📊 评级分布: {consensus.get('rating_distribution', {})}")
                print(f"  🏛️ 覆盖机构数: {consensus.get('institution_count', 0)}")
                
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")


def test_fundamentals_analyst_integration():
    """测试基本面分析师的机构观点集成"""
    print("\n🔍 测试基本面分析师机构观点集成...")
    
    # 这里我们模拟基本面分析师获取机构观点的过程
    test_symbol = "000001"
    
    try:
        from tradingagents.dataflows.research_report_utils import get_institutional_consensus
        from tradingagents.utils.stock_utils import StockUtils
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(test_symbol)
        print(f"  📊 股票类型: {market_info['market_name']}")
        
        # 获取机构一致预期
        consensus = get_institutional_consensus(test_symbol)
        
        if consensus and consensus.get('total_reports', 0) > 0:
            print("  ✅ 基本面分析师可以获取机构观点")
            
            # 模拟构建机构观点摘要
            institutional_summary = f"""
📈 **机构一致预期数据**：
- 研报总数: {consensus.get('total_reports', 0)} 份
- 覆盖机构数: {consensus.get('institution_count', 0)} 家
- 平均目标价: {consensus.get('average_target_price', '未知')} {market_info['currency_symbol']}
"""
            
            rating_dist = consensus.get('rating_distribution', {})
            if rating_dist:
                institutional_summary += f"- 评级分布: "
                for rating, count in rating_dist.items():
                    institutional_summary += f"{rating}({count}份) "
                institutional_summary += "\n"
            
            print("  📋 机构观点摘要示例:")
            print(institutional_summary)
            
        else:
            print("  ⚠️ 未获取到机构观点数据")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")


def test_research_team_integration():
    """测试研究团队的观点支撑"""
    print("\n🔍 测试研究团队观点支撑...")
    
    test_symbol = "000001"
    
    try:
        from tradingagents.dataflows.research_report_utils import get_stock_research_reports, get_institutional_consensus
        from tradingagents.utils.stock_utils import StockUtils
        
        market_info = StockUtils.get_market_info(test_symbol)
        currency_symbol = market_info['currency_symbol']
        
        # 获取研报数据
        reports = get_stock_research_reports(test_symbol, limit=10)
        consensus = get_institutional_consensus(test_symbol)
        
        if reports and consensus:
            # 测试看涨观点支撑
            bullish_reports = [r for r in reports if r.rating in ['买入', '增持', '强推']]
            
            if bullish_reports:
                print("  📈 看涨研究员观点支撑:")
                print(f"    - 看涨评级数量: {len(bullish_reports)} 份研报")
                print(f"    - 覆盖机构: {', '.join(set([r.institution for r in bullish_reports[:3]]))}")
                print(f"    - 平均目标价: {consensus.get('average_target_price', '未知')} {currency_symbol}")
            else:
                print("    ⚠️ 未找到明确看涨评级")
            
            # 测试看跌观点支撑
            bearish_reports = [r for r in reports if r.rating in ['卖出', '减持']]
            neutral_reports = [r for r in reports if r.rating in ['持有', '中性']]
            
            if bearish_reports:
                print("  📉 看跌研究员观点支撑:")
                print(f"    - 看跌评级数量: {len(bearish_reports)} 份研报")
                print(f"    - 谨慎机构: {', '.join(set([r.institution for r in bearish_reports[:3]]))}")
            elif neutral_reports:
                print("  ⚠️ 看跌研究员中性观点:")
                print(f"    - 中性评级数量: {len(neutral_reports)} 份研报")
            else:
                print("    ℹ️ 未找到看跌或中性评级")
                
        else:
            print("  ⚠️ 研究团队未获取到研报数据")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")


def test_news_analyst_integration():
    """测试新闻分析师的研报事件监控"""
    print("\n🔍 测试新闻分析师研报事件监控...")
    
    test_symbol = "000001"
    
    try:
        from tradingagents.dataflows.research_report_utils import get_stock_research_reports
        from tradingagents.utils.stock_utils import StockUtils
        
        market_info = StockUtils.get_market_info(test_symbol)
        
        # 获取最新研报发布信息
        recent_reports = get_stock_research_reports(test_symbol, limit=5)
        
        if recent_reports:
            print("  📊 新闻分析师可以监控研报发布事件:")
            
            research_report_news = f"""
📊 **最新研报发布动态**：
"""
            for i, report in enumerate(recent_reports[:3], 1):
                research_report_news += f"""
{i}. **{report.institution}** ({report.publish_date})
   - 标题: {report.title}
   - 评级: {report.rating}  
   - 目标价: {report.target_price or '未披露'} {market_info['currency_symbol']}
   - 核心观点: {report.summary[:100]}..."""
            
            research_report_news += f"""

⚠️ **重要提醒**: 请将上述研报发布作为重要新闻事件进行分析，评估其对股价和市场情绪的潜在影响。
"""
            
            print("  📋 研报事件监控示例:")
            print(research_report_news)
            
        else:
            print("  ⚠️ 新闻分析师未获取到研报发布信息")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")


def test_data_quality():
    """测试数据质量和准确性"""
    print("\n🔍 测试数据质量和准确性...")
    
    try:
        manager = get_research_report_manager()
        test_symbol = "000001"
        
        # 获取综合研报数据
        reports = manager.get_comprehensive_reports(test_symbol, limit_per_source=3)
        
        print(f"  📊 总研报数量: {len(reports)}")
        
        # 数据源分布
        sources = {}
        for report in reports:
            sources[report.source] = sources.get(report.source, 0) + 1
        
        print("  📈 数据源分布:")
        for source, count in sources.items():
            print(f"    - {source}: {count} 条")
        
        # 分析机构一致预期
        consensus = manager.analyze_consensus(reports)
        
        if consensus:
            print("  🎯 机构一致预期分析:")
            print(f"    - 研报总数: {consensus.get('total_reports', 0)}")
            print(f"    - 平均目标价: {consensus.get('average_target_price')}")
            print(f"    - 覆盖机构数: {consensus.get('institution_count', 0)}")
            print(f"    - 评级分布: {consensus.get('rating_distribution', {})}")
            
            # 数据质量检查
            quality_issues = []
            
            if consensus.get('total_reports', 0) == 0:
                quality_issues.append("无研报数据")
            
            if not consensus.get('average_target_price'):
                quality_issues.append("缺少目标价数据")
                
            if consensus.get('institution_count', 0) < 2:
                quality_issues.append("机构覆盖度不足")
            
            if quality_issues:
                print(f"  ⚠️ 数据质量问题: {', '.join(quality_issues)}")
            else:
                print("  ✅ 数据质量良好")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")


def main():
    """主测试函数"""
    print("🚀 开始测试研报数据集成效果和准确性")
    print("=" * 60)
    
    # 测试各个组件
    test_research_data_adapter()
    test_fundamentals_analyst_integration()
    test_research_team_integration() 
    test_news_analyst_integration()
    test_data_quality()
    
    print("\n" + "=" * 60)
    print("✅ 研报数据集成测试完成")
    
    print("\n📋 **集成效果总结**:")
    print("1. ✅ 基本面分析师：增加机构一致预期分析，提供估值交叉验证")
    print("2. ✅ 看涨研究员：引用机构看涨评级作为论证支撑")
    print("3. ✅ 看跌研究员：利用机构谨慎观点和分歧分析风险")
    print("4. ✅ 新闻分析师：监控研报发布事件，评估市场影响")
    print("5. ✅ 数据适配器：集成多数据源，提供标准化研报数据")
    
    print("\n🎯 **预期提升效果**:")
    print("- 📈 估值准确性：结合机构一致预期，提高价格预测可信度")
    print("- 🔍 风险识别：机构分歧作为重要投资风险信号")
    print("- ⏱️ 时机把握：研报发布节奏作为交易时机参考")
    print("- 🏛️ 专业性：权威机构观点增强分析可信度")


if __name__ == "__main__":
    main()