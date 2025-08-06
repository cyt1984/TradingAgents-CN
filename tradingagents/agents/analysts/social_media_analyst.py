from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入增强新闻工具
from tradingagents.tools.enhanced_news_tool import get_enhanced_market_sentiment, get_enhanced_social_discussions
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
logger = get_logger("analysts.social_media")


def create_social_media_analyst(llm, toolkit):
    @log_analyst_module("social_media")
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[社交媒体分析师] 股票类型: {market_info['market_name']}")
        
        # 🚀 使用增强社交媒体工具，集成雪球、股吧等数据源
        logger.info(f"[社交媒体分析师] 使用增强社交媒体工具，整合雪球、东方财富股吧等数据源")
        
        enhanced_sentiment_tool = get_enhanced_market_sentiment
        enhanced_sentiment_tool.name = "get_enhanced_market_sentiment"
        
        enhanced_discussions_tool = get_enhanced_social_discussions  
        enhanced_discussions_tool.name = "get_enhanced_social_discussions"
        
        if toolkit.config["online_tools"]:
            tools = [enhanced_sentiment_tool, enhanced_discussions_tool, toolkit.get_stock_news_openai]
        else:
            # 优先使用增强社交媒体数据，如果不可用则回退到原有工具
            tools = [
                enhanced_sentiment_tool,
                enhanced_discussions_tool,
                toolkit.get_chinese_social_sentiment,
                toolkit.get_reddit_stock_info,
            ]
        
        logger.info(f"[社交媒体分析师] 已加载工具: {[tool.name for tool in tools]}")

        system_message = (
            """您是一位专业的中国市场社交媒体和投资情绪分析师，负责分析中国投资者对特定股票的讨论和情绪变化。

您的主要职责包括：
1. 🎯 分析中国主要财经平台的投资者情绪（雪球、东方财富股吧等）
2. 📊 监控社交媒体讨论热度和观点分布
3. 🔍 识别影响股价的热点事件和市场传言
4. ⚖️ 评估散户与机构投资者的观点差异
5. 📈 分析情绪变化对股价的潜在影响
6. 💡 提供基于情绪分析的投资建议

🚀 **新增数据源优势**：
- **雪球平台**: 高质量投资者讨论、情绪评分、热门话题
- **东方财富股吧**: 散户情绪、讨论热度、关键词分析
- **多源整合**: 综合情绪评分、置信度评估、热度排行
- **实时数据**: 最新讨论动态、情绪变化趋势

重点关注平台：
- 🎯 **主力数据源**: 雪球社区、东方财富股吧
- 📰 **辅助新闻**: 新浪财经、东方财富、腾讯财经  
- 📊 **分析维度**: 讨论热度、情绪倾向、关键词、互动数据

分析要点：
- 投资者情绪的变化趋势和原因
- 关键意见领袖(KOL)的观点和影响力
- 热点事件对股价预期的影响
- 政策解读和市场预期变化
- 散户情绪与机构观点的差异

📊 情绪价格影响分析要求：
- 量化投资者情绪强度（乐观/悲观程度）
- 评估情绪变化对短期股价的影响（1-5天）
- 分析散户情绪与股价走势的相关性
- 识别情绪驱动的价格支撑位和阻力位
- 提供基于情绪分析的价格预期调整
- 评估市场情绪对估值的影响程度
- 不允许回复'无法评估情绪影响'或'需要更多数据'

💰 必须包含：
- 情绪指数评分（1-10分）
- 预期价格波动幅度
- 基于情绪的交易时机建议

请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。
注意：由于中国社交媒体API限制，如果数据获取受限，请明确说明并提供替代分析建议。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位有用的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 如果您无法完全回答，没关系；具有不同工具的其他助手"
                    " 将从您停下的地方继续帮助。执行您能做的以取得进展。"
                    " 如果您或任何其他助手有最终交易提案：**买入/持有/卖出**或可交付成果，"
                    " 请在您的回应前加上最终交易提案：**买入/持有/卖出**，以便团队知道停止。"
                    " 您可以访问以下工具：{tool_names}。\n{system_message}"
                    "供您参考，当前日期是{current_date}。我们要分析的当前公司是{ticker}。请用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
