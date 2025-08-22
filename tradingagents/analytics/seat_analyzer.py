#!/usr/bin/env python3
"""
席位智能识别分析系统
识别和评估龙虎榜中的各类重要席位，包括知名牛散、公募基金、私募机构等
提供席位影响力评分和投资行为分析功能
"""

import re
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.longhubang_utils import SeatInfo, LongHuBangData

logger = get_logger('seat_analyzer')


class SeatType(Enum):
    """席位类型枚举"""
    FAMOUS_INVESTOR = "famous_investor"     # 知名牛散
    PUBLIC_FUND = "public_fund"            # 公募基金
    PRIVATE_FUND = "private_fund"          # 私募基金
    HOT_MONEY = "hot_money"                # 游资
    INSTITUTION = "institution"            # 机构专用
    SECURITIES_FIRM = "securities_firm"    # 券商自营
    RETAIL_BRANCH = "retail_branch"        # 散户营业部
    UNKNOWN = "unknown"                    # 未知类型


@dataclass
class SeatProfile:
    """席位档案"""
    name: str                              # 席位名称
    seat_type: SeatType                    # 席位类型
    influence_score: float                 # 影响力评分(0-100)
    success_rate: float                    # 历史成功率
    avg_holding_days: int                  # 平均持股天数
    preferred_sectors: List[str] = field(default_factory=list)  # 偏好行业
    trading_style: str = ""                # 交易风格
    description: str = ""                  # 描述信息
    aliases: List[str] = field(default_factory=list)  # 别名
    last_updated: str = ""                 # 最后更新时间


@dataclass
class SeatAnalysisResult:
    """席位分析结果"""
    seat_info: SeatInfo                    # 原始席位信息
    seat_profile: SeatProfile             # 席位档案
    analysis_score: float                 # 分析评分
    risk_level: str                       # 风险等级
    follow_suggestion: str                 # 跟随建议
    confidence: float                      # 置信度


