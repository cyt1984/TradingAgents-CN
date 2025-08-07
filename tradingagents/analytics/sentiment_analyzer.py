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
import jieba
import math

# 导入新浪财经数据源
from ..dataflows.sina_utils import get_sina_provider
from ..utils.logging_manager import get_logger

logger = get_logger('agents')


class SentimentAnalyzer:
    """情绪分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 初始化新浪财经数据提供器
        try:
            self.sina_provider = get_sina_provider()
        except Exception as e:
            logger.warning(f"⚠️ 新浪财经数据源初始化失败: {e}")
            self.sina_provider = None
        
        # 初始化jieba分词
        jieba.initialize()
        
        # 扩展的情感词典
        self.positive_words = set([
            # 涨幅相关
            '上涨', '涨停', '涨幅', '大涨', '暴涨', '飙升', '攀升', '走高', '突破', '创新高',
            '强势', '反弹', '回升', '上扬', '拉升', '冲高', '连涨', '持续上涨',
            '看涨', '买入', '拉升', '利好', '机会', '看好', '支撑', '抄底', '抢筹',
            
            # 业绩相关
            '增长', '盈利', '收益', '营收', '利润', '业绩', '超预期', '亮眼', '优秀', '出色',
            '改善', '好转', '提升', '增强', '扩大', '发展', '成功', '突出',
            
            # 市场情绪
            '乐观', '推荐', '持有', '积极', '潜力', '前景', '信心', '稳定', '健康', '强劲',
            '活跃', '繁荣', '复苏', '向好', '牛市',
            
            # 其他积极词汇
            '领先', '优势', '创新', '合作', '签约', '中标', '获得', '批准', '通过',
            '完成', '实现', '达成', '建设', '投资', '扩产', '并购', '重组'
        ])
        
        self.negative_words = set([
            # 跌幅相关
            '下跌', '跌停', '跌幅', '大跌', '暴跌', '重挫', '下滑', '走低', '破位', '创新低',
            '弱势', '回调', '调整', '下探', '杀跌', '连跌', '持续下跌', '崩盘',
            '看跌', '卖出', '跳水', '利空', '风险', '看空', '阻力', '割肉', '跑路', '踩踏',
            
            # 业绩相关
            '亏损', '下降', '减少', '低于', '不及', '逊色', '恶化', '放缓', '萎缩', '收缩',
            '困难', '挑战', '压力', '问题', '危机', '担忧', '疑虑',
            
            # 市场情绪
            '悲观', '减持', '谨慎', '消极', '威胁', '不利', '恐慌', '动荡', '不稳',
            '疲软', '低迷', '衰退', '萧条', '熊市',
            
            # 其他消极词汇
            '停产', '停工', '关闭', '退出', '失败', '取消', '延期', '暂停', '中断', '损失',
            '违规', '处罚', '调查', '诉讼', '纠纷', '争议', '质疑', '否认'
        ])
        
        self.neutral_words = set(['震荡', '横盘', '观望', '等待', '谨慎', '持平', '维持'])
        
        # 股票相关关键词
        self.stock_keywords = set([
            '股票', '股价', '股市', 'A股', '港股', '美股', '个股', '板块', '指数',
            '主力', '机构', '散户', '资金', '成交量', '换手率', '市盈率', '市净率'
        ])
        
        # 强化词和否定词
        self.intensifiers = set(['很', '非常', '极其', '特别', '相当', '十分', '大幅', '显著', '明显'])
        self.negators = set(['不', '没', '无', '非', '未', '否'])
    
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
        """分析新闻情绪（增强版）"""
        try:
            # 从新浪财经获取新闻
            news_items = []
            
            if self.sina_provider:
                try:
                    sina_news = self.sina_provider.get_stock_news(symbol, limit=50)
                    news_items.extend(sina_news)
                    logger.info(f"✅ 从新浪财经获取到 {len(sina_news)} 条新闻")
                except Exception as e:
                    logger.warning(f"⚠️ 新浪财经新闻获取失败: {e}")
            
            # 如果没有获取到新闻，使用模拟数据
            if not news_items:
                news_items = self._get_news_items(symbol)
                logger.info("使用模拟新闻数据")
            
            if not news_items:
                return self._get_default_sentiment()
            
            # 使用增强的文本情感分析
            sentiment_results = []
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for news in news_items:
                title = news.get('title', '')
                summary = news.get('summary', '')
                
                # 综合标题和摘要进行分析
                full_text = f"{title} {summary}"
                
                # 分析情感
                sentiment = self._analyze_enhanced_text_sentiment(full_text)
                
                # 计算相关性权重
                relevance_score = news.get('relevance_score', 0.8)
                time_weight = self._calculate_time_weight(news.get('publish_time', ''))
                
                # 综合权重
                weight = relevance_score * time_weight
                total_weighted_score += sentiment['sentiment_score'] * weight
                total_weight += weight
                
                sentiment_results.append({
                    'title': title,
                    'sentiment_score': sentiment['sentiment_score'],
                    'confidence': sentiment['confidence'],
                    'relevance_score': relevance_score,
                    'time_weight': time_weight,
                    'source': news.get('source', ''),
                    'publish_time': news.get('publish_time', '')
                })
            
            # 计算总体情感分数
            if total_weight > 0:
                avg_sentiment_score = total_weighted_score / total_weight
            else:
                avg_sentiment_score = 0.0
            
            # 统计分布
            positive_count = sum(1 for r in sentiment_results if r['sentiment_score'] > 0.1)
            negative_count = sum(1 for r in sentiment_results if r['sentiment_score'] < -0.1)
            neutral_count = len(sentiment_results) - positive_count - negative_count
            total = len(sentiment_results)
            
            # 计算置信度
            confidence = sum(r['confidence'] for r in sentiment_results) / total if total > 0 else 0.0
            
            return {
                'news_count': total,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_ratio': positive_count / total if total > 0 else 0,
                'negative_ratio': negative_count / total if total > 0 else 0,
                'neutral_ratio': neutral_count / total if total > 0 else 0,
                'sentiment_score': round(avg_sentiment_score * 100, 2),  # 转换为百分制
                'confidence': round(confidence, 3),
                'sentiment_label': self._get_sentiment_label(avg_sentiment_score * 100),
                'latest_news': news_items[0] if news_items else None,
                'sentiment_distribution': sentiment_results[:10],  # 前10条新闻的详细分析
                'data_source': 'sina_finance' if self.sina_provider else 'mock_data'
            }
            
        except Exception as e:
            logger.error(f"❌ 新闻情绪分析失败: {e}")
            return self._get_default_sentiment()
    
    def _analyze_enhanced_text_sentiment(self, text: str) -> Dict:
        """增强的文本情感分析"""
        try:
            if not text:
                return {'sentiment_score': 0.0, 'confidence': 0.0}
            
            # 文本预处理
            cleaned_text = self._clean_text(text)
            
            # 分词
            words = list(jieba.cut(cleaned_text))
            
            # 计算情感分数
            sentiment_result = self._calculate_enhanced_sentiment_score(words)
            
            # 添加股票相关性权重
            stock_relevance = self._calculate_stock_relevance(words)
            
            # 调整最终得分
            final_score = sentiment_result['sentiment_score'] * (0.5 + 0.5 * stock_relevance)
            
            return {
                'sentiment_score': round(final_score, 3),
                'confidence': round(sentiment_result['confidence'], 3),
                'stock_relevance': round(stock_relevance, 3),
                'details': sentiment_result['details']
            }
            
        except Exception as e:
            logger.error(f"❌ 增强文本情感分析失败: {str(e)}")
            return {'sentiment_score': 0.0, 'confidence': 0.0}
    
    def _calculate_enhanced_sentiment_score(self, words: List[str]) -> Dict:
        """计算增强的情感分数"""
        try:
            positive_count = 0
            negative_count = 0
            total_words = len(words)
            
            i = 0
            while i < len(words):
                word = words[i]
                weight = 1.0
                
                # 检查前面的强化词
                if i > 0 and words[i-1] in self.intensifiers:
                    weight = 1.5
                elif i > 0 and words[i-1] in self.negators:
                    weight = -1.0
                
                # 计算情感分数
                if word in self.positive_words:
                    positive_count += weight
                elif word in self.negative_words:
                    negative_count += abs(weight) if weight > 0 else -weight
                
                i += 1
            
            # 计算最终分数
            if total_words == 0:
                sentiment_score = 0.0
                confidence = 0.0
            else:
                # 归一化分数到 [-1, 1] 区间
                raw_score = (positive_count - negative_count) / total_words
                sentiment_score = math.tanh(raw_score * 2)  # 使用tanh函数平滑化
                
                # 计算置信度
                total_sentiment_words = abs(positive_count) + abs(negative_count)
                confidence = min(1.0, total_sentiment_words / max(1, total_words * 0.1))
            
            return {
                'sentiment_score': sentiment_score,
                'confidence': confidence,
                'details': {
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'total_words': total_words
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 计算增强情感分数失败: {str(e)}")
            return {'sentiment_score': 0.0, 'confidence': 0.0, 'details': {}}
    
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
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        try:
            # 去除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 去除特殊字符，保留中文、数字、字母
            text = re.sub(r'[^\u4e00-\u9fa5\w\s]', '', text)
            
            # 去除多余空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception:
            return text
    
    def _calculate_stock_relevance(self, words: List[str]) -> float:
        """计算文本与股票的相关性"""
        try:
            stock_word_count = 0
            
            for word in words:
                if word in self.stock_keywords:
                    stock_word_count += 1
            
            # 计算相关性得分
            relevance = min(1.0, stock_word_count / max(1, len(words) * 0.1))
            
            return relevance
            
        except Exception:
            return 0.5
    
    def _calculate_time_weight(self, publish_time: str) -> float:
        """计算时间权重（越新的新闻权重越高）"""
        try:
            if not publish_time:
                return 0.8
            
            # 尝试解析时间
            try:
                # 假设时间格式类似 "2024-08-06 10:30" 或 "2小时前"
                if '小时前' in publish_time:
                    hours_match = re.search(r'(\d+)小时前', publish_time)
                    if hours_match:
                        hours = int(hours_match.group(1))
                        weight = max(0.3, 1.0 - hours / 48.0)  # 48小时内有效
                    else:
                        weight = 0.8
                elif '天前' in publish_time:
                    days_match = re.search(r'(\d+)天前', publish_time)
                    if days_match:
                        days = int(days_match.group(1))
                        weight = max(0.1, 1.0 - days / 14.0)  # 14天内有效
                    else:
                        weight = 0.5
                elif '-' in publish_time and ':' in publish_time:
                    # 假设是标准日期格式 YYYY-MM-DD HH:MM
                    weight = 0.9  # 标准格式给较高权重
                else:
                    weight = 0.6
                
                return round(weight, 2)
                
            except Exception:
                return 0.6
                
        except Exception:
            return 0.5
    
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
    
    def analyze_news_sentiment(self, news_data: List[Dict]) -> Dict:
        """分析新闻数据的情感"""
        try:
            if not news_data:
                return {
                    'overall_sentiment': 0.0,
                    'total_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'positive_ratio': 0.0,
                    'negative_ratio': 0.0,
                    'neutral_ratio': 1.0,
                    'confidence': 0.3
                }
            
            sentiment_scores = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for news_item in news_data:
                title = news_item.get('title', '')
                summary = news_item.get('summary', '')
                text = f"{title} {summary}".strip()
                
                if text:
                    sentiment_result = self._analyze_enhanced_text_sentiment(text)
                    score = sentiment_result.get('sentiment_score', 0.0)
                    sentiment_scores.append(score)
                    
                    if score > 0.1:
                        positive_count += 1
                    elif score < -0.1:
                        negative_count += 1
                    else:
                        neutral_count += 1
                else:
                    sentiment_scores.append(0.0)
                    neutral_count += 1
            
            total_count = len(news_data)
            overall_sentiment = sum(sentiment_scores) / total_count if total_count > 0 else 0.0
            
            # 计算置信度
            confidence = min(1.0, total_count / 10)  # 10条新闻为满置信度
            
            return {
                'overall_sentiment': round(overall_sentiment, 3),
                'total_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_ratio': positive_count / total_count if total_count > 0 else 0.0,
                'negative_ratio': negative_count / total_count if total_count > 0 else 0.0,
                'neutral_ratio': neutral_count / total_count if total_count > 0 else 1.0,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"新闻情感分析失败: {e}")
            return {
                'overall_sentiment': 0.0,
                'total_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'confidence': 0.3
            }

    def _get_error_result(self, symbol: str, error: str) -> Dict:
        """获取错误结果"""
        return {
            'symbol': symbol,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }