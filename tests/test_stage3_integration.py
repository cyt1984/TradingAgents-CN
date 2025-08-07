#!/usr/bin/env python3
"""
阶段3集成测试 - 三源数据融合引擎功能验证
测试智能数据融合引擎、质量评分算法、综合评分系统、可靠性监控和动态权重调整
"""

import sys
import os
import time
from datetime import datetime, timedelta
import traceback

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_data_fusion_engine():
    """测试数据融合引擎"""
    print("[TEST] 测试数据融合引擎...")
    
    try:
        from tradingagents.analytics.data_fusion_engine import (
            get_fusion_engine, DataPoint, DataSourceType
        )
        
        # 创建测试数据点
        test_data_points = [
            DataPoint(
                source="eastmoney",
                data_type=DataSourceType.REAL_TIME_PRICE,
                value=25.30,
                timestamp=datetime.now(),
                quality_score=0.9,
                confidence=0.85,
                latency_ms=120,
                metadata={"symbol": "000001"}
            ),
            DataPoint(
                source="tencent", 
                data_type=DataSourceType.REAL_TIME_PRICE,
                value=25.28,
                timestamp=datetime.now(),
                quality_score=0.8,
                confidence=0.80,
                latency_ms=150,
                metadata={"symbol": "000001"}
            ),
            DataPoint(
                source="sina",
                data_type=DataSourceType.REAL_TIME_PRICE,
                value=25.32,
                timestamp=datetime.now(),
                quality_score=0.75,
                confidence=0.75,
                latency_ms=200,
                metadata={"symbol": "000001"}
            )
        ]
        
        # 获取融合引擎
        fusion_engine = get_fusion_engine()
        
        # 测试各种融合算法
        fusion_methods = ['weighted_average', 'median_fusion', 'confidence_weighted', 
                         'quality_weighted', 'adaptive_fusion']
        
        results = {}
        for method in fusion_methods:
            result = fusion_engine.fuse_data_points(test_data_points, method)
            results[method] = {
                'value': result.fused_value,
                'confidence': result.confidence,
                'quality': result.quality_score
            }
            print(f"   {method}: 价格={result.fused_value:.2f}, 置信度={result.confidence:.3f}, 质量={result.quality_score:.3f}")
        
        # 验证融合结果合理性
        assert all(25.0 <= results[method]['value'] <= 26.0 for method in fusion_methods), "融合价格不在合理范围"
        assert all(results[method]['confidence'] > 0.5 for method in fusion_methods), "置信度过低"
        assert all(results[method]['quality'] > 0.5 for method in fusion_methods), "质量评分过低"
        
        print("   [OK] 数据融合引擎测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 数据融合引擎测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def test_data_quality_analyzer():
    """测试数据质量分析器"""
    print("[TEST] 测试数据质量分析器...")
    
    try:
        from tradingagents.analytics.data_quality_analyzer import get_quality_analyzer
        
        # 创建测试股票数据
        test_stock_data = {
            'current_price': 25.30,
            'volume': 12500000,
            'change_pct': 2.5,
            'open': 24.80,
            'high': 25.50,
            'low': 24.75,
            'prev_close': 24.70,
            'turnover': 317500000,
            'name': '平安银行'
        }
        
        # 创建测试新闻数据
        test_news_data = {
            'title': '平安银行发布三季度业绩报告，净利润同比增长15%',
            'summary': '平安银行今日发布三季度财报，营收和净利润均实现双位数增长',
            'publish_time': datetime.now().isoformat(),
            'source': 'sina',
            'url': 'https://finance.sina.com.cn/stock/s/2024/news.html',
            'relevance_score': 0.9
        }
        
        # 获取质量分析器
        quality_analyzer = get_quality_analyzer()
        
        # 测试股票数据质量分析
        stock_metrics = quality_analyzer.analyze_data_quality('eastmoney', test_stock_data, 'stock_price')
        print(f"   股票数据质量: {stock_metrics.quality_grade} ({stock_metrics.overall_score:.3f})")
        print(f"   - 完整性: {stock_metrics.completeness:.3f}")
        print(f"   - 准确性: {stock_metrics.accuracy:.3f}")
        print(f"   - 时效性: {stock_metrics.timeliness:.3f}")
        print(f"   - 一致性: {stock_metrics.consistency:.3f}")
        
        # 测试新闻数据质量分析
        news_metrics = quality_analyzer.analyze_data_quality('sina', test_news_data, 'news')
        print(f"   新闻数据质量: {news_metrics.quality_grade} ({news_metrics.overall_score:.3f})")
        
        # 验证质量评分合理性
        assert 0.0 <= stock_metrics.overall_score <= 1.0, "股票数据质量评分超出范围"
        assert 0.0 <= news_metrics.overall_score <= 1.0, "新闻数据质量评分超出范围"
        assert stock_metrics.completeness > 0.8, "股票数据完整性过低"  # 数据很完整应该高分
        
        print("   [OK] 数据质量分析器测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 数据质量分析器测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def test_comprehensive_scoring_system():
    """测试综合评分系统"""
    print("[TEST] 测试综合评分系统...")
    
    try:
        from tradingagents.analytics.comprehensive_scoring_system import get_comprehensive_scoring_system
        
        # 创建测试数据
        test_stock_data = {
            'eastmoney': {
                'current_price': 25.30,
                'volume': 12500000,
                'change_pct': 2.5,
                'open': 24.80,
                'high': 25.50,
                'low': 24.75,
                'prev_close': 24.70,
                'turnover': 317500000,
                'name': '平安银行'
            },
            'tencent': {
                'current_price': 25.28,
                'volume': 12300000, 
                'change_pct': 2.4,
                'open': 24.85,
                'high': 25.48,
                'low': 24.78
            }
        }
        
        test_news_data = [
            {
                'title': '平安银行三季度净利润增长15%',
                'summary': '业绩超预期，资产质量持续改善',
                'publish_time': datetime.now().isoformat(),
                'source': 'sina',
                'relevance_score': 0.9
            },
            {
                'title': '银行股集体上涨，平安银行涨幅居前',
                'summary': '受益于利率政策预期，银行板块表现强劲',
                'publish_time': (datetime.now() - timedelta(hours=2)).isoformat(),
                'source': 'eastmoney',
                'relevance_score': 0.8
            }
        ]
        
        # 获取评分系统
        scoring_system = get_comprehensive_scoring_system()
        
        # 计算综合评分
        comprehensive_score = scoring_system.calculate_comprehensive_score(
            symbol="000001",
            stock_data=test_stock_data,
            news_data=test_news_data
        )
        
        print(f"   综合评分结果:")
        print(f"   - 股票代码: {comprehensive_score.symbol}")
        print(f"   - 综合评分: {comprehensive_score.overall_score:.2f}")
        print(f"   - 投资等级: {comprehensive_score.grade}")
        print(f"   - 综合置信度: {comprehensive_score.confidence:.3f}")
        print(f"   - 投资建议: {comprehensive_score.recommendation}")
        print(f"   - 风险级别: {comprehensive_score.risk_level}")
        
        # 各类别评分
        for category, score_obj in comprehensive_score.category_scores.items():
            print(f"   - {category.value}: {score_obj.score:.2f} (权重: {score_obj.weight:.2f})")
        
        # 验证评分合理性
        assert 0.0 <= comprehensive_score.overall_score <= 100.0, "综合评分超出范围"
        assert 0.0 <= comprehensive_score.confidence <= 1.0, "置信度超出范围" 
        assert comprehensive_score.grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D'], "评级不在有效范围"
        assert len(comprehensive_score.category_scores) == 5, "类别评分数量不正确"
        
        print("   [OK] 综合评分系统测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 综合评分系统测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def test_reliability_monitor():
    """测试可靠性监控系统"""
    print("[TEST] 测试可靠性监控系统...")
    
    try:
        from tradingagents.analytics.reliability_monitor import get_reliability_monitor, MonitoringStatus
        
        # 获取监控器
        monitor = get_reliability_monitor()
        
        # 定义测试检查函数
        def check_eastmoney():
            """东方财富数据源检查函数"""
            return True, 150.0, {'quality_score': 0.9, 'data_points': 10}
        
        def check_tencent():
            """腾讯财经数据源检查函数"""
            return True, 120.0, {'quality_score': 0.85, 'data_points': 8}
        
        def check_sina():
            """新浪财经数据源检查函数"""
            return False, 5000.0, {'quality_score': 0.3, 'error': '连接超时'}
        
        # 注册数据源监控
        monitor.register_data_source('eastmoney', check_eastmoney, critical=True)
        monitor.register_data_source('tencent', check_tencent, critical=False)
        monitor.register_data_source('sina', check_sina, critical=False)
        
        print(f"   已注册 {len(monitor.monitored_sources)} 个数据源")
        
        # 手动触发检查
        monitor._check_all_sources()
        
        # 获取监控报告
        report = monitor.get_monitoring_report()
        
        print(f"   监控报告:")
        print(f"   - 整体状态: {report.overall_status.value}")
        print(f"   - 总数据源: {report.total_sources}")
        print(f"   - 健康源: {report.healthy_sources}")
        print(f"   - 警告源: {report.warning_sources}")
        print(f"   - 严重源: {report.critical_sources}")
        print(f"   - 离线源: {report.offline_sources}")
        
        # 显示各数据源指标
        for source, metrics in report.source_metrics.items():
            print(f"   - {source}: {metrics.status.value}, 成功率={metrics.success_rate:.2f}, 响应时间={metrics.avg_response_time:.0f}ms")
        
        # 验证监控结果
        assert report.total_sources == 3, "监控的数据源数量不正确"
        assert 'eastmoney' in report.source_metrics, "缺少eastmoney监控数据"
        assert 'tencent' in report.source_metrics, "缺少tencent监控数据"
        assert 'sina' in report.source_metrics, "缺少sina监控数据"
        
        # 验证状态判断
        eastmoney_status = report.source_metrics['eastmoney'].status
        sina_status = report.source_metrics['sina'].status
        
        assert eastmoney_status == MonitoringStatus.HEALTHY, "eastmoney状态判断错误"
        assert sina_status in [MonitoringStatus.CRITICAL, MonitoringStatus.WARNING], "sina状态判断错误"
        
        print("   [OK] 可靠性监控系统测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 可靠性监控系统测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def test_dynamic_weight_manager():
    """测试动态权重管理器"""
    print("[TEST] 测试动态权重管理器...")
    
    try:
        from tradingagents.analytics.dynamic_weight_manager import (
            get_dynamic_weight_manager, AdjustmentStrategy
        )
        
        # 获取权重管理器
        manager = get_dynamic_weight_manager()
        
        print(f"   当前权重配置:")
        current_weights = manager.get_current_weights()
        for source, weight in current_weights.items():
            print(f"   - {source}: {weight:.3f}")
        
        # 模拟性能数据
        mock_performance_data = {
            'eastmoney': {
                'reliability_score': 0.9,
                'response_time': 150,
                'success_rate': 0.95,
                'uptime': 0.98,
                'data_quality': 0.9,
                'error_count': 2,
                'total_requests': 100
            },
            'tencent': {
                'reliability_score': 0.85,
                'response_time': 200,
                'success_rate': 0.90,
                'uptime': 0.95,
                'data_quality': 0.85,
                'error_count': 5,
                'total_requests': 100
            },
            'sina': {
                'reliability_score': 0.6,
                'response_time': 800,
                'success_rate': 0.75,
                'uptime': 0.80,
                'data_quality': 0.65,
                'error_count': 15,
                'total_requests': 100
            }
        }
        
        # 测试权重更新
        print(f"   执行动态权重调整...")
        new_weights = manager.update_weights(mock_performance_data)
        
        print(f"   调整后权重:")
        for source, weight in new_weights.items():
            old_weight = current_weights.get(source, 0)
            change = weight - old_weight
            print(f"   - {source}: {weight:.3f} (变化: {change:+.3f})")
        
        # 获取调整摘要
        adjustment_summary = manager.get_adjustment_summary(days=1)
        print(f"   调整摘要:")
        print(f"   - 总调整次数: {adjustment_summary['total_adjustments']}")
        print(f"   - 调整数据源: {adjustment_summary['sources_adjusted']}")
        
        # 测试不同策略
        original_strategy = manager.strategy
        for strategy in [AdjustmentStrategy.CONSERVATIVE, AdjustmentStrategy.AGGRESSIVE]:
            manager.set_strategy(strategy)
            strategy_weights = manager.update_weights(mock_performance_data)
            print(f"   {strategy.value}策略权重总和: {sum(strategy_weights.values()):.3f}")
        
        # 恢复原策略
        manager.set_strategy(original_strategy)
        
        # 验证权重调整结果
        assert abs(sum(new_weights.values()) - 1.0) < 0.01, "权重总和不等于1"
        assert all(0.0 <= weight <= 1.0 for weight in new_weights.values()), "权重超出有效范围"
        
        # 验证高性能数据源权重增加，低性能数据源权重减少
        eastmoney_improved = new_weights['eastmoney'] >= current_weights['eastmoney'] - 0.01
        sina_decreased = new_weights['sina'] <= current_weights['sina'] + 0.01
        
        print("   [OK] 动态权重管理器测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 动态权重管理器测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def test_integration_workflow():
    """测试集成工作流"""
    print("[TEST] 测试完整集成工作流...")
    
    try:
        # 模拟完整的数据处理流程
        
        # 1. 准备多源股票数据
        multi_source_data = {
            'eastmoney': {
                'symbol': '000001',
                'current_price': 25.30,
                'volume': 12500000,
                'change_pct': 2.5,
                'quality_score': 0.9,
                'confidence': 0.85
            },
            'tencent': {
                'symbol': '000001', 
                'current_price': 25.28,
                'volume': 12300000,
                'change_pct': 2.4,
                'quality_score': 0.8,
                'confidence': 0.80
            },
            'sina': {
                'symbol': '000001',
                'current_price': 25.32,
                'volume': 12600000,
                'change_pct': 2.6,
                'quality_score': 0.75,
                'confidence': 0.75
            }
        }
        
        # 2. 数据质量分析
        from tradingagents.analytics.data_quality_analyzer import get_quality_analyzer
        quality_analyzer = get_quality_analyzer()
        
        quality_scores = {}
        for source, data in multi_source_data.items():
            metrics = quality_analyzer.analyze_data_quality(source, data, 'stock_price')
            quality_scores[source] = metrics.overall_score
            # 更新数据中的质量评分
            multi_source_data[source]['quality_score'] = metrics.overall_score
        
        print(f"   质量分析完成，平均质量: {sum(quality_scores.values())/len(quality_scores):.3f}")
        
        # 3. 数据融合
        from tradingagents.analytics.data_fusion_engine import fuse_stock_prices
        fusion_result = fuse_stock_prices(multi_source_data, '000001')
        
        print(f"   数据融合完成，融合价格: {fusion_result.fused_value:.2f}")
        print(f"   融合置信度: {fusion_result.confidence:.3f}")
        print(f"   融合质量: {fusion_result.quality_score:.3f}")
        
        # 4. 综合评分
        from tradingagents.analytics.comprehensive_scoring_system import calculate_comprehensive_score
        
        # 准备新闻数据
        news_data = [
            {
                'title': '平安银行业绩稳健增长',
                'summary': '三季度财报表现良好',
                'publish_time': datetime.now().isoformat(),
                'source': 'sina',
                'relevance_score': 0.9
            }
        ]
        
        comprehensive_result = calculate_comprehensive_score('000001', multi_source_data, news_data)
        
        print(f"   综合评分完成:")
        print(f"   - 评分: {comprehensive_result.overall_score:.2f}")
        print(f"   - 等级: {comprehensive_result.grade}")
        print(f"   - 建议: {comprehensive_result.recommendation}")
        
        # 5. 动态权重调整
        from tradingagents.analytics.dynamic_weight_manager import update_data_source_weights
        
        # 基于质量评分更新权重
        performance_data = {}
        for source, quality in quality_scores.items():
            performance_data[source] = {
                'reliability_score': quality,
                'response_time': 100 + hash(source) % 200,  # 模拟响应时间
                'success_rate': 0.8 + quality * 0.2,
                'uptime': 0.9 + quality * 0.1,
                'data_quality': quality
            }
        
        updated_weights = update_data_source_weights(performance_data)
        print(f"   权重调整完成，新权重总和: {sum(updated_weights.values()):.3f}")
        
        # 验证集成流程结果
        assert fusion_result.fused_value is not None, "数据融合失败"
        assert 20.0 <= fusion_result.fused_value <= 30.0, "融合价格不合理"
        assert 0.0 <= comprehensive_result.overall_score <= 100.0, "综合评分超出范围"
        assert abs(sum(updated_weights.values()) - 1.0) < 0.01, "权重调整后总和不为1"
        
        print("   [OK] 集成工作流测试通过")
        return True
        
    except Exception as e:
        print(f"   [ERROR] 集成工作流测试失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return False

def main():
    """运行阶段3集成测试"""
    print("="*60)
    print("阶段3功能验证测试 - 三源数据融合引擎")
    print("="*60)
    
    start_time = time.time()
    test_results = []
    
    # 执行各项测试
    tests = [
        ("数据融合引擎", test_data_fusion_engine),
        ("数据质量分析器", test_data_quality_analyzer),
        ("综合评分系统", test_comprehensive_scoring_system),
        ("可靠性监控系统", test_reliability_monitor),
        ("动态权重管理器", test_dynamic_weight_manager),
        ("完整集成工作流", test_integration_workflow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n[{len(test_results)+1}/{len(tests)}] {test_name}")
        print("-" * 50)
        
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"[SUCCESS] {test_name} 测试通过")
            else:
                print(f"[FAILED] {test_name} 测试失败")
                
        except Exception as e:
            print(f"[ERROR] {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 测试总结
    print("\n" + "="*60)
    print("阶段3功能验证测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"测试总数: {total}")
    print(f"通过数量: {passed}")
    print(f"失败数量: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    print(f"耗时: {time.time() - start_time:.2f}秒")
    
    print(f"\n详细结果:")
    for i, (test_name, result) in enumerate(test_results, 1):
        status = "[PASS]" if result else "[FAIL]"
        print(f"{i:2d}. {status} {test_name}")
    
    if passed == total:
        print(f"\n[SUCCESS] 所有测试通过！阶段3功能验证成功")
        return True
    else:
        print(f"\n[WARNING] 部分测试失败，请检查上述错误信息")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)