class SeatAnalyzer:
    """席位智能分析器"""
    
    def __init__(self):
        """初始化席位分析器"""
        self.seat_database = {}
        self.seat_patterns = {}
        
        # 初始化席位数据库
        self._init_seat_database()
        self._init_seat_patterns()
        
        logger.info(f"✅ 席位分析器初始化成功，加载{len(self.seat_database)}个知名席位")
    
    def _init_seat_database(self):
        """初始化席位数据库"""
        
        # 知名牛散席位
        famous_investors = {
            "章建平": SeatProfile(
                name="章建平",
                seat_type=SeatType.FAMOUS_INVESTOR,
                influence_score=95.0,
                success_rate=0.68,
                avg_holding_days=15,
                preferred_sectors=["医药生物", "电子", "计算机"],
                trading_style="短线投机，善于捕捉热点题材",
                description="知名游资大佬，擅长题材炒作",
                aliases=["章盟主"]
            ),
            "赵建平": SeatProfile(
                name="赵建平", 
                seat_type=SeatType.FAMOUS_INVESTOR,
                influence_score=88.0,
                success_rate=0.62,
                avg_holding_days=20,
                preferred_sectors=["新能源", "医药", "军工"],
                trading_style="中短线结合，偏爱成长股",
                description="著名价值投资者，选股眼光独到"
            ),
            "徐开东": SeatProfile(
                name="徐开东",
                seat_type=SeatType.FAMOUS_INVESTOR, 
                influence_score=85.0,
                success_rate=0.58,
                avg_holding_days=12,
                preferred_sectors=["科技", "新材料"],
                trading_style="激进短线，追涨杀跌",
                description="知名短线客，操作凶悍"
            ),
            "林园": SeatProfile(
                name="林园",
                seat_type=SeatType.FAMOUS_INVESTOR,
                influence_score=92.0,
                success_rate=0.71,
                avg_holding_days=180,
                preferred_sectors=["消费", "医药", "白酒"],
                trading_style="长线价值投资，重仓白马股",
                description="价值投资代表人物，长期持股"
            )
        }
        
        # 知名公募基金
        public_funds = {
            "易方达基金": SeatProfile(
                name="易方达基金",
                seat_type=SeatType.PUBLIC_FUND,
                influence_score=88.0,
                success_rate=0.61,
                avg_holding_days=90,
                preferred_sectors=["科技", "消费", "医药"],
                trading_style="均衡配置，长期持有",
                description="国内顶级公募基金公司"
            ),
            "华夏基金": SeatProfile(
                name="华夏基金",
                seat_type=SeatType.PUBLIC_FUND,
                influence_score=85.0,
                success_rate=0.59,
                avg_holding_days=120,
                preferred_sectors=["金融", "地产", "基建"],
                trading_style="稳健投资，注重业绩",
                description="老牌基金公司，管理规模庞大"
            ),
            "南方基金": SeatProfile(
                name="南方基金",
                seat_type=SeatType.PUBLIC_FUND,
                influence_score=83.0,
                success_rate=0.57,
                avg_holding_days=100,
                preferred_sectors=["制造业", "新能源"],
                trading_style="价值投资为主，适度成长",
                description="综合性大型基金公司"
            ),
            "嘉实基金": SeatProfile(
                name="嘉实基金",
                seat_type=SeatType.PUBLIC_FUND,
                influence_score=82.0,
                success_rate=0.56,
                avg_holding_days=110,
                preferred_sectors=["科技", "消费"],
                trading_style="成长投资，重视研究",
                description="研究驱动的基金公司"
            )
        }
        
        # 知名私募机构
        private_funds = {
            "高毅资产": SeatProfile(
                name="高毅资产",
                seat_type=SeatType.PRIVATE_FUND,
                influence_score=92.0,
                success_rate=0.72,
                avg_holding_days=200,
                preferred_sectors=["消费", "医药", "科技"],
                trading_style="精选个股，长期持有",
                description="顶级私募机构，投资能力突出"
            ),
            "景林资产": SeatProfile(
                name="景林资产",
                seat_type=SeatType.PRIVATE_FUND,
                influence_score=89.0,
                success_rate=0.69,
                avg_holding_days=150,
                preferred_sectors=["消费", "互联网"],
                trading_style="深度研究，价值投资",
                description="老牌私募，投研实力强劲"
            ),
            "千合资本": SeatProfile(
                name="千合资本",
                seat_type=SeatType.PRIVATE_FUND,
                influence_score=86.0,
                success_rate=0.65,
                avg_holding_days=120,
                preferred_sectors=["科技", "新能源"],
                trading_style="量化与基本面结合",
                description="知名量化私募机构"
            ),
            "重阳投资": SeatProfile(
                name="重阳投资",
                seat_type=SeatType.PRIVATE_FUND,
                influence_score=87.0,
                success_rate=0.66,
                avg_holding_days=180,
                preferred_sectors=["金融", "地产", "能源"],
                trading_style="价值投资，逆向思维",
                description="价值投资典型代表"
            )
        }
        
        # 知名游资营业部
        hot_money_branches = {
            "中信建投成都一环路": SeatProfile(
                name="中信建投成都一环路",
                seat_type=SeatType.HOT_MONEY,
                influence_score=85.0,
                success_rate=0.58,
                avg_holding_days=3,
                preferred_sectors=["题材股", "次新股"],
                trading_style="超短线，炒作题材",
                description="知名游资营业部，操作激进"
            ),
            "华泰证券深圳益田路": SeatProfile(
                name="华泰证券深圳益田路",
                seat_type=SeatType.HOT_MONEY,
                influence_score=82.0,
                success_rate=0.55,
                avg_holding_days=5,
                preferred_sectors=["科技股", "概念股"],
                trading_style="短线投机，追热点",
                description="活跃游资席位"
            ),
            "国泰君安深圳宝安南路": SeatProfile(
                name="国泰君安深圳宝安南路",
                seat_type=SeatType.HOT_MONEY,
                influence_score=80.0,
                success_rate=0.52,
                avg_holding_days=4,
                preferred_sectors=["小盘股", "概念股"],
                trading_style="快进快出，炒作概念",
                description="游资聚集地"
            )
        }
        
        # 合并所有席位
        self.seat_database.update(famous_investors)
        self.seat_database.update(public_funds) 
        self.seat_database.update(private_funds)
        self.seat_database.update(hot_money_branches)
    
    def _init_seat_patterns(self):
        """初始化席位识别模式"""
        self.seat_patterns = {
            # 公募基金模式
            SeatType.PUBLIC_FUND: [
                r'.*基金.*', r'.*资管.*', r'.*投资.*基金.*',
                r'.*易方达.*', r'.*华夏.*', r'.*南方.*', r'.*嘉实.*',
                r'.*博时.*', r'.*广发.*', r'.*大成.*', r'.*富国.*',
                r'.*工银瑞信.*', r'.*建信.*', r'.*中银.*', r'.*招商.*'
            ],
            
            # 私募基金模式
            SeatType.PRIVATE_FUND: [
                r'.*私募.*', r'.*资产.*', r'.*投资.*公司.*',
                r'.*高毅.*', r'.*景林.*', r'.*千合.*', r'.*重阳.*',
                r'.*淡水泉.*', r'.*星石.*', r'.*朱雀.*', r'.*东方港湾.*'
            ],
            
            # 机构专用模式
            SeatType.INSTITUTION: [
                r'.*机构专用.*', r'.*机构.*', r'.*专用.*',
                r'.*QFII.*', r'.*社保.*', r'.*保险.*', r'.*年金.*'
            ],
            
            # 券商自营模式
            SeatType.SECURITIES_FIRM: [
                r'.*自营.*', r'.*投资.*自营.*',
                r'.*中信.*自营.*', r'.*华泰.*自营.*', r'.*国泰君安.*自营.*'
            ],
            
            # 游资模式（特定营业部）
            SeatType.HOT_MONEY: [
                r'.*成都.*一环路.*', r'.*深圳.*益田路.*', r'.*宝安南路.*',
                r'.*温州.*', r'.*绍兴.*', r'.*杭州.*文三路.*',
                r'.*上海.*打浦路.*', r'.*北京.*安定路.*'
            ]
        }
    
    def identify_seat_type(self, seat_name: str) -> Tuple[SeatType, float]:
        """
        识别席位类型
        
        Args:
            seat_name: 席位名称
            
        Returns:
            (席位类型, 置信度)
        """
        # 首先查找已知席位数据库
        for known_name, profile in self.seat_database.items():
            if known_name in seat_name or seat_name in known_name:
                return profile.seat_type, 0.95
            
            # 检查别名
            for alias in profile.aliases:
                if alias in seat_name:
                    return profile.seat_type, 0.90
        
        # 使用模式匹配
        for seat_type, patterns in self.seat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, seat_name, re.IGNORECASE):
                    confidence = 0.7 if seat_type == SeatType.HOT_MONEY else 0.8
                    return seat_type, confidence
        
        # 默认为散户营业部
        return SeatType.RETAIL_BRANCH, 0.3
    
    def get_seat_profile(self, seat_name: str) -> Optional[SeatProfile]:
        """
        获取席位档案
        
        Args:
            seat_name: 席位名称
            
        Returns:
            席位档案或None
        """
        # 精确匹配
        if seat_name in self.seat_database:
            return self.seat_database[seat_name]
        
        # 模糊匹配
        for known_name, profile in self.seat_database.items():
            if known_name in seat_name or seat_name in known_name:
                return profile
            
            # 检查别名
            for alias in profile.aliases:
                if alias in seat_name:
                    return profile
        
        return None
    
    def calculate_seat_influence_score(self, seat_info: SeatInfo) -> float:
        """
        计算席位影响力评分
        
        Args:
            seat_info: 席位信息
            
        Returns:
            影响力评分(0-100)
        """
        base_score = 50.0
        
        # 获取席位档案
        profile = self.get_seat_profile(seat_info.seat_name)
        if profile:
            base_score = profile.influence_score
        else:
            # 根据席位类型给基础分
            seat_type, confidence = self.identify_seat_type(seat_info.seat_name)
            type_scores = {
                SeatType.FAMOUS_INVESTOR: 85.0,
                SeatType.PRIVATE_FUND: 75.0,
                SeatType.PUBLIC_FUND: 70.0,
                SeatType.INSTITUTION: 65.0,
                SeatType.HOT_MONEY: 60.0,
                SeatType.SECURITIES_FIRM: 55.0,
                SeatType.RETAIL_BRANCH: 30.0,
                SeatType.UNKNOWN: 25.0
            }
            base_score = type_scores.get(seat_type, 50.0) * confidence
        
        # 根据交易金额调整
        trade_amount = max(seat_info.buy_amount, seat_info.sell_amount)
        if trade_amount > 50000:  # 超过5亿
            base_score += 15
        elif trade_amount > 20000:  # 超过2亿
            base_score += 10
        elif trade_amount > 10000:  # 超过1亿
            base_score += 5
        
        # 根据净买入比例调整
        total_amount = seat_info.buy_amount + seat_info.sell_amount
        if total_amount > 0:
            net_ratio = abs(seat_info.net_amount) / total_amount
            if net_ratio > 0.8:  # 单向交易
                base_score += 5
        
        return min(100.0, max(0.0, base_score))
    
    def analyze_seat_pattern(self, seats: List[SeatInfo]) -> Dict[str, Any]:
        """
        分析席位模式
        
        Args:
            seats: 席位列表
            
        Returns:
            席位模式分析结果
        """
        if not seats:
            return {"pattern": "无数据", "confidence": 0.0}
        
        # 统计席位类型分布
        type_stats = {}
        total_amount = 0
        
        for seat in seats:
            seat_type, confidence = self.identify_seat_type(seat.seat_name)
            if seat_type not in type_stats:
                type_stats[seat_type] = {
                    "count": 0,
                    "amount": 0,
                    "confidence": 0
                }
            
            type_stats[seat_type]["count"] += 1
            type_stats[seat_type]["amount"] += max(seat.buy_amount, seat.sell_amount)
            type_stats[seat_type]["confidence"] += confidence
            total_amount += max(seat.buy_amount, seat.sell_amount)
        
        # 计算各类型占比
        for seat_type in type_stats:
            type_stats[seat_type]["amount_ratio"] = type_stats[seat_type]["amount"] / total_amount if total_amount > 0 else 0
            type_stats[seat_type]["avg_confidence"] = type_stats[seat_type]["confidence"] / type_stats[seat_type]["count"]
        
        # 判断主导模式
        dominant_type = max(type_stats.keys(), key=lambda x: type_stats[x]["amount_ratio"])
        dominant_ratio = type_stats[dominant_type]["amount_ratio"]
        
        # 生成模式描述
        if dominant_ratio > 0.6:
            if dominant_type == SeatType.FAMOUS_INVESTOR:
                pattern = "知名投资者主导"
            elif dominant_type == SeatType.PRIVATE_FUND:
                pattern = "私募机构主导"
            elif dominant_type == SeatType.PUBLIC_FUND:
                pattern = "公募基金主导"
            elif dominant_type == SeatType.HOT_MONEY:
                pattern = "游资主导"
            elif dominant_type == SeatType.INSTITUTION:
                pattern = "机构主导"
            else:
                pattern = "散户主导"
        elif len(type_stats) >= 3:
            pattern = "多方博弈"
        else:
            pattern = "混合模式"
        
        return {
            "pattern": pattern,
            "dominant_type": dominant_type.value,
            "dominant_ratio": dominant_ratio,
            "type_distribution": {t.value: stats for t, stats in type_stats.items()},
            "confidence": type_stats[dominant_type]["avg_confidence"],
            "analysis_summary": self._generate_pattern_summary(type_stats, pattern)
        }
    
    def _generate_pattern_summary(self, type_stats: Dict, pattern: str) -> str:
        """生成模式分析摘要"""
        summary_parts = [f"席位模式: {pattern}"]
        
        # 按金额排序显示前3个类型
        sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["amount_ratio"], reverse=True)[:3]
        
        for seat_type, stats in sorted_types:
            if stats["amount_ratio"] > 0.1:  # 占比超过10%才显示
                summary_parts.append(f"{seat_type.value}: {stats['amount_ratio']:.1%}")
        
        return ", ".join(summary_parts)
    
    def analyze_buy_sell_battle(self, buy_seats: List[SeatInfo], sell_seats: List[SeatInfo]) -> Dict[str, Any]:
        """
        分析买卖双方实力对比
        
        Args:
            buy_seats: 买方席位
            sell_seats: 卖方席位
            
        Returns:
            实力对比分析结果
        """
        buy_analysis = self.analyze_seat_pattern(buy_seats)
        sell_analysis = self.analyze_seat_pattern(sell_seats)
        
        # 计算实力评分
        buy_power = sum(self.calculate_seat_influence_score(seat) * seat.buy_amount / 10000 for seat in buy_seats)
        sell_power = sum(self.calculate_seat_influence_score(seat) * seat.sell_amount / 10000 for seat in sell_seats)
        
        total_power = buy_power + sell_power
        if total_power > 0:
            buy_advantage = buy_power / total_power
            sell_advantage = sell_power / total_power
        else:
            buy_advantage = sell_advantage = 0.5
        
        # 判断胜负
        if buy_advantage > 0.6:
            battle_result = "买方占优"
            winner = "buy"
        elif sell_advantage > 0.6:
            battle_result = "卖方占优" 
            winner = "sell"
        else:
            battle_result = "势均力敌"
            winner = "balanced"
        
        # 计算置信度
        confidence = abs(buy_advantage - sell_advantage)
        
        return {
            "battle_result": battle_result,
            "winner": winner,
            "buy_power": buy_power,
            "sell_power": sell_power,
            "buy_advantage": buy_advantage,
            "sell_advantage": sell_advantage,
            "confidence": confidence,
            "buy_pattern": buy_analysis,
            "sell_pattern": sell_analysis,
            "recommendation": self._generate_battle_recommendation(battle_result, buy_analysis, sell_analysis, confidence)
        }
    
    def _generate_battle_recommendation(self, result: str, buy_analysis: Dict, sell_analysis: Dict, confidence: float) -> str:
        """生成实力对比建议"""
        if confidence > 0.3:  # 优势明显
            if result == "买方占优":
                if buy_analysis["dominant_type"] in ["famous_investor", "private_fund"]:
                    return "建议跟随，知名投资者看好"
                else:
                    return "谨慎跟随，注意游资炒作风险"
            elif result == "卖方占优":
                if sell_analysis["dominant_type"] in ["famous_investor", "private_fund"]:
                    return "建议观望，重要机构在减持"
                else:
                    return "可考虑逢低布局，可能是获利了结"
        
        return "建议观察，多空分歧较大"
    
    def detect_coordinated_trading(self, seats: List[SeatInfo]) -> Dict[str, Any]:
        """
        检测协同交易迹象
        
        Args:
            seats: 席位列表
            
        Returns:
            协同交易检测结果
        """
        if len(seats) < 2:
            return {"coordinated": False, "confidence": 0.0, "reason": "席位数量不足"}
        
        # 检查同一类型席位的集中度
        type_groups = {}
        for seat in seats:
            seat_type, _ = self.identify_seat_type(seat.seat_name)
            if seat_type not in type_groups:
                type_groups[seat_type] = []
            type_groups[seat_type].append(seat)
        
        # 检查是否有多个同类型席位
        coordinated_signals = []
        
        for seat_type, group_seats in type_groups.items():
            if len(group_seats) >= 3:  # 3个或更多同类型席位
                total_amount = sum(max(seat.buy_amount, seat.sell_amount) for seat in group_seats)
                avg_amount = total_amount / len(group_seats)
                
                if avg_amount > 5000:  # 平均超过5000万
                    coordinated_signals.append(f"{seat_type.value}类席位集中出现({len(group_seats)}个)")
        
        # 检查席位名称相似性（可能是同一资金的不同账户）
        similar_seats = self._find_similar_seat_names(seats)
        if similar_seats:
            coordinated_signals.extend(similar_seats)
        
        # 检查交易金额的规律性
        amounts = [max(seat.buy_amount, seat.sell_amount) for seat in seats]
        if len(amounts) >= 3:
            # 检查是否有明显的整数倍关系
            amounts.sort()
            for i in range(len(amounts) - 1):
                if amounts[i] > 0 and amounts[i+1] / amounts[i] > 1.8 and amounts[i+1] / amounts[i] < 2.2:
                    coordinated_signals.append("交易金额呈现规律性")
                    break
        
        coordinated = len(coordinated_signals) > 0
        confidence = min(0.9, len(coordinated_signals) * 0.3)
        
        return {
            "coordinated": coordinated,
            "confidence": confidence,
            "signals": coordinated_signals,
            "reason": "; ".join(coordinated_signals) if coordinated_signals else "未发现协同交易迹象"
        }
    
    def _find_similar_seat_names(self, seats: List[SeatInfo]) -> List[str]:
        """查找相似的席位名称"""
        similar_signals = []
        
        for i, seat1 in enumerate(seats):
            for j, seat2 in enumerate(seats[i+1:], i+1):
                # 计算名称相似度
                name1 = seat1.seat_name
                name2 = seat2.seat_name
                
                # 简单的相似度判断
                common_parts = []
                words1 = re.split(r'[^\w]', name1)
                words2 = re.split(r'[^\w]', name2)
                
                for word in words1:
                    if len(word) > 2 and word in name2:
                        common_parts.append(word)
                
                if len(common_parts) >= 2:
                    similar_signals.append(f"发现相似席位: {name1} 与 {name2}")
        
        return similar_signals
    
    def analyze_comprehensive_seats(self, longhubang_data: LongHuBangData) -> Dict[str, Any]:
        """
        对龙虎榜数据进行综合席位分析
        
        Args:
            longhubang_data: 龙虎榜数据
            
        Returns:
            综合分析结果
        """
        # 分析买方席位
        buy_results = []
        for seat in longhubang_data.buy_seats:
            profile = self.get_seat_profile(seat.seat_name)
            influence_score = self.calculate_seat_influence_score(seat)
            seat_type, confidence = self.identify_seat_type(seat.seat_name)
            
            buy_results.append(SeatAnalysisResult(
                seat_info=seat,
                seat_profile=profile,
                analysis_score=influence_score,
                risk_level=self._calculate_risk_level(seat_type, influence_score),
                follow_suggestion=self._generate_follow_suggestion(seat_type, influence_score, seat.buy_amount),
                confidence=confidence
            ))
        
        # 分析卖方席位
        sell_results = []
        for seat in longhubang_data.sell_seats:
            profile = self.get_seat_profile(seat.seat_name)
            influence_score = self.calculate_seat_influence_score(seat)
            seat_type, confidence = self.identify_seat_type(seat.seat_name)
            
            sell_results.append(SeatAnalysisResult(
                seat_info=seat,
                seat_profile=profile,
                analysis_score=influence_score,
                risk_level=self._calculate_risk_level(seat_type, influence_score),
                follow_suggestion=self._generate_follow_suggestion(seat_type, influence_score, seat.sell_amount),
                confidence=confidence
            ))
        
        # 进行对比分析
        battle_analysis = self.analyze_buy_sell_battle(longhubang_data.buy_seats, longhubang_data.sell_seats)
        
        # 检测协同交易
        all_seats = longhubang_data.buy_seats + longhubang_data.sell_seats
        coordination_analysis = self.detect_coordinated_trading(all_seats)
        
        # 计算综合评分
        overall_score = self._calculate_overall_score(buy_results, sell_results, battle_analysis)
        
        return {
            "symbol": longhubang_data.symbol,
            "name": longhubang_data.name,
            "buy_seat_analysis": buy_results,
            "sell_seat_analysis": sell_results,
            "battle_analysis": battle_analysis,
            "coordination_analysis": coordination_analysis,
            "overall_score": overall_score,
            "investment_suggestion": self._generate_investment_suggestion(overall_score, battle_analysis, coordination_analysis),
            "analysis_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_risk_level(self, seat_type: SeatType, influence_score: float) -> str:
        """计算风险等级"""
        if seat_type == SeatType.HOT_MONEY:
            return "高风险"
        elif seat_type in [SeatType.FAMOUS_INVESTOR, SeatType.PRIVATE_FUND] and influence_score > 80:
            return "中低风险"
        elif seat_type == SeatType.PUBLIC_FUND:
            return "低风险"
        elif influence_score > 70:
            return "中等风险"
        else:
            return "高风险"
    
    def _generate_follow_suggestion(self, seat_type: SeatType, influence_score: float, amount: float) -> str:
        """生成跟随建议"""
        if seat_type == SeatType.FAMOUS_INVESTOR and influence_score > 85:
            return "强烈建议跟随" if amount > 20000 else "建议跟随"
        elif seat_type == SeatType.PRIVATE_FUND and influence_score > 80:
            return "建议关注" if amount > 10000 else "可考虑跟随"
        elif seat_type == SeatType.HOT_MONEY:
            return "谨慎跟随，注意风险"
        elif seat_type == SeatType.PUBLIC_FUND:
            return "稳健跟随"
        else:
            return "观察为主"
    
    def _calculate_overall_score(self, buy_results: List[SeatAnalysisResult], 
                                sell_results: List[SeatAnalysisResult], 
                                battle_analysis: Dict) -> float:
        """计算综合评分"""
        base_score = 50.0
        
        # 买方席位加分
        for result in buy_results:
            if result.analysis_score > 80:
                base_score += 10
            elif result.analysis_score > 60:
                base_score += 5
        
        # 卖方席位减分
        for result in sell_results:
            if result.analysis_score > 80:
                base_score -= 8
            elif result.analysis_score > 60:
                base_score -= 4
        
        # 实力对比调整
        if battle_analysis["winner"] == "buy":
            base_score += 10 * battle_analysis["confidence"]
        elif battle_analysis["winner"] == "sell":
            base_score -= 10 * battle_analysis["confidence"]
        
        return min(100.0, max(0.0, base_score))
    
    def _generate_investment_suggestion(self, overall_score: float, 
                                      battle_analysis: Dict, 
                                      coordination_analysis: Dict) -> str:
        """生成投资建议"""
        suggestions = []
        
        if overall_score > 75:
            suggestions.append("综合评分较高，值得关注")
        elif overall_score < 25:
            suggestions.append("综合评分较低，建议谨慎")
        
        if battle_analysis["winner"] == "buy" and battle_analysis["confidence"] > 0.3:
            suggestions.append("买方实力占优，可考虑跟随")
        elif battle_analysis["winner"] == "sell" and battle_analysis["confidence"] > 0.3:
            suggestions.append("卖方实力占优，建议观望")
        
        if coordination_analysis["coordinated"]:
            suggestions.append("检测到协同交易迹象，需要额外关注")
        
        if not suggestions:
            suggestions.append("情况复杂，建议深入研究后决策")
        
        return "; ".join(suggestions)


# 全局实例
_seat_analyzer = None

def get_seat_analyzer() -> SeatAnalyzer:
    """获取席位分析器单例"""
    global _seat_analyzer
    if _seat_analyzer is None:
        _seat_analyzer = SeatAnalyzer()
    return _seat_analyzer


if __name__ == "__main__":
    # 测试代码
    analyzer = get_seat_analyzer()
    
    # 测试席位识别
    test_seats = ["章建平", "易方达基金", "高毅资产", "中信建投成都一环路"]
    for seat_name in test_seats:
        seat_type, confidence = analyzer.identify_seat_type(seat_name)
        profile = analyzer.get_seat_profile(seat_name)
        print(f"{seat_name}: {seat_type.value} (置信度: {confidence:.2f})")
        if profile:
            print(f"  影响力评分: {profile.influence_score}, 成功率: {profile.success_rate:.2f}")