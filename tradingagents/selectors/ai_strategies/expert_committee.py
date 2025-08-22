#!/usr/bin/env python3
"""
AI专家委员会选股系统
整合现有的AI分析师，形成协作决策机制
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import statistics
import json

from tradingagents.utils.logging_manager import get_logger
from tradingagents.analytics.comprehensive_scoring_system import get_comprehensive_scoring_system
from tradingagents.graph.trading_graph import TradingAgentsGraph

logger = get_logger('agents')


@dataclass
class ExpertAnalysisResult:
    """AI专家分析结果"""
    expert_name: str                    # 专家名称
    symbol: str                         # 股票代码
    score: float                        # 专家评分 (0-100)
    confidence: float                   # 置信度 (0-1)
    recommendation: str                 # 投资建议
    key_insights: List[str]             # 关键见解
    analysis_details: Dict[str, Any]    # 详细分析结果
    processing_time: float              # 处理时间
    timestamp: datetime                 # 分析时间


class AIExpertCommittee:
    """AI专家委员会选股系统"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化AI专家委员会
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 专家权重配置
        self.expert_weights = {
            'market_analyst': 0.20,        # 市场分析师 20%
            'fundamentals_analyst': 0.25,  # 基本面分析师 25%
            'news_analyst': 0.15,          # 新闻分析师 15%
            'social_analyst': 0.10,        # 社交媒体分析师 10%
            'heat_analyst': 0.15,          # 热度分析师 15%
            'comprehensive_scorer': 0.15   # 综合评分系统 15%
        }
        
        # 一致性阈值配置
        self.consensus_thresholds = {
            'strong_buy': 0.8,      # 强烈推荐阈值
            'buy': 0.65,            # 推荐阈值
            'hold': 0.4,            # 持有阈值
            'sell': 0.2,            # 卖出阈值
            'min_confidence': 0.6   # 最低置信度要求
        }
        
        # 初始化组件
        self.trading_graph = None
        self.scoring_system = get_comprehensive_scoring_system()
        
        # 专家分析历史
        self.analysis_history = {}
        
        logger.info("AI专家委员会初始化完成")
        logger.info(f"   专家数量: {len(self.expert_weights)}")
        logger.info(f"   专家权重: {self.expert_weights}")

    def _get_trading_graph(self) -> TradingAgentsGraph:
        """获取交易图实例"""
        if self.trading_graph is None:
            # 使用所有分析师
            selected_analysts = ["market", "social", "news", "fundamentals", "heat"]
            self.trading_graph = TradingAgentsGraph(
                selected_analysts=selected_analysts,
                debug=False,
                config=self.config
            )
        return self.trading_graph

    def switch_ai_model(self, model_key: str) -> bool:
        """
        切换AI模型
        
        Args:
            model_key: 模型键值
            
        Returns:
            是否切换成功
        """
        try:
            logger.info(f"🔄 [AI专家委员会] 切换AI模型: {model_key}")
            
            # 如果已有交易图实例，则切换其模型
            if self.trading_graph:
                success = self.trading_graph.switch_llm_model(model_key)
                if success:
                    logger.info(f"✅ [AI专家委员会] 模型切换成功: {model_key}")
                    return True
                else:
                    logger.error(f"❌ [AI专家委员会] 模型切换失败: {model_key}")
                    return False
            else:
                # 如果没有交易图实例，先创建一个并设置模型
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                success = llm_manager.set_current_model(model_key)
                if success:
                    logger.info(f"✅ [AI专家委员会] 预设模型成功: {model_key}")
                    return True
                else:
                    logger.error(f"❌ [AI专家委员会] 预设模型失败: {model_key}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ [AI专家委员会] 模型切换异常: {e}")
            return False

    def get_available_ai_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的AI模型列表"""
        try:
            from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
            llm_manager = get_llm_manager()
            return llm_manager.get_enabled_models()
        except Exception as e:
            logger.error(f"❌ [AI专家委员会] 获取可用模型失败: {e}")
            return {}

    def get_current_ai_model_info(self) -> Optional[Dict[str, Any]]:
        """获取当前AI模型信息"""
        try:
            if self.trading_graph:
                return self.trading_graph.get_current_model_info()
            else:
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                current_config = llm_manager.get_current_config()
                if current_config:
                    return {
                        'provider': current_config.provider,
                        'model_name': current_config.model_name,
                        'display_name': current_config.display_name,
                        'description': current_config.description,
                        'temperature': current_config.temperature,
                        'max_tokens': current_config.max_tokens
                    }
                return None
        except Exception as e:
            logger.error(f"❌ [AI专家委员会] 获取当前模型信息失败: {e}")
            return None

    def analyze_stock_committee(self, symbol: str, 
                              stock_data: Dict[str, Any] = None,
                              news_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        专家委员会股票分析
        
        Args:
            symbol: 股票代码
            stock_data: 股票数据
            news_data: 新闻数据
            
        Returns:
            委员会分析结果
        """
        try:
            start_time = datetime.now()
            logger.info(f"🤖 [AI专家委员会] 开始分析股票: {symbol}")
            
            # 收集专家分析结果
            expert_results = {}
            
            # 1. 获取TradingAgents分析结果
            trading_analysis = self._get_trading_agents_analysis(symbol)
            if trading_analysis:
                expert_results.update(trading_analysis)
            
            # 2. 获取综合评分系统结果
            if stock_data:
                scoring_result = self._get_comprehensive_scoring_analysis(symbol, stock_data, news_data)
                if scoring_result:
                    expert_results['comprehensive_scorer'] = scoring_result
            
            # 3. 计算委员会一致性决策
            committee_decision = self._calculate_committee_consensus(expert_results)
            
            # 4. 生成最终推荐
            final_recommendation = self._generate_final_recommendation(symbol, expert_results, committee_decision)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 构造完整结果
            result = {
                'symbol': symbol,
                'committee_decision': committee_decision,
                'expert_analyses': expert_results,
                'final_recommendation': final_recommendation,
                'consensus_metrics': self._calculate_consensus_metrics(expert_results),
                'processing_time': processing_time,
                'timestamp': datetime.now(),
                'metadata': {
                    'experts_count': len(expert_results),
                    'data_sources': list(stock_data.keys()) if stock_data else [],
                    'version': '2.0'
                }
            }
            
            # 更新历史记录
            self._update_analysis_history(symbol, result)
            
            logger.info(f"🤖 [AI专家委员会] 分析完成: {symbol} - {committee_decision['recommendation']} (置信度: {committee_decision['confidence']:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ [AI专家委员会] 分析失败: {symbol} - {str(e)}")
            return self._create_error_result(symbol, str(e))

    def _get_trading_agents_analysis(self, symbol: str) -> Dict[str, ExpertAnalysisResult]:
        """获取TradingAgents多专家分析"""
        try:
            logger.debug(f"📊 调用TradingAgents分析: {symbol}")
            
            trading_graph = self._get_trading_graph()
            
            # 执行分析流程
            current_date = datetime.now().strftime('%Y-%m-%d')
            final_state, processed_signal = trading_graph.propagate(symbol, current_date)
            
            expert_results = {}
            
            # 提取各专家分析结果
            if 'market_report' in final_state:
                expert_results['market_analyst'] = self._parse_analyst_result(
                    'market_analyst', symbol, final_state['market_report']
                )
            
            if 'fundamentals_report' in final_state:
                expert_results['fundamentals_analyst'] = self._parse_analyst_result(
                    'fundamentals_analyst', symbol, final_state['fundamentals_report']
                )
            
            if 'news_report' in final_state:
                expert_results['news_analyst'] = self._parse_analyst_result(
                    'news_analyst', symbol, final_state['news_report']
                )
            
            if 'sentiment_report' in final_state:
                expert_results['social_analyst'] = self._parse_analyst_result(
                    'social_analyst', symbol, final_state['sentiment_report']
                )
            
            if 'heat_report' in final_state:
                expert_results['heat_analyst'] = self._parse_analyst_result(
                    'heat_analyst', symbol, final_state['heat_report']
                )
            
            logger.debug(f"📊 TradingAgents分析完成，获得 {len(expert_results)} 个专家结果")
            return expert_results
            
        except Exception as e:
            logger.warning(f"⚠️ TradingAgents分析失败: {e}")
            return {}

    def _get_comprehensive_scoring_analysis(self, symbol: str, 
                                          stock_data: Dict[str, Any],
                                          news_data: List[Dict[str, Any]] = None) -> ExpertAnalysisResult:
        """获取综合评分系统分析"""
        try:
            logger.debug(f"📈 调用综合评分系统: {symbol}")
            
            score_result = self.scoring_system.calculate_comprehensive_score(
                symbol, stock_data, news_data
            )
            
            # 转换为专家分析结果格式
            expert_result = ExpertAnalysisResult(
                expert_name='comprehensive_scorer',
                symbol=symbol,
                score=score_result.overall_score,
                confidence=score_result.confidence,
                recommendation=score_result.recommendation,
                key_insights=[
                    f"综合评级: {score_result.grade}",
                    f"风险级别: {score_result.risk_level}"
                ] + score_result.key_factors[:3],
                analysis_details={
                    'category_scores': {
                        cat.value: {
                            'score': score.score,
                            'confidence': score.confidence,
                            'weight': score.weight
                        }
                        for cat, score in score_result.category_scores.items()
                    },
                    'grade': score_result.grade,
                    'risk_level': score_result.risk_level
                },
                processing_time=0.5,  # 估算处理时间
                timestamp=score_result.timestamp
            )
            
            logger.debug(f"📈 综合评分分析完成: {score_result.overall_score:.2f}")
            return expert_result
            
        except Exception as e:
            logger.warning(f"⚠️ 综合评分分析失败: {e}")
            return None

    def _parse_analyst_result(self, analyst_name: str, symbol: str, report: str) -> ExpertAnalysisResult:
        """解析分析师报告为专家结果格式"""
        try:
            # 提取评分和建议 (简化实现)
            score = self._extract_score_from_report(report)
            confidence = self._extract_confidence_from_report(report)
            recommendation = self._extract_recommendation_from_report(report)
            key_insights = self._extract_key_insights_from_report(report)
            
            return ExpertAnalysisResult(
                expert_name=analyst_name,
                symbol=symbol,
                score=score,
                confidence=confidence,
                recommendation=recommendation,
                key_insights=key_insights,
                analysis_details={'raw_report': report},
                processing_time=1.0,  # 估算
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"⚠️ 解析分析师报告失败 {analyst_name}: {e}")
            # 返回默认结果
            return ExpertAnalysisResult(
                expert_name=analyst_name,
                symbol=symbol,
                score=50.0,
                confidence=0.5,
                recommendation="观望",
                key_insights=["数据解析失败"],
                analysis_details={'error': str(e)},
                processing_time=0.1,
                timestamp=datetime.now()
            )

    def _extract_score_from_report(self, report: str) -> float:
        """从报告中提取评分"""
        try:
            # 首先尝试从报告中提取数值评分
            import re
            
            # 查找明确的评分模式
            score_patterns = [
                r'评分[:：]\s*(\d+(?:\.\d+)?)',
                r'得分[:：]\s*(\d+(?:\.\d+)?)',
                r'分数[:：]\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)分',
                r'(\d+(?:\.\d+)?)/100',
                r'综合评分.*?(\d+(?:\.\d+)?)'
            ]
            
            for pattern in score_patterns:
                matches = re.findall(pattern, report, re.IGNORECASE)
                if matches:
                    score = float(matches[0])
                    # 确保分数在合理范围内
                    if 0 <= score <= 100:
                        return score
                    elif score > 100:  # 可能是百分比
                        return min(score / 10, 100)
            
            # 如果没有找到明确评分，使用关键词分析
            positive_keywords = ['推荐', '买入', '看涨', '积极', '上涨', '增长', '利好', '强烈推荐', '优秀', '良好']
            negative_keywords = ['卖出', '看跌', '下跌', '风险', '亏损', '不推荐', '谨慎', '避免', '警告']
            
            # 计算关键词权重
            positive_score = 0
            negative_score = 0
            
            for word in positive_keywords:
                count = report.count(word)
                if word in ['强烈推荐', '优秀']:
                    positive_score += count * 8  # 高权重词
                elif word in ['推荐', '买入', '看涨']:
                    positive_score += count * 6
                else:
                    positive_score += count * 3
            
            for word in negative_keywords:
                count = report.count(word)
                if word in ['不推荐', '避免', '警告']:
                    negative_score += count * 8  # 高权重词
                elif word in ['卖出', '看跌', '风险']:
                    negative_score += count * 6
                else:
                    negative_score += count * 3
            
            # 计算最终评分
            score_delta = positive_score - negative_score
            base_score = 50 + score_delta * 2
            
            return max(15, min(90, base_score))
            
        except Exception as e:
            logger.debug(f"评分提取失败: {e}")
            return 50.0  # 默认中性评分

    def _extract_confidence_from_report(self, report: str) -> float:
        """从报告中提取置信度"""
        try:
            import re
            
            # 首先尝试从报告中提取明确的置信度数值
            confidence_patterns = [
                r'置信度[:：]\s*(\d+(?:\.\d+)?)%',
                r'信心度[:：]\s*(\d+(?:\.\d+)?)%',
                r'确信度[:：]\s*(\d+(?:\.\d+)?)%',
                r'置信度[:：]\s*(\d+(?:\.\d+)?)',
                r'可信度[:：]\s*(\d+(?:\.\d+)?)'
            ]
            
            for pattern in confidence_patterns:
                matches = re.findall(pattern, report, re.IGNORECASE)
                if matches:
                    confidence = float(matches[0])
                    if confidence <= 1.0:  # 0-1范围
                        return max(0.1, min(1.0, confidence))
                    elif confidence <= 100:  # 百分比形式
                        return max(0.1, min(1.0, confidence / 100))
            
            # 基于内容质量分析计算置信度
            report_length = len(report)
            
            # 基础置信度：基于报告长度
            if report_length > 800:
                base_confidence = 0.8
            elif report_length > 400:
                base_confidence = 0.7
            elif report_length > 200:
                base_confidence = 0.6
            else:
                base_confidence = 0.4
            
            # 高置信度关键词
            high_confidence_keywords = ['确信', '明确', '肯定', '强烈', '显著', '清晰', '确定', '毫无疑问']
            medium_confidence_keywords = ['认为', '预计', '预期', '判断', '分析显示', '数据表明']
            low_confidence_keywords = ['可能', '或许', '大概', '也许', '不确定', '有待观察', '需要关注']
            
            confidence_boost = 0
            confidence_penalty = 0
            
            for word in high_confidence_keywords:
                confidence_boost += report.count(word) * 0.15
            
            for word in medium_confidence_keywords:
                confidence_boost += report.count(word) * 0.08
                
            for word in low_confidence_keywords:
                confidence_penalty += report.count(word) * 0.12
            
            # 数据支撑度分析
            data_keywords = ['数据', '指标', '财报', '业绩', '统计', '图表', '分析']
            data_support = sum(report.count(word) for word in data_keywords) * 0.05
            
            # 计算最终置信度
            final_confidence = base_confidence + confidence_boost - confidence_penalty + data_support
            return max(0.15, min(0.95, final_confidence))
            
        except Exception as e:
            logger.debug(f"置信度提取失败: {e}")
            return 0.6  # 默认中等置信度

    def _extract_recommendation_from_report(self, report: str) -> str:
        """从报告中提取投资建议"""
        try:
            import re
            
            # 首先查找明确的建议语句
            recommendation_patterns = [
                r'建议[:：]\s*(强烈推荐|推荐|买入|增持|持有|观望|减持|卖出)',
                r'投资建议[:：]\s*(强烈推荐|推荐|买入|增持|持有|观望|减持|卖出)',
                r'操作建议[:：]\s*(强烈推荐|推荐|买入|增持|持有|观望|减持|卖出)',
                r'(强烈推荐|推荐|买入|增持|持有|观望|减持|卖出)该股'
            ]
            
            for pattern in recommendation_patterns:
                matches = re.findall(pattern, report, re.IGNORECASE)
                if matches:
                    recommendation = matches[0]
                    return self._normalize_recommendation(recommendation)
            
            # 如果没有找到明确建议，通过关键词权重分析
            recommendation_weights = {
                '强烈推荐': ['强烈推荐', '重点推荐', '首推'],
                '推荐': ['推荐', '买入', '增持', '建议买入', '值得关注'],
                '持有': ['持有', '维持', '中性', '等待'],
                '观望': ['观望', '谨慎', '关注', '待定'],
                '不推荐': ['不推荐', '避免', '减持', '卖出', '建议卖出']
            }
            
            max_weight = 0
            best_recommendation = '观望'
            
            for recommendation, keywords in recommendation_weights.items():
                weight = sum(report.count(keyword) for keyword in keywords)
                if weight > max_weight:
                    max_weight = weight
                    best_recommendation = recommendation
            
            return best_recommendation if max_weight > 0 else '观望'
            
        except Exception as e:
            logger.debug(f"投资建议提取失败: {e}")
            return '观望'
    
    def _normalize_recommendation(self, recommendation: str) -> str:
        """标准化投资建议"""
        recommendation = recommendation.strip().lower()
        
        if recommendation in ['强烈推荐', '重点推荐', '首推']:
            return '强烈推荐'
        elif recommendation in ['推荐', '买入', '增持', '建议买入']:
            return '推荐'
        elif recommendation in ['持有', '维持', '中性']:
            return '持有'
        elif recommendation in ['不推荐', '避免', '减持', '卖出', '建议卖出']:
            return '不推荐'
        else:
            return '观望'

    def _extract_key_insights_from_report(self, report: str) -> List[str]:
        """从报告中提取关键见解"""
        insights = []
        
        # 查找关键句子模式
        sentences = report.split('。')
        
        for sentence in sentences[:5]:  # 只看前5句
            sentence = sentence.strip()
            if len(sentence) > 10 and any(keyword in sentence for keyword in 
                ['分析', '显示', '表明', '预期', '建议', '认为', '预测']):
                insights.append(sentence[:50] + '...' if len(sentence) > 50 else sentence)
        
        return insights[:3] if insights else ['暂无关键见解']

    def _calculate_committee_consensus(self, expert_results: Dict[str, ExpertAnalysisResult]) -> Dict[str, Any]:
        """计算专家委员会一致性决策"""
        try:
            if not expert_results:
                return self._create_default_consensus()
            
            # 收集所有专家评分和建议
            scores = []
            recommendations = []
            confidences = []
            weights = []
            
            for expert_name, result in expert_results.items():
                if expert_name in self.expert_weights:
                    weight = self.expert_weights[expert_name]
                    scores.append(result.score * weight)
                    recommendations.append(result.recommendation)
                    confidences.append(result.confidence * weight)
                    weights.append(weight)
            
            if not scores:
                return self._create_default_consensus()
            
            # 计算加权评分
            total_weight = sum(weights)
            weighted_score = sum(scores) / total_weight if total_weight > 0 else 50
            weighted_confidence = sum(confidences) / total_weight if total_weight > 0 else 0.5
            
            # 统计建议分布
            recommendation_counts = {}
            for rec in recommendations:
                recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
            
            # 确定最终建议
            if weighted_score >= self.consensus_thresholds['strong_buy']:
                final_recommendation = '强烈推荐'
            elif weighted_score >= self.consensus_thresholds['buy']:
                final_recommendation = '推荐'
            elif weighted_score >= self.consensus_thresholds['hold']:
                final_recommendation = '持有'
            elif weighted_score >= self.consensus_thresholds['sell']:
                final_recommendation = '观望'
            else:
                final_recommendation = '不推荐'
            
            # 计算一致性指标
            consensus_level = self._calculate_consensus_level(expert_results)
            
            return {
                'score': round(weighted_score, 2),
                'confidence': round(weighted_confidence, 3),
                'recommendation': final_recommendation,
                'consensus_level': consensus_level,
                'expert_agreement': recommendation_counts,
                'participating_experts': list(expert_results.keys()),
                'decision_factors': self._extract_decision_factors(expert_results)
            }
            
        except Exception as e:
            logger.error(f"❌ 计算委员会一致性失败: {e}")
            return self._create_default_consensus()

    def _calculate_consensus_level(self, expert_results: Dict[str, ExpertAnalysisResult]) -> str:
        """计算一致性水平"""
        if len(expert_results) < 2:
            return '单一意见'
        
        scores = [result.score for result in expert_results.values()]
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0
        
        if score_std < 10:
            return '高度一致'
        elif score_std < 20:
            return '基本一致'
        elif score_std < 30:
            return '存在分歧'
        else:
            return '意见分化'

    def _extract_decision_factors(self, expert_results: Dict[str, ExpertAnalysisResult]) -> List[str]:
        """提取决策关键因素"""
        factors = []
        
        # 从每个专家提取关键见解
        for expert_name, result in expert_results.items():
            if result.key_insights:
                best_insight = result.key_insights[0]  # 取第一个见解
                factors.append(f"{expert_name}: {best_insight}")
        
        return factors[:5]  # 限制为5个因素

    def _generate_final_recommendation(self, symbol: str, 
                                     expert_results: Dict[str, ExpertAnalysisResult],
                                     committee_decision: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终投资建议"""
        try:
            recommendation = {
                'symbol': symbol,
                'action': committee_decision['recommendation'],
                'confidence_level': committee_decision['confidence'],
                'consensus_strength': committee_decision['consensus_level'],
                'key_reasons': committee_decision['decision_factors'][:3],
                'risk_assessment': self._assess_investment_risk(expert_results),
                'suggested_allocation': self._suggest_position_allocation(committee_decision),
                'monitoring_points': self._identify_monitoring_points(expert_results),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ 生成最终建议失败: {e}")
            return {
                'symbol': symbol,
                'action': '观望',
                'confidence_level': 0.3,
                'error': str(e)
            }

    def _assess_investment_risk(self, expert_results: Dict[str, ExpertAnalysisResult]) -> str:
        """评估投资风险"""
        # 基于专家一致性和置信度评估风险
        confidences = [result.confidence for result in expert_results.values()]
        avg_confidence = statistics.mean(confidences) if confidences else 0.5
        
        if avg_confidence > 0.8:
            return '低风险'
        elif avg_confidence > 0.6:
            return '中等风险'
        else:
            return '高风险'

    def _suggest_position_allocation(self, committee_decision: Dict[str, Any]) -> str:
        """建议仓位分配"""
        score = committee_decision['score']
        confidence = committee_decision['confidence']
        
        # 基于评分和置信度建议仓位
        position_factor = (score / 100) * confidence
        
        if position_factor > 0.8:
            return '重仓 (30-50%)'
        elif position_factor > 0.65:
            return '中等仓位 (15-30%)'
        elif position_factor > 0.4:
            return '轻仓 (5-15%)'
        else:
            return '观望 (0%)'

    def _identify_monitoring_points(self, expert_results: Dict[str, ExpertAnalysisResult]) -> List[str]:
        """识别监控要点"""
        points = []
        
        # 基于专家分析结果提取监控点
        for expert_name, result in expert_results.items():
            if 'fundamentals' in expert_name:
                points.append('关注财务报表发布')
            elif 'news' in expert_name:
                points.append('跟踪相关新闻动态')
            elif 'market' in expert_name:
                points.append('监控技术指标变化')
            elif 'heat' in expert_name:
                points.append('观察市场热度波动')
        
        # 添加通用监控点
        points.append('关注大盘走势')
        points.append('留意政策变化')
        
        return list(set(points))[:4]  # 去重并限制数量

    def _calculate_consensus_metrics(self, expert_results: Dict[str, ExpertAnalysisResult]) -> Dict[str, Any]:
        """计算一致性指标"""
        if not expert_results:
            return {}
        
        scores = [result.score for result in expert_results.values()]
        confidences = [result.confidence for result in expert_results.values()]
        
        return {
            'score_average': round(statistics.mean(scores), 2),
            'score_median': round(statistics.median(scores), 2),
            'score_std': round(statistics.stdev(scores) if len(scores) > 1 else 0, 2),
            'confidence_average': round(statistics.mean(confidences), 3),
            'expert_count': len(expert_results),
            'agreement_ratio': self._calculate_agreement_ratio(expert_results)
        }

    def _calculate_agreement_ratio(self, expert_results: Dict[str, ExpertAnalysisResult]) -> float:
        """计算专家意见一致性比例"""
        if len(expert_results) < 2:
            return 1.0
        
        recommendations = [result.recommendation for result in expert_results.values()]
        most_common = max(set(recommendations), key=recommendations.count)
        agreement_count = recommendations.count(most_common)
        
        return round(agreement_count / len(recommendations), 3)

    def _create_default_consensus(self) -> Dict[str, Any]:
        """创建默认一致性结果"""
        return {
            'score': 50.0,
            'confidence': 0.3,
            'recommendation': '观望',
            'consensus_level': '数据不足',
            'expert_agreement': {},
            'participating_experts': [],
            'decision_factors': ['数据获取失败']
        }

    def _create_error_result(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'symbol': symbol,
            'committee_decision': self._create_default_consensus(),
            'expert_analyses': {},
            'final_recommendation': {
                'symbol': symbol,
                'action': '观望',
                'confidence_level': 0.1,
                'error': error_msg
            },
            'consensus_metrics': {},
            'processing_time': 0.0,
            'timestamp': datetime.now(),
            'error': True,
            'error_message': error_msg
        }

    def _update_analysis_history(self, symbol: str, result: Dict[str, Any]):
        """更新分析历史"""
        try:
            if symbol not in self.analysis_history:
                self.analysis_history[symbol] = []
            
            history = self.analysis_history[symbol]
            history.append({
                'timestamp': result['timestamp'],
                'recommendation': result['committee_decision']['recommendation'],
                'score': result['committee_decision']['score'],
                'confidence': result['committee_decision']['confidence']
            })
            
            # 保持最近20条记录
            if len(history) > 20:
                history.pop(0)
                
        except Exception as e:
            logger.debug(f"更新分析历史失败: {e}")

    def get_analysis_history(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """获取分析历史"""
        try:
            if symbol not in self.analysis_history:
                return {'error': '无历史数据'}
            
            history = self.analysis_history[symbol]
            cutoff_time = datetime.now().replace(hour=0, minute=0, second=0) - \
                         datetime.timedelta(days=days)
            
            recent_analyses = [
                h for h in history
                if h['timestamp'] >= cutoff_time
            ]
            
            if not recent_analyses:
                return {'error': f'无{days}天内的数据'}
            
            return {
                'symbol': symbol,
                'period_days': days,
                'analysis_count': len(recent_analyses),
                'recent_analyses': recent_analyses,
                'trend_analysis': self._analyze_recommendation_trend(recent_analyses)
            }
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {e}")
            return {'error': str(e)}

    def _analyze_recommendation_trend(self, analyses: List[Dict[str, Any]]) -> str:
        """分析建议趋势"""
        if len(analyses) < 2:
            return '数据不足'
        
        latest = analyses[-1]
        previous = analyses[-2]
        
        if latest['score'] > previous['score'] + 5:
            return '趋势向好'
        elif latest['score'] < previous['score'] - 5:
            return '趋势转差'
        else:
            return '趋势平稳'

    def batch_analyze_committee(self, symbols: List[str], 
                              stock_data_batch: Dict[str, Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """批量专家委员会分析"""
        try:
            logger.info(f"🤖 [AI专家委员会] 开始批量分析 {len(symbols)} 只股票")
            
            results = {}
            
            for symbol in symbols:
                try:
                    stock_data = stock_data_batch.get(symbol) if stock_data_batch else None
                    result = self.analyze_stock_committee(symbol, stock_data)
                    results[symbol] = result
                    
                    logger.debug(f"✅ 完成分析: {symbol}")
                    
                except Exception as e:
                    logger.error(f"❌ 分析失败: {symbol} - {e}")
                    results[symbol] = self._create_error_result(symbol, str(e))
            
            logger.info(f"🤖 [AI专家委员会] 批量分析完成，成功: {len([r for r in results.values() if not r.get('error')])} 只")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量分析失败: {e}")
            return {}