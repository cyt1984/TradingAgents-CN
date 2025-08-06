#!/usr/bin/env python3
"""
热度分析系统命令行界面
提供简单易用的热度分析功能
"""

import sys
import os
import argparse
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.analytics import HeatAnalyzer, SocialMediaAPI, VolumeAnomalyDetector, SentimentAnalyzer
from tradingagents.analytics.integration import HeatAnalysisIntegration
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HeatCLI:
    """热度分析命令行界面"""
    
    def __init__(self):
        self.heat_integration = HeatAnalysisIntegration()
        self.heat_analyzer = HeatAnalyzer()
        self.social_api = SocialMediaAPI()
        self.volume_detector = VolumeAnomalyDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze_single(self, symbol: str, detailed: bool = False):
        """分析单个股票"""
        print(f"🔥 正在分析 {symbol} 的热度数据...")
        print("=" * 50)
        
        try:
            result = self.heat_integration.analyze_with_heat(symbol)
            
            # 显示综合热度
            heat_analysis = result.get('heat_analysis', {})
            heat_score = heat_analysis.get('heat_score', 0)
            heat_level = heat_analysis.get('heat_level', '未知')
            
            print(f"📊 综合热度: {heat_level}")
            print(f"📈 热度分数: {heat_score:.2f}/100")
            print()
            
            # 显示热度信号
            signals = result.get('heat_signals', [])
            if signals:
                print("🎯 热度信号:")
                for signal in signals:
                    icon = "🔴" if signal['level'] == 'high' else "🟡" if signal['level'] == 'medium' else "🟢"
                    print(f"   {icon} {signal['message']} (置信度: {signal['confidence']:.1f})")
                print()
            
            # 显示风险评估
            risk = result.get('risk_assessment', {})
            risk_level = risk.get('risk_level', '未知')
            risk_desc = risk.get('risk_description', '')
            print(f"⚠️ 风险评估: {risk_level.upper()}")
            print(f"   {risk_desc}")
            print()
            
            # 显示操作建议
            recommendations = result.get('action_recommendations', [])
            if recommendations:
                print("💡 操作建议:")
                for rec in recommendations:
                    print(f"   {rec}")
                print()
            
            # 详细信息
            if detailed:
                self._show_detailed_info(heat_analysis)
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    
    def _show_detailed_info(self, heat_analysis: dict):
        """显示详细信息"""
        details = heat_analysis.get('details', {})
        
        # 社交媒体热度
        social = details.get('social', {})
        if social:
            print("📱 社交媒体热度详情:")
            platforms = social.get('platforms', {})
            for platform, data in platforms.items():
                if isinstance(data, dict) and 'score' in data:
                    print(f"   {platform}: {data.get('score', 0):.1f}")
            print()
        
        # 成交量异动
        volume = details.get('volume', {})
        if volume:
            print("📊 成交量分析:")
            print(f"   异动得分: {volume.get('anomaly_score', 0):.1f}")
            print(f"   成交量比率: {volume.get('volume_analysis', {}).get('volume_ratio_5', 0):.2f}")
            print(f"   换手率: {volume.get('turnover_analysis', {}).get('latest_turnover', 0):.2f}%")
            print()
        
        # 情绪分析
        sentiment = details.get('sentiment', {})
        if sentiment:
            overall = sentiment.get('overall_sentiment', {})
            print("😊 市场情绪:")
            print(f"   综合情绪: {overall.get('sentiment_label', '未知')}")
            print(f"   情绪得分: {overall.get('sentiment_score', 0):.1f}")
            
            # 散户-机构博弈
            battle = sentiment.get('retail_institutional', {})
            if battle.get('is_divergence'):
                print(f"   ⚔️  博弈状态: {battle.get('battle_direction', '未知')}")
            print()
    
    def batch_analyze(self, symbols: list):
        """批量分析"""
        print(f"🔥 批量分析 {len(symbols)} 只股票...")
        print("=" * 50)
        
        try:
            results = self.heat_integration.batch_analyze_with_heat(symbols)
            
            print("🏆 热度排行榜:")
            for i, result in enumerate(results, 1):
                symbol = result['symbol']
                heat_score = result.get('heat_analysis', {}).get('heat_score', 0)
                heat_level = result.get('heat_analysis', {}).get('heat_level', '未知')
                print(f"   {i:2d}. {symbol:6s} - {heat_level} ({heat_score:.1f})")
                
        except Exception as e:
            print(f"❌ 批量分析失败: {e}")
    
    def watchlist_monitor(self, symbols: list, min_score: int = 60):
        """监控列表"""
        print(f"👀 监控热度 ≥ {min_score} 的股票...")
        print("=" * 50)
        
        try:
            watchlist = self.heat_integration.get_heat_watchlist(symbols, min_score)
            
            if watchlist:
                print("🔥 高热度监控列表:")
                for result in watchlist:
                    symbol = result['symbol']
                    heat_score = result.get('heat_analysis', {}).get('heat_score', 0)
                    heat_level = result.get('heat_analysis', {}).get('heat_level', '未知')
                    
                    print(f"   {symbol:6s} - {heat_level} ({heat_score:.1f})")
                    
                    # 显示主要信号
                    signals = result.get('heat_signals', [])
                    for signal in signals[:2]:  # 显示前2个信号
                        print(f"      {signal['message']}")
            else:
                print("❄️ 暂无高热度股票")
                
        except Exception as e:
            print(f"❌ 监控列表生成失败: {e}")
    
    def interactive_mode(self):
        """交互模式"""
        print("🔥 热度分析系统 - 交互模式")
        print("=" * 50)
        print("命令:")
        print("  analyze <symbol>    - 分析单个股票")
        print("  batch <symbol1,symbol2...> - 批量分析")
        print("  watch <symbols> [min_score] - 监控列表")
        print("  quit               - 退出")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！")
                    break
                
                elif command.startswith('analyze '):
                    symbol = command[8:].strip()
                    if symbol:
                        self.analyze_single(symbol, detailed=True)
                    else:
                        print("❌ 请提供股票代码")
                
                elif command.startswith('batch '):
                    symbols_str = command[6:].strip()
                    symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
                    if symbols:
                        self.batch_analyze(symbols)
                    else:
                        print("❌ 请提供股票代码列表")
                
                elif command.startswith('watch '):
                    parts = command[6:].strip().split()
                    if parts:
                        symbols = [s.strip() for s in parts[0].split(',') if s.strip()]
                        min_score = int(parts[1]) if len(parts) > 1 else 60
                        self.watchlist_monitor(symbols, min_score)
                    else:
                        print("❌ 请提供股票代码列表")
                
                else:
                    print("❌ 未知命令，请输入 help 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='热度分析系统')
    parser.add_argument('symbol', nargs='?', help='股票代码')
    parser.add_argument('-b', '--batch', help='批量分析，用逗号分隔')
    parser.add_argument('-w', '--watch', help='监控列表，用逗号分隔')
    parser.add_argument('-m', '--min-score', type=int, default=60, help='最小热度分数')
    parser.add_argument('-d', '--detailed', action='store_true', help='显示详细信息')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    cli = HeatCLI()
    
    if args.interactive:
        cli.interactive_mode()
    elif args.batch:
        symbols = [s.strip() for s in args.batch.split(',')]
        cli.batch_analyze(symbols)
    elif args.watch:
        symbols = [s.strip() for s in args.watch.split(',')]
        cli.watchlist_monitor(symbols, args.min_score)
    elif args.symbol:
        cli.analyze_single(args.symbol, detailed=args.detailed)
    else:
        # 默认测试模式
        print("🔥 热度分析系统")
        print("=" * 50)
        print("示例股票: 000001, 600519, 000858")
        
        test_symbols = ['000001', '600519', '000858']
        cli.batch_analyze(test_symbols)

if __name__ == "__main__":
    main()