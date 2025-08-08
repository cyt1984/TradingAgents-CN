#!/usr/bin/env python3
"""
阶段2 AI增强选股系统集成测试
测试AI专家委员会、模式识别、自适应引擎和相似性推荐的集成功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# 导入AI增强选股模块
from tradingagents.selectors.ai_strategies.expert_committee import AIExpertCommittee, ExpertAnalysisResult
from tradingagents.selectors.ai_strategies.pattern_recognizer import PatternRecognizer, PatternType
from tradingagents.selectors.ai_strategies.adaptive_engine import AdaptiveEngine, MarketRegime, StrategyType
from tradingagents.selectors.ai_strategies.similarity_engine import SimilarityEngine, SimilarityDimension

# 导入基础选股模块
from tradingagents.selectors.stock_selector import StockSelector
from tradingagents.selectors.filter_conditions import SelectionCriteria, NumericFilter, FilterOperator

# 导入工具和配置
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


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
            'symbol': '000002',
            'name': '万科A',
            'current_price': 15.80,
            'change_pct': -1.2,
            'volume': 85000000,
            'turnover': 1343000000,
            'market_cap': 175000000000,
            'pe_ratio': 8.5,
            'pb_ratio': 1.2,
            'roe': 0.15,
            'roa': 0.05,
            'debt_ratio': 0.75,
            'revenue_growth': -0.05,
            'profit_growth': -0.12,
            'industry': '房地产',
            'score': 65.2,
            'technical_score': 58,
            'fundamental_score': 70,
            'sentiment_score': 55,
            'quality_score': 75,
            'risk_level': 0.6,
            'volatility': 0.32
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
            'symbol': '600036',
            'name': '招商银行',
            'current_price': 42.30,
            'change_pct': 1.8,
            'volume': 25000000,
            'turnover': 1057500000,
            'market_cap': 1080000000000,
            'pe_ratio': 6.8,
            'pb_ratio': 1.1,
            'roe': 0.16,
            'roa': 0.012,
            'debt_ratio': 0.88,
            'revenue_growth': 0.10,
            'profit_growth': 0.12,
            'industry': '金融银行',
            'score': 88.2,
            'technical_score': 82,
            'fundamental_score': 92,
            'sentiment_score': 85,
            'quality_score': 90,
            'risk_level': 0.3,
            'volatility': 0.22
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


def create_test_price_data(symbol: str) -> List[Dict[str, Any]]:
    """创建测试价格历史数据"""
    base_price = {
        '000001': 12.00,
        '000002': 16.00,
        '000858': 160.00,
        '002027': 6.50,
        '600036': 41.00,
        '600519': 1650.00
    }.get(symbol, 50.0)
    
    price_data = []
    current_price = base_price
    
    # 生成30天的价格数据
    for i in range(30):
        # 简单的随机波动
        change = (hash(f"{symbol}_{i}") % 200 - 100) / 10000  # -1% to +1%
        current_price *= (1 + change)
        
        price_data.append({
            'date': (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d'),
            'open': current_price * 0.999,
            'high': current_price * 1.015,
            'low': current_price * 0.985,
            'close': current_price,
            'volume': 50000000 + (hash(f"{symbol}_vol_{i}") % 100000000)
        })
    
    return price_data


def create_test_market_data() -> Dict[str, Any]:
    """创建测试市场数据"""
    return {
        'index_name': '上证指数',
        'current_value': 3250.5,
        'change_pct': 1.2,
        'price_data': [
            {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
             'close': 3200 + i * 2 + (hash(f"market_{i}") % 100 - 50),
             'volume': 400000000000 + (hash(f"market_vol_{i}") % 100000000000)}
            for i in range(30)
        ]
    }


def create_test_news_data() -> List[Dict[str, Any]]:
    """创建测试新闻数据"""
    return [
        {
            'title': '央行宣布降准0.5个百分点，释放流动性约1万亿元',
            'content': '中国人民银行决定下调金融机构存款准备金率0.5个百分点，释放长期流动性约1万亿元...',
            'source': '新华社',
            'sentiment': 0.7,
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'title': '科技股集体上涨，人工智能板块领涨',
            'content': '今日A股市场科技股表现强劲，人工智能、芯片、新能源等板块均有不错涨幅...',
            'source': '财联社',
            'sentiment': 0.8,
            'timestamp': datetime.now() - timedelta(hours=4)
        },
        {
            'title': '房地产政策边际放松，多地调整限购政策',
            'content': '近期多个城市相继调整房地产限购政策，市场预期政策将进一步优化...',
            'source': '证券时报',
            'sentiment': 0.6,
            'timestamp': datetime.now() - timedelta(hours=6)
        }
    ]


def test_ai_expert_committee():
    """测试AI专家委员会功能"""
    print("\n" + "="*50)
    print("🤖 测试AI专家委员会")
    print("="*50)
    
    try:
        # 初始化专家委员会
        committee = AIExpertCommittee()
        
        # 测试数据
        test_symbol = '002027'
        stock_data = {
            'tushare': create_test_stock_data()[3],  # 分众传媒数据
            'akshare': create_test_stock_data()[3]
        }
        news_data = create_test_news_data()
        
        # 执行专家委员会分析
        print(f"分析股票: {test_symbol}")
        result = committee.analyze_stock_committee(test_symbol, stock_data, news_data)
        
        # 输出结果
        print(f"✅ 专家委员会分析完成")
        print(f"   股票代码: {result['symbol']}")
        print(f"   委员会决策: {result['committee_decision']['recommendation']}")
        print(f"   综合评分: {result['committee_decision']['score']}")
        print(f"   置信度: {result['committee_decision']['confidence']:.3f}")
        print(f"   一致性水平: {result['committee_decision']['consensus_level']}")
        print(f"   参与专家数: {len(result['expert_analyses'])}")
        print(f"   处理时间: {result['processing_time']:.2f}秒")
        
        # 显示专家分析结果
        if result['expert_analyses']:
            print("\n📊 专家分析结果:")
            for expert_name, analysis in result['expert_analyses'].items():
                if hasattr(analysis, 'score'):
                    print(f"   {expert_name}: 评分={analysis.score:.1f}, 置信度={analysis.confidence:.3f}, 建议={analysis.recommendation}")
        
        # 显示最终推荐
        final_rec = result['final_recommendation']
        print(f"\n🎯 最终推荐:")
        print(f"   操作建议: {final_rec['action']}")
        print(f"   置信水平: {final_rec['confidence_level']:.3f}")
        print(f"   风险评估: {final_rec['risk_assessment']}")
        print(f"   建议仓位: {final_rec['suggested_allocation']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI专家委员会测试失败: {e}")
        return False


def test_pattern_recognizer():
    """测试模式识别功能"""
    print("\n" + "="*50)
    print("🔍 测试模式识别引擎")
    print("="*50)
    
    try:
        # 初始化模式识别引擎
        recognizer = PatternRecognizer()
        
        # 测试数据
        test_symbol = '000858'
        price_data = create_test_price_data(test_symbol)
        volume_data = [p['volume'] for p in price_data]
        
        # 执行模式识别
        print(f"识别股票模式: {test_symbol}")
        patterns = recognizer.recognize_patterns(test_symbol, price_data, volume_data)
        
        # 输出结果
        print(f"✅ 模式识别完成")
        print(f"   发现模式数量: {len(patterns)}")
        
        if patterns:
            print("\n📈 识别到的模式:")
            for i, pattern in enumerate(patterns, 1):
                print(f"   {i}. {pattern.pattern_type.value}")
                print(f"      强度: {pattern.strength:.1f}")
                print(f"      置信度: {pattern.confidence:.3f}")
                print(f"      持续天数: {pattern.duration_days}")
                print(f"      描述: {pattern.description}")
                print(f"      预期方向: {pattern.expected_direction}")
                print(f"      风险级别: {pattern.risk_level}")
                
                # 显示关键指标
                if pattern.key_metrics:
                    print(f"      关键指标: {json.dumps(pattern.key_metrics, indent=8, ensure_ascii=False)}")
                print()
        
        # 测试模式预测
        if patterns:
            prediction = recognizer.predict_next_patterns(test_symbol, patterns)
            print(f"🔮 模式预测:")
            print(f"   预测方向: {prediction['prediction']}")
            print(f"   预测置信度: {prediction['confidence']:.3f}")
            print(f"   基于模式: {prediction['based_on_pattern']}")
            print(f"   时间范围: {prediction['time_horizon']}天")
            print(f"   风险级别: {prediction['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模式识别测试失败: {e}")
        return False


def test_adaptive_engine():
    """测试自适应引擎功能"""
    print("\n" + "="*50)
    print("🌡️ 测试自适应选股引擎")
    print("="*50)
    
    try:
        # 初始化自适应引擎
        adaptive_engine = AdaptiveEngine()
        
        # 测试数据
        market_data = create_test_market_data()
        stock_candidates = create_test_stock_data()
        
        # 测试市场环境检测
        print("检测市场环境...")
        market_regime = adaptive_engine.detect_market_regime(market_data)
        print(f"✅ 市场环境检测完成: {market_regime.value}")
        
        # 选择最优策略
        print("选择最优策略...")
        optimal_strategy = adaptive_engine.select_optimal_strategy(market_regime)
        print(f"✅ 策略选择完成: {optimal_strategy.strategy_type.value}")
        print(f"   预期收益: {optimal_strategy.expected_performance:.2%}")
        print(f"   历史准确率: {optimal_strategy.historical_accuracy:.2%}")
        print(f"   风险承受度: {optimal_strategy.risk_tolerance:.2%}")
        print(f"   置信度要求: {optimal_strategy.confidence_threshold:.2%}")
        
        # 获取自适应推荐
        print("生成自适应推荐...")
        recommendations = adaptive_engine.get_adaptive_recommendations(market_data, stock_candidates)
        
        print(f"✅ 自适应推荐完成")
        print(f"   市场环境: {recommendations['market_regime']}")
        print(f"   选定策略: {recommendations['selected_strategy']['type']}")
        print(f"   推荐股票数: {len(recommendations['recommended_stocks'])}")
        print(f"   总候选数: {recommendations['adaptation_metrics']['total_candidates']}")
        print(f"   筛选后数: {recommendations['adaptation_metrics']['filtered_candidates']}")
        print(f"   策略准确率: {recommendations['adaptation_metrics']['strategy_accuracy']:.2%}")
        
        # 显示推荐股票
        if recommendations['recommended_stocks']:
            print("\n🎯 推荐股票 (前5名):")
            for i, stock in enumerate(recommendations['recommended_stocks'][:5], 1):
                print(f"   {i}. {stock['symbol']} - {stock.get('name', 'N/A')}")
                print(f"      自适应评分: {stock.get('adaptive_score', 0):.1f}")
                print(f"      基础评分: {stock.get('score', 0):.1f}")
                print(f"      风险级别: {stock.get('risk_level', 0):.2f}")
        
        # 显示风险评估
        risk_assessment = recommendations['risk_assessment']
        print(f"\n⚠️ 风险评估:")
        print(f"   整体风险: {risk_assessment['overall_risk']}")
        print(f"   平均风险评分: {risk_assessment['average_risk_score']}")
        print(f"   平均波动率: {risk_assessment['average_volatility']:.2%}")
        
        # 显示策略推理
        print(f"\n💡 策略推理:")
        reasoning = recommendations['strategy_reasoning']
        print(reasoning[:500] + "..." if len(reasoning) > 500 else reasoning)
        
        return True
        
    except Exception as e:
        print(f"❌ 自适应引擎测试失败: {e}")
        return False


def test_similarity_engine():
    """测试相似性引擎功能"""
    print("\n" + "="*50)
    print("🔗 测试相似股票推荐引擎")
    print("="*50)
    
    try:
        # 初始化相似性引擎
        similarity_engine = SimilarityEngine()
        
        # 测试数据
        target_symbol = '600036'  # 招商银行
        target_data = create_test_stock_data()[4]
        candidate_stocks = create_test_stock_data()
        
        # 寻找相似股票
        print(f"寻找与 {target_symbol} 相似的股票...")
        similarities = similarity_engine.find_similar_stocks(
            target_symbol, target_data, candidate_stocks, top_k=5
        )
        
        print(f"✅ 相似股票查找完成")
        print(f"   目标股票: {target_symbol} - {target_data['name']}")
        print(f"   发现相似股票: {len(similarities)}")
        
        # 显示相似股票
        if similarities:
            print("\n🎯 相似股票推荐:")
            for i, sim in enumerate(similarities, 1):
                print(f"   {i}. {sim.similar_symbol}")
                print(f"      综合相似度: {sim.overall_similarity:.3f}")
                print(f"      推荐强度: {sim.recommendation_strength:.3f}")
                print(f"      风险差异: {sim.risk_differential:.3f}")
                print(f"      预期相关性: {sim.expected_correlation:.3f}")
                
                # 显示匹配原因
                if sim.match_reasons:
                    print(f"      匹配原因: {', '.join(sim.match_reasons[:3])}")
                
                # 显示各维度评分
                if sim.dimension_scores:
                    print("      维度评分:")
                    sorted_dims = sorted(
                        sim.dimension_scores.items(),
                        key=lambda x: x[1].score,
                        reverse=True
                    )
                    for dim, score in sorted_dims[:3]:
                        print(f"        {dim.value}: {score.score:.3f} (权重: {score.weight:.2f})")
                print()
        
        # 测试聚类分析
        print("构建相似性聚类...")
        cluster_info = similarity_engine.build_similarity_clusters(candidate_stocks, n_clusters=3)
        
        if 'error' not in cluster_info:
            print(f"✅ 聚类分析完成")
            print(f"   总股票数: {cluster_info['total_stocks']}")
            print(f"   集群数量: {cluster_info['n_clusters']}")
            print(f"   集群分布: {cluster_info['cluster_sizes']}")
            
            # 基于聚类推荐
            cluster_recommendations = similarity_engine.recommend_from_cluster(
                target_symbol, cluster_info, top_k=3
            )
            if cluster_recommendations:
                print(f"   聚类推荐: {cluster_recommendations}")
        
        # 获取相似性洞察
        if similarities:
            print("分析相似性洞察...")
            insights = similarity_engine.get_similarity_insights(similarities)
            
            print(f"✅ 相似性洞察分析")
            print(f"   相似股票总数: {insights['total_similar_stocks']}")
            print(f"   平均相似度: {insights['avg_similarity']:.3f}")
            print(f"   最高相似度: {insights['max_similarity']:.3f}")
            print(f"   高相似度股票数: {insights['high_similarity_count']}")
            print(f"   中等相似度股票数: {insights['medium_similarity_count']}")
            
            # 显示维度分析
            if insights['dimension_analysis']:
                print("   维度贡献分析:")
                for dim, analysis in insights['dimension_analysis'].items():
                    print(f"     {dim}: 平均{analysis['avg_score']:.3f}, 贡献{analysis['contribution']:.3f}")
            
            # 显示常见匹配原因
            if insights['top_match_reasons']:
                print("   主要匹配原因:")
                for reason, count in insights['top_match_reasons'][:3]:
                    print(f"     {reason}: {count}次")
        
        return True
        
    except Exception as e:
        print(f"❌ 相似性引擎测试失败: {e}")
        return False


def test_integrated_selection():
    """测试完整集成选股流程"""
    print("\n" + "="*50)
    print("🚀 测试完整AI增强选股流程")
    print("="*50)
    
    try:
        # 初始化所有组件
        print("初始化AI选股组件...")
        expert_committee = AIExpertCommittee()
        pattern_recognizer = PatternRecognizer()
        adaptive_engine = AdaptiveEngine()
        similarity_engine = SimilarityEngine()
        stock_selector = StockSelector()
        
        # 测试数据
        test_stocks = create_test_stock_data()
        market_data = create_test_market_data()
        news_data = create_test_news_data()
        
        print("✅ 组件初始化完成")
        
        # 第1步：基础选股筛选
        print("\n第1步：执行基础选股筛选...")
        selection_criteria = SelectionCriteria(
            min_score=70.0,
            max_risk_level=0.6,
            filters=[
                NumericFilter("market_cap", "市值", FilterOperator.GREATER, 10000000000),  # 大于100亿
                NumericFilter("pe_ratio", "PE比率", FilterOperator.LESS, 30),
                NumericFilter("roe", "ROE", FilterOperator.GREATER, 0.10)
            ],
            max_results=10
        )
        
        base_result = stock_selector.select_stocks(selection_criteria, test_stocks)
        print(f"✅ 基础筛选完成，通过股票数: {len(base_result.selected_stocks)}")
        
        # 第2步：AI专家委员会分析
        print("\n第2步：AI专家委员会深度分析...")
        expert_results = {}
        
        for stock_data in base_result.selected_stocks[:3]:  # 分析前3只
            symbol = stock_data['symbol']
            print(f"   分析 {symbol}...")
            
            # 构造多源数据格式
            multi_source_data = {
                'primary': stock_data,
                'secondary': stock_data  # 简化处理，实际应该是不同数据源
            }
            
            expert_result = expert_committee.analyze_stock_committee(
                symbol, multi_source_data, news_data
            )
            expert_results[symbol] = expert_result
        
        print(f"✅ AI专家分析完成，分析股票数: {len(expert_results)}")
        
        # 第3步：模式识别分析
        print("\n第3步：执行模式识别分析...")
        pattern_results = {}
        
        for symbol in expert_results.keys():
            price_data = create_test_price_data(symbol)
            volume_data = [p['volume'] for p in price_data]
            
            patterns = pattern_recognizer.recognize_patterns(symbol, price_data, volume_data)
            if patterns:
                pattern_results[symbol] = patterns
                print(f"   {symbol}: 发现 {len(patterns)} 个模式")
        
        print(f"✅ 模式识别完成，发现模式的股票数: {len(pattern_results)}")
        
        # 第4步：自适应策略优化
        print("\n第4步：应用自适应策略优化...")
        adaptive_recommendations = adaptive_engine.get_adaptive_recommendations(
            market_data, list(test_stocks)
        )
        print(f"✅ 自适应优化完成")
        print(f"   市场环境: {adaptive_recommendations['market_regime']}")
        print(f"   推荐策略: {adaptive_recommendations['selected_strategy']['type']}")
        
        # 第5步：相似股票推荐
        print("\n第5步：生成相似股票推荐...")
        similarity_results = {}
        
        # 为每只通过专家分析的股票找相似股票
        for symbol, expert_result in expert_results.items():
            if expert_result['committee_decision']['score'] > 80:  # 高评分股票
                target_data = next(s for s in test_stocks if s['symbol'] == symbol)
                similarities = similarity_engine.find_similar_stocks(
                    symbol, target_data, test_stocks, top_k=3
                )
                if similarities:
                    similarity_results[symbol] = similarities
                    print(f"   {symbol}: 找到 {len(similarities)} 只相似股票")
        
        print(f"✅ 相似股票推荐完成，推荐组数: {len(similarity_results)}")
        
        # 第6步：生成综合投资建议
        print("\n第6步：生成综合投资建议...")
        
        final_recommendations = []
        
        for symbol, expert_result in expert_results.items():
            recommendation = {
                'symbol': symbol,
                'name': next(s['name'] for s in test_stocks if s['symbol'] == symbol),
                'expert_score': expert_result['committee_decision']['score'],
                'expert_recommendation': expert_result['committee_decision']['recommendation'],
                'expert_confidence': expert_result['committee_decision']['confidence'],
                'patterns': len(pattern_results.get(symbol, [])),
                'similar_stocks': len(similarity_results.get(symbol, [])),
                'final_rating': 'A'  # 简化评级
            }
            
            # 计算综合评分
            base_score = expert_result['committee_decision']['score']
            pattern_bonus = len(pattern_results.get(symbol, [])) * 2
            similarity_bonus = len(similarity_results.get(symbol, [])) * 1
            
            comprehensive_score = base_score + pattern_bonus + similarity_bonus
            recommendation['comprehensive_score'] = min(100, comprehensive_score)
            
            final_recommendations.append(recommendation)
        
        # 按综合评分排序
        final_recommendations.sort(key=lambda x: x['comprehensive_score'], reverse=True)
        
        print(f"✅ 综合投资建议生成完成")
        print(f"\n🏆 最终推荐结果 (AI增强选股):")
        print("-" * 80)
        print(f"{'排名':<4} {'股票代码':<8} {'股票名称':<12} {'综合评分':<8} {'专家建议':<12} {'模式数':<6} {'相似股':<6}")
        print("-" * 80)
        
        for i, rec in enumerate(final_recommendations, 1):
            print(f"{i:<4} {rec['symbol']:<8} {rec['name']:<12} "
                  f"{rec['comprehensive_score']:<8.1f} {rec['expert_recommendation']:<12} "
                  f"{rec['patterns']:<6} {rec['similar_stocks']:<6}")
        
        # 显示详细分析摘要
        print(f"\n📊 AI增强选股分析摘要:")
        print(f"   基础筛选通过: {len(base_result.selected_stocks)} 只")
        print(f"   AI专家深度分析: {len(expert_results)} 只")
        print(f"   模式识别覆盖: {len(pattern_results)} 只")
        print(f"   相似推荐组数: {len(similarity_results)} 组")
        print(f"   最终推荐股票: {len(final_recommendations)} 只")
        print(f"   平均综合评分: {sum(r['comprehensive_score'] for r in final_recommendations)/len(final_recommendations):.1f}")
        
        # 显示策略建议
        strategy_info = adaptive_recommendations['selected_strategy']
        print(f"\n💡 策略建议:")
        print(f"   当前市场环境: {adaptive_recommendations['market_regime']}")
        print(f"   建议策略类型: {strategy_info['type']}")
        print(f"   策略置信度: {strategy_info['confidence']:.2%}")
        print(f"   风险承受度: {strategy_info['risk_tolerance']:.2%}")
        print(f"   预期收益率: {strategy_info['expected_performance']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🎯 开始阶段2 AI增强选股系统集成测试")
    print("=" * 60)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("AI专家委员会", test_ai_expert_committee),
        ("模式识别引擎", test_pattern_recognizer),
        ("自适应选股引擎", test_adaptive_engine),
        ("相似股票推荐", test_similarity_engine),
        ("完整集成流程", test_integrated_selection)
    ]
    
    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        result = test_func()
        test_results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    # 输出测试总结
    print("\n" + "="*60)
    print("🏁 测试总结")
    print("="*60)
    
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    print(f"总测试项目: {total_count}")
    print(f"通过测试: {passed_count}")
    print(f"失败测试: {total_count - passed_count}")
    print(f"通过率: {passed_count/total_count:.1%}")
    
    print("\n详细结果:")
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name:<20} {status}")
    
    if passed_count == total_count:
        print(f"\n🎉 所有测试通过！阶段2 AI增强选股系统集成测试成功！")
        return True
    else:
        print(f"\n⚠️ 部分测试失败，请检查相关模块。")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)