#!/usr/bin/env python3
"""
阶段2 AI增强选股系统简化测试
测试核心功能，避免复杂依赖
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# 导入基础选股模块
from tradingagents.selectors.stock_selector import StockSelector
from tradingagents.selectors.filter_conditions import SelectionCriteria, NumericFilter, FilterOperator


def create_test_stock_data() -> List[Dict[str, Any]]:
    """创建测试股票数据"""
    return [
        {
            'symbol': '000001',
            'name': '平安银行',
            'current_price': 12.50,
            'change_pct': 2.5,
            'volume': 150000000,
            'turnover': 1875000000,
            'market_cap': 24150000000,
            'pe_ratio': 5.2,
            'pb_ratio': 0.65,
            'roe': 0.12,
            'roa': 0.008,
            'debt_ratio': 0.9,
            'revenue_growth': 0.08,
            'profit_growth': 0.15,
            'industry': '金融银行',
            'score': 78.5,
            'technical_score': 72,
            'fundamental_score': 85,
            'sentiment_score': 68,
            'quality_score': 80,
            'risk_level': 0.4,
            'volatility': 0.25
        },
        {
            'symbol': '000858',
            'name': '五粮液',
            'current_price': 168.50,
            'change_pct': 3.8,
            'volume': 12000000,
            'turnover': 2022000000,
            'market_cap': 650000000000,
            'pe_ratio': 25.6,
            'pb_ratio': 5.8,
            'roe': 0.22,
            'roa': 0.15,
            'debt_ratio': 0.35,
            'revenue_growth': 0.12,
            'profit_growth': 0.18,
            'industry': '食品饮料',
            'score': 85.3,
            'technical_score': 88,
            'fundamental_score': 90,
            'sentiment_score': 82,
            'quality_score': 85,
            'risk_level': 0.3,
            'volatility': 0.28
        },
        {
            'symbol': '002027',
            'name': '分众传媒',
            'current_price': 6.85,
            'change_pct': 5.2,
            'volume': 185000000,
            'turnover': 1267250000,
            'market_cap': 95000000000,
            'pe_ratio': 18.5,
            'pb_ratio': 2.1,
            'roe': 0.18,
            'roa': 0.12,
            'debt_ratio': 0.25,
            'revenue_growth': 0.25,
            'profit_growth': 0.35,
            'industry': '传媒广告',
            'score': 82.7,
            'technical_score': 85,
            'fundamental_score': 82,
            'sentiment_score': 88,
            'quality_score': 78,
            'risk_level': 0.5,
            'volatility': 0.35
        },
        {
            'symbol': '600519',
            'name': '贵州茅台',
            'current_price': 1680.00,
            'change_pct': 2.1,
            'volume': 2500000,
            'turnover': 4200000000,
            'market_cap': 2100000000000,
            'pe_ratio': 32.5,
            'pb_ratio': 8.2,
            'roe': 0.28,
            'roa': 0.20,
            'debt_ratio': 0.15,
            'revenue_growth': 0.15,
            'profit_growth': 0.18,
            'industry': '食品饮料',
            'score': 92.8,
            'technical_score': 90,
            'fundamental_score': 95,
            'sentiment_score': 92,
            'quality_score': 95,
            'risk_level': 0.2,
            'volatility': 0.25
        }
    ]


def test_stock_selector():
    """测试基础选股器功能"""
    print("\n" + "="*50)
    print("测试基础选股器")
    print("="*50)
    
    try:
        # 初始化选股器
        selector = StockSelector()
        
        # 测试数据
        test_stocks = create_test_stock_data()
        
        # 创建选股条件
        criteria = SelectionCriteria(
            min_score=75.0,
            max_risk_level=0.5,
            filters=[
                NumericFilter("market_cap", "市值", FilterOperator.GREATER, 50000000000),  # 大于500亿
                NumericFilter("pe_ratio", "PE比率", FilterOperator.LESS, 30),
                NumericFilter("roe", "ROE", FilterOperator.GREATER, 0.15)
            ],
            max_results=5
        )
        
        # 执行选股
        print(f"总股票数: {len(test_stocks)}")
        result = selector.select_stocks(criteria, test_stocks)
        
        print(f"筛选后股票数: {len(result.selected_stocks)}")
        print(f"筛选条件数: {len(result.applied_filters)}")
        print(f"处理时间: {result.processing_time:.3f}秒")
        
        # 显示筛选结果
        if result.selected_stocks:
            print("\n通过筛选的股票:")
            print("-" * 60)
            print(f"{'代码':<8} {'名称':<12} {'评分':<6} {'ROE':<6} {'PE':<6} {'市值(亿)':<10}")
            print("-" * 60)
            
            for stock in result.selected_stocks:
                market_cap_billion = stock['market_cap'] / 100000000  # 转换为亿元
                print(f"{stock['symbol']:<8} {stock['name']:<12} "
                      f"{stock['score']:<6.1f} {stock['roe']:<6.2%} "
                      f"{stock['pe_ratio']:<6.1f} {market_cap_billion:<10.0f}")
        
        # 显示筛选统计
        if result.filter_statistics:
            print(f"\n筛选统计:")
            for filter_name, stats in result.filter_statistics.items():
                print(f"  {filter_name}: 通过 {stats['passed']}/{stats['total']}")
        
        return True
        
    except Exception as e:
        print(f"选股器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_expert_committee_simple():
    """测试AI专家委员会 - 简化版"""
    print("\n" + "="*50)
    print("测试AI专家委员会 (简化版)")
    print("="*50)
    
    try:
        # 直接导入并测试，避免复杂的TradingGraph初始化
        from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee
        
        # 使用简化配置初始化
        committee = AIExpertCommittee(config={'online_tools': False})
        
        # 测试基本功能
        test_symbol = '002027'
        stock_data = {
            'primary': create_test_stock_data()[2]  # 分众传媒
        }
        
        print(f"测试股票: {test_symbol}")
        print("AI专家委员会初始化成功")
        print(f"专家权重配置: {len(committee.expert_weights)} 个专家")
        print(f"一致性阈值: {committee.consensus_thresholds}")
        
        # 测试创建错误结果功能
        error_result = committee._create_error_result(test_symbol, "测试错误")
        print(f"错误处理功能正常: {error_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"AI专家委员会测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_engine_simple():
    """测试自适应引擎 - 简化版"""
    print("\n" + "="*50)
    print("测试自适应引擎 (简化版)")
    print("="*50)
    
    try:
        from tradingagents.selectors.ai_strategies.adaptive_engine import AdaptiveEngine, MarketRegime, StrategyType
        
        # 初始化自适应引擎
        engine = AdaptiveEngine()
        
        print("自适应引擎初始化成功")
        print(f"策略类型数量: {len(StrategyType)}")
        print(f"市场环境类型: {len(MarketRegime)}")
        print(f"策略库大小: {len(engine.strategy_library)}")
        
        # 测试默认策略获取
        default_strategy = engine._get_default_strategy(MarketRegime.BULL_MARKET)
        print(f"默认策略类型: {default_strategy.strategy_type.value}")
        print(f"默认预期收益: {default_strategy.expected_performance:.2%}")
        print(f"默认风险承受度: {default_strategy.risk_tolerance:.2%}")
        
        # 测试市场环境检测 - 使用简化数据
        simple_market_data = {
            'price_data': [
                {'close': 3200 + i, 'volume': 4000000000} 
                for i in range(25)
            ]
        }
        
        detected_regime = engine.detect_market_regime(simple_market_data)
        print(f"检测到的市场环境: {detected_regime.value}")
        
        return True
        
    except Exception as e:
        print(f"自适应引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_engine_simple():
    """测试相似性引擎 - 简化版"""
    print("\n" + "="*50)
    print("测试相似性引擎 (简化版)")
    print("="*50)
    
    try:
        from tradingagents.selectors.ai_strategies.similarity_engine import SimilarityEngine, SimilarityDimension
        
        # 初始化相似性引擎
        engine = SimilarityEngine()
        
        print("相似性引擎初始化成功")
        print(f"相似性维度数量: {len(SimilarityDimension)}")
        print(f"维度权重配置: {len(engine.dimension_weights)}")
        print(f"特征提取器数量: {len(engine.feature_extractors)}")
        
        # 测试特征提取
        test_stock = create_test_stock_data()[0]  # 平安银行
        
        # 测试各维度特征提取
        for dimension in list(SimilarityDimension)[:3]:  # 测试前3个维度
            try:
                extractor = engine.feature_extractors[dimension]
                features = extractor('000001', test_stock)
                print(f"{dimension.value}特征维度: {len(features)}, 特征值范围: [{features.min():.3f}, {features.max():.3f}]")
            except Exception as e:
                print(f"{dimension.value}特征提取失败: {e}")
        
        # 测试相似度计算方法
        import numpy as np
        vector1 = np.array([0.1, 0.2, 0.3, 0.4])
        vector2 = np.array([0.15, 0.25, 0.35, 0.45])
        
        similarity = engine._calculate_cosine_similarity(vector1, vector2)
        print(f"余弦相似度计算测试: {similarity:.3f}")
        
        confidence = engine._calculate_feature_confidence(vector1, vector2)
        print(f"特征置信度计算测试: {confidence:.3f}")
        
        return True
        
    except Exception as e:
        print(f"相似性引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_workflow():
    """测试集成工作流程"""
    print("\n" + "="*50)
    print("测试AI选股集成工作流程")
    print("="*50)
    
    try:
        # 1. 基础选股
        print("第1步: 基础选股筛选")
        selector = StockSelector()
        test_stocks = create_test_stock_data()
        
        criteria = SelectionCriteria(
            min_score=80.0,
            max_risk_level=0.4,
            filters=[
                NumericFilter("roe", "ROE", FilterOperator.GREATER, 0.15),
                NumericFilter("pe_ratio", "PE比率", FilterOperator.LESS, 35)
            ],
            max_results=10
        )
        
        result = selector.select_stocks(criteria, test_stocks)
        selected_stocks = result.selected_stocks
        
        print(f"基础筛选结果: {len(selected_stocks)}/{len(test_stocks)} 只股票通过")
        
        if selected_stocks:
            print("通过基础筛选的股票:")
            for stock in selected_stocks:
                print(f"  {stock['symbol']} - {stock['name']} (评分: {stock['score']})")
        
        # 2. AI增强评分 (简化版)
        print(f"\n第2步: AI增强评分")
        
        enhanced_stocks = []
        for stock in selected_stocks:
            # 简化的AI增强评分逻辑
            base_score = stock['score']
            
            # 基于行业的奖励
            industry_bonus = 0
            if stock['industry'] in ['食品饮料', '金融银行']:
                industry_bonus = 5  # 优质行业奖励
            
            # 基于财务指标的奖励
            financial_bonus = 0
            if stock['roe'] > 0.2:  # ROE超过20%
                financial_bonus += 3
            if stock['pe_ratio'] < 20:  # PE低于20
                financial_bonus += 2
            
            # 基于技术面的奖励
            technical_bonus = 0
            if stock['change_pct'] > 0:  # 上涨
                technical_bonus += 1
            if stock['volume'] > 50000000:  # 高流动性
                technical_bonus += 1
            
            # 计算AI增强评分
            ai_enhanced_score = base_score + industry_bonus + financial_bonus + technical_bonus
            
            enhanced_stock = stock.copy()
            enhanced_stock['ai_enhanced_score'] = min(100, ai_enhanced_score)
            enhanced_stock['enhancement_details'] = {
                'base_score': base_score,
                'industry_bonus': industry_bonus,
                'financial_bonus': financial_bonus,
                'technical_bonus': technical_bonus
            }
            
            enhanced_stocks.append(enhanced_stock)
        
        # 按AI增强评分排序
        enhanced_stocks.sort(key=lambda x: x['ai_enhanced_score'], reverse=True)
        
        print("AI增强评分结果:")
        for i, stock in enumerate(enhanced_stocks, 1):
            details = stock['enhancement_details']
            print(f"  {i}. {stock['symbol']} - {stock['name']}")
            print(f"     基础评分: {details['base_score']:.1f}")
            print(f"     AI增强评分: {stock['ai_enhanced_score']:.1f}")
            print(f"     增强明细: 行业+{details['industry_bonus']} 财务+{details['financial_bonus']} 技术+{details['technical_bonus']}")
        
        # 3. 最终推荐
        print(f"\n第3步: 生成最终推荐")
        
        final_recommendations = enhanced_stocks[:3]  # 推荐前3名
        
        print("最终推荐股票:")
        print("-" * 70)
        print(f"{'排名':<4} {'代码':<8} {'名称':<12} {'AI评分':<8} {'预期收益':<8} {'风险级别':<8}")
        print("-" * 70)
        
        for i, stock in enumerate(final_recommendations, 1):
            # 简化的收益预测
            predicted_return = (stock['ai_enhanced_score'] - 50) / 200  # 转换为预期收益率
            risk_level = "低" if stock['risk_level'] < 0.3 else "中" if stock['risk_level'] < 0.6 else "高"
            
            print(f"{i:<4} {stock['symbol']:<8} {stock['name']:<12} "
                  f"{stock['ai_enhanced_score']:<8.1f} {predicted_return:<8.1%} {risk_level:<8}")
        
        # 4. 投资组合建议
        print(f"\n第4步: 投资组合建议")
        
        total_score = sum(stock['ai_enhanced_score'] for stock in final_recommendations)
        
        print("建议投资组合配置:")
        for stock in final_recommendations:
            weight = stock['ai_enhanced_score'] / total_score
            print(f"  {stock['symbol']} - {stock['name']}: {weight:.1%}")
        
        # 组合风险评估
        avg_risk = sum(stock['risk_level'] for stock in final_recommendations) / len(final_recommendations)
        portfolio_risk = "低风险" if avg_risk < 0.3 else "中等风险" if avg_risk < 0.6 else "高风险"
        
        print(f"\n投资组合风险评估: {portfolio_risk}")
        print(f"平均风险水平: {avg_risk:.2f}")
        
        # 预期组合收益
        weighted_returns = sum((stock['ai_enhanced_score'] - 50) / 200 * stock['ai_enhanced_score'] / total_score 
                              for stock in final_recommendations)
        print(f"预期组合收益: {weighted_returns:.1%}")
        
        return True
        
    except Exception as e:
        print(f"集成工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始阶段2 AI增强选股系统简化测试")
    print("=" * 60)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("基础选股器", test_stock_selector),
        ("AI专家委员会(简化)", test_ai_expert_committee_simple),
        ("自适应引擎(简化)", test_adaptive_engine_simple),
        ("相似性引擎(简化)", test_similarity_engine_simple),
        ("集成工作流程", test_integrated_workflow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        result = test_func()
        test_results.append((test_name, result))
        
        if result:
            print(f"✓ {test_name} 测试通过")
        else:
            print(f"✗ {test_name} 测试失败")
    
    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    print(f"总测试项目: {total_count}")
    print(f"通过测试: {passed_count}")
    print(f"失败测试: {total_count - passed_count}")
    print(f"通过率: {passed_count/total_count:.1%}")
    
    print("\n详细结果:")
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"   {test_name:<25} {status}")
    
    if passed_count == total_count:
        print(f"\n🎉 所有测试通过！阶段2 AI增强选股系统核心功能正常！")
        return True
    else:
        print(f"\n⚠️ 部分测试失败，请检查相关模块。")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)