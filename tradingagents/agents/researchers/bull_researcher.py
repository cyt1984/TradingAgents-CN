from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        logger.debug(f"🐂 [DEBUG] ===== 看涨研究员节点开始 =====")

        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # 使用统一的股票类型检测
        company_name = state.get('company_of_interest', 'Unknown')
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(company_name)
        is_china = market_info['is_china']
        is_hk = market_info['is_hk']
        is_us = market_info['is_us']

        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        logger.debug(f"🐂 [DEBUG] 接收到的报告:")
        logger.debug(f"🐂 [DEBUG] - 市场报告长度: {len(market_research_report)}")
        logger.debug(f"🐂 [DEBUG] - 情绪报告长度: {len(sentiment_report)}")
        logger.debug(f"🐂 [DEBUG] - 新闻报告长度: {len(news_report)}")
        logger.debug(f"🐂 [DEBUG] - 基本面报告长度: {len(fundamentals_report)}")
        logger.debug(f"🐂 [DEBUG] - 基本面报告前200字符: {fundamentals_report[:200]}...")
        logger.debug(f"🐂 [DEBUG] - 股票代码: {company_name}, 类型: {market_info['market_name']}, 货币: {currency}")
        logger.debug(f"🐂 [DEBUG] - 市场详情: 中国A股={is_china}, 港股={is_hk}, 美股={is_us}")

        # 获取机构研报观点支撑
        institutional_support = ""
        try:
            from tradingagents.dataflows.research_report_utils import get_stock_research_reports, get_institutional_consensus
            
            # 获取研报数据
            reports = get_stock_research_reports(company_name, limit=10)
            consensus = get_institutional_consensus(company_name)
            
            if reports and consensus and consensus.get('total_reports', 0) > 0:
                # 提取看涨观点支撑
                bullish_reports = [r for r in reports if r.rating in ['买入', '增持', '强推']]
                
                if bullish_reports:
                    institutional_support = f"""

📈 **机构看涨观点支撑**：
- 看涨评级数量: {len(bullish_reports)} 份研报
- 覆盖机构: {', '.join(set([r.institution for r in bullish_reports[:5]]))}
- 平均目标价: {consensus.get('average_target_price', '未知')} {currency_symbol}
- 目标价上限: {consensus.get('target_price_range', {}).get('max', '未知')} {currency_symbol}

**核心看涨论点**："""
                    
                    # 提取关键观点
                    for i, report in enumerate(bullish_reports[:3], 1):
                        institutional_support += f"""
{i}. **{report.institution}**: {report.rating}
   - {report.summary}
   - 关键观点: {', '.join(report.key_points) if report.key_points else '持续看好'}"""
                    
                    if consensus.get('average_profit_growth'):
                        institutional_support += f"\n- 机构预期利润增长: {consensus['average_profit_growth']:.1%}"
                else:
                    # 即使没有明确看涨评级，也提取正面信息
                    if consensus.get('average_target_price'):
                        institutional_support = f"""

📊 **机构观点参考**：
- 机构平均目标价: {consensus['average_target_price']} {currency_symbol}
- 覆盖机构数: {consensus.get('institution_count', 0)} 家
- 可作为估值参考和论证支撑"""
                        
                logger.debug(f"🐂 [看涨研究员] 获取到机构支撑观点，看涨报告数: {len(bullish_reports)}")
            else:
                logger.debug(f"🐂 [看涨研究员] 暂无机构研报数据，将基于其他分析师报告进行论证")
                institutional_support = ""
                
        except Exception as e:
            logger.warning(f"⚠️ [看涨研究员] 获取机构观点失败: {e}")
            institutional_support = ""

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}{institutional_support}"

        # 安全检查：确保memory不为None
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""你是一位看涨分析师，负责为股票 {company_name} 的投资建立强有力的论证。

⚠️ 重要提醒：当前分析的是 {'中国A股' if is_china else '海外股票'}，所有价格和估值请使用 {currency}（{currency_symbol}）作为单位。

你的任务是构建基于证据的强有力案例，强调增长潜力、竞争优势和积极的市场指标。利用提供的研究和数据来解决担忧并有效反驳看跌论点。

请用中文回答，重点关注以下几个方面：
- 增长潜力：突出公司的市场机会、收入预测和可扩展性
- 竞争优势：强调独特产品、强势品牌或主导市场地位等因素
- 积极指标：使用财务健康状况、行业趋势和最新积极消息作为证据
- **机构观点支撑**：如有机构看涨评级和目标价，请作为权威论证引用
- **专业背书**：利用知名券商的分析师观点增强论证可信度
- 反驳看跌观点：用具体数据和合理推理批判性分析看跌论点，全面解决担忧并说明为什么看涨观点更有说服力
- 参与讨论：以对话风格呈现你的论点，直接回应看跌分析师的观点并进行有效辩论，而不仅仅是列举数据

可用资源：
市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务新闻：{news_report}
公司基本面报告：{fundamentals_report}
辩论对话历史：{history}
最后的看跌论点：{current_response}
类似情况的反思和经验教训：{past_memory_str}

请使用这些信息提供令人信服的看涨论点，反驳看跌担忧，并参与动态辩论，展示看涨立场的优势。你还必须处理反思并从过去的经验教训和错误中学习。

请确保所有回答都使用中文。
"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
