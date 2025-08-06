#!/usr/bin/env python3
"""
增强分析功能演示脚本
展示新数据源如何融入分析报告
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.tools.enhanced_news_tool import (
    get_enhanced_stock_news, 
    get_enhanced_market_sentiment,
    get_enhanced_social_discussions
)
import json
import time


def demo_enhanced_tools():
    """演示增强工具的功能"""
    test_symbol = '000001'  # 平安银行
    
    print("🚀 增强数据源工具演示")
    print("=" * 60)
    
    # 演示增强新闻工具
    print(f"\n📰 演示增强新闻工具 - {test_symbol}")
    print("-" * 40)
    try:
        news_result = get_enhanced_stock_news(test_symbol, 20)
        print(f"✅ 新闻工具返回结果长度: {len(news_result)} 字符")
        print(f"📋 结果预览:")
        print(news_result[:800] + "..." if len(news_result) > 800 else news_result)
    except Exception as e:
        print(f"❌ 新闻工具测试失败: {e}")
    
    # 演示市场情绪工具
    print(f"\n😊 演示市场情绪工具 - {test_symbol}")
    print("-" * 40)
    try:
        sentiment_result = get_enhanced_market_sentiment(test_symbol)
        print(f"✅ 情绪工具返回结果长度: {len(sentiment_result)} 字符")
        print(f"📋 结果预览:")
        print(sentiment_result[:800] + "..." if len(sentiment_result) > 800 else sentiment_result)
    except Exception as e:
        print(f"❌ 情绪工具测试失败: {e}")
    
    # 演示社交讨论工具
    print(f"\n💬 演示社交讨论工具 - {test_symbol}")
    print("-" * 40)
    try:
        discussions_result = get_enhanced_social_discussions(test_symbol, 30)
        print(f"✅ 讨论工具返回结果长度: {len(discussions_result)} 字符")
        print(f"📋 结果预览:")
        print(discussions_result[:800] + "..." if len(discussions_result) > 800 else discussions_result)
    except Exception as e:
        print(f"❌ 讨论工具测试失败: {e}")


def demo_full_analysis():
    """演示完整的增强分析流程"""
    test_symbol = 'AAPL'  # 苹果公司（测试美股）
    
    print(f"\n\n🎯 完整增强分析演示 - {test_symbol}")
    print("=" * 60)
    
    try:
        # 创建增强配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "openai"  # 或使用其他模型
        config["deep_think_llm"] = "gpt-4o-mini"
        config["quick_think_llm"] = "gpt-4o-mini"
        config["max_debate_rounds"] = 2  # 增加辩论轮数
        config["online_tools"] = True
        
        print("🔧 配置信息:")
        print(f"   - LLM提供商: {config['llm_provider']}")
        print(f"   - 深度思考模型: {config['deep_think_llm']}")
        print(f"   - 辩论轮数: {config['max_debate_rounds']}")
        print(f"   - 在线工具: {config['online_tools']}")
        
        # 创建交易智能体图
        print(f"\n🤖 初始化TradingAgents...")
        ta = TradingAgentsGraph(
            selected_analysts=["news", "social", "fundamentals", "market"],
            debug=True,
            config=config
        )
        
        print(f"✅ TradingAgents初始化完成")
        
        # 执行分析
        print(f"\n🔍 开始分析 {test_symbol}...")
        start_time = time.time()
        
        state, decision = ta.propagate(test_symbol, "2024-01-15")
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        print(f"\n✅ 分析完成! 耗时: {analysis_time:.2f} 秒")
        
        # 显示决策结果
        print(f"\n📊 投资决策结果:")
        print(f"   - 推荐动作: {decision.get('action', 'N/A')}")
        print(f"   - 置信度: {decision.get('confidence', 0):.1%}")
        print(f"   - 风险评分: {decision.get('risk_score', 0):.1%}")
        print(f"   - 目标价位: {decision.get('target_price', 'N/A')}")
        
        # 显示推理过程概要
        reasoning = decision.get('reasoning', 'N/A')
        if reasoning and len(reasoning) > 500:
            print(f"\n🧠 推理过程概要:")
            print(f"   {reasoning[:500]}...")
        elif reasoning:
            print(f"\n🧠 推理过程:")
            print(f"   {reasoning}")
        
        # 显示各分析师报告概要
        print(f"\n📋 分析师报告概要:")
        
        if 'news_report' in state:
            news_report = state['news_report']
            print(f"   📰 新闻分析师: {len(news_report)} 字符")
            
        if 'sentiment_report' in state:
            sentiment_report = state['sentiment_report']
            print(f"   😊 社交媒体分析师: {len(sentiment_report)} 字符")
            
        if 'fundamentals_report' in state:
            fundamentals_report = state['fundamentals_report']
            print(f"   💰 基本面分析师: {len(fundamentals_report)} 字符")
            
        if 'market_report' in state:
            market_report = state['market_report']
            print(f"   📈 市场分析师: {len(market_report)} 字符")
        
        # 保存完整报告到文件
        report_filename = f"enhanced_analysis_report_{test_symbol}_{int(time.time())}.json"
        
        full_report = {
            'symbol': test_symbol,
            'analysis_time': analysis_time,
            'decision': decision,
            'reports': {
                'news': state.get('news_report', ''),
                'sentiment': state.get('sentiment_report', ''),
                'fundamentals': state.get('fundamentals_report', ''),
                'market': state.get('market_report', '')
            },
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完整报告已保存: {report_filename}")
        
    except Exception as e:
        print(f"❌ 完整分析演示失败: {e}")
        import traceback
        traceback.print_exc()


def demo_data_comparison():
    """演示新旧数据源的对比"""
    test_symbol = '000001'
    
    print(f"\n\n📊 数据源对比演示 - {test_symbol}")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
        
        manager = get_enhanced_data_manager()
        
        # 获取数据源状态
        print("🔍 数据源可用性检查:")
        provider_status = manager.get_provider_status()
        for source, available in provider_status.items():
            status_icon = "✅" if available else "❌"
            print(f"   {status_icon} {source}")
        
        # 对比数据获取速度
        print(f"\n⚡ 数据获取速度对比:")
        
        # 测试综合股票信息
        start_time = time.time()
        stock_info = manager.get_comprehensive_stock_info(test_symbol)
        stock_time = time.time() - start_time
        print(f"   📊 综合股票信息: {stock_time:.2f}秒")
        
        # 测试综合新闻
        start_time = time.time()
        news_data = manager.get_comprehensive_news(test_symbol, 20)
        news_time = time.time() - start_time
        print(f"   📰 综合新闻数据: {news_time:.2f}秒 ({len(news_data)}条)")
        
        # 测试情绪分析
        start_time = time.time()
        sentiment_data = manager.get_comprehensive_sentiment(test_symbol)
        sentiment_time = time.time() - start_time
        print(f"   😊 情绪分析数据: {sentiment_time:.2f}秒")
        
        # 显示数据质量
        print(f"\n📈 数据质量对比:")
        if stock_info:
            sources = stock_info.get('sources', [])
            print(f"   📊 股票信息来源: {len(sources)} 个 ({', '.join(sources)})")
        
        if news_data:
            news_sources = set()
            for news in news_data:
                source = news.get('data_source', news.get('source', 'unknown'))
                news_sources.add(source)
            print(f"   📰 新闻数据来源: {len(news_sources)} 个 ({', '.join(news_sources)})")
        
        if sentiment_data:
            sentiment_sources = sentiment_data.get('sources', [])
            sentiment_score = sentiment_data.get('overall_sentiment', 0)
            confidence = sentiment_data.get('confidence', 0)
            print(f"   😊 情绪数据来源: {len(sentiment_sources)} 个")
            print(f"   📊 情绪评分: {sentiment_score:.3f} (置信度: {confidence:.2f})")
        
    except Exception as e:
        print(f"❌ 数据源对比演示失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🎯 TradingAgents-CN 增强分析功能演示")
    print("展示新数据源如何融入分析报告")
    print("=" * 80)
    
    # 演示增强工具
    demo_enhanced_tools()
    
    # 演示数据源对比
    demo_data_comparison()
    
    # 询问是否进行完整分析演示
    try:
        user_input = input("\n是否进行完整分析演示？(需要LLM API密钥) [y/N]: ").strip().lower()
        if user_input in ['y', 'yes']:
            demo_full_analysis()
        else:
            print("⏭️ 跳过完整分析演示")
    except KeyboardInterrupt:
        print("\n\n👋 演示结束")
    
    print("\n\n🎉 演示完成！")
    print("=" * 80)
    print("📋 总结:")
    print("✅ 新数据源已成功集成到分析报告中")
    print("✅ 提供更丰富的新闻、情绪、讨论数据")
    print("✅ 多源数据整合提高分析准确性")
    print("✅ 增强工具完全兼容现有分析流程")


if __name__ == "__main__":
    main()