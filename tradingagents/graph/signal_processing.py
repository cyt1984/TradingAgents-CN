# TradingAgents/graph/signal_processing.py

from langchain_openai import ChatOpenAI

# 导入统一日志系统和图处理模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_graph_module
logger = get_logger("graph.signal_processing")


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    @log_graph_module("signal_processing")
    def process_signal(self, full_signal: str, stock_symbol: str = None) -> dict:
        """
        Process a full trading signal to extract structured decision information.

        Args:
            full_signal: Complete trading signal text
            stock_symbol: Stock symbol to determine currency type

        Returns:
            Dictionary containing extracted decision information
        """

        # 检测股票类型和货币
        from tradingagents.utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(stock_symbol)
        is_china = market_info['is_china']
        is_hk = market_info['is_hk']
        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        logger.info(f"🔍 [SignalProcessor] 处理信号: 股票={stock_symbol}, 市场={market_info['market_name']}, 货币={currency}",
                   extra={'stock_symbol': stock_symbol, 'market': market_info['market_name'], 'currency': currency})

        messages = [
            (
                "system",
                f"""您是一位专业的金融分析助手，负责从交易员的分析报告中提取结构化的投资决策信息。

请从提供的分析报告中提取以下信息，并以JSON格式返回：

{{
    "action": "买入/持有/卖出",
    "target_price": 数字({currency}价格，**必须提供具体数值，不能为null**),
    "confidence": 数字(0-1之间，如果没有明确提及则为0.7),
    "risk_score": 数字(0-1之间，如果没有明确提及则为0.5),
    "reasoning": "决策的主要理由摘要"
}}

请确保：
1. action字段必须是"买入"、"持有"或"卖出"之一（绝对不允许使用英文buy/hold/sell）
2. target_price必须是具体的数字,target_price应该是合理的{currency}价格数字（使用{currency_symbol}符号）
3. confidence和risk_score应该在0-1之间
4. reasoning应该是简洁的中文摘要
5. 所有内容必须使用中文，不允许任何英文投资建议

特别注意：
- 股票代码 {stock_symbol or '未知'} 是{market_info['market_name']}，使用{currency}计价
- 目标价格必须与股票的交易货币一致（{currency_symbol}）

如果某些信息在报告中没有明确提及，请使用合理的默认值。""",
            ),
            ("human", full_signal),
        ]

        try:
            response = self.quick_thinking_llm.invoke(messages).content
            logger.debug(f"🔍 [SignalProcessor] LLM响应: {response[:200]}...")

            # 尝试解析JSON响应
            import json
            import re

            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                logger.debug(f"🔍 [SignalProcessor] 提取的JSON: {json_text}")
                decision_data = json.loads(json_text)

                # 验证和标准化数据
                action = decision_data.get('action', '持有')
                if action not in ['买入', '持有', '卖出']:
                    # 尝试映射英文和其他变体
                    action_map = {
                        'buy': '买入', 'hold': '持有', 'sell': '卖出',
                        'BUY': '买入', 'HOLD': '持有', 'SELL': '卖出',
                        '购买': '买入', '保持': '持有', '出售': '卖出',
                        'purchase': '买入', 'keep': '持有', 'dispose': '卖出'
                    }
                    action = action_map.get(action, '持有')
                    if action != decision_data.get('action', '持有'):
                        logger.debug(f"🔍 [SignalProcessor] 投资建议映射: {decision_data.get('action')} -> {action}")

                # 处理目标价格，确保正确提取
                target_price = decision_data.get('target_price')
                if target_price is None or target_price == "null" or target_price == "":
                    # 如果JSON中没有目标价格，尝试从reasoning和完整文本中提取
                    reasoning = decision_data.get('reasoning', '')
                    full_text = f"{reasoning} {full_signal}"  # 扩大搜索范围
                    
                    # 大幅增强的价格匹配模式
                    price_patterns = [
                        # 目标价格相关
                        r'目标价[位格]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',  # 目标价位: 45.50
                        r'\*\*目标价[位格]?\*\*[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',  # **目标价位**: 45.50
                        r'目标[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 目标: 45.50
                        r'目标价格[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',      # 目标价格: 45.50
                        # 价格、价位相关
                        r'价格[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 价格: 45.50
                        r'价位[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 价位: 45.50
                        r'股价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 股价: 45.50
                        r'现价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 现价: 45.50
                        r'当前价[格位]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)', # 当前价格: 45.50
                        r'当前股价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',      # 当前股价: 45.50
                        r'最新价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',       # 最新价: 45.50
                        r'收盘价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',       # 收盘价: 45.50
                        r'合理[价位格]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)', # 合理价位: 45.50
                        r'估值[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',         # 估值: 45.50
                        # 货币符号开头
                        r'[¥\$￥](\d+(?:\.\d+)?)',                      # ¥45.50 或 $190 或 ￥45.50
                        r'(\d+(?:\.\d+)?)元',                         # 45.50元
                        r'(\d+(?:\.\d+)?)美元',                       # 190美元
                        r'(\d+(?:\.\d+)?)港[币元]',                   # 45.50港币
                        # 建议、预期相关
                        r'建议[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',        # 建议: 45.50
                        r'预期[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',        # 预期: 45.50
                        r'看[到至]\s*[¥\$￥]?(\d+(?:\.\d+)?)',          # 看到45.50
                        r'上涨[到至]\s*[¥\$￥]?(\d+(?:\.\d+)?)',        # 上涨到45.50
                        r'(\d+(?:\.\d+)?)\s*[¥\$￥]',                  # 45.50¥
                        # 价格区间处理
                        r'(\d+(?:\.\d+)?)[-~到至](\d+(?:\.\d+)?)',      # 13.5-14.5 或 13.5~14.5
                        # 纯数字价格（最后匹配，避免误匹配）
                        r'(?<!\d)(\d{1,3}(?:\.\d{1,2})?)(?=\s*(?:元|美元|港[币元]|左右|附近))', # 13.52元
                    ]
                    
                    for pattern in price_patterns:
                        price_match = re.search(pattern, full_text, re.IGNORECASE)
                        if price_match:
                            try:
                                # 处理价格区间情况
                                if len(price_match.groups()) > 1 and price_match.group(2):
                                    # 价格区间，取中间值
                                    price1 = float(price_match.group(1))
                                    price2 = float(price_match.group(2))
                                    target_price = round((price1 + price2) / 2, 2)
                                    logger.debug(f"🔍 [SignalProcessor] 从价格区间提取目标价格: {price1}-{price2} -> {target_price}")
                                else:
                                    target_price = float(price_match.group(1))
                                    logger.debug(f"🔍 [SignalProcessor] 从文本中提取到目标价格: {target_price} (模式: {pattern})")
                                
                                # 价格合理性检查
                                if self._is_price_reasonable(target_price, is_china):
                                    break
                                else:
                                    logger.warning(f"⚠️ [SignalProcessor] 提取的价格不合理: {target_price}，继续尝试其他模式")
                                    target_price = None
                                    continue
                            except (ValueError, IndexError):
                                continue

                    # 如果仍然没有找到价格，尝试智能推算
                    if target_price is None or target_price == "null" or target_price == "":
                        target_price = self._smart_price_estimation(full_text, action, stock_symbol, is_china)
                        if target_price:
                            logger.debug(f"🔍 [SignalProcessor] 智能推算目标价格: {target_price}")
                        else:
                            # 最后手段：尝试从数据源获取当前股价并估算
                            target_price = self._fallback_price_estimation(stock_symbol, action, is_china)
                            if target_price:
                                logger.info(f"✅ [SignalProcessor] 使用数据源价格推算目标价格: {target_price}")
                            else:
                                logger.warning(f"⚠️ [SignalProcessor] 所有方法均未能提取到目标价格，设置为None")
                else:
                    # 确保价格是数值类型
                    try:
                        if isinstance(target_price, str):
                            # 清理字符串格式的价格
                            clean_price = target_price.replace('$', '').replace('¥', '').replace('￥', '').replace('元', '').replace('美元', '').strip()
                            target_price = float(clean_price) if clean_price and clean_price.lower() not in ['none', 'null', ''] else None
                        elif isinstance(target_price, (int, float)):
                            target_price = float(target_price)
                        logger.debug(f"🔍 [SignalProcessor] 处理后的目标价格: {target_price}")
                    except (ValueError, TypeError):
                        target_price = None
                        logger.warning(f"🔍 [SignalProcessor] 价格转换失败，设置为None")

                result = {
                    'action': action,
                    'target_price': target_price,
                    'confidence': float(decision_data.get('confidence', 0.7)),
                    'risk_score': float(decision_data.get('risk_score', 0.5)),
                    'reasoning': decision_data.get('reasoning', '基于综合分析的投资建议')
                }
                logger.info(f"🔍 [SignalProcessor] 处理结果: {result}",
                           extra={'action': result['action'], 'target_price': result['target_price'],
                                 'confidence': result['confidence'], 'stock_symbol': stock_symbol})
                return result
            else:
                # 如果无法解析JSON，使用简单的文本提取
                return self._extract_simple_decision(response)

        except Exception as e:
            logger.error(f"信号处理错误: {e}", exc_info=True, extra={'stock_symbol': stock_symbol})
            # 回退到简单提取
            return self._extract_simple_decision(full_signal)

    def _smart_price_estimation(self, text: str, action: str, stock_symbol: str, is_china: bool) -> float:
        """增强的智能价格推算方法"""
        import re
        
        logger.debug(f"🤖 [SmartEstimation] 开始智能价格推算: 股票={stock_symbol}, 动作={action}")
        
        # 尝试从文本中提取当前价格和涨跌幅信息
        current_price = None
        percentage_change = None
        
        # 增强的当前价格提取模式
        current_price_patterns = [
            r'当前价[格位]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'现价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'股价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'最新价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'收盘价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'交易价[格]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'[¥\$￥](\d+(?:\.\d+)?)',  # 简单货币符号
            r'(\d+(?:\.\d+)?)元',  # XX元
        ]
        
        for pattern in current_price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    current_price = float(match.group(1))
                    logger.debug(f"🤖 [SmartEstimation] 提取到当前价格: {current_price}")
                    break
                except ValueError:
                    continue
        
        # 增强的涨跌幅提取模式
        percentage_patterns = [
            r'上涨\s*(\d+(?:\.\d+)?)%',
            r'涨幅\s*(\d+(?:\.\d+)?)%',
            r'增长\s*(\d+(?:\.\d+)?)%',
            r'下跌\s*(\d+(?:\.\d+)?)%',
            r'跌幅\s*(\d+(?:\.\d+)?)%',
            r'(\d+(?:\.\d+)?)%\s*的?[上涨下跌]',
            r'[上涨下跌]\s*(\d+(?:\.\d+)?)%',
        ]
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    percentage_change = float(match.group(1)) / 100
                    # 判断是上涨还是下跌
                    if '下跌' in match.group(0) or '跌幅' in match.group(0):
                        percentage_change = -percentage_change
                    logger.debug(f"🤖 [SmartEstimation] 提取到涨跌幅: {percentage_change*100}%")
                    break
                except ValueError:
                    continue
        
        # 基于动作和信息推算目标价
        if current_price and percentage_change:
            if action == '买入':
                target = round(current_price * (1 + abs(percentage_change)), 2)
                logger.debug(f"🤖 [SmartEstimation] 基于涨幅计算买入目标: {target}")
                return target
            elif action == '卖出':
                target = round(current_price * (1 - abs(percentage_change)), 2)
                logger.debug(f"🤖 [SmartEstimation] 基于跌幅计算卖出目标: {target}")
                return target
        
        # 如果有当前价格但没有涨跌幅，使用默认估算
        if current_price:
            if action == '买入':
                # 买入建议默认10-20%涨幅
                multiplier = 1.15 if is_china else 1.12
                target = round(current_price * multiplier, 2)
                logger.debug(f"🤖 [SmartEstimation] 使用默认买入倍数: {target}")
                return target
            elif action == '卖出':
                # 卖出建议默认5-10%跌幅
                multiplier = 0.95 if is_china else 0.92
                target = round(current_price * multiplier, 2)
                logger.debug(f"🤖 [SmartEstimation] 使用默认卖出倍数: {target}")
                return target
            else:  # 持有
                # 持有建议使用当前价格
                logger.debug(f"🤖 [SmartEstimation] 持有建议使用当前价格: {current_price}")
                return current_price
        
        logger.debug(f"🤖 [SmartEstimation] 未能从文本提取到当前价格")
        return None
    
    def _is_price_reasonable(self, price: float, is_china: bool) -> bool:
        """检查价格合理性"""
        if price is None or price <= 0:
            return False
        
        # 不同市场的合理价格范围
        if is_china:
            # A股价格范围: 1-1000元
            return 1.0 <= price <= 1000.0
        else:
            # 美股/港股价格范围: 0.1-5000美元/港币
            return 0.1 <= price <= 5000.0
    
    def _fallback_price_estimation(self, stock_symbol: str, action: str, is_china: bool) -> float:
        """最后手段：从数据源获取当前股价并估算目标价格"""
        try:
            logger.debug(f"🔄 [FallbackEstimation] 尝试从数据源获取{stock_symbol}的当前股价")
            
            current_price = None
            
            # 尝试从数据源管理器获取最新价格
            try:
                from tradingagents.dataflows.data_source_manager import get_data_source_manager
                from datetime import datetime, timedelta
                
                manager = get_data_source_manager()
                
                # 获取最近三天的数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
                
                data_str = manager.get_stock_data(stock_symbol, start_date, end_date)
                
                if data_str and '最新价格' in data_str:
                    # 从数据结果中提取价格
                    import re
                    price_match = re.search(r'最新价格[:：]?\s*￥?(\d+(?:\.\d+)?)', data_str)
                    if price_match:
                        current_price = float(price_match.group(1))
                        logger.debug(f"🔄 [FallbackEstimation] 从数据源获取到价格: {current_price}")
                
            except Exception as e:
                logger.debug(f"🔄 [FallbackEstimation] 数据源获取失败: {e}")
            
            # 如果仍然没有获取到，尝试AKShare实时数据
            if current_price is None and is_china:
                try:
                    import akshare as ak
                    
                    # 获取A股实时数据
                    real_data = ak.stock_zh_a_spot_em()
                    stock_real = real_data[real_data['代码'] == stock_symbol]
                    
                    if not stock_real.empty:
                        current_price = float(stock_real.iloc[0]['最新价'])
                        logger.debug(f"🔄 [FallbackEstimation] 从AKShare获取到价格: {current_price}")
                        
                except Exception as e:
                    logger.debug(f"🔄 [FallbackEstimation] AKShare获取失败: {e}")
            
            # 如果成功获取到当前价格，计算目标价格
            if current_price and self._is_price_reasonable(current_price, is_china):
                if action == '买入':
                    # 买入目标: 当前价格 + 10-15%
                    multiplier = 1.12 if is_china else 1.10
                    target_price = round(current_price * multiplier, 2)
                    logger.debug(f"🔄 [FallbackEstimation] 计算买入目标: {current_price} * {multiplier} = {target_price}")
                    return target_price
                elif action == '卖出':
                    # 卖出目标: 当前价格 - 5-8%
                    multiplier = 0.95 if is_china else 0.92
                    target_price = round(current_price * multiplier, 2)
                    logger.debug(f"🔄 [FallbackEstimation] 计算卖出目标: {current_price} * {multiplier} = {target_price}")
                    return target_price
                else:  # 持有
                    # 持有目标: 当前价格附近
                    target_price = current_price
                    logger.debug(f"🔄 [FallbackEstimation] 持有目标: {target_price}")
                    return target_price
            
            logger.debug(f"🔄 [FallbackEstimation] 未能获取到有效的当前股价")
            return None
            
        except Exception as e:
            logger.error(f"❌ [FallbackEstimation] 备用价格估算失败: {e}")
            return None

    def _extract_simple_decision(self, text: str) -> dict:
        """简单的决策提取方法作为备用"""
        import re

        # 提取动作
        action = '持有'  # 默认
        if re.search(r'买入|BUY', text, re.IGNORECASE):
            action = '买入'
        elif re.search(r'卖出|SELL', text, re.IGNORECASE):
            action = '卖出'
        elif re.search(r'持有|HOLD', text, re.IGNORECASE):
            action = '持有'

        # 尝试提取目标价格（使用增强的模式）
        target_price = None
        price_patterns = [
            r'目标价[位格]?[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',  # 目标价位: 45.50
            r'\*\*目标价[位格]?\*\*[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',  # **目标价位**: 45.50
            r'目标[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',         # 目标: 45.50
            r'价格[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',         # 价格: 45.50
            r'[¥\$](\d+(?:\.\d+)?)',                      # ¥45.50 或 $190
            r'(\d+(?:\.\d+)?)元',                         # 45.50元
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, text)
            if price_match:
                try:
                    target_price = float(price_match.group(1))
                    break
                except ValueError:
                    continue

        # 如果没有找到价格，尝试智能推算
        if target_price is None:
            # 检测股票类型
            is_china = True  # 默认假设是A股，实际应该从上下文获取
            stock_symbol = "unknown"  # 简单提取方法中没有stock_symbol
            target_price = self._smart_price_estimation(text, action, stock_symbol, is_china)

        return {
            'action': action,
            'target_price': target_price,
            'confidence': 0.7,
            'risk_score': 0.5,
            'reasoning': '基于综合分析的投资建议'
        }
