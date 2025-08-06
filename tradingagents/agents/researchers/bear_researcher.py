from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

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

        # 获取机构研报观点（重点关注谨慎观点）
        institutional_caution = ""
        try:
            from tradingagents.dataflows.research_report_utils import get_stock_research_reports, get_institutional_consensus
            
            # 获取研报数据
            reports = get_stock_research_reports(company_name, limit=10)  
            consensus = get_institutional_consensus(company_name)
            
            if reports and consensus and consensus.get('total_reports', 0) > 0:
                # 提取看跌/谨慎观点支撑
                bearish_reports = [r for r in reports if r.rating in ['卖出', '减持']]
                neutral_reports = [r for r in reports if r.rating in ['持有', '中性']]
                
                if bearish_reports:
                    institutional_caution = f"""

📉 **机构谨慎观点支撑**：
- 看跌评级数量: {len(bearish_reports)} 份研报
- 谨慎机构: {', '.join(set([r.institution for r in bearish_reports[:5]]))}

**核心风险观点**："""
                    
                    for i, report in enumerate(bearish_reports[:3], 1):
                        institutional_caution += f"""
{i}. **{report.institution}**: {report.rating}
   - {report.summary}
   - 风险提示: {', '.join(report.key_points) if report.key_points else '存在下行风险'}"""
                
                elif neutral_reports:
                    institutional_caution = f"""

⚠️ **机构中性观望态度**：
- 中性评级数量: {len(neutral_reports)} 份研报
- 观望机构: {', '.join(set([r.institution for r in neutral_reports[:3]]))}
- 表明机构对前景存在不确定性"""
                
                # 分析目标价下行风险
                if consensus.get('target_price_range', {}).get('min'):
                    min_target = consensus['target_price_range']['min']
                    institutional_caution += f"""

📊 **估值风险分析**：
- 机构目标价下限: {min_target} {currency_symbol}
- 可能存在下行空间，需谨慎评估风险"""
                    
                # 分析机构分歧
                rating_dist = consensus.get('rating_distribution', {})
                if len(rating_dist) > 1:
                    institutional_caution += f"""

🔍 **机构观点分歧**：
- 评级分布: {rating_dist}
- 机构间存在明显分歧，增加投资不确定性"""
                        
                logger.debug(f"🐻 [看跌研究员] 获取到机构谨慎观点，看跌报告数: {len(bearish_reports)}")
            else:
                logger.debug(f"🐻 [看跌研究员] 暂无机构研报数据，将基于其他分析师报告识别风险点")
                institutional_caution = ""
                
        except Exception as e:
            logger.warning(f"⚠️ [看跌研究员] 获取机构观点失败: {e}")
            institutional_caution = ""

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}{institutional_caution}"

        # 安全检查：确保memory不为None
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""你是一位看跌分析师，负责论证不投资股票 {company_name} 的理由。

⚠️ 重要提醒：当前分析的是 {market_info['market_name']}，所有价格和估值请使用 {currency}（{currency_symbol}）作为单位。

你的目标是提出合理的论证，强调风险、挑战和负面指标。利用提供的研究和数据来突出潜在的不利因素并有效反驳看涨论点。

请用中文回答，重点关注以下几个方面：

- 风险和挑战：突出市场饱和、财务不稳定或宏观经济威胁等可能阻碍股票表现的因素
- 竞争劣势：强调市场地位较弱、创新下降或来自竞争对手威胁等脆弱性
- 负面指标：使用财务数据、市场趋势或最近不利消息的证据来支持你的立场
- **机构谨慎观点**：如有机构降级、减持评级或风险提示，请作为专业警示引用
- **分歧分析**：利用机构间观点分歧说明投资不确定性
- **估值下行风险**：基于机构目标价下限分析潜在损失空间
- 反驳看涨观点：用具体数据和合理推理批判性分析看涨论点，揭露弱点或过度乐观的假设
- 参与讨论：以对话风格呈现你的论点，直接回应看涨分析师的观点并进行有效辩论，而不仅仅是列举事实

可用资源：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务新闻：{news_report}
公司基本面报告：{fundamentals_report}
辩论对话历史：{history}
最后的看涨论点：{current_response}
类似情况的反思和经验教训：{past_memory_str}

请使用这些信息提供令人信服的看跌论点，反驳看涨声明，并参与动态辩论，展示投资该股票的风险和弱点。你还必须处理反思并从过去的经验教训和错误中学习。

请确保所有回答都使用中文。
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
