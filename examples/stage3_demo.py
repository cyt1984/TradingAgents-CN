#!/usr/bin/env python3
"""
阶段3功能演示脚本
展示智能数据融合引擎、综合评分系统等核心功能的使用方法
"""

import sys
import os
from datetime import datetime
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def demo_data_fusion():
    """演示数据融合引擎功能"""
    print("\n" + "="*60)
    print("[ENGINE] 数据融合引擎演示")
    print("="*60)
    
    try:
        from tradingagents.analytics.data_fusion_engine import (
            get_fusion_engine, DataPoint, DataSourceType
        )
        
        # 模拟多源股票价格数据
        data_points = [
            DataPoint(
                source="eastmoney",
                data_type=DataSourceType.REAL_TIME_PRICE,
                value=25.30,
                timestamp=datetime.now(),
                quality_score=0.9,
                confidence=0.85,
                latency_ms=120,
                metadata={"source_type": "api"}
            ),
            DataPoint(
                source="tencent",
                data_type=DataSourceType.REAL_TIME_PRICE, 
                value=25.28,
                timestamp=datetime.now(),
                quality_score=0.85,
                confidence=0.80,
                latency_ms=150,
                metadata={"source_type": "api"}
            ),
            DataPoint(
                source="sina",
                data_type=DataSourceType.REAL_TIME_PRICE,
                value=25.32,
                timestamp=datetime.now(),
                quality_score=0.75,
                confidence=0.75,
                latency_ms=200,
                metadata={"source_type": "web"}
            )
        ]
        
        fusion_engine = get_fusion_engine()
        
        print("[CHART] 原始数据:")
        for dp in data_points:
            print(f"   {dp.source}: {dp.value:.2f}元 (质量:{dp.quality_score:.2f}, 置信度:{dp.confidence:.2f})")
        
        # 测试不同融合算法
        algorithms = ['weighted_average', 'median_fusion', 'adaptive_fusion']
        
        print("\n[RESULT] 融合结果:")
        for alg in algorithms:
            result = fusion_engine.fuse_data_points(data_points, alg)
            print(f"   {alg}: {result.fused_value:.2f}元 (置信度:{result.confidence:.3f}, 质量:{result.quality_score:.3f})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据融合演示失败: {e}")
        return False

def demo_quality_analysis():
    """演示数据质量分析功能"""
    print("\n" + "="*60)
    print("[QUALITY] 数据质量分析演示")
    print("="*60)
    
    try:
        from tradingagents.analytics.data_quality_analyzer import get_quality_analyzer
        
        # 测试股票数据
        stock_data = {
            'symbol': '000001',
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
        
        analyzer = get_quality_analyzer()
        metrics = analyzer.analyze_data_quality('eastmoney', stock_data, 'stock_price')
        
        print("[DATA] 股票数据质量分析:")
        print(f"   数据源: eastmoney")
        print(f"   综合评分: {metrics.overall_score:.3f}")
        print(f"   质量等级: {metrics.quality_grade}")
        print(f"   完整性: {metrics.completeness:.3f}")
        print(f"   准确性: {metrics.accuracy:.3f}")
        print(f"   时效性: {metrics.timeliness:.3f}")
        print(f"   一致性: {metrics.consistency:.3f}")
        print(f"   有效性: {metrics.validity:.3f}")
        print(f"   可靠性: {metrics.reliability:.3f}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据质量分析演示失败: {e}")
        return False

def demo_comprehensive_scoring():
    """演示综合评分系统功能"""
    print("\n" + "="*60)
    print("[CHART] 综合评分系统演示")
    print("="*60)
    
    try:
        from tradingagents.analytics.comprehensive_scoring_system import get_comprehensive_scoring_system
        
        # 模拟多源股票数据
        stock_data = {
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
        
        # 模拟新闻数据
        news_data = [
            {
                'title': '平安银行三季度业绩超预期，净利润同比增长15%',
                'summary': '平安银行发布财报，营收和净利润均实现双位数增长',
                'publish_time': datetime.now().isoformat(),
                'source': 'sina',
                'relevance_score': 0.9
            },
            {
                'title': '银行股集体上涨，平安银行涨幅居前',
                'summary': '受益于利率政策预期，银行板块表现强劲',
                'publish_time': datetime.now().isoformat(),
                'source': 'eastmoney',
                'relevance_score': 0.8
            }
        ]
        
        scoring_system = get_comprehensive_scoring_system()
        result = scoring_system.calculate_comprehensive_score('000001', stock_data, news_data)
        
        print("[RESULT] 综合评分结果:")
        print(f"   股票代码: {result.symbol}")
        print(f"   综合评分: {result.overall_score:.2f}/100")
        print(f"   投资等级: {result.grade}")
        print(f"   投资建议: {result.recommendation}")
        print(f"   风险级别: {result.risk_level}")
        print(f"   综合置信度: {result.confidence:.3f}")
        
        print("\n[INFO] 各类别评分:")
        for category, score_obj in result.category_scores.items():
            print(f"   {category.value}: {score_obj.score:.1f} (权重:{score_obj.weight:.1%})")
        
        print("\n[KEY] 关键因素:")
        for factor in result.key_factors[:3]:
            print(f"   • {factor}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 综合评分演示失败: {e}")
        return False

def demo_reliability_monitoring():
    """演示可靠性监控功能"""
    print("\n" + "="*60)
    print("[MONITOR] 可靠性监控系统演示")
    print("="*60)
    
    try:
        from tradingagents.analytics.reliability_monitor import get_reliability_monitor
        
        monitor = get_reliability_monitor()
        
        # 定义模拟检查函数
        def check_good_source():
            return True, 150.0, {'quality_score': 0.9}
        
        def check_slow_source():
            return True, 3000.0, {'quality_score': 0.7}
        
        def check_bad_source():
            return False, 8000.0, {'quality_score': 0.3}
        
        # 注册数据源
        monitor.register_data_source('good_source', check_good_source, critical=True)
        monitor.register_data_source('slow_source', check_slow_source, critical=False)
        monitor.register_data_source('bad_source', check_bad_source, critical=False)
        
        print("[INFO] 注册数据源: 3个")
        
        # 执行健康检查
        monitor._check_all_sources()
        
        # 获取监控报告
        report = monitor.get_monitoring_report()
        
        print(f"\n[CHART] 监控报告:")
        print(f"   整体状态: {report.overall_status.value}")
        print(f"   健康源: {report.healthy_sources}")
        print(f"   警告源: {report.warning_sources}")  
        print(f"   严重源: {report.critical_sources}")
        print(f"   离线源: {report.offline_sources}")
        
        print(f"\n[DATA] 数据源详情:")
        for source, metrics in report.source_metrics.items():
            print(f"   {source}: {metrics.status.value} (响应:{metrics.response_time_ms:.0f}ms)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 可靠性监控演示失败: {e}")
        return False

def demo_dynamic_weights():
    """演示动态权重调整功能"""
    print("\n" + "="*60)
    print("[WEIGHTS] 动态权重管理演示")
    print("="*60)
    
    try:
        from tradingagents.analytics.dynamic_weight_manager import get_dynamic_weight_manager
        
        manager = get_dynamic_weight_manager()
        
        print("[CHART] 初始权重配置:")
        initial_weights = manager.get_current_weights()
        for source, weight in initial_weights.items():
            print(f"   {source}: {weight:.3f}")
        
        # 模拟性能数据
        performance_data = {
            'eastmoney': {
                'reliability_score': 0.9,
                'response_time': 150,
                'success_rate': 0.95,
                'uptime': 0.98,
                'data_quality': 0.9
            },
            'tencent': {
                'reliability_score': 0.85,
                'response_time': 200,
                'success_rate': 0.90,
                'uptime': 0.95,
                'data_quality': 0.85
            },
            'sina': {
                'reliability_score': 0.6,
                'response_time': 800,
                'success_rate': 0.75,
                'uptime': 0.80,
                'data_quality': 0.65
            }
        }
        
        print(f"\n[PROCESS] 执行权重调整...")
        new_weights = manager.update_weights(performance_data)
        
        print(f"\n[DATA] 调整后权重:")
        for source in initial_weights.keys():
            old_w = initial_weights[source]
            new_w = new_weights.get(source, 0)
            change = ((new_w - old_w) / old_w * 100) if old_w > 0 else 0
            print(f"   {source}: {new_w:.3f} ({change:+.1f}%)")
        
        # 获取调整摘要
        summary = manager.get_adjustment_summary(days=1)
        print(f"\n[INFO] 调整摘要:")
        print(f"   调整次数: {summary['total_adjustments']}")
        print(f"   涉及数据源: {summary['sources_adjusted']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 动态权重管理演示失败: {e}")
        return False

def main():
    """主演示函数"""
    print("[DEMO] TradingAgents-CN 阶段3功能演示")
    print("智能多源数据融合系统")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demos = [
        ("数据融合引擎", demo_data_fusion),
        ("数据质量分析", demo_quality_analysis), 
        ("综合评分系统", demo_comprehensive_scoring),
        ("可靠性监控", demo_reliability_monitoring),
        ("动态权重管理", demo_dynamic_weights)
    ]
    
    results = []
    start_time = time.time()
    
    for name, demo_func in demos:
        try:
            result = demo_func()
            results.append((name, result))
            if result:
                print(f"[OK] {name} 演示成功")
            else:
                print(f"[FAIL] {name} 演示失败")
        except Exception as e:
            print(f"[ERROR] {name} 演示异常: {e}")
            results.append((name, False))
    
    # 总结
    elapsed = time.time() - start_time
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print("\n" + "="*60)
    print("[DATA] 演示总结")
    print("="*60)
    print(f"总演示项目: {total_count}")
    print(f"成功项目: {success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    print(f"运行时间: {elapsed:.2f}秒")
    
    print(f"\n详细结果:")
    for i, (name, result) in enumerate(results, 1):
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"{i:2d}. {status} {name}")
    
    if success_count == total_count:
        print(f"\n[SUCCESS] 所有功能演示成功！阶段3系统运行正常！")
    else:
        print(f"\n[WARNING] 部分功能演示失败，请检查系统配置")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n[STOP] 用户中断演示")
        exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 演示程序异常: {e}")
        exit(1)