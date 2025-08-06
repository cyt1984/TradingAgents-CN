"""
热度分析系统集成模块
将免费热度分析整合到现有交易系统中
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from .heat_analyzer import HeatAnalyzer
from tradingagents.dataflows.data_source_manager import DataSourceManager

logger = logging.getLogger(__name__)

class HeatAnalysisIntegration:
    """热度分析系统集成器"""
    
    def __init__(self):
        self.heat_analyzer = HeatAnalyzer()
        self.data_source_manager = DataSourceManager()
        
    def analyze_with_heat(self, symbol: str, include_heat: bool = True) -> Dict:
        """
        整合热度分析的股票分析
        
        Args:
            symbol: 股票代码
            include_heat: 是否包含热度分析
            
        Returns:
            包含热度数据的综合分析结果
        """
        try:
            logger.info(f"[START] 开始整合热度分析: {symbol}")
            
            # 基础数据分析
            basic_analysis = self._get_basic_analysis(symbol)
            
            if not include_heat:
                return basic_analysis
            
            # 热度分析
            heat_analysis = self.heat_analyzer.analyze_heat(symbol)
            
            # 整合结果
            integrated_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'basic_analysis': basic_analysis,
                'heat_analysis': heat_analysis,
                'heat_signals': self._generate_heat_signals(heat_analysis),
                'risk_assessment': self._assess_heat_risk(heat_analysis),
                'action_recommendations': self._generate_recommendations(heat_analysis)
            }
            
            logger.info(f"[COMPLETE] {symbol} 热度整合分析完成")
            return integrated_result
            
        except Exception as e:
            logger.error(f"[ERROR] 热度整合分析失败 {symbol}: {e}")
            return self._get_error_result(symbol, str(e))
    
    def _get_basic_analysis(self, symbol: str) -> Dict:
        """获取基础分析数据"""
        try:
            # 这里可以集成现有的股票分析逻辑
            return {
                'current_price': 0,
                'price_change': 0,
                'volume': 0,
                'status': 'basic_data_ready'
            }
        except Exception as e:
            logger.warning(f"[WARN] 基础数据获取失败 {symbol}: {e}")
            return {'status': 'basic_data_unavailable'}
    
    def _generate_heat_signals(self, heat_analysis: Dict) -> List[Dict]:
        """生成热度交易信号"""
        signals = []
        
        try:
            heat_score = heat_analysis.get('heat_score', 0)
            alerts = heat_analysis.get('alerts', [])
            
            # 基于热度分数生成信号
            if heat_score >= 80:
                signals.append({
                    'type': 'heat_extreme',
                    'level': 'high',
                    'direction': 'caution',
                    'message': '极高热度，注意短期回调风险',
                    'score': heat_score,
                    'confidence': 0.8
                })
            elif heat_score >= 60:
                signals.append({
                    'type': 'heat_high',
                    'level': 'medium',
                    'direction': 'bullish',
                    'message': '高热度，关注资金动向',
                    'score': heat_score,
                    'confidence': 0.7
                })
            elif heat_score >= 40:
                signals.append({
                    'type': 'heat_medium',
                    'level': 'low',
                    'direction': 'neutral',
                    'message': '中等热度，正常交易',
                    'score': heat_score,
                    'confidence': 0.6
                })
            
            # 基于预警生成信号
            for alert in alerts:
                if alert['level'] == 'high':
                    signals.append({
                        'type': f"alert_{alert['type']}",
                        'level': 'high',
                        'direction': 'caution',
                        'message': alert['message'],
                        'score': alert.get('score', 0),
                        'confidence': 0.75
                    })
            
        except Exception as e:
            logger.error(f"[ERROR] 信号生成失败: {e}")
        
        return signals
    
    def _assess_heat_risk(self, heat_analysis: Dict) -> Dict:
        """评估热度相关风险"""
        try:
            heat_score = heat_analysis.get('heat_score', 0)
            
            # 风险等级评估
            if heat_score >= 80:
                risk_level = 'high'
                risk_description = '极高热度可能导致剧烈波动'
            elif heat_score >= 60:
                risk_level = 'medium'
                risk_description = '高热度需关注市场情绪'
            elif heat_score >= 40:
                risk_level = 'low'
                risk_description = '正常热度水平'
            else:
                risk_level = 'minimal'
                risk_description = '低热度，风险较小'
            
            # 具体风险因子
            risk_factors = []
            
            # 成交量异动风险
            volume_data = heat_analysis.get('details', {}).get('volume', {})
            if volume_data.get('anomaly_score', 0) > 70:
                risk_factors.append('volume_spike')
            
            # 情绪突变风险
            sentiment_data = heat_analysis.get('details', {}).get('sentiment', {})
            if abs(sentiment_data.get('sentiment_change', 0)) > 0.5:
                risk_factors.append('sentiment_shift')
            
            return {
                'risk_level': risk_level,
                'risk_description': risk_description,
                'risk_factors': risk_factors,
                'heat_score': heat_score
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 风险评估失败: {e}")
            return {'risk_level': 'unknown', 'error': str(e)}
    
    def _generate_recommendations(self, heat_analysis: Dict) -> List[str]:
        """生成操作建议"""
        recommendations = []
        
        try:
            heat_score = heat_analysis.get('heat_score', 0)
            risk_assessment = self._assess_heat_risk(heat_analysis)
            
            # 基于热度分数的建议
            if heat_score >= 80:
                recommendations.extend([
                    "[CAUTION] 极高热度，建议谨慎追高",
                    "[WATCH] 关注成交量变化，防范短期回调",
                    "[ACTION] 可考虑分批减仓或设置止损"
                ])
            elif heat_score >= 60:
                recommendations.extend([
                    "[OPPORTUNITY] 高热度，可适度参与",
                    "[MONITOR] 密切关注资金流向和情绪变化",
                    "[MANAGE] 设置合理的止盈止损位"
                ])
            elif heat_score >= 40:
                recommendations.extend([
                    "[NORMAL] 正常热度，按技术分析操作",
                    "[WATCH] 关注是否有热度上升趋势",
                    "[IDEA] 可适当关注相关板块轮动"
                ])
            else:
                recommendations.extend([
                    "[OPPORTUNITY] 低热度，可能存在机会",
                    "[RESEARCH] 关注基本面是否有改善迹象",
                    "[STRATEGY] 可考虑逢低布局"
                ])
            
            # 基于风险因子的建议
            risk_factors = risk_assessment.get('risk_factors', [])
            if 'volume_spike' in risk_factors:
                recommendations.append("[ALERT] 成交量异常，注意主力动向")
            if 'sentiment_shift' in risk_factors:
                recommendations.append("[CAUTION] 情绪突变，建议观望确认")
            
        except Exception as e:
            logger.error(f"[ERROR] 建议生成失败: {e}")
            recommendations.append("[WARN] 数据异常，建议谨慎操作")
        
        return recommendations
    
    def batch_analyze_with_heat(self, symbols: List[str]) -> List[Dict]:
        """批量分析多个股票的热度"""
        results = []
        
        for symbol in symbols:
            try:
                result = self.analyze_with_heat(symbol)
                results.append(result)
            except Exception as e:
                logger.error(f"[ERROR] 批量分析失败 {symbol}: {e}")
                results.append(self._get_error_result(symbol, str(e)))
        
        # 按热度排序
        results.sort(key=lambda x: x.get('heat_analysis', {}).get('heat_score', 0), reverse=True)
        return results
    
    def get_heat_watchlist(self, symbols: List[str], min_heat_score: int = 60) -> List[Dict]:
        """获取热度监控列表"""
        all_results = self.batch_analyze_with_heat(symbols)
        
        # 筛选高热度股票
        watchlist = [
            result for result in all_results
            if result.get('heat_analysis', {}).get('heat_score', 0) >= min_heat_score
        ]
        
        return watchlist
    
    def _get_error_result(self, symbol: str, error: str) -> Dict:
        """获取错误结果"""
        return {
            'symbol': symbol,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }

# 全局实例
heat_integration = HeatAnalysisIntegration()