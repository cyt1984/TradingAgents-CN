"""
情绪分析模块
分析社交媒体情绪、新闻情感、散户-机构博弈等
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情绪分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 情感词典
        self.positive_words = [
            '看涨', '买入', '强势', '突破', '拉升', '涨停', '利好', '增长', 
            '上涨', '反弹', '牛市', '机会', '看好', '支撑', '抄底', '抢筹'
        ]
        
        self.negative_words = [
            '看跌', '卖出', '弱势', '跌破', '跳水', '跌停', '利空', '下跌',
            '暴跌', '熊市', '风险', '看空', '阻力', '割肉', '跑路', '踩踏'
        ]
        
        self.neutral_words = ['震荡', '横盘', '观望', '等待', '谨慎']
    
    def analyze_sentiment(self, symbol: str) -> Dict:
        """
        分析市场情绪
        
        Args:
            symbol: 股票代码
            
        Returns:
            情绪分析结果
        """
        try:
            logger.info(f"[ANALYZE] 开始分析 {symbol} 市场情绪...")
            
            # 获取多渠道数据
            social_sentiment = self._analyze_social_sentiment(symbol)
            news_sentiment = self._analyze_news_sentiment(symbol)
            forum_sentiment = self._analyze_forum_sentiment(symbol)
            
            # 计算综合情绪
            overall_sentiment = self._calculate_overall_sentiment(
                social_sentiment, news_sentiment, forum_sentiment
            )
            
            # 散户-机构博弈分析
            retail_institutional = self._analyze_retail_institutional_battle(symbol)
            
            # 情绪突变检测
            sentiment_shifts = self._detect_sentiment_shifts(symbol)
            
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'overall_sentiment': overall_sentiment,
                'social_sentiment': social_sentiment,
                'news_sentiment': news_sentiment,
                'forum_sentiment': forum_sentiment,
                'retail_institutional': retail_institutional,
                'sentiment_shifts': sentiment_shifts,
                'discussion_score': self._calculate_discussion_score(forum_sentiment),
                'alerts': self._generate_sentiment_alerts(overall_sentiment, sentiment_shifts)
            }
            
            logger.info(f"[COMPLETE] {symbol} 情绪分析完成: {overall_sentiment['sentiment_label']}")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] 情绪分析失败 {symbol}: {e}")
            return self._get_error_result(symbol, str(e))
    
    def _analyze_social_sentiment(self, symbol: str) -> Dict:
        """分析社交媒体情绪"""
        try:
            # 模拟从微博、雪球等平台获取数据
            posts = self._get_social_posts(symbol)
            
            if not posts:
                return self._get_default_sentiment()
            
            # 情感分析
            sentiments = []
            for post in posts:
                sentiment = self._analyze_text_sentiment(post['content'])
                sentiments.append(sentiment)
            
            # 计算统计指标
            positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
            negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
            neutral_count = len(sentiments) - positive_count - negative_count
            
            total = len(sentiments)
            if total > 0:
                positive_ratio = positive_count / total
                negative_ratio = negative_count / total
                neutral_ratio = neutral_count / total
                
                # 计算情感强度
                avg_strength = np.mean([s['strength'] for s in sentiments])
                
                # 情感倾向
                sentiment_score = (positive_ratio - negative_ratio) * 100
                
                return {
                    'positive_ratio': positive_ratio,
                    'negative_ratio': negative_ratio,
                    'neutral_ratio': neutral_ratio,
                    'sentiment_score': sentiment_score,
                    'avg_strength': avg_strength,
                    'post_count': total,
                    'sentiment_label': self._get_sentiment_label(sentiment_score)
                }
            
        except Exception as e:
            logger.error(f"[ERROR] 社交媒体情绪分析失败: {e}")
        
        return self._get_default_sentiment()
    
    def _analyze_news_sentiment(self, symbol: str) -> Dict:
        """分析新闻情绪"""
        try:
            # 模拟从新浪财经、东方财富等获取新闻
            news_items = self._get_news_items(symbol)
            
            if not news_items:
                return self._get_default_sentiment()
            
            # 分析新闻标题情感
            sentiments = []
            for news in news_items:
                sentiment = self._analyze_text_sentiment(news['title'])
                sentiments.append(sentiment)
            
            # 计算新闻情感
            positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
            negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
            total = len(sentiments)
            
            if total > 0:
                news_sentiment_score = (positive_count - negative_count) / total * 100
                
                return {
                    'news_count': total,
                    'positive_ratio': positive_count / total,
                    'negative_ratio': negative_count / total,
                    'sentiment_score': news_sentiment_score,
                    'sentiment_label': self._get_sentiment_label(news_sentiment_score),
                    'latest_news': news_items[0] if news_items else None
                }
            
        except Exception as e:
            logger.error(f"[ERROR] 新闻情绪分析失败: {e}")
        
        return self._get_default_sentiment()
    
    def _analyze_forum_sentiment(self, symbol: str) -> Dict:
        """分析论坛情绪"""
        try:
            # 模拟从股吧、雪球等获取讨论
            discussions = self._get_forum_discussions(symbol)
            
            if not discussions:
                return self._get_default_sentiment()
            
            # 分析讨论内容
            sentiments = []
            for discussion in discussions:
                sentiment = self._analyze_text_sentiment(discussion['content'])
                sentiments.append(sentiment)
            
            # 计算论坛情感
            positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
            negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
            total = len(sentiments)
            
            if total > 0:
                # 计算讨论热度
                discussion_score = min(total * 10, 100)
                
                return {
                    'discussion_count': total,
                    'discussion_score': discussion_score,
                    'positive_ratio': positive_count / total,
                    'negative_ratio': negative_count / total,
                    'sentiment_score': (positive_count - negative_count) / total * 100,
                    'sentiment_label': self._get_sentiment_label((positive_count - negative_count) / total * 100)
                }
            
        except Exception as e:
            logger.error(f"[ERROR] 论坛情绪分析失败: {e}")
        
        return self._get_default_sentiment()
    
    def _analyze_retail_institutional_battle(self, symbol: str) -> Dict:
        """分析散户-机构博弈"""
        try:
            # 获取资金流向数据
            flow_data = self._get_money_flow_data(symbol)
            
            if not flow_data:
                return self._get_default_battle_result()
            
            # 计算博弈指标
            main_inflow = flow_data.get('main_net_inflow', 0)
            retail_inflow = flow_data.get('retail_net_inflow', 0)
            
            # 博弈强度
            battle_intensity = abs(main_inflow - retail_inflow) / max(abs(main_inflow) + abs(retail_inflow), 1)
            
            # 博弈方向
            if main_inflow > 0 and retail_inflow < 0:
                battle_direction = "机构买入-散户卖出"
                battle_score = battle_intensity * 100
            elif main_inflow < 0 and retail_inflow > 0:
                battle_direction = "机构卖出-散户买入"
                battle_score = -battle_intensity * 100
            else:
                battle_direction = "同向操作"
                battle_score = 0
            
            return {
                'battle_direction': battle_direction,
                'battle_intensity': battle_intensity,
                'battle_score': battle_score,
                'main_inflow': main_inflow,
                'retail_inflow': retail_inflow,
                'is_divergence': abs(battle_score) > 50,
                'warning_level': 'high' if abs(battle_score) > 70 else 'medium' if abs(battle_score) > 30 else 'low'
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 散户-机构博弈分析失败: {e}")
            return self._get_default_battle_result()
    
    def _detect_sentiment_shifts(self, symbol: str) -> Dict:
        """检测情绪突变"""
        try:
            # 获取历史情绪数据
            historical_sentiment = self._get_historical_sentiment(symbol)
            
            if len(historical_sentiment) < 2:
                return self._get_default_shift_result()
            
            # 计算情绪变化
            latest_sentiment = historical_sentiment[-1]['score']
            previous_sentiment = historical_sentiment[-2]['score']
            
            sentiment_change = latest_sentiment - previous_sentiment
            change_magnitude = abs(sentiment_change)
            
            # 判断突变
            is_significant_shift = change_magnitude > 20
            shift_direction = 'positive' if sentiment_change > 0 else 'negative'
            
            return {
                'sentiment_change': sentiment_change,
                'change_magnitude': change_magnitude,
                'is_significant_shift': is_significant_shift,
                'shift_direction': shift_direction,
                'shift_strength': 'strong' if change_magnitude > 40 else 'moderate' if change_magnitude > 20 else 'weak',
                'previous_sentiment': previous_sentiment,
                'current_sentiment': latest_sentiment
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 情绪突变检测失败: {e}")
            return self._get_default_shift_result()
    
    def _analyze_text_sentiment(self, text: str) -> Dict:
        """分析文本情感"""
        try:
            text = str(text).lower()
            
            # 计算正负词频
            positive_count = sum(1 for word in self.positive_words if word in text)
            negative_count = sum(1 for word in self.negative_words if word in text)
            neutral_count = sum(1 for word in self.neutral_words if word in text)
            
            # 确定情感标签
            if positive_count > negative_count:
                label = 'positive'
                strength = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            elif negative_count > positive_count:
                label = 'negative'
                strength = (negative_count - positive_count) / max(positive_count + negative_count, 1)
            else:
                label = 'neutral'
                strength = 0
            
            return {
                'label': label,
                'strength': strength,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 文本情感分析失败: {e}")
            return {'label': 'neutral', 'strength': 0, 'positive_count': 0, 'negative_count': 0}
    
    def _calculate_discussion_score(self, forum_data: Dict) -> float:
        """计算讨论热度得分"""
        try:
            discussion_count = forum_data.get('discussion_count', 0)
            
            # 根据讨论数量计算得分
            if discussion_count > 1000:
                return 100
            elif discussion_count > 500:
                return 80
            elif discussion_count > 100:
                return 60
            elif discussion_count > 50:
                return 40
            elif discussion_count > 10:
                return 20
            else:
                return 5
                
        except Exception as e:
            logger.error(f"[ERROR] 讨论热度计算失败: {e}")
            return 0
    
    def _calculate_overall_sentiment(self, social: Dict, news: Dict, forum: Dict) -> Dict:
        """计算综合情绪"""
        try:
            # 权重配置
            weights = {
                'social': 0.4,  # 社交媒体权重
                'news': 0.3,    # 新闻权重
                'forum': 0.3    # 论坛权重
            }
            
            # 计算加权平均情绪得分
            social_score = social.get('sentiment_score', 0)
            news_score = news.get('sentiment_score', 0)
            forum_score = forum.get('sentiment_score', 0)
            
            overall_score = (
                social_score * weights['social'] +
                news_score * weights['news'] +
                forum_score * weights['forum']
            )
            
            return {
                'sentiment_score': overall_score,
                'sentiment_label': self._get_sentiment_label(overall_score),
                'confidence': min(
                    (social.get('post_count', 0) + 
                     news.get('news_count', 0) + 
                     forum.get('discussion_count', 0)) / 100,
                    1.0
                )
            }
            
        except Exception as e:
            logger.error(f"[ERROR] 综合情绪计算失败: {e}")
            return {'sentiment_score': 0, 'sentiment_label': 'neutral', 'confidence': 0}
    
    def _get_sentiment_label(self, score: float) -> str:
        """根据得分返回情感标签"""
        if score > 30:
            return "非常乐观"
        elif score > 10:
            return "乐观"
        elif score > -10:
            return "中性"
        elif score > -30:
            return "悲观"
        else:
            return "非常悲观"
    
    def _generate_sentiment_alerts(self, overall: Dict, shifts: Dict) -> List[Dict]:
        """生成情绪预警"""
        alerts = []
        
        try:
            # 情绪极值预警
            sentiment_score = abs(overall.get('sentiment_score', 0))
            if sentiment_score > 50:
                alerts.append({
                    'type': 'extreme_sentiment',
                    'level': 'high',
                    'message': f"市场情绪极{'度乐观' if overall['sentiment_score'] > 0 else '度悲观'}",
                    'score': sentiment_score
                })
            
            # 情绪突变预警
            if shifts.get('is_significant_shift', False):
                alerts.append({
                    'type': 'sentiment_shift',
                    'level': 'medium',
                    'message': f"市场情绪{shifts['shift_strength']}转向{shifts['shift_direction']}",
                    'change': shifts['sentiment_change']
                })
                
        except Exception as e:
            logger.error(f"[ERROR] 情绪预警生成失败: {e}")
        
        return alerts
    
    # 模拟数据获取方法
    def _get_social_posts(self, symbol: str) -> List[Dict]:
        """获取社交媒体帖子"""
        # 这里应该集成实际的社交媒体API
        # 暂时返回模拟数据
        import random
        
        sample_posts = [
            {"content": f"{symbol}今天表现强势，有望突破前高！", "time": datetime.now()},
            {"content": f"{symbol}量能放大，主力明显介入", "time": datetime.now()},
            {"content": f"{symbol}这个位置风险较大，建议谨慎", "time": datetime.now()},
            {"content": f"{symbol}基本面不错，可以长期持有", "time": datetime.now()},
            {"content": f"{symbol}短期回调就是机会", "time": datetime.now()}
        ]
        
        return random.sample(sample_posts, min(5, len(sample_posts)))
    
    def _get_news_items(self, symbol: str) -> List[Dict]:
        """获取新闻数据"""
        import random
        
        sample_news = [
            {"title": f"{symbol}业绩超预期，多家机构上调评级", "time": datetime.now()},
            {"title": f"{symbol}获得大额订单，未来发展可期", "time": datetime.now()},
            {"title": f"{symbol}风险提示：估值偏高需谨慎", "time": datetime.now()}
        ]
        
        return random.sample(sample_news, min(3, len(sample_news)))
    
    def _get_forum_discussions(self, symbol: str) -> List[Dict]:
        """获取论坛讨论"""
        import random
        
        sample_discussions = [
            {"content": f"{symbol}股吧今天很热闹，大家都在讨论", "time": datetime.now()},
            {"content": f"{symbol}雪球上关注度很高", "time": datetime.now()}
        ]
        
        return random.sample(sample_discussions, min(2, len(sample_discussions)))
    
    def _get_money_flow_data(self, symbol: str) -> Dict:
        """获取资金流向数据"""
        # 这里应该集成实际的资金流向API
        import random
        
        return {
            'main_net_inflow': random.uniform(-5000, 5000),
            'retail_net_inflow': random.uniform(-3000, 3000),
            'main_net_ratio': random.uniform(-10, 10),
            'retail_net_ratio': random.uniform(-5, 5)
        }
    
    def _get_historical_sentiment(self, symbol: str) -> List[Dict]:
        """获取历史情绪数据"""
        import random
        
        historical = []
        for i in range(7):
            historical.append({
                'date': datetime.now() - timedelta(days=i),
                'score': random.uniform(-50, 50)
            })
        
        return historical
    
    def _get_default_sentiment(self) -> Dict:
        """获取默认情绪数据"""
        return {
            'positive_ratio': 0,
            'negative_ratio': 0,
            'neutral_ratio': 1,
            'sentiment_score': 0,
            'sentiment_label': '中性',
            'post_count': 0
        }
    
    def _get_default_battle_result(self) -> Dict:
        """获取默认博弈结果"""
        return {
            'battle_direction': '数据不足',
            'battle_intensity': 0,
            'battle_score': 0,
            'main_inflow': 0,
            'retail_inflow': 0,
            'is_divergence': False,
            'warning_level': 'low'
        }
    
    def _get_default_shift_result(self) -> Dict:
        """获取默认突变结果"""
        return {
            'sentiment_change': 0,
            'change_magnitude': 0,
            'is_significant_shift': False,
            'shift_direction': 'stable',
            'shift_strength': 'weak',
            'previous_sentiment': 0,
            'current_sentiment': 0
        }
    
    def _get_error_result(self, symbol: str, error: str) -> Dict:
        """获取错误结果"""
        return {
            'symbol': symbol,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }