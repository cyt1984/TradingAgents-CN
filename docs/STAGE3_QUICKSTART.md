# 🚀 阶段3快速入门指南

## 📋 概述

阶段3为TradingAgents-CN系统提供了完整的**智能多源数据融合**能力，包含5个核心组件：

- 🔧 **数据融合引擎** - 5种算法智能合并多源数据
- 🔍 **数据质量分析器** - 6维度质量评估 
- 📊 **综合评分系统** - 投资级别评分和建议
- 🔔 **可靠性监控** - 实时监控和告警
- ⚖️ **动态权重管理** - 自适应权重优化

## 🏃 快速开始

### 1. 运行完整演示

```bash
# 进入项目目录
cd TradingAgents-CN

# 运行阶段3功能演示
python examples/stage3_demo.py
```

### 2. 运行集成测试

```bash
# 验证所有功能正常工作
python tests/test_stage3_integration.py
```

## 📖 使用示例

### 数据融合引擎

```python
from tradingagents.analytics.data_fusion_engine import get_fusion_engine, DataPoint, DataSourceType
from datetime import datetime

# 创建多源数据点
data_points = [
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
    )
]

# 获取融合引擎并执行融合
fusion_engine = get_fusion_engine()
result = fusion_engine.fuse_data_points(data_points, 'adaptive_fusion')

print(f"融合价格: {result.fused_value:.2f}")
print(f"融合置信度: {result.confidence:.3f}")
print(f"融合质量: {result.quality_score:.3f}")
```

### 数据质量分析

```python
from tradingagents.analytics.data_quality_analyzer import get_quality_analyzer

# 准备股票数据
stock_data = {
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

# 分析数据质量
analyzer = get_quality_analyzer()
metrics = analyzer.analyze_data_quality('eastmoney', stock_data, 'stock_price')

print(f"质量等级: {metrics.quality_grade}")
print(f"综合评分: {metrics.overall_score:.3f}")
print(f"完整性: {metrics.completeness:.3f}")
print(f"准确性: {metrics.accuracy:.3f}")
```

### 综合评分系统

```python
from tradingagents.analytics.comprehensive_scoring_system import calculate_comprehensive_score

# 多源股票数据
stock_data = {
    'eastmoney': {
        'current_price': 25.30,
        'volume': 12500000,
        'change_pct': 2.5,
        # ... 更多数据
    },
    'tencent': {
        'current_price': 25.28,
        'volume': 12300000,
        'change_pct': 2.4,
        # ... 更多数据
    }
}

# 新闻数据
news_data = [
    {
        'title': '平安银行三季度业绩超预期',
        'summary': '净利润同比增长15%',
        'publish_time': '2024-08-06T10:30:00',
        'source': 'sina',
        'relevance_score': 0.9
    }
]

# 计算综合评分
result = calculate_comprehensive_score('000001', stock_data, news_data)

print(f"综合评分: {result.overall_score:.2f}/100")
print(f"投资等级: {result.grade}")
print(f"投资建议: {result.recommendation}")
print(f"风险级别: {result.risk_level}")
```

### 可靠性监控

```python
from tradingagents.analytics.reliability_monitor import get_reliability_monitor

# 获取监控器
monitor = get_reliability_monitor()

# 定义数据源检查函数
def check_eastmoney():
    # 实际的健康检查逻辑
    return True, 150.0, {'quality_score': 0.9}

# 注册数据源监控
monitor.register_data_source('eastmoney', check_eastmoney, critical=True)

# 开始监控
monitor.start_monitoring()

# 获取监控报告
report = monitor.get_monitoring_report()
print(f"整体状态: {report.overall_status.value}")
print(f"健康数据源: {report.healthy_sources}")
```

### 动态权重管理

```python
from tradingagents.analytics.dynamic_weight_manager import get_dynamic_weight_manager

# 获取权重管理器
manager = get_dynamic_weight_manager()

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
    }
}

# 更新权重
new_weights = manager.update_weights(performance_data)

print("调整后权重:")
for source, weight in new_weights.items():
    print(f"{source}: {weight:.3f}")

# 获取调整历史
summary = manager.get_adjustment_summary()
print(f"调整次数: {summary['total_adjustments']}")
```

## 🔧 系统配置

### 权重调整策略

系统支持4种调整策略：

- **conservative** - 保守策略，调整幅度小
- **balanced** - 平衡策略，默认策略
- **aggressive** - 激进策略，调整幅度大  
- **adaptive** - 自适应策略，根据情况调整

```python
from tradingagents.analytics.dynamic_weight_manager import AdjustmentStrategy

manager.set_strategy(AdjustmentStrategy.CONSERVATIVE)
```

### 监控阈值配置

```python
# 更新监控阈值
new_thresholds = {
    'response_time_warning_ms': 3000,    # 响应时间警告阈值
    'response_time_critical_ms': 8000,   # 响应时间严重阈值
    'success_rate_warning': 0.85,        # 成功率警告阈值
    'success_rate_critical': 0.7         # 成功率严重阈值
}

monitor.update_thresholds(new_thresholds)
```

## 📊 核心算法

### 融合算法

1. **weighted_average** - 基于权重的加权平均
2. **median_fusion** - 中位数融合，抗异常值
3. **confidence_weighted** - 基于置信度加权
4. **quality_weighted** - 基于质量评分加权
5. **adaptive_fusion** - 自适应选择最佳算法

### 质量维度

1. **completeness** - 数据完整性 (20%)
2. **accuracy** - 数据准确性 (25%)
3. **timeliness** - 数据时效性 (20%)
4. **consistency** - 数据一致性 (15%)
5. **validity** - 数据有效性 (15%)
6. **reliability** - 数据可靠性 (5%)

### 评分类别

1. **technical** - 技术面分析 (25%)
2. **fundamental** - 基本面分析 (30%)
3. **sentiment** - 情绪面分析 (20%)
4. **quality** - 数据质量 (15%)
5. **risk** - 风险评估 (10%)

## 🚨 监控告警

### 告警级别

- **INFO** - 信息性告警
- **WARNING** - 警告级告警
- **CRITICAL** - 严重级告警

### 状态定义

- **HEALTHY** - 健康状态
- **WARNING** - 警告状态
- **CRITICAL** - 严重状态
- **OFFLINE** - 离线状态
- **UNKNOWN** - 未知状态

## 📁 文件结构

```
tradingagents/analytics/
├── data_fusion_engine.py          # 数据融合引擎
├── data_quality_analyzer.py       # 数据质量分析器
├── comprehensive_scoring_system.py # 综合评分系统
├── reliability_monitor.py         # 可靠性监控器
├── dynamic_weight_manager.py      # 动态权重管理器
└── sentiment_analyzer.py         # 情感分析器

examples/
└── stage3_demo.py                 # 功能演示脚本

tests/  
└── test_stage3_integration.py     # 集成测试脚本
```

## ❓ 常见问题

### Q: 如何选择合适的融合算法？

A: 系统提供`adaptive_fusion`算法，会根据数据分散度自动选择最合适的方法：
- 数据一致性高 → 加权平均
- 数据分散较大 → 中位数融合  
- 中等分散 → 质量加权

### Q: 如何提高数据质量评分？

A: 重点关注以下方面：
- 确保数据完整性（所有必需字段都有值）
- 检查数据逻辑一致性（如价格范围合理）
- 保证数据时效性（使用最新数据）
- 验证数据准确性（交叉验证多个数据源）

### Q: 监控系统如何处理数据源故障？

A: 系统提供多层次处理：
- 自动状态检测和分级告警
- 动态权重调整降低故障源影响
- 历史性能记录用于趋势分析
- 可配置告警阈值和处理策略

## 🔗 相关文档

- [开发进度记录](../DEVELOPMENT_PROGRESS.md)
- [项目README](../README.md)
- [阶段2快速入门](STAGE2_QUICKSTART.md)

---

*最后更新: 2025年8月6日*