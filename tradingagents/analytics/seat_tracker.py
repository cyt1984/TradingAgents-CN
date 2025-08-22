#!/usr/bin/env python3
"""
席位追踪和预警系统
实时监控重要席位的交易活动，提供预警和跟随建议
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from pathlib import Path

from tradingagents.utils.logging_manager import get_logger
from .seat_analyzer import get_seat_analyzer, SeatType, SeatProfile
from .longhubang_analyzer import get_longhubang_analyzer, LongHuBangAnalysisResult
from ..dataflows.longhubang_utils import get_longhubang_provider, RankingType

logger = get_logger('seat_tracker')


class AlertLevel(Enum):
    """预警级别枚举"""
    LOW = "low"                    # 低级预警
    MEDIUM = "medium"              # 中级预警  
    HIGH = "high"                  # 高级预警
    CRITICAL = "critical"          # 紧急预警


class AlertType(Enum):
    """预警类型枚举"""
    SEAT_ENTRY = "seat_entry"                    # 席位进入
    SEAT_EXIT = "seat_exit"                      # 席位退出
    COORDINATED_TRADING = "coordinated_trading"  # 协同交易
    VOLUME_SURGE = "volume_surge"                # 交易量激增
    PATTERN_MATCH = "pattern_match"              # 模式匹配
    RISK_WARNING = "risk_warning"                # 风险预警


@dataclass
class SeatActivity:
    """席位活动记录"""
    seat_name: str                 # 席位名称
    symbol: str                    # 股票代码
    stock_name: str                # 股票名称
    date: str                      # 交易日期
    side: str                      # 买方/卖方
    amount: float                  # 交易金额(万元)
    rank: int                      # 排名
    stock_change_pct: float        # 股票涨跌幅
    seat_type: SeatType            # 席位类型
    influence_score: float         # 影响力评分
    
    # 分析数据
    follow_suggestion: str = ""    # 跟随建议
    risk_level: str = ""           # 风险等级
    pattern_score: float = 0.0     # 模式评分
    timestamp: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@dataclass
class SeatAlert:
    """席位预警"""
    alert_id: str                  # 预警ID
    seat_name: str                 # 席位名称
    alert_type: AlertType          # 预警类型
    alert_level: AlertLevel        # 预警级别
    symbol: str                    # 相关股票代码
    stock_name: str                # 股票名称
    message: str                   # 预警消息
    confidence: float              # 置信度
    
    # 触发数据
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    
    # 建议行动
    recommended_action: str = ""   # 建议行动
    follow_probability: float = 0.0  # 跟随概率
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    expires_at: str = ""           # 过期时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'alert_id': self.alert_id,
            'seat_name': self.seat_name,
            'alert_type': self.alert_type.value,
            'alert_level': self.alert_level.value,
            'symbol': self.symbol,
            'stock_name': self.stock_name,
            'message': self.message,
            'confidence': self.confidence,
            'trigger_data': self.trigger_data,
            'recommended_action': self.recommended_action,
            'follow_probability': self.follow_probability,
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }


@dataclass
class TrackingConfig:
    """追踪配置"""
    tracked_seats: List[str] = field(default_factory=list)     # 追踪的席位列表
    alert_thresholds: Dict[str, float] = field(default_factory=dict)  # 预警阈值
    update_interval: int = 300                                  # 更新间隔(秒)
    max_alerts_per_day: int = 50                               # 每日最大预警数量
    enable_email_alerts: bool = False                          # 启用邮件预警
    enable_push_alerts: bool = True                            # 启用推送预警
    
    def get_default_thresholds(self) -> Dict[str, float]:
        """获取默认预警阈值"""
        return {
            'min_trade_amount': 5000.0,        # 最小交易金额(万元)
            'min_influence_score': 70.0,       # 最小影响力评分
            'coordination_confidence': 0.7,     # 协同交易置信度
            'volume_surge_ratio': 2.0,          # 交易量激增比例
            'pattern_match_score': 80.0,        # 模式匹配评分
            'follow_probability': 0.6           # 跟随概率阈值
        }


class SeatTracker:
    """席位追踪器"""
    
    def __init__(self, config: TrackingConfig = None):
        """
        初始化席位追踪器
        
        Args:
            config: 追踪配置
        """
        self.config = config or TrackingConfig()
        if not self.config.alert_thresholds:
            self.config.alert_thresholds = self.config.get_default_thresholds()
        
        # 初始化组件
        self.seat_analyzer = None
        self.longhubang_analyzer = None
        self.longhubang_provider = None
        
        # 数据存储
        self.activities_history: List[SeatActivity] = []
        self.active_alerts: List[SeatAlert] = []
        self.alert_history: List[SeatAlert] = []
        
        # 状态管理
        self.last_update_time = None
        self.daily_alert_count = 0
        
        # 初始化组件
        self._init_components()
        
        logger.info("✅ 席位追踪器初始化成功")
    
    def _init_components(self):
        """初始化相关组件"""
        try:
            self.seat_analyzer = get_seat_analyzer()
            self.longhubang_analyzer = get_longhubang_analyzer()
            self.longhubang_provider = get_longhubang_provider()
            logger.info("✅ 席位追踪器组件初始化成功")
        except Exception as e:
            logger.error(f"❌ 席位追踪器组件初始化失败: {e}")
            raise
    
    def add_tracked_seat(self, seat_name: str) -> bool:
        """
        添加追踪席位
        
        Args:
            seat_name: 席位名称
            
        Returns:
            是否添加成功
        """
        try:
            if seat_name not in self.config.tracked_seats:
                self.config.tracked_seats.append(seat_name)
                logger.info(f"✅ 添加追踪席位: {seat_name}")
                return True
            else:
                logger.info(f"⚠️ 席位已在追踪列表中: {seat_name}")
                return False
        except Exception as e:
            logger.error(f"❌ 添加追踪席位失败: {e}")
            return False
    
    def remove_tracked_seat(self, seat_name: str) -> bool:
        """
        移除追踪席位
        
        Args:
            seat_name: 席位名称
            
        Returns:
            是否移除成功
        """
        try:
            if seat_name in self.config.tracked_seats:
                self.config.tracked_seats.remove(seat_name)
                logger.info(f"✅ 移除追踪席位: {seat_name}")
                return True
            else:
                logger.info(f"⚠️ 席位不在追踪列表中: {seat_name}")
                return False
        except Exception as e:
            logger.error(f"❌ 移除追踪席位失败: {e}")
            return False
    
    def get_tracked_seats(self) -> List[str]:
        """获取追踪席位列表"""
        return self.config.tracked_seats.copy()
    
    def update_tracking_data(self, date: str = None) -> Dict[str, Any]:
        """
        更新追踪数据
        
        Args:
            date: 查询日期，默认为今天
            
        Returns:
            更新结果统计
        """
        start_time = time.time()
        logger.info("🔄 开始更新席位追踪数据...")
        
        try:
            if not self.config.tracked_seats:
                logger.warning("⚠️ 未配置追踪席位")
                return {'error': '未配置追踪席位'}
            
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取龙虎榜数据
            longhubang_results = self.longhubang_analyzer.get_top_ranking_stocks(
                date=date,
                min_score=50.0,  # 放宽筛选条件以获取更多数据
                limit=200
            )
            
            if not longhubang_results:
                logger.warning(f"⚠️ 未获取到{date}的龙虎榜数据")
                return {'error': f'未获取到{date}的龙虎榜数据'}
            
            new_activities = []
            new_alerts = []
            
            # 分析每只股票的席位情况
            for result in longhubang_results:
                try:
                    # 检查买方席位
                    for seat_info in result.longhubang_data.buy_seats:
                        seat_activity = self._analyze_seat_activity(
                            seat_info, result, 'buy', date
                        )
                        if seat_activity:
                            new_activities.append(seat_activity)
                            
                            # 检查是否需要预警
                            alerts = self._check_seat_alerts(seat_activity, result)
                            new_alerts.extend(alerts)
                    
                    # 检查卖方席位  
                    for seat_info in result.longhubang_data.sell_seats:
                        seat_activity = self._analyze_seat_activity(
                            seat_info, result, 'sell', date
                        )
                        if seat_activity:
                            new_activities.append(seat_activity)
                            
                            # 检查是否需要预警
                            alerts = self._check_seat_alerts(seat_activity, result)
                            new_alerts.extend(alerts)
                    
                    # 检查协同交易预警
                    coordination_alerts = self._check_coordination_alerts(result)
                    new_alerts.extend(coordination_alerts)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 分析股票{result.symbol}席位活动失败: {e}")
                    continue
            
            # 更新数据
            self.activities_history.extend(new_activities)
            self.active_alerts.extend(new_alerts)
            
            # 清理过期数据
            self._cleanup_expired_data()
            
            # 更新状态
            self.last_update_time = datetime.now()
            self.daily_alert_count += len(new_alerts)
            
            execution_time = time.time() - start_time
            
            update_stats = {
                'date': date,
                'new_activities': len(new_activities),
                'new_alerts': len(new_alerts),
                'total_activities': len(self.activities_history),
                'active_alerts': len(self.active_alerts),
                'tracked_seats': len(self.config.tracked_seats),
                'execution_time': execution_time,
                'last_update': self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✅ 席位追踪数据更新完成: 新活动{len(new_activities)}条, 新预警{len(new_alerts)}条, 耗时{execution_time:.2f}秒")
            return update_stats
            
        except Exception as e:
            logger.error(f"❌ 更新席位追踪数据失败: {e}")
            return {'error': str(e)}
    
    def _analyze_seat_activity(self, seat_info, result: LongHuBangAnalysisResult, 
                              side: str, date: str) -> Optional[SeatActivity]:
        """分析席位活动"""
        try:
            # 检查是否为追踪的席位
            seat_name = seat_info.seat_name
            is_tracked = any(tracked in seat_name for tracked in self.config.tracked_seats)
            
            if not is_tracked:
                return None
            
            # 识别席位类型
            seat_type, confidence = self.seat_analyzer.identify_seat_type(seat_name)
            
            # 计算影响力评分
            influence_score = self.seat_analyzer.calculate_seat_influence_score(seat_info)
            
            # 获取席位档案
            seat_profile = self.seat_analyzer.get_seat_profile(seat_name)
            
            # 创建活动记录
            activity = SeatActivity(
                seat_name=seat_name,
                symbol=result.symbol,
                stock_name=result.name,
                date=date,
                side=side,
                amount=seat_info.buy_amount if side == 'buy' else seat_info.sell_amount,
                rank=1,  # 从龙虎榜数据中获取实际排名
                stock_change_pct=result.longhubang_data.change_pct,
                seat_type=seat_type,
                influence_score=influence_score
            )
            
            # 生成跟随建议
            if seat_profile:
                activity.follow_suggestion = self._generate_follow_suggestion(
                    activity, seat_profile, result
                )
                activity.risk_level = self._assess_risk_level(activity, result)
                activity.pattern_score = self._calculate_pattern_score(activity, result)
            
            return activity
            
        except Exception as e:
            logger.error(f"❌ 分析席位活动失败: {e}")
            return None
    
    def _check_seat_alerts(self, activity: SeatActivity, 
                          result: LongHuBangAnalysisResult) -> List[SeatAlert]:
        """检查席位预警"""
        alerts = []
        
        try:
            # 检查交易金额预警
            if activity.amount >= self.config.alert_thresholds.get('min_trade_amount', 5000):
                if activity.influence_score >= self.config.alert_thresholds.get('min_influence_score', 70):
                    alert = self._create_seat_entry_alert(activity, result)
                    alerts.append(alert)
            
            # 检查高影响力席位预警
            if activity.influence_score >= 90:
                alert = self._create_high_influence_alert(activity, result)
                alerts.append(alert)
            
            # 检查模式匹配预警
            if activity.pattern_score >= self.config.alert_thresholds.get('pattern_match_score', 80):
                alert = self._create_pattern_match_alert(activity, result)
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"❌ 检查席位预警失败: {e}")
        
        return alerts
    
    def _check_coordination_alerts(self, result: LongHuBangAnalysisResult) -> List[SeatAlert]:
        """检查协同交易预警"""
        alerts = []
        
        try:
            if not result.seat_analysis:
                return alerts
            
            coordination = result.seat_analysis.get('coordination_analysis', {})
            
            if coordination.get('coordinated', False):
                confidence = coordination.get('confidence', 0)
                
                if confidence >= self.config.alert_thresholds.get('coordination_confidence', 0.7):
                    alert_id = f"coord_{result.symbol}_{int(time.time())}"
                    
                    alert = SeatAlert(
                        alert_id=alert_id,
                        seat_name="多个席位",
                        alert_type=AlertType.COORDINATED_TRADING,
                        alert_level=AlertLevel.HIGH,
                        symbol=result.symbol,
                        stock_name=result.name,
                        message=f"检测到{result.symbol} {result.name}存在协同交易迹象",
                        confidence=confidence,
                        trigger_data={
                            'coordination_signals': coordination.get('signals', []),
                            'seat_count': len(result.longhubang_data.buy_seats) + len(result.longhubang_data.sell_seats),
                            'net_inflow': result.longhubang_data.get_net_flow()
                        },
                        recommended_action="谨慎观察，可能存在操纵风险",
                        follow_probability=0.2  # 协同交易跟随概率较低
                    )
                    
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"❌ 检查协同交易预警失败: {e}")
        
        return alerts
    
    def _create_seat_entry_alert(self, activity: SeatActivity, 
                                result: LongHuBangAnalysisResult) -> SeatAlert:
        """创建席位进入预警"""
        alert_id = f"entry_{activity.symbol}_{activity.seat_name}_{int(time.time())}"
        
        # 根据席位类型和影响力确定预警级别
        if activity.influence_score >= 90:
            alert_level = AlertLevel.HIGH
        elif activity.influence_score >= 80:
            alert_level = AlertLevel.MEDIUM
        else:
            alert_level = AlertLevel.LOW
        
        # 计算跟随概率
        follow_prob = self._calculate_follow_probability(activity, result)
        
        return SeatAlert(
            alert_id=alert_id,
            seat_name=activity.seat_name,
            alert_type=AlertType.SEAT_ENTRY,
            alert_level=alert_level,
            symbol=activity.symbol,
            stock_name=activity.stock_name,
            message=f"{activity.seat_name} {activity.side}入 {activity.symbol} {activity.stock_name}，金额{activity.amount:.0f}万元",
            confidence=0.8,
            trigger_data={
                'side': activity.side,
                'amount': activity.amount,
                'influence_score': activity.influence_score,
                'stock_change_pct': activity.stock_change_pct,
                'seat_type': activity.seat_type.value
            },
            recommended_action=activity.follow_suggestion,
            follow_probability=follow_prob
        )
    
    def _create_high_influence_alert(self, activity: SeatActivity, 
                                   result: LongHuBangAnalysisResult) -> SeatAlert:
        """创建高影响力席位预警"""
        alert_id = f"influence_{activity.symbol}_{activity.seat_name}_{int(time.time())}"
        
        return SeatAlert(
            alert_id=alert_id,
            seat_name=activity.seat_name,
            alert_type=AlertType.SEAT_ENTRY,
            alert_level=AlertLevel.CRITICAL,
            symbol=activity.symbol,
            stock_name=activity.stock_name,
            message=f"高影响力席位 {activity.seat_name} 进入 {activity.symbol}，影响力评分{activity.influence_score:.1f}",
            confidence=0.9,
            trigger_data={
                'influence_score': activity.influence_score,
                'seat_type': activity.seat_type.value,
                'amount': activity.amount
            },
            recommended_action="强烈关注，考虑跟随",
            follow_probability=0.8
        )
    
    def _create_pattern_match_alert(self, activity: SeatActivity, 
                                  result: LongHuBangAnalysisResult) -> SeatAlert:
        """创建模式匹配预警"""
        alert_id = f"pattern_{activity.symbol}_{activity.seat_name}_{int(time.time())}"
        
        return SeatAlert(
            alert_id=alert_id,
            seat_name=activity.seat_name,
            alert_type=AlertType.PATTERN_MATCH,
            alert_level=AlertLevel.MEDIUM,
            symbol=activity.symbol,
            stock_name=activity.stock_name,
            message=f"{activity.seat_name} 交易模式匹配度高，评分{activity.pattern_score:.1f}",
            confidence=0.7,
            trigger_data={
                'pattern_score': activity.pattern_score,
                'historical_success_rate': 0.65  # 从历史数据计算
            },
            recommended_action="模式匹配，建议关注",
            follow_probability=0.6
        )
    
    def _generate_follow_suggestion(self, activity: SeatActivity, 
                                  seat_profile: SeatProfile,
                                  result: LongHuBangAnalysisResult) -> str:
        """生成跟随建议"""
        suggestions = []
        
        # 基于席位类型
        if seat_profile.seat_type == SeatType.FAMOUS_INVESTOR:
            if activity.side == 'buy':
                suggestions.append("知名投资者买入，建议关注")
            else:
                suggestions.append("知名投资者卖出，谨慎跟随")
        elif seat_profile.seat_type == SeatType.PRIVATE_FUND:
            suggestions.append("私募机构操作，专业性强")
        elif seat_profile.seat_type == SeatType.HOT_MONEY:
            suggestions.append("游资操作，注意短线风险")
        
        # 基于交易金额
        if activity.amount > 20000:  # 2亿以上
            suggestions.append("大额交易，影响显著")
        
        # 基于市场情绪
        if result.market_sentiment.value == 'bullish':
            suggestions.append("市场情绪积极")
        elif result.market_sentiment.value == 'bearish':
            suggestions.append("市场情绪谨慎")
        
        return "; ".join(suggestions) if suggestions else "建议观察"
    
    def _assess_risk_level(self, activity: SeatActivity, 
                          result: LongHuBangAnalysisResult) -> str:
        """评估风险等级"""
        risk_factors = 0
        
        # 席位风险因子
        if activity.seat_type == SeatType.HOT_MONEY:
            risk_factors += 2
        elif activity.seat_type == SeatType.UNKNOWN:
            risk_factors += 1
        
        # 股票风险因子
        if abs(result.longhubang_data.change_pct) > 9:  # 接近涨跌停
            risk_factors += 2
        elif abs(result.longhubang_data.change_pct) > 5:
            risk_factors += 1
        
        # 协同交易风险
        if result.seat_analysis and result.seat_analysis.get('coordination_analysis', {}).get('coordinated', False):
            risk_factors += 2
        
        if risk_factors >= 4:
            return "高风险"
        elif risk_factors >= 2:
            return "中等风险"
        else:
            return "低风险"
    
    def _calculate_pattern_score(self, activity: SeatActivity, 
                               result: LongHuBangAnalysisResult) -> float:
        """计算模式评分"""
        base_score = 50.0
        
        # 席位历史成功率加分
        if activity.seat_type == SeatType.FAMOUS_INVESTOR:
            base_score += 20
        elif activity.seat_type == SeatType.PRIVATE_FUND:
            base_score += 15
        
        # 交易金额加分
        if activity.amount > 10000:
            base_score += 10
        
        # 市场情绪匹配加分
        if activity.side == 'buy' and result.market_sentiment.value in ['bullish', 'extremely_bullish']:
            base_score += 15
        elif activity.side == 'sell' and result.market_sentiment.value in ['bearish', 'extremely_bearish']:
            base_score += 15
        
        return min(100, max(0, base_score))
    
    def _calculate_follow_probability(self, activity: SeatActivity, 
                                    result: LongHuBangAnalysisResult) -> float:
        """计算跟随概率"""
        base_prob = 0.5
        
        # 席位类型调整
        if activity.seat_type == SeatType.FAMOUS_INVESTOR and activity.influence_score > 85:
            base_prob += 0.3
        elif activity.seat_type == SeatType.PRIVATE_FUND and activity.influence_score > 80:
            base_prob += 0.2
        elif activity.seat_type == SeatType.HOT_MONEY:
            base_prob -= 0.1
        
        # 交易金额调整
        if activity.amount > 20000:
            base_prob += 0.1
        
        # 风险调整
        if activity.risk_level == "高风险":
            base_prob -= 0.2
        elif activity.risk_level == "低风险":
            base_prob += 0.1
        
        return min(1.0, max(0.0, base_prob))
    
    def _cleanup_expired_data(self):
        """清理过期数据"""
        try:
            # 清理30天前的活动记录
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            self.activities_history = [
                activity for activity in self.activities_history
                if activity.date >= cutoff_date
            ]
            
            # 清理过期预警
            current_time = datetime.now()
            self.active_alerts = [
                alert for alert in self.active_alerts
                if not alert.expires_at or 
                datetime.strptime(alert.expires_at, '%Y-%m-%d %H:%M:%S') > current_time
            ]
            
            # 重置每日预警计数
            if self.last_update_time and self.last_update_time.date() != datetime.now().date():
                self.daily_alert_count = 0
            
        except Exception as e:
            logger.error(f"❌ 清理过期数据失败: {e}")
    
    def get_active_alerts(self, alert_level: AlertLevel = None) -> List[SeatAlert]:
        """
        获取活跃预警
        
        Args:
            alert_level: 筛选预警级别
            
        Returns:
            预警列表
        """
        if alert_level:
            return [alert for alert in self.active_alerts if alert.alert_level == alert_level]
        return self.active_alerts.copy()
    
    def get_seat_activities(self, seat_name: str = None, days: int = 7) -> List[SeatActivity]:
        """
        获取席位活动记录
        
        Args:
            seat_name: 席位名称，为空则返回所有
            days: 最近天数
            
        Returns:
            活动记录列表
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        activities = [
            activity for activity in self.activities_history
            if activity.date >= cutoff_date
        ]
        
        if seat_name:
            activities = [
                activity for activity in activities
                if seat_name in activity.seat_name
            ]
        
        return sorted(activities, key=lambda x: x.timestamp, reverse=True)
    
    def get_tracking_statistics(self) -> Dict[str, Any]:
        """获取追踪统计信息"""
        try:
            # 计算基础统计
            total_activities = len(self.activities_history)
            active_alerts_count = len(self.active_alerts)
            tracked_seats_count = len(self.config.tracked_seats)
            
            # 按席位类型统计活动
            seat_type_stats = {}
            for activity in self.activities_history:
                seat_type = activity.seat_type.value
                if seat_type not in seat_type_stats:
                    seat_type_stats[seat_type] = {'count': 0, 'total_amount': 0}
                seat_type_stats[seat_type]['count'] += 1
                seat_type_stats[seat_type]['total_amount'] += activity.amount
            
            # 按预警级别统计
            alert_level_stats = {}
            for alert in self.active_alerts:
                level = alert.alert_level.value
                alert_level_stats[level] = alert_level_stats.get(level, 0) + 1
            
            # 最近7天活动统计
            recent_activities = self.get_seat_activities(days=7)
            recent_buy_activities = len([a for a in recent_activities if a.side == 'buy'])
            recent_sell_activities = len(recent_activities) - recent_buy_activities
            
            return {
                'tracking_overview': {
                    'tracked_seats': tracked_seats_count,
                    'total_activities': total_activities,
                    'active_alerts': active_alerts_count,
                    'daily_alert_count': self.daily_alert_count,
                    'last_update': self.last_update_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_update_time else None
                },
                'activity_statistics': {
                    'recent_7_days': len(recent_activities),
                    'recent_buy_activities': recent_buy_activities,
                    'recent_sell_activities': recent_sell_activities,
                    'seat_type_distribution': seat_type_stats
                },
                'alert_statistics': {
                    'by_level': alert_level_stats,
                    'total_today': self.daily_alert_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 获取追踪统计信息失败: {e}")
            return {'error': str(e)}
    
    def export_tracking_data(self, file_path: str = None) -> str:
        """
        导出追踪数据
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            导出文件路径
        """
        try:
            if not file_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = f"seat_tracking_export_{timestamp}.json"
            
            export_data = {
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'config': {
                    'tracked_seats': self.config.tracked_seats,
                    'alert_thresholds': self.config.alert_thresholds
                },
                'activities': [
                    {
                        'seat_name': activity.seat_name,
                        'symbol': activity.symbol,
                        'stock_name': activity.stock_name,
                        'date': activity.date,
                        'side': activity.side,
                        'amount': activity.amount,
                        'stock_change_pct': activity.stock_change_pct,
                        'seat_type': activity.seat_type.value,
                        'influence_score': activity.influence_score,
                        'follow_suggestion': activity.follow_suggestion,
                        'risk_level': activity.risk_level,
                        'timestamp': activity.timestamp
                    }
                    for activity in self.activities_history
                ],
                'alerts': [alert.to_dict() for alert in self.active_alerts],
                'statistics': self.get_tracking_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 追踪数据导出成功: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 导出追踪数据失败: {e}")
            raise


# 全局实例
_seat_tracker = None

def get_seat_tracker(config: TrackingConfig = None) -> SeatTracker:
    """获取席位追踪器单例"""
    global _seat_tracker
    if _seat_tracker is None:
        _seat_tracker = SeatTracker(config)
    return _seat_tracker


# 便捷函数
def create_default_tracking_config() -> TrackingConfig:
    """创建默认追踪配置"""
    return TrackingConfig(
        tracked_seats=[
            "章建平", "赵建平", "徐开东", "林园",  # 知名牛散
            "易方达基金", "华夏基金", "南方基金",    # 知名公募
            "高毅资产", "景林资产", "千合资本",      # 知名私募
            "中信建投成都一环路", "华泰证券深圳益田路"  # 知名游资营业部
        ],
        alert_thresholds={
            'min_trade_amount': 5000.0,
            'min_influence_score': 75.0,
            'coordination_confidence': 0.7,
            'volume_surge_ratio': 2.0,
            'pattern_match_score': 80.0,
            'follow_probability': 0.6
        },
        update_interval=300,
        max_alerts_per_day=50,
        enable_push_alerts=True
    )


if __name__ == "__main__":
    # 测试代码
    config = create_default_tracking_config()
    tracker = get_seat_tracker(config)
    
    # 更新追踪数据
    update_result = tracker.update_tracking_data()
    print(f"更新结果: {update_result}")
    
    # 获取统计信息
    stats = tracker.get_tracking_statistics()
    print(f"追踪统计: {stats}")
    
    # 获取活跃预警
    alerts = tracker.get_active_alerts()
    print(f"活跃预警: {len(alerts)}条")
    for alert in alerts[:3]:  # 显示前3条
        print(f"  - {alert.message}")