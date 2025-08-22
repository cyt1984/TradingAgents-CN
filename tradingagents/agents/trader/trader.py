import functools
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # 使用统一的股票类型检测
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(company_name)
        is_china = market_info['is_china']
        is_hk = market_info['is_hk']
        is_us = market_info['is_us']

        # 根据股票类型确定货币单位
        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        logger.debug(f"💰 [DEBUG] ===== 交易员节点开始 =====")
        logger.debug(f"💰 [DEBUG] 交易员检测股票类型: {company_name} -> {market_info['market_name']}, 货币: {currency}")
        logger.debug(f"💰 [DEBUG] 货币符号: {currency_symbol}")
        logger.debug(f"💰 [DEBUG] 市场详情: 中国A股={is_china}, 港股={is_hk}, 美股={is_us}")
        logger.debug(f"💰 [DEBUG] 基本面报告长度: {len(fundamentals_report)}")
        logger.debug(f"💰 [DEBUG] 基本面报告前200字符: {fundamentals_report[:200]}...")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        # 获取实时股价信息用于准确计算目标价格
        current_stock_price = None
        price_info_str = "暂无实时股价数据"
        
        try:
            logger.debug(f"💰 [DEBUG] 开始获取{company_name}的实时股价...")
            
            if is_china:
                # A股：尝试获取实时数据
                try:
                    import akshare as ak
                    real_data = ak.stock_zh_a_spot_em()
                    stock_real = real_data[real_data['代码'] == company_name]
                    
                    if not stock_real.empty:
                        current_stock_price = float(stock_real.iloc[0]['最新价'])
                        change_pct = stock_real.iloc[0]['涨跌幅']
                        change_amount = stock_real.iloc[0]['涨跌额']
                        price_info_str = f"""📊 {company_name} 实时股价信息：
- 最新价：¥{current_stock_price}
- 涨跌幅：{change_pct}%
- 涨跌额：¥{change_amount}
- 数据来源：东方财富（实时）"""
                        logger.debug(f"💰 [DEBUG] 获取到A股实时价格: {current_stock_price}")
                except Exception as e:
                    logger.debug(f"💰 [DEBUG] A股实时数据获取失败: {e}")
            
            # 如果实时数据获取失败，尝试从数据源管理器获取最新数据
            if current_stock_price is None:
                try:
                    from tradingagents.dataflows.data_source_manager import get_data_source_manager
                    from datetime import datetime, timedelta
                    
                    manager = get_data_source_manager()
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
                    
                    data_str = manager.get_stock_data(company_name, start_date, end_date)
                    
                    if data_str and ('最新价格' in data_str or '收盘' in data_str):
                        import re
                        # 尝试多种价格模式
                        price_patterns = [
                            r'最新价格[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
                            r'收盘[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
                            r'价格[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
                        ]
                        
                        for pattern in price_patterns:
                            price_match = re.search(pattern, data_str)
                            if price_match:
                                current_stock_price = float(price_match.group(1))
                                price_info_str = f"""📊 {company_name} 股价信息：
- 当前价格：{currency_symbol}{current_stock_price}
- 数据来源：历史数据（最新）"""
                                logger.debug(f"💰 [DEBUG] 从数据源获取到价格: {current_stock_price}")
                                break
                                
                except Exception as e:
                    logger.debug(f"💰 [DEBUG] 数据源获取失败: {e}")
            
        except Exception as e:
            logger.error(f"💰 [ERROR] 获取股价信息失败: {e}")
        
        # 检查memory是否可用
        if memory is not None:
            logger.warning(f"⚠️ [DEBUG] memory可用，获取历史记忆")
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = ""
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []
            past_memory_str = "暂无历史记忆数据可参考。"

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""您是一位专业的交易员，负责分析市场数据并做出投资决策。基于您的分析，请提供具体的买入、卖出或持有建议。

⚠️ 重要提醒：当前分析的股票代码是 {company_name}，请使用正确的货币单位：{currency}（{currency_symbol}）

{price_info_str}

🎯 **目标价格计算基准**：
{'- 当前股价基准：' + currency_symbol + str(current_stock_price) if current_stock_price else '- 请基于基本面分析中的最新股价数据'}
- 必须基于真实的当前股价进行目标价格计算
- 目标价格应该合理反映股票的内在价值和市场预期

🔴 严格要求：
- 股票代码 {company_name} 的公司名称必须严格按照基本面报告中的真实数据
- 绝对禁止使用错误的公司名称或混淆不同的股票
- 所有分析必须基于提供的真实数据，不允许假设或编造
- **必须提供具体的目标价位，不允许设置为null或空值**

请在您的分析中包含以下关键信息：
1. **投资建议**: 明确的买入/持有/卖出决策
2. **目标价位**: 基于分析的合理目标价格({currency}) - 🚨 强制要求提供具体数值
   - 买入建议：提供目标价位和预期涨幅
   - 持有建议：提供合理价格区间（如：{currency_symbol}XX-XX）
   - 卖出建议：提供止损价位和目标卖出价
3. **置信度**: 对决策的信心程度(0-1之间)
4. **风险评分**: 投资风险等级(0-1之间，0为低风险，1为高风险)
5. **详细推理**: 支持决策的具体理由

🎯 目标价位计算指导：
- **严格基于上述提供的当前股价进行计算**
- 基于基本面分析中的估值数据（P/E、P/B、DCF等）
- 参考技术分析的支撑位和阻力位
- 考虑行业平均估值水平
- 结合市场情绪和新闻影响
- 即使市场情绪过热，也要基于合理估值给出目标价
- **目标价格必须在当前股价的合理范围内（±50%以内）**
- **如果计算出的目标价格与当前股价差异过大，请重新检查计算逻辑**

特别注意：
- 如果是中国A股（6位数字代码），请使用人民币（¥）作为价格单位
- 如果是美股或港股，请使用美元（$）作为价格单位
- 目标价位必须与当前股价的货币单位保持一致
- 必须使用基本面报告中提供的正确公司名称
- **绝对不允许说"无法确定目标价"或"需要更多信息"**

请用中文撰写分析内容，并始终以'最终交易建议: **买入/持有/卖出**'结束您的回应以确认您的建议。

请不要忘记利用过去决策的经验教训来避免重复错误。以下是类似情况下的交易反思和经验教训: {past_memory_str}""",
            },
            context,
        ]

        logger.debug(f"💰 [DEBUG] 准备调用LLM，系统提示包含货币: {currency}")
        logger.debug(f"💰 [DEBUG] 系统提示中的关键部分: 目标价格({currency})")

        result = llm.invoke(messages)

        logger.debug(f"💰 [DEBUG] LLM调用完成")
        logger.debug(f"💰 [DEBUG] 交易员回复长度: {len(result.content)}")
        logger.debug(f"💰 [DEBUG] 交易员回复前500字符: {result.content[:500]}...")
        logger.debug(f"💰 [DEBUG] ===== 交易员节点结束 =====")

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
