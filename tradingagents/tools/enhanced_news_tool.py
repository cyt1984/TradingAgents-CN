#!/usr/bin/env python3
"""
增强新闻工具
集成多个新闻数据源，提供更丰富的新闻数据
"""

from langchain_core.tools import tool
from typing import Dict, Any, List
import json
from datetime import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入增强数据源管理器
from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager

# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils


@tool
def get_enhanced_stock_news(ticker: str, limit: int = 30) -> str:
    """
    获取股票的增强新闻数据，整合多个新闻源
    
    Args:
        ticker: 股票代码（如：000001, AAPL, 0700.HK）
        limit: 返回新闻数量限制，默认30条
    
    Returns:
        str: 格式化的新闻分析数据，包含多数据源整合的新闻信息
    """
    try:
        logger.info(f"🔍 开始获取增强新闻数据: {ticker}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        market_name = market_info['market_name']
        
        logger.info(f"📊 股票类型: {market_name}")
        
        # 获取增强数据管理器
        manager = get_enhanced_data_manager()
        
        # 获取综合新闻数据
        news_data = manager.get_comprehensive_news(ticker, limit)
        
        if not news_data:
            logger.warning(f"⚠️ 未获取到新闻数据: {ticker}")
            return f"未能获取到股票 {ticker} 的新闻数据。请检查股票代码是否正确。"
        
        # 格式化新闻数据
        formatted_news = format_enhanced_news_data(ticker, news_data, market_info)
        
        logger.info(f"✅ 成功获取 {len(news_data)} 条增强新闻: {ticker}")
        return formatted_news
        
    except Exception as e:
        logger.error(f"❌ 获取增强新闻失败: {ticker}, 错误: {str(e)}")
        return f"获取股票 {ticker} 的新闻数据时发生错误: {str(e)}"


@tool 
def get_enhanced_market_sentiment(ticker: str) -> str:
    """
    获取股票的增强市场情绪分析，整合社交媒体数据
    
    Args:
        ticker: 股票代码（如：000001, AAPL, 0700.HK）
    
    Returns:
        str: 格式化的市场情绪分析报告
    """
    try:
        logger.info(f"😊 开始获取市场情绪分析: {ticker}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        
        # 获取增强数据管理器
        manager = get_enhanced_data_manager()
        
        # 获取综合情绪分析
        sentiment_data = manager.get_comprehensive_sentiment(ticker)
        
        if not sentiment_data:
            logger.warning(f"⚠️ 未获取到情绪数据: {ticker}")
            return f"未能获取到股票 {ticker} 的市场情绪数据。"
        
        # 获取社交讨论数据
        discussions = manager.get_social_discussions(ticker, 20)
        
        # 格式化情绪分析报告
        formatted_sentiment = format_sentiment_analysis(ticker, sentiment_data, discussions, market_info)
        
        logger.info(f"✅ 成功获取市场情绪分析: {ticker}")
        return formatted_sentiment
        
    except Exception as e:
        logger.error(f"❌ 获取市场情绪分析失败: {ticker}, 错误: {str(e)}")
        return f"获取股票 {ticker} 的市场情绪分析时发生错误: {str(e)}"


@tool
def get_enhanced_social_discussions(ticker: str, limit: int = 50) -> str:
    """
    获取股票的社交媒体讨论数据
    
    Args:
        ticker: 股票代码（如：000001, AAPL, 0700.HK）
        limit: 返回讨论数量限制，默认50条
    
    Returns:
        str: 格式化的社交讨论分析报告
    """
    try:
        logger.info(f"💬 开始获取社交讨论数据: {ticker}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        
        # 获取增强数据管理器
        manager = get_enhanced_data_manager()
        
        # 获取社交讨论数据
        discussions = manager.get_social_discussions(ticker, limit)
        
        if not discussions:
            logger.warning(f"⚠️ 未获取到讨论数据: {ticker}")
            return f"未能获取到股票 {ticker} 的社交讨论数据。"
        
        # 格式化讨论数据
        formatted_discussions = format_social_discussions(ticker, discussions, market_info)
        
        logger.info(f"✅ 成功获取 {len(discussions)} 条社交讨论: {ticker}")
        return formatted_discussions
        
    except Exception as e:
        logger.error(f"❌ 获取社交讨论失败: {ticker}, 错误: {str(e)}")
        return f"获取股票 {ticker} 的社交讨论数据时发生错误: {str(e)}"


def format_enhanced_news_data(ticker: str, news_data: List[Dict], market_info: Dict) -> str:
    """格式化增强新闻数据"""
    try:
        report = f"""# 📰 {ticker} 增强新闻分析报告

## 📊 基本信息
- **股票代码**: {ticker}
- **市场类型**: {market_info['market_name']}
- **货币单位**: {market_info['currency_name']}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **新闻总数**: {len(news_data)} 条

## 📰 最新新闻动态

"""
        
        # 按数据源分组新闻
        news_by_source = {}
        for news in news_data:
            source = news.get('data_source', news.get('source', '未知'))
            if source not in news_by_source:
                news_by_source[source] = []
            news_by_source[source].append(news)
        
        # 显示各数据源的新闻
        for source, source_news in news_by_source.items():
            report += f"### 📡 {source} ({len(source_news)} 条)\n\n"
            
            for i, news in enumerate(source_news[:10], 1):  # 每个源最多显示10条
                title = news.get('title', '无标题')
                publish_time = news.get('publish_time', news.get('publish_date', '时间未知'))
                summary = news.get('summary', news.get('content', ''))[:200]
                
                report += f"**{i}. {title}**\n"
                report += f"   - 发布时间: {publish_time}\n"
                if summary:
                    report += f"   - 内容摘要: {summary}...\n"
                report += "\n"
        
        # 新闻统计分析
        report += "## 📊 新闻分析统计\n\n"
        
        # 新闻来源分布
        report += "### 数据源分布\n\n"
        report += "| 数据源 | 新闻数量 | 占比 |\n"
        report += "|--------|----------|------|\n"
        
        total_news = len(news_data)
        for source, source_news in news_by_source.items():
            count = len(source_news)
            percentage = (count / total_news * 100) if total_news > 0 else 0
            report += f"| {source} | {count} | {percentage:.1f}% |\n"
        
        # 新闻时效性分析
        recent_news = sum(1 for news in news_data if is_recent_news(news))
        report += f"\n### 时效性分析\n"
        report += f"- **24小时内新闻**: {recent_news} 条\n"
        report += f"- **新闻时效性**: {'高' if recent_news > total_news * 0.3 else '中等' if recent_news > 0 else '低'}\n"
        
        # 关键词分析
        keywords = extract_keywords_from_news(news_data)
        if keywords:
            report += f"\n### 热门关键词\n"
            for i, (keyword, count) in enumerate(keywords[:10], 1):
                report += f"{i}. **{keyword}** ({count}次)\n"
        
        return report
        
    except Exception as e:
        logger.error(f"❌ 格式化新闻数据失败: {str(e)}")
        return f"格式化新闻数据时发生错误: {str(e)}"


def format_sentiment_analysis(ticker: str, sentiment_data: Dict, discussions: List[Dict], market_info: Dict) -> str:
    """格式化情绪分析报告"""
    try:
        overall_sentiment = sentiment_data.get('overall_sentiment', 0)
        confidence = sentiment_data.get('confidence', 0)
        sources = sentiment_data.get('sources', [])
        
        # 情绪等级判定
        if overall_sentiment > 0.3:
            sentiment_level = "积极乐观"
            sentiment_emoji = "📈"
        elif overall_sentiment > 0.1:
            sentiment_level = "偏向积极"
            sentiment_emoji = "🔼"
        elif overall_sentiment > -0.1:
            sentiment_level = "中性观望"
            sentiment_emoji = "🔸"
        elif overall_sentiment > -0.3:
            sentiment_level = "偏向悲观"
            sentiment_emoji = "🔽"
        else:
            sentiment_level = "消极悲观"
            sentiment_emoji = "📉"
        
        report = f"""# 😊 {ticker} 市场情绪分析报告

## 📊 基本信息
- **股票代码**: {ticker}
- **市场类型**: {market_info['market_name']}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 整体情绪评估

### 综合情绪评分
- **情绪评分**: {overall_sentiment:.3f} (范围: -1.0 到 1.0)
- **情绪等级**: {sentiment_emoji} {sentiment_level}
- **置信度**: {confidence:.2f}
- **数据源**: {', '.join(sources)}

### 情绪指标解读
"""
        
        # 情绪详细分析
        details = sentiment_data.get('details', {})
        for source, source_data in details.items():
            report += f"\n#### 📡 {source} 情绪分析\n"
            report += f"- **讨论总数**: {source_data.get('total_discussions', 0)} 条\n"
            report += f"- **积极比例**: {source_data.get('positive_ratio', 0):.1%}\n"
            report += f"- **消极比例**: {source_data.get('negative_ratio', 0):.1%}\n"
            report += f"- **中性比例**: {source_data.get('neutral_ratio', 0):.1%}\n"
            
            # 热门关键词
            if 'hot_keywords' in source_data:
                keywords = source_data['hot_keywords']
                if keywords:
                    report += f"- **热门关键词**: {', '.join(keywords[:5])}\n"
        
        # 社交讨论分析
        if discussions:
            report += f"\n## 💬 社交讨论热度分析\n\n"
            report += f"### 讨论概况\n"
            report += f"- **讨论总数**: {len(discussions)} 条\n"
            
            # 按数据源分类讨论
            discussion_by_source = {}
            total_heat = 0
            for disc in discussions:
                source = disc.get('data_source', '未知')
                if source not in discussion_by_source:
                    discussion_by_source[source] = []
                discussion_by_source[source].append(disc)
                total_heat += disc.get('heat_score', 0)
            
            report += f"- **平均热度**: {total_heat / len(discussions):.1f}\n"
            report += f"- **数据源**: {', '.join(discussion_by_source.keys())}\n"
            
            # 热门讨论
            top_discussions = sorted(discussions, key=lambda x: x.get('heat_score', 0), reverse=True)[:5]
            report += f"\n### 🔥 热门讨论\n\n"
            
            for i, disc in enumerate(top_discussions, 1):
                title = disc.get('title', '无标题')[:80]
                heat_score = disc.get('heat_score', 0)
                source = disc.get('data_source', '未知')
                sentiment_score = disc.get('sentiment_score', 0)
                
                sentiment_icon = "📈" if sentiment_score > 0.1 else "📉" if sentiment_score < -0.1 else "➡️"
                
                report += f"**{i}. {title}...**\n"
                report += f"   - 热度评分: {heat_score}\n"
                report += f"   - 情绪倾向: {sentiment_icon} {sentiment_score:.2f}\n"
                report += f"   - 数据源: {source}\n\n"
        
        # 投资建议
        report += f"\n## 💡 基于情绪的投资参考\n\n"
        
        if overall_sentiment > 0.2:
            report += "### 🟢 积极信号\n"
            report += "- 市场情绪偏向积极，投资者信心较强\n"
            report += "- 社交媒体讨论热度较高，关注度提升\n"
            report += "- **参考建议**: 可关注短期上涨机会，但需注意风险控制\n"
        elif overall_sentiment < -0.2:
            report += "### 🔴 消极信号\n"
            report += "- 市场情绪偏向悲观，投资者情绪低迷\n"
            report += "- 需关注潜在的负面因素和风险点\n"
            report += "- **参考建议**: 建议谨慎观望，等待情绪改善信号\n"
        else:
            report += "### 🟡 中性观望\n"
            report += "- 市场情绪相对中性，投资者观望情绪较重\n"
            report += "- 缺乏明确的方向性信号\n"
            report += "- **参考建议**: 持续关注基本面变化和消息面动态\n"
        
        return report
        
    except Exception as e:
        logger.error(f"❌ 格式化情绪分析失败: {str(e)}")
        return f"格式化情绪分析时发生错误: {str(e)}"


def format_social_discussions(ticker: str, discussions: List[Dict], market_info: Dict) -> str:
    """格式化社交讨论报告"""
    try:
        report = f"""# 💬 {ticker} 社交媒体讨论分析

## 📊 基本信息
- **股票代码**: {ticker}
- **市场类型**: {market_info['market_name']}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **讨论总数**: {len(discussions)} 条

## 🔥 讨论热度排行

"""
        
        # 按热度排序显示讨论
        sorted_discussions = sorted(discussions, key=lambda x: x.get('heat_score', 0), reverse=True)
        
        for i, disc in enumerate(sorted_discussions[:20], 1):  # 显示前20条
            title = disc.get('title', '无标题')
            heat_score = disc.get('heat_score', 0)
            reply_count = disc.get('reply_count', 0)
            read_count = disc.get('read_count', disc.get('view_count', 0))
            source = disc.get('data_source', disc.get('source', '未知'))
            sentiment_score = disc.get('sentiment_score', 0)
            
            sentiment_icon = "📈" if sentiment_score > 0.1 else "📉" if sentiment_score < -0.1 else "➡️"
            
            report += f"### {i}. {title}\n"
            report += f"- **热度评分**: {heat_score}\n"
            report += f"- **回复数**: {reply_count}\n"
            report += f"- **阅读数**: {read_count}\n"
            report += f"- **情绪倾向**: {sentiment_icon} {sentiment_score:.2f}\n"
            report += f"- **数据源**: {source}\n\n"
        
        # 统计分析
        report += "## 📊 讨论统计分析\n\n"
        
        # 按数据源分组
        source_stats = {}
        total_interactions = 0
        sentiment_scores = []
        
        for disc in discussions:
            source = disc.get('data_source', disc.get('source', '未知'))
            if source not in source_stats:
                source_stats[source] = {'count': 0, 'total_heat': 0}
            
            source_stats[source]['count'] += 1
            source_stats[source]['total_heat'] += disc.get('heat_score', 0)
            
            total_interactions += disc.get('reply_count', 0) + disc.get('read_count', disc.get('view_count', 0))
            
            sentiment = disc.get('sentiment_score', 0)
            if sentiment != 0:
                sentiment_scores.append(sentiment)
        
        # 数据源统计
        report += "### 数据源分布\n\n"
        report += "| 数据源 | 讨论数量 | 平均热度 |\n"
        report += "|--------|----------|----------|\n"
        
        for source, stats in source_stats.items():
            avg_heat = stats['total_heat'] / stats['count'] if stats['count'] > 0 else 0
            report += f"| {source} | {stats['count']} | {avg_heat:.1f} |\n"
        
        # 情绪分布
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            positive_count = sum(1 for s in sentiment_scores if s > 0.1)
            negative_count = sum(1 for s in sentiment_scores if s < -0.1)
            neutral_count = len(sentiment_scores) - positive_count - negative_count
            
            report += f"\n### 情绪分布\n"
            report += f"- **平均情绪**: {avg_sentiment:.3f}\n"
            report += f"- **积极讨论**: {positive_count} 条 ({positive_count/len(sentiment_scores):.1%})\n"
            report += f"- **消极讨论**: {negative_count} 条 ({negative_count/len(sentiment_scores):.1%})\n"
            report += f"- **中性讨论**: {neutral_count} 条 ({neutral_count/len(sentiment_scores):.1%})\n"
        
        report += f"\n### 互动统计\n"
        report += f"- **总互动数**: {total_interactions:,}\n"
        report += f"- **平均互动数**: {total_interactions/len(discussions):.1f}\n"
        
        return report
        
    except Exception as e:
        logger.error(f"❌ 格式化社交讨论失败: {str(e)}")
        return f"格式化社交讨论时发生错误: {str(e)}"


def is_recent_news(news: Dict) -> bool:
    """判断新闻是否为最近24小时内的"""
    try:
        publish_time = news.get('publish_time', news.get('publish_date', ''))
        if not publish_time:
            return False
        
        # 简单的时间判断，可以根据需要改进
        current_time = datetime.now()
        
        # 如果包含"小时前"、"分钟前"等词汇，认为是最近的
        if any(keyword in str(publish_time) for keyword in ['小时前', '分钟前', '刚刚', '今天']):
            return True
        
        return False
        
    except Exception:
        return False


def extract_keywords_from_news(news_data: List[Dict]) -> List[tuple]:
    """从新闻中提取关键词"""
    try:
        keyword_freq = {}
        
        for news in news_data:
            title = news.get('title', '')
            content = news.get('summary', news.get('content', ''))
            text = title + ' ' + content
            
            # 简单的关键词提取（可以改进为更复杂的NLP方法）
            import re
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)  # 提取中文词汇
            
            for word in words:
                if len(word) >= 2 and word not in ['股票', '公司', '市场', '投资', '分析', '报告']:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1
        
        # 按频率排序
        return sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        
    except Exception:
        return []


def create_enhanced_news_toolkit():
    """创建增强新闻工具包"""
    return [
        get_enhanced_stock_news,
        get_enhanced_market_sentiment,
        get_enhanced_social_discussions
    ]