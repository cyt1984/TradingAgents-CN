#!/usr/bin/env python3
"""
数据源可靠性监控系统
实时监控各数据源的可靠性、响应时间、数据质量等指标
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
from collections import defaultdict, deque

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class MonitoringStatus(Enum):
    """监控状态"""
    HEALTHY = "healthy"         # 健康
    WARNING = "warning"         # 警告
    CRITICAL = "critical"       # 严重
    OFFLINE = "offline"         # 离线
    UNKNOWN = "unknown"         # 未知


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DataSourceMetrics:
    """数据源指标"""
    source_name: str
    last_check: datetime
    status: MonitoringStatus
    response_time_ms: float = 0.0
    success_rate: float = 0.0
    data_quality_score: float = 0.0
    uptime_percentage: float = 0.0
    error_count: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReliabilityAlert:
    """可靠性告警"""
    timestamp: datetime
    source: str
    alert_level: AlertLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class MonitoringReport:
    """监控报告"""
    timestamp: datetime
    overall_status: MonitoringStatus
    total_sources: int
    healthy_sources: int
    warning_sources: int
    critical_sources: int
    offline_sources: int
    source_metrics: Dict[str, DataSourceMetrics]
    recent_alerts: List[ReliabilityAlert]
    performance_summary: Dict[str, Any]


class ReliabilityMonitor:
    """数据源可靠性监控器"""

    def __init__(self, check_interval: int = 300):  # 默认5分钟检查一次
        """初始化可靠性监控器"""
        self.check_interval = check_interval
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # 数据源监控配置
        self.monitored_sources = {}
        
        # 性能指标存储
        self.source_metrics = {}
        self.performance_history = defaultdict(lambda: deque(maxlen=288))  # 保持24小时数据(5分钟间隔)
        
        # 告警系统
        self.alerts = deque(maxlen=1000)  # 保持最近1000条告警
        self.alert_handlers = []
        
        # 阈值配置
        self.thresholds = {
            'response_time_warning_ms': 5000,     # 响应时间警告阈值: 5秒
            'response_time_critical_ms': 10000,   # 响应时间严重阈值: 10秒
            'success_rate_warning': 0.9,          # 成功率警告阈值: 90%
            'success_rate_critical': 0.8,         # 成功率严重阈值: 80%
            'quality_score_warning': 0.7,         # 质量评分警告阈值: 0.7
            'quality_score_critical': 0.5,        # 质量评分严重阈值: 0.5
            'uptime_warning': 0.95,              # 可用性警告阈值: 95%
            'uptime_critical': 0.9               # 可用性严重阈值: 90%
        }
        
        logger.info("数据源可靠性监控器初始化完成")
        logger.info(f"   检查间隔: {check_interval}秒")

    def register_data_source(self, source_name: str, 
                           check_function: Callable[[], Tuple[bool, float, Dict[str, Any]]],
                           critical: bool = False):
        """
        注册数据源监控
        
        Args:
            source_name: 数据源名称
            check_function: 检查函数，返回(成功标志, 响应时间ms, 额外数据)
            critical: 是否为关键数据源
        """
        try:
            self.monitored_sources[source_name] = {
                'check_function': check_function,
                'critical': critical,
                'registered_at': datetime.now()
            }
            
            # 初始化指标
            self.source_metrics[source_name] = DataSourceMetrics(
                source_name=source_name,
                last_check=datetime.now(),
                status=MonitoringStatus.UNKNOWN,
                metadata={'critical': critical}
            )
            
            logger.info(f"注册数据源监控: {source_name} ({'关键' if critical else '普通'})")
            
        except Exception as e:
            logger.error(f"注册数据源监控失败: {source_name} - {e}")

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring_active:
            logger.warning("监控已在运行中")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("数据源可靠性监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        logger.info("数据源可靠性监控已停止")

    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                self._check_all_sources()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.check_interval)

    def _check_all_sources(self):
        """检查所有数据源"""
        check_time = datetime.now()
        
        for source_name, source_config in self.monitored_sources.items():
            try:
                self._check_single_source(source_name, source_config, check_time)
            except Exception as e:
                logger.error(f"检查数据源失败: {source_name} - {e}")
                self._handle_source_error(source_name, str(e))

    def _check_single_source(self, source_name: str, source_config: Dict[str, Any], check_time: datetime):
        """检查单个数据源"""
        check_function = source_config['check_function']
        metrics = self.source_metrics[source_name]
        
        # 执行健康检查
        start_time = time.time()
        try:
            success, response_time_ms, extra_data = check_function()
            actual_response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 使用实际测量的响应时间
            if response_time_ms <= 0:
                response_time_ms = actual_response_time
            
        except Exception as e:
            success = False
            response_time_ms = (time.time() - start_time) * 1000
            extra_data = {'error': str(e)}
            logger.debug(f"数据源检查异常: {source_name} - {e}")

        # 更新指标
        self._update_source_metrics(source_name, success, response_time_ms, extra_data, check_time)
        
        # 检查告警条件
        self._check_alert_conditions(source_name, metrics)

    def _update_source_metrics(self, source_name: str, success: bool, 
                             response_time_ms: float, extra_data: Dict[str, Any], check_time: datetime):
        """更新数据源指标"""
        metrics = self.source_metrics[source_name]
        
        # 更新基本信息
        metrics.last_check = check_time
        metrics.response_time_ms = response_time_ms
        metrics.total_requests += 1
        
        if not success:
            metrics.error_count += 1
            metrics.last_error = extra_data.get('error', '未知错误')
        
        # 计算成功率
        metrics.success_rate = (metrics.total_requests - metrics.error_count) / metrics.total_requests
        
        # 更新平均响应时间
        history = self.performance_history[f"{source_name}_response_time"]
        history.append(response_time_ms)
        metrics.avg_response_time = statistics.mean(history) if history else response_time_ms
        
        # 计算可用性百分比
        uptime_history = self.performance_history[f"{source_name}_uptime"]
        uptime_history.append(1 if success else 0)
        metrics.uptime_percentage = statistics.mean(uptime_history) if uptime_history else (1 if success else 0)
        
        # 更新数据质量评分 (从extra_data获取)
        if 'quality_score' in extra_data:
            metrics.data_quality_score = extra_data['quality_score']
        
        # 确定状态
        metrics.status = self._determine_source_status(metrics)
        
        # 更新元数据
        metrics.metadata.update(extra_data)

    def _determine_source_status(self, metrics: DataSourceMetrics) -> MonitoringStatus:
        """确定数据源状态"""
        try:
            # 检查是否离线
            time_since_check = (datetime.now() - metrics.last_check).total_seconds()
            if time_since_check > self.check_interval * 3:  # 超过3个检查间隔认为离线
                return MonitoringStatus.OFFLINE
            
            # 检查严重问题
            critical_issues = [
                metrics.success_rate < self.thresholds['success_rate_critical'],
                metrics.response_time_ms > self.thresholds['response_time_critical_ms'],
                metrics.data_quality_score < self.thresholds['quality_score_critical'],
                metrics.uptime_percentage < self.thresholds['uptime_critical']
            ]
            
            if any(critical_issues):
                return MonitoringStatus.CRITICAL
            
            # 检查警告问题
            warning_issues = [
                metrics.success_rate < self.thresholds['success_rate_warning'],
                metrics.response_time_ms > self.thresholds['response_time_warning_ms'],
                metrics.data_quality_score < self.thresholds['quality_score_warning'],
                metrics.uptime_percentage < self.thresholds['uptime_warning']
            ]
            
            if any(warning_issues):
                return MonitoringStatus.WARNING
            
            return MonitoringStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"确定数据源状态失败: {e}")
            return MonitoringStatus.UNKNOWN

    def _check_alert_conditions(self, source_name: str, metrics: DataSourceMetrics):
        """检查告警条件"""
        current_time = datetime.now()
        
        # 检查状态变化
        previous_status = metrics.metadata.get('previous_status', MonitoringStatus.UNKNOWN)
        if previous_status != metrics.status:
            self._create_status_change_alert(source_name, previous_status, metrics.status, current_time)
            metrics.metadata['previous_status'] = metrics.status
        
        # 检查性能问题
        self._check_performance_alerts(source_name, metrics, current_time)

    def _create_status_change_alert(self, source_name: str, old_status: MonitoringStatus, 
                                  new_status: MonitoringStatus, timestamp: datetime):
        """创建状态变化告警"""
        if new_status == MonitoringStatus.CRITICAL:
            alert_level = AlertLevel.CRITICAL
            message = f"数据源 {source_name} 状态变为严重"
        elif new_status == MonitoringStatus.WARNING:
            alert_level = AlertLevel.WARNING
            message = f"数据源 {source_name} 状态变为警告"
        elif new_status == MonitoringStatus.OFFLINE:
            alert_level = AlertLevel.CRITICAL
            message = f"数据源 {source_name} 离线"
        elif new_status == MonitoringStatus.HEALTHY and old_status in [MonitoringStatus.CRITICAL, MonitoringStatus.WARNING, MonitoringStatus.OFFLINE]:
            alert_level = AlertLevel.INFO
            message = f"数据源 {source_name} 状态恢复正常"
        else:
            return  # 不需要告警
        
        alert = ReliabilityAlert(
            timestamp=timestamp,
            source=source_name,
            alert_level=alert_level,
            message=message,
            details={
                'old_status': old_status.value,
                'new_status': new_status.value
            }
        )
        
        self.alerts.append(alert)
        self._trigger_alert_handlers(alert)

    def _check_performance_alerts(self, source_name: str, metrics: DataSourceMetrics, timestamp: datetime):
        """检查性能告警"""
        # 响应时间告警
        if metrics.response_time_ms > self.thresholds['response_time_critical_ms']:
            self._create_performance_alert(
                source_name, AlertLevel.CRITICAL, 
                f"响应时间过长: {metrics.response_time_ms:.0f}ms", timestamp
            )
        elif metrics.response_time_ms > self.thresholds['response_time_warning_ms']:
            self._create_performance_alert(
                source_name, AlertLevel.WARNING, 
                f"响应时间较长: {metrics.response_time_ms:.0f}ms", timestamp
            )
        
        # 成功率告警
        if metrics.success_rate < self.thresholds['success_rate_critical']:
            self._create_performance_alert(
                source_name, AlertLevel.CRITICAL, 
                f"成功率过低: {metrics.success_rate:.1%}", timestamp
            )
        elif metrics.success_rate < self.thresholds['success_rate_warning']:
            self._create_performance_alert(
                source_name, AlertLevel.WARNING, 
                f"成功率较低: {metrics.success_rate:.1%}", timestamp
            )

    def _create_performance_alert(self, source_name: str, alert_level: AlertLevel, 
                                message: str, timestamp: datetime):
        """创建性能告警"""
        # 避免重复告警 (10分钟内相同类型不重复)
        cutoff_time = timestamp - timedelta(minutes=10)
        recent_similar_alerts = [
            alert for alert in self.alerts 
            if alert.source == source_name and 
               alert.alert_level == alert_level and 
               alert.timestamp > cutoff_time and
               message.split(':')[0] in alert.message  # 相同类型的告警
        ]
        
        if recent_similar_alerts:
            return  # 跳过重复告警
        
        alert = ReliabilityAlert(
            timestamp=timestamp,
            source=source_name,
            alert_level=alert_level,
            message=message,
            details={'type': 'performance'}
        )
        
        self.alerts.append(alert)
        self._trigger_alert_handlers(alert)

    def _handle_source_error(self, source_name: str, error_message: str):
        """处理数据源错误"""
        metrics = self.source_metrics.get(source_name)
        if metrics:
            metrics.error_count += 1
            metrics.total_requests += 1
            metrics.last_error = error_message
            metrics.status = MonitoringStatus.CRITICAL
            
            # 创建错误告警
            alert = ReliabilityAlert(
                timestamp=datetime.now(),
                source=source_name,
                alert_level=AlertLevel.CRITICAL,
                message=f"数据源检查异常: {error_message}",
                details={'type': 'error', 'error': error_message}
            )
            
            self.alerts.append(alert)
            self._trigger_alert_handlers(alert)

    def add_alert_handler(self, handler: Callable[[ReliabilityAlert], None]):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
        logger.info(f"添加告警处理器: {handler.__name__}")

    def _trigger_alert_handlers(self, alert: ReliabilityAlert):
        """触发告警处理器"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

    def get_monitoring_report(self) -> MonitoringReport:
        """获取监控报告"""
        try:
            current_time = datetime.now()
            
            # 统计各状态数据源数量
            status_counts = defaultdict(int)
            for metrics in self.source_metrics.values():
                status_counts[metrics.status] += 1
            
            # 确定整体状态
            if status_counts[MonitoringStatus.CRITICAL] > 0:
                overall_status = MonitoringStatus.CRITICAL
            elif status_counts[MonitoringStatus.WARNING] > 0:
                overall_status = MonitoringStatus.WARNING
            elif status_counts[MonitoringStatus.OFFLINE] > 0:
                overall_status = MonitoringStatus.WARNING  # 离线也算警告
            else:
                overall_status = MonitoringStatus.HEALTHY
            
            # 性能汇总
            performance_summary = self._generate_performance_summary()
            
            # 最近告警
            recent_alerts = list(self.alerts)[-50:]  # 最近50条告警
            
            report = MonitoringReport(
                timestamp=current_time,
                overall_status=overall_status,
                total_sources=len(self.source_metrics),
                healthy_sources=status_counts[MonitoringStatus.HEALTHY],
                warning_sources=status_counts[MonitoringStatus.WARNING],
                critical_sources=status_counts[MonitoringStatus.CRITICAL],
                offline_sources=status_counts[MonitoringStatus.OFFLINE],
                source_metrics=self.source_metrics.copy(),
                recent_alerts=recent_alerts,
                performance_summary=performance_summary
            )
            
            return report
            
        except Exception as e:
            logger.error(f"生成监控报告失败: {e}")
            return MonitoringReport(
                timestamp=datetime.now(),
                overall_status=MonitoringStatus.UNKNOWN,
                total_sources=0, healthy_sources=0, warning_sources=0,
                critical_sources=0, offline_sources=0,
                source_metrics={}, recent_alerts=[], performance_summary={}
            )

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """生成性能汇总"""
        try:
            summary = {
                'avg_response_time': 0,
                'overall_success_rate': 0,
                'overall_uptime': 0,
                'best_performing_source': None,
                'worst_performing_source': None
            }
            
            if not self.source_metrics:
                return summary
            
            # 计算平均指标
            response_times = [m.avg_response_time for m in self.source_metrics.values() if m.avg_response_time > 0]
            success_rates = [m.success_rate for m in self.source_metrics.values()]
            uptime_rates = [m.uptime_percentage for m in self.source_metrics.values()]
            
            if response_times:
                summary['avg_response_time'] = statistics.mean(response_times)
            if success_rates:
                summary['overall_success_rate'] = statistics.mean(success_rates)
            if uptime_rates:
                summary['overall_uptime'] = statistics.mean(uptime_rates)
            
            # 找出最佳和最差数据源
            if self.source_metrics:
                # 综合评分 = 成功率 * 0.4 + 可用性 * 0.4 + (1 - 响应时间/10000) * 0.2
                scored_sources = []
                for name, metrics in self.source_metrics.items():
                    response_score = max(0, 1 - metrics.avg_response_time / 10000) if metrics.avg_response_time > 0 else 0.5
                    composite_score = (metrics.success_rate * 0.4 + 
                                     metrics.uptime_percentage * 0.4 + 
                                     response_score * 0.2)
                    scored_sources.append((name, composite_score))
                
                if scored_sources:
                    scored_sources.sort(key=lambda x: x[1], reverse=True)
                    summary['best_performing_source'] = scored_sources[0][0]
                    summary['worst_performing_source'] = scored_sources[-1][0]
            
            return summary
            
        except Exception as e:
            logger.error(f"生成性能汇总失败: {e}")
            return {}

    def get_source_reliability_score(self, source_name: str) -> float:
        """获取数据源可靠性评分 (0-1)"""
        try:
            if source_name not in self.source_metrics:
                return 0.5  # 默认评分
            
            metrics = self.source_metrics[source_name]
            
            # 综合可靠性评分
            success_weight = 0.3
            uptime_weight = 0.3
            response_weight = 0.2
            quality_weight = 0.2
            
            # 响应时间评分 (响应时间越低评分越高)
            response_score = max(0, 1 - metrics.avg_response_time / 10000) if metrics.avg_response_time > 0 else 0.5
            
            reliability_score = (
                metrics.success_rate * success_weight +
                metrics.uptime_percentage * uptime_weight +
                response_score * response_weight +
                metrics.data_quality_score * quality_weight
            )
            
            return min(1.0, max(0.0, reliability_score))
            
        except Exception as e:
            logger.error(f"计算可靠性评分失败: {source_name} - {e}")
            return 0.5

    def update_thresholds(self, new_thresholds: Dict[str, Any]):
        """更新告警阈值"""
        try:
            self.thresholds.update(new_thresholds)
            logger.info("告警阈值已更新")
            logger.info(f"   新阈值: {new_thresholds}")
        except Exception as e:
            logger.error(f"更新告警阈值失败: {e}")

    def export_metrics(self, filepath: str = None) -> Dict[str, Any]:
        """导出监控指标"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'source_metrics': {},
                'performance_history': {},
                'recent_alerts': [],
                'thresholds': self.thresholds
            }
            
            # 导出数据源指标
            for name, metrics in self.source_metrics.items():
                export_data['source_metrics'][name] = {
                    'source_name': metrics.source_name,
                    'last_check': metrics.last_check.isoformat(),
                    'status': metrics.status.value,
                    'response_time_ms': metrics.response_time_ms,
                    'success_rate': metrics.success_rate,
                    'data_quality_score': metrics.data_quality_score,
                    'uptime_percentage': metrics.uptime_percentage,
                    'error_count': metrics.error_count,
                    'total_requests': metrics.total_requests,
                    'avg_response_time': metrics.avg_response_time,
                    'last_error': metrics.last_error
                }
            
            # 导出最近告警
            for alert in list(self.alerts)[-100:]:  # 最近100条
                export_data['recent_alerts'].append({
                    'timestamp': alert.timestamp.isoformat(),
                    'source': alert.source,
                    'alert_level': alert.alert_level.value,
                    'message': alert.message,
                    'acknowledged': alert.acknowledged
                })
            
            # 如果指定了文件路径，保存到文件
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                logger.info(f"监控指标已导出到: {filepath}")
            
            return export_data
            
        except Exception as e:
            logger.error(f"导出监控指标失败: {e}")
            return {}


# 全局实例
_reliability_monitor = None

def get_reliability_monitor() -> ReliabilityMonitor:
    """获取可靠性监控器实例"""
    global _reliability_monitor
    if _reliability_monitor is None:
        _reliability_monitor = ReliabilityMonitor()
    return _reliability_monitor


# 便捷函数
def start_monitoring():
    """启动数据源监控"""
    monitor = get_reliability_monitor()
    monitor.start_monitoring()

def get_monitoring_report() -> MonitoringReport:
    """获取监控报告"""
    monitor = get_reliability_monitor()
    return monitor.get_monitoring_report()

def register_source_monitor(source_name: str, check_function: Callable, critical: bool = False):
    """注册数据源监控"""
    monitor = get_reliability_monitor()
    monitor.register_data_source(source_name, check_function, critical)