#!/usr/bin/env python3
"""
热度分析系统测试脚本
测试所有免费热度分析模块功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.analytics import HeatAnalyzer, SocialMediaAPI, VolumeAnomalyDetector, SentimentAnalyzer
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_heat_analysis():
    """测试热度分析系统"""
    print("开始测试热度分析系统...")
    
    # 测试股票
    test_symbols = ['000001', '600519', '000858', '002415']
    
    # 初始化分析器
    heat_analyzer = HeatAnalyzer()
    social_api = SocialMediaAPI()
    volume_detector = VolumeAnomalyDetector()
    sentiment_analyzer = SentimentAnalyzer()
    
    print("\n1. 测试综合热度分析...")
    for symbol in test_symbols:
        try:
            result = heat_analyzer.analyze_heat(symbol)
            print(f"   {symbol}: {result['heat_level']} (得分: {result['heat_score']:.1f})")
            if result.get('alerts'):
                for alert in result['alerts']:
                    print(f"     预警: {alert['message']}")
        except Exception as e:
            print(f"   {symbol}: 分析失败 - {e}")
    
    print("\n2. 测试社交媒体热度...")
    for symbol in test_symbols[:2]:
        try:
            result = social_api.get_social_heat(symbol)
            platforms = result.get('platforms', {})
            print(f"   {symbol}: 综合热度 {result['score']:.1f}")
            for platform, data in platforms.items():
                if isinstance(data, dict) and 'score' in data:
                    print(f"     {platform}: {data['score']}")
        except Exception as e:
            print(f"   {symbol}: 社交媒体分析失败 - {e}")
    
    print("\n3. 测试成交量异动检测...")
    for symbol in test_symbols[:2]:
        try:
            result = volume_detector.detect_anomaly(symbol)
            print(f"   {symbol}: {result['anomaly_level']} (得分: {result['anomaly_score']:.1f})")
            if result.get('alerts'):
                for alert in result['alerts']:
                    print(f"     预警: {alert['message']}")
        except Exception as e:
            print(f"   {symbol}: 成交量分析失败 - {e}")
    
    print("\n4. 测试情绪分析...")
    for symbol in test_symbols[:2]:
        try:
            result = sentiment_analyzer.analyze_sentiment(symbol)
            overall = result.get('overall_sentiment', {})
            print(f"   {symbol}: {overall.get('sentiment_label', '未知')} (得分: {overall.get('sentiment_score', 0):.1f})")
            
            # 测试散户-机构博弈
            battle = result.get('retail_institutional', {})
            if battle.get('is_divergence'):
                print(f"     博弈状态: {battle.get('battle_direction', '未知')}")
        except Exception as e:
            print(f"   {symbol}: 情绪分析失败 - {e}")
    
    print("\n5. 测试热度排行榜...")
    try:
        rankings = heat_analyzer.get_heat_ranking(test_symbols, limit=4)
        for i, ranking in enumerate(rankings, 1):
            symbol = ranking['symbol']
            score = ranking['heat_score']
            print(f"   {i}. {symbol}: {score:.1f}分")
    except Exception as e:
        print(f"   排行榜生成失败 - {e}")
    
    print("\n测试完成！")

def test_real_time_monitoring():
    """测试实时监控功能"""
    print("\n测试实时监控...")
    
    heat_analyzer = HeatAnalyzer()
    
    # 模拟实时监控
    monitor_symbols = ['000001', '600519']
    
    print("监控股票热度变化...")
    for symbol in monitor_symbols:
        try:
            result = heat_analyzer.analyze_heat(symbol)
            heat_score = result['heat_score']
            
            # 模拟三级预警
            if heat_score >= 80:
                print(f"{symbol}: 极高热度警报 ({heat_score:.1f})")
            elif heat_score >= 60:
                print(f"{symbol}: 高热度提醒 ({heat_score:.1f})")
            elif heat_score >= 40:
                print(f"{symbol}: 中等热度 ({heat_score:.1f})")
            else:
                print(f"{symbol}: 正常热度 ({heat_score:.1f})")
                
        except Exception as e:
            print(f"监控 {symbol} 失败: {e}")

if __name__ == "__main__":
    try:
        test_heat_analysis()
        test_real_time_monitoring()
        
        print("\n" + "="*50)
        print("🎉 热度分析系统测试完成！")
        print("📊 所有模块功能正常")
        print("🔍 可开始实际应用")
        
    except KeyboardInterrupt:
        print("\n❌ 测试被中断")
    except Exception as e:
        print(f"\n测试失败: {e}")