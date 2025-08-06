"""
金融热度分析器
整合社交媒体热度、成交异动、资金流向等多维度数据
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .social_apis import SocialMediaAPI
from .volume_detector import VolumeAnomalyDetector
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)


class HeatAnalyzer:
    """金融热度综合分析器"""
    
    def __init__(self):
        self.social_api = SocialMediaAPI()
        self.volume_detector = VolumeAnomalyDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # 热度权重配置
        self.weights = {
            'social_media': 0.30,      # 社交媒体
            'search_volume': 0.25,     # 搜索量
            'news_mentions': 0.20,     # 新闻提及
            'user_attention': 0.15,    # 用户关注
            'forum_discussion': 0.10   # 论坛讨论
        }
        
    def analyze_heat(self, symbol: str, days: int = 7) -> Dict:
        """
        分析股票综合热度
        
        Args:
            symbol: 股票代码
            days: 分析天数
            
        Returns:
            热度分析结果
        """
        try:
            logger.info(f"[START] 开始分析 {symbol} 热度数据...")
            
            # 并行获取各类数据
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    'social': executor.submit(self.social_api.get_social_heat, symbol),
                    'volume': executor.submit(self.volume_detector.detect_anomaly, symbol, days),
                    'sentiment': executor.submit(self.sentiment_analyzer.analyze_sentiment, symbol),
                    'search': executor.submit(self._get_search_trend, symbol),
                    'news': executor.submit(self._get_news_mentions, symbol)
                }
                
                results = {}
                for key, future in futures.items():
                    try:
                        results[key] = future.result(timeout=10)
                    except Exception as e:
                        logger.warning(f"[WARN] {key} 数据获取失败: {e}")
                        results[key] = self._get_default_result()
            
            # 计算综合热度指数
            heat_score = self._calculate_heat_index(results)
            
            # 生成分析结果
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'heat_score': heat_score,
                'heat_level': self._get_heat_level(heat_score),
                'details': results,
                'alerts': self._generate_alerts(results),
                'trend': self._analyze_trend(results)
            }
            
            logger.info(f"[COMPLETE] {symbol} 热度分析完成: {heat_score:.2f}/100")
            return analysis
            
        except Exception as e:
            logger.error(f"[ERROR] 热度分析失败 {symbol}: {e}")
            return self._get_error_result(symbol, str(e))
    
    def _calculate_heat_index(self, results: Dict) -> float:
        """计算综合热度指数"""
        try:
            scores = []
            
            # 社交媒体热度 (0-100)
            social_score = min(results.get('social', {}).get('score', 0), 100)
            scores.append(social_score * self.weights['social_media'])
            
            # 搜索量 (0-100)
            search_score = min(results.get('search', {}).get('score', 0), 100)
            scores.append(search_score * self.weights['search_volume'])
            
            # 新闻提及 (0-100)
            news_score = min(results.get('news', {}).get('score', 0), 100)
            scores.append(news_score * self.weights['news_mentions'])
            
            # 用户关注 (0-100)
            attention_score = min(results.get('volume', {}).get('attention_score', 0), 100)
            scores.append(attention_score * self.weights['user_attention'])
            
            # 论坛讨论 (0-100)
            forum_score = min(results.get('sentiment', {}).get('discussion_score', 0), 100)
            scores.append(forum_score * self.weights['forum_discussion'])
            
            return sum(scores)
            
        except Exception as e:
            logger.error(f"[ERROR] 热度指数计算失败: {e}")
            return 0.0
    
    def _get_heat_level(self, score: float) -> str:
        """根据分数返回热度等级"""
        if score >= 80:
            return "[HIGH] 极高热度"
        elif score >= 60:
            return "[HIGH] 高热度"
        elif score >= 40:
            return "[MEDIUM] 中等热度"
        elif score >= 20:
            return "[LOW] 低热度"
        else:
            return "[LOW] 极低热度"
    
    def _generate_alerts(self, results: Dict) -> List[Dict]:
        """生成预警信息"""
        alerts = []
        
        try:
            # 成交量异动预警
            volume_data = results.get('volume', {})
            if volume_data.get('anomaly_score', 0) > 70:
                alerts.append({
                    'type': 'volume_anomaly',
                    'level': 'high',
                    'message': f"成交量异常放大 {volume_data.get('volume_ratio', 0):.1f} 倍",
                    'score': volume_data.get('anomaly_score', 0)
                })
            
            # 情绪突变预警
            sentiment_data = results.get('sentiment', {})
            if abs(sentiment_data.get('sentiment_change', 0)) > 0.5:
                direction = "急剧转暖" if sentiment_data.get('sentiment_change', 0) > 0 else "急剧转冷"
                alerts.append({
                    'type': 'sentiment_shift',
                    'level': 'medium',
                    'message': f"市场情绪{direction}",
                    'score': abs(sentiment_data.get('sentiment_change', 0)) * 100
                })
            
            # 热度突增预警
            social_data = results.get('social', {})
            if social_data.get('trend', {}).get('change_24h', 0) > 200:
                alerts.append({
                    'type': 'heat_spike',
                    'level': 'medium',
                    'message': "社交媒体热度突然增加200%+",
                    'score': social_data.get('trend', {}).get('change_24h', 0)
                })
                
        except Exception as e:
            logger.error(f"[ERROR] 预警生成失败: {e}")
        
        return alerts
    
    def _analyze_trend(self, results: Dict) -> Dict:
        """分析热度趋势"""
        try:
            trends = {}
            
            # 社交媒体趋势
            social_trend = results.get('social', {}).get('trend', {})
            trends['social'] = {
                'direction': social_trend.get('direction', 'stable'),
                'change_24h': social_trend.get('change_24h', 0),
                'momentum': social_trend.get('momentum', 'neutral')
            }
            
            # 搜索量趋势
            search_trend = results.get('search', {}).get('trend', {})
            trends['search'] = {
                'direction': search_trend.get('direction', 'stable'),
                'change_7d': search_trend.get('change_7d', 0)
            }
            
            # 成交量趋势
            volume_trend = results.get('volume', {}).get('trend', {})
            trends['volume'] = {
                'direction': volume_trend.get('direction', 'stable'),
                'strength': volume_trend.get('strength', 'normal')
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"[ERROR] 趋势分析失败: {e}")
            return {}
    
    def _get_search_trend(self, symbol: str) -> Dict:
        """获取搜索趋势数据"""
        # 这里将集成百度指数API
        # 暂时返回模拟数据
        return {
            'score': 45.6,
            'trend': {
                'direction': 'up',
                'change_7d': 23.4
            },
            'peak_hours': ['09:30', '10:00', '14:00']
        }
    
    def _get_news_mentions(self, symbol: str) -> Dict:
        """获取新闻提及数据"""
        # 这里将集成新浪财经等新闻API
        # 暂时返回模拟数据
        return {
            'score': 32.1,
            'count_24h': 15,
            'sentiment': 'neutral',
            'top_keywords': ['业绩预增', '机构调研', '板块轮动']
        }
    
    def _get_default_result(self) -> Dict:
        """获取默认结果"""
        return {
            'score': 0,
            'trend': {'direction': 'stable', 'change': 0},
            'status': 'data_unavailable'
        }
    
    def _get_error_result(self, symbol: str, error: str) -> Dict:
        """获取错误结果"""
        return {
            'symbol': symbol,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }
    
    def batch_analyze(self, symbols: List[str]) -> List[Dict]:
        """批量分析多个股票"""
        results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_heat, symbol): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"[ERROR] {symbol} 批量分析失败: {e}")
                    results.append(self._get_error_result(symbol, str(e)))
        
        # 按热度排序
        results.sort(key=lambda x: x.get('heat_score', 0), reverse=True)
        return results
    
    def get_heat_ranking(self, symbols: List[str], limit: int = 10) -> List[Dict]:
        """获取热度排行榜"""
        results = self.batch_analyze(symbols)
        return results[:limit]