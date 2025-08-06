"""
热度分析师Agent
基于多维度数据的热度分析和预警系统
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage
from ...analytics.heat_analyzer import HeatAnalyzer
from ...analytics.integration import HeatAnalysisIntegration

logger = logging.getLogger(__name__)


class HeatAnalystAgent:
    """热度分析师 - 专门负责市场热度分析和预警"""
    
    def __init__(self):
        self.name = "heat_analyst"
        self.description = "热度分析师 - 基于多维度数据的市场热度分析和预警专家"
        self.state = "idle"
        
        # 核心分析工具
        self.heat_analyzer = HeatAnalyzer()
        self.heat_integration = HeatAnalysisIntegration()
        
        # 分析配置
        self.config = {
            'high_heat_threshold': 80,    # 高热度阈值
            'medium_heat_threshold': 60,  # 中等热度阈值
            'alert_thresholds': {
                'volume_anomaly': 70,     # 成交量异动阈值
                'sentiment_shift': 0.5,    # 情绪突变阈值
                'heat_spike': 200          # 热度突增阈值
            }
        }
    
    def analyze_symbol(self, symbol: str, include_heat: bool = True) -> Dict[str, Any]:
        """
        分析单个股票的热度情况
        
        Args:
            symbol: 股票代码
            include_heat: 是否包含热度分析
            
        Returns:
            分析结果字典
        """
        try:
            self.state = "analyzing"
            logger.info(f"[HEAT_ANALYST] 开始分析 {symbol} 的热度数据")
            
            # 获取整合分析结果
            result = self.heat_integration.analyze_with_heat(symbol, include_heat)
            
            # 添加热度分析师的专业判断
            heat_analysis = self._generate_heat_insights(result)
            
            # 生成交易建议
            trading_recommendation = self._generate_trading_recommendation(heat_analysis)
            
            # 组装最终结果
            final_result = {
                'analyst': self.name,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'heat_analysis': heat_analysis,
                'trading_recommendation': trading_recommendation,
                'risk_assessment': self._assess_heat_risks(heat_analysis),
                'confidence': self._calculate_confidence(heat_analysis)
            }
            
            self.state = "completed"
            logger.info(f"[HEAT_ANALYST] {symbol} 热度分析完成")
            
            return final_result
            
        except Exception as e:
            self.state = "error"
            logger.error(f"[HEAT_ANALYST] 分析失败 {symbol}: {e}")
            return {
                'analyst': self.name,
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'state': 'error'
            }
    
    def batch_analyze(self, symbols: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        批量分析多个股票的热度情况
        
        Args:
            symbols: 股票代码列表
            limit: 返回结果数量限制
            
        Returns:
            批量分析结果
        """
        try:
            self.state = "analyzing"
            logger.info(f"[HEAT_ANALYST] 开始批量分析 {len(symbols)} 只股票")
            
            # 获取热度排行榜
            ranking = self.heat_analyzer.get_heat_ranking(symbols, limit)
            
            # 对每只股票进行详细分析
            detailed_results = []
            for stock_data in ranking:
                symbol = stock_data.get('symbol')
                if symbol:
                    detailed_result = self.analyze_symbol(symbol)
                    detailed_results.append(detailed_result)
            
            # 生成市场整体热度判断
            market_heat_summary = self._generate_market_heat_summary(ranking)
            
            result = {
                'analyst': self.name,
                'analysis_type': 'batch_heat_analysis',
                'timestamp': datetime.now().isoformat(),
                'market_heat_summary': market_heat_summary,
                'heat_ranking': ranking,
                'detailed_analysis': detailed_results,
                'total_symbols': len(symbols),
                'analyzed_symbols': len(detailed_results)
            }
            
            self.state = "completed"
            logger.info(f"[HEAT_ANALYST] 批量分析完成，共分析 {len(detailed_results)} 只股票")
            
            return result
            
        except Exception as e:
            self.state = "error"
            logger.error(f"[HEAT_ANALYST] 批量分析失败: {e}")
            return {
                'analyst': self.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'state': 'error'
            }
    
    def _generate_heat_insights(self, analysis_result: Dict) -> Dict[str, Any]:
        """生成热度洞察"""
        heat_data = analysis_result.get('heat_analysis', {})
        
        insights = {
            'heat_score': heat_data.get('heat_score', 0),
            'heat_level': heat_data.get('heat_level', '未知'),
            'key_signals': [],
            'market_attention': 'low',
            'trading_liquidity': 'normal',
            'risk_level': 'low'
        }
        
        # 解析热度信号
        alerts = heat_data.get('alerts', [])
        for alert in alerts:
            signal_type = alert.get('type', 'unknown')
            level = alert.get('level', 'low')
            message = alert.get('message', '')
            
            insights['key_signals'].append({
                'type': signal_type,
                'level': level,
                'message': message
            })
            
            # 根据信号调整风险等级
            if level == 'high':
                insights['risk_level'] = 'high'
            elif level == 'medium' and insights['risk_level'] != 'high':
                insights['risk_level'] = 'medium'
        
        # 根据热度分数判断市场关注度
        heat_score = insights['heat_score']
        if heat_score >= 80:
            insights['market_attention'] = 'very_high'
            insights['trading_liquidity'] = 'very_high'
        elif heat_score >= 60:
            insights['market_attention'] = 'high'
            insights['trading_liquidity'] = 'high'
        elif heat_score >= 40:
            insights['market_attention'] = 'medium'
            insights['trading_liquidity'] = 'medium'
        
        return insights
    
    def _generate_trading_recommendation(self, heat_insights: Dict) -> Dict[str, Any]:
        """基于热度分析生成交易建议"""
        heat_score = heat_insights.get('heat_score', 0)
        heat_level = heat_insights.get('heat_level', '未知')
        risk_level = heat_insights.get('risk_level', 'low')
        signals = heat_insights.get('key_signals', [])
        
        recommendation = {
            'action': 'hold',
            'confidence': 0.5,
            'reasoning': [],
            'time_horizon': 'short_term',
            'risk_warning': []
        }
        
        # 基于热度等级的基本判断
        if heat_score >= 80:
            recommendation['action'] = 'caution'
            recommendation['confidence'] = 0.8
            recommendation['reasoning'].append("市场热度极高，需警惕回调风险")
            recommendation['risk_warning'].append("高热度可能意味着短期过热")
            
        elif heat_score >= 60:
            recommendation['action'] = 'watch'
            recommendation['confidence'] = 0.7
            recommendation['reasoning'].append("市场热度较高，可关注但需谨慎")
            
        elif heat_score >= 40:
            recommendation['action'] = 'hold'
            recommendation['confidence'] = 0.6
            recommendation['reasoning'].append("市场热度适中，保持现有仓位")
            
        else:
            recommendation['action'] = 'accumulate'
            recommendation['confidence'] = 0.5
            recommendation['reasoning'].append("市场热度较低，可能存在布局机会")
        
        # 基于具体信号的调整
        for signal in signals:
            if signal['type'] == 'volume_anomaly' and signal['level'] == 'high':
                recommendation['action'] = 'caution'
                recommendation['confidence'] = min(recommendation['confidence'] + 0.1, 1.0)
                recommendation['reasoning'].append("成交量异常放大，需关注资金流向")
                
            elif signal['type'] == 'sentiment_shift':
                direction = "转暖" if '转暖' in signal['message'] else "转冷"
                if direction == "转暖":
                    recommendation['action'] = 'buy'
                    recommendation['confidence'] = min(recommendation['confidence'] + 0.1, 1.0)
                else:
                    recommendation['action'] = 'sell'
                    recommendation['confidence'] = min(recommendation['confidence'] + 0.1, 1.0)
                recommendation['reasoning'].append(f"市场情绪{direction}，调整策略")
        
        return recommendation
    
    def _assess_heat_risks(self, heat_insights: Dict) -> Dict[str, Any]:
        """评估热度相关风险"""
        risks = {
            'overall_risk': heat_insights.get('risk_level', 'low'),
            'specific_risks': [],
            'mitigation_suggestions': []
        }
        
        heat_score = heat_insights.get('heat_score', 0)
        
        # 高热度风险
        if heat_score >= 80:
            risks['specific_risks'].append({
                'type': 'overheating',
                'level': 'high',
                'description': '市场热度极高，存在短期回调风险'
            })
            risks['mitigation_suggestions'].append('建议减仓或设置止损')
        
        # 低热度风险
        elif heat_score < 20:
            risks['specific_risks'].append({
                'type': 'liquidity',
                'level': 'medium',
                'description': '市场关注度低，流动性可能不足'
            })
            risks['mitigation_suggestions'].append('分批建仓，避免大单冲击')
        
        # 信号相关风险
        for signal in heat_insights.get('key_signals', []):
            if signal['level'] == 'high':
                risks['specific_risks'].append({
                    'type': signal['type'],
                    'level': 'high',
                    'description': signal['message']
                })
        
        return risks
    
    def _calculate_confidence(self, heat_insights: Dict) -> float:
        """计算分析置信度"""
        base_confidence = 0.6
        
        # 基于热度信号数量调整
        signal_count = len(heat_insights.get('key_signals', []))
        signal_bonus = min(signal_count * 0.1, 0.3)
        
        # 基于热度分数调整
        heat_score = heat_insights.get('heat_score', 0)
        if 40 <= heat_score <= 80:
            score_bonus = 0.2  # 适中热度置信度更高
        else:
            score_bonus = 0.1
        
        confidence = base_confidence + signal_bonus + score_bonus
        return min(confidence, 1.0)
    
    def _generate_market_heat_summary(self, ranking: List[Dict]) -> Dict[str, Any]:
        """生成市场整体热度总结"""
        if not ranking:
            return {'status': 'no_data', 'message': '无热度数据'}
        
        total_stocks = len(ranking)
        high_heat_count = len([s for s in ranking if s.get('heat_score', 0) >= 60])
        medium_heat_count = len([s for s in ranking if 40 <= s.get('heat_score', 0) < 60])
        
        avg_heat_score = sum(s.get('heat_score', 0) for s in ranking) / total_stocks
        
        summary = {
            'total_analyzed': total_stocks,
            'average_heat_score': round(avg_heat_score, 2),
            'heat_distribution': {
                'high_heat': high_heat_count,
                'medium_heat': medium_heat_count,
                'low_heat': total_stocks - high_heat_count - medium_heat_count
            },
            'market_heat_status': self._get_market_heat_status(avg_heat_score),
            'top_heat_stocks': ranking[:3] if len(ranking) >= 3 else ranking
        }
        
        return summary
    
    def _get_market_heat_status(self, avg_score: float) -> str:
        """根据平均热度分数判断市场状态"""
        if avg_score >= 70:
            return "市场整体热度很高，需警惕过热风险"
        elif avg_score >= 50:
            return "市场热度适中，交易活跃"
        elif avg_score >= 30:
            return "市场热度偏低，关注度有限"
        else:
            return "市场热度很低，交投清淡"
    
    def get_state(self) -> Dict[str, Any]:
        """获取分析师状态"""
        return {
            'name': self.name,
            'description': self.description,
            'state': self.state,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset(self):
        """重置分析师状态"""
        self.state = "idle"
        logger.info(f"[HEAT_ANALYST] 分析师状态已重置")


def create_heat_analyst(llm, toolkit):
    """创建热度分析师节点函数"""
    def heat_analyst_node(state):
        logger.debug(f"🔥 [DEBUG] ===== 热度分析师节点开始 =====")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        logger.debug(f"🔥 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        
        try:
            # 创建热度分析师实例
            heat_analyst = HeatAnalystAgent()
            
            # 执行热度分析
            result = heat_analyst.analyze_symbol(ticker)
            
            # 生成热度分析报告
            if result.get('state') == 'error':
                report = f"热度分析失败: {result.get('error', '未知错误')}"
            else:
                heat_analysis = result.get('heat_analysis', {})
                trading_recommendation = result.get('trading_recommendation', {})
                risk_assessment = result.get('risk_assessment', {})
                
                report = f"""## 🔥 热度分析报告

### 基本信息
- **股票代码**: {ticker}
- **分析时间**: {current_date}
- **热度分数**: {heat_analysis.get('heat_score', 0)}
- **热度等级**: {heat_analysis.get('heat_level', '未知')}

### 热度指标分析
- **市场关注度**: {heat_analysis.get('market_attention', '未知')}
- **交易流动性**: {heat_analysis.get('trading_liquidity', '未知')}
- **风险等级**: {heat_analysis.get('risk_level', '未知')}

### 关键信号
{format_key_signals(heat_analysis.get('key_signals', []))}

### 交易建议
- **操作建议**: {format_trading_action(trading_recommendation.get('action', 'hold'))}
- **置信度**: {trading_recommendation.get('confidence', 0):.1%}
- **建议理由**: {format_reasoning(trading_recommendation.get('reasoning', []))}

### 风险评估
{format_risk_assessment(risk_assessment)}

### 投资建议
基于热度分析，建议采取{format_trading_action(trading_recommendation.get('action', 'hold'))}策略。"""
            
            logger.info(f"🔥 [热度分析师] 分析完成，报告长度: {len(report)}")
            
        except Exception as e:
            logger.error(f"❌ [热度分析师] 分析失败: {e}")
            report = f"热度分析失败: {str(e)}"
        
        logger.debug(f"🔥 [DEBUG] ===== 热度分析师节点结束 =====")
        
        return {
            "messages": [AIMessage(content=report)],
            "heat_report": report,
        }
    
    return heat_analyst_node


def format_key_signals(signals):
    """格式化关键信号"""
    if not signals:
        return "暂无明显的热度信号"
    
    formatted = []
    for signal in signals:
        signal_type = signal.get('type', '未知')
        level = signal.get('level', 'low')
        message = signal.get('message', '')
        
        level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        formatted.append(f"- {level_emoji} **{signal_type}**: {message}")
    
    return "\n".join(formatted)


def format_trading_action(action):
    """格式化交易动作"""
    action_map = {
        'buy': '买入',
        'sell': '卖出',
        'hold': '持有',
        'watch': '关注',
        'caution': '谨慎',
        'accumulate': '建仓'
    }
    return action_map.get(action, action)


def format_reasoning(reasoning):
    """格式化建议理由"""
    if not reasoning:
        return "无特别理由"
    
    if isinstance(reasoning, list):
        return "；".join(reasoning)
    
    return str(reasoning)


def format_risk_assessment(risk_assessment):
    """格式化风险评估"""
    overall_risk = risk_assessment.get('overall_risk', 'low')
    specific_risks = risk_assessment.get('specific_risks', [])
    mitigation_suggestions = risk_assessment.get('mitigation_suggestions', [])
    
    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(overall_risk, "⚪")
    
    result = f"- **整体风险等级**: {risk_emoji} {overall_risk.upper()}\n"
    
    if specific_risks:
        result += "- **具体风险**:\n"
        for risk in specific_risks:
            risk_type = risk.get('type', '未知')
            level = risk.get('level', 'low')
            description = risk.get('description', '')
            level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
            result += f"  - {level_emoji} {risk_type}: {description}\n"
    
    if mitigation_suggestions:
        result += "- **缓解建议**:\n"
        for suggestion in mitigation_suggestions:
            result += f"  - {suggestion}\n"
    
    return result