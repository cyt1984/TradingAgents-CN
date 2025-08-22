# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from tradingagents.llm_adapters import ChatDashScope, ChatDashScopeOpenAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config

# 导入动态LLM管理器
from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals", "heat"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs using Dynamic LLM Manager
        self.llm_manager = get_llm_manager()
        
        # Check if specific models are configured in config
        deep_think_model = self.config.get("deep_think_llm")
        quick_think_model = self.config.get("quick_think_llm")
        
        # Try to use the configured model or auto-select available one
        if deep_think_model:
            # Try to find a matching model in available models
            available_models = self.llm_manager.get_enabled_models()
            matching_model = None
            
            for model_key, model_info in available_models.items():
                if (model_info['model_name'] == deep_think_model or 
                    deep_think_model in model_info['model_name'] or
                    model_key.endswith(deep_think_model.replace('-', '_'))):
                    matching_model = model_key
                    break
            
            if matching_model:
                success = self.llm_manager.set_current_model(matching_model)
                if success:
                    logger.info(f"🤖 [动态LLM] 已设置指定模型: {deep_think_model}")
                else:
                    logger.warning(f"⚠️ [动态LLM] 无法设置指定模型: {deep_think_model}, 将自动选择")
            else:
                logger.warning(f"⚠️ [动态LLM] 未找到匹配的模型: {deep_think_model}, 将自动选择")
        
        # Get LLM instances from the manager
        try:
            current_llm = self.llm_manager.get_current_llm()
            if current_llm is None:
                raise ValueError("无法获取任何可用的LLM实例，请检查API密钥配置")
            
            # Use the same LLM for both deep and quick thinking for now
            # In the future, we could support different models for different purposes
            self.deep_thinking_llm = current_llm
            self.quick_thinking_llm = current_llm
            
            current_config = self.llm_manager.get_current_config()
            if current_config:
                logger.info(f"🤖 [动态LLM] 已初始化: {current_config.display_name or current_config.model_name}")
                logger.info(f"   提供商: {current_config.provider}")
                logger.info(f"   模型: {current_config.model_name}")
            else:
                logger.info("🤖 [动态LLM] 已初始化，使用默认配置")
                
        except Exception as e:
            logger.error(f"❌ [动态LLM] 初始化失败: {e}")
            # 如果动态LLM失败，尝试使用旧的配置方式作为fallback
            logger.warning("⚠️ [动态LLM] 尝试使用传统配置方式作为备选")
            if self.config.get("llm_provider", "").lower() == "openai":
                self.deep_thinking_llm = ChatOpenAI(
                    model=self.config.get("deep_think_llm", "gpt-4o"),
                    base_url=self.config.get("backend_url"),
                    temperature=0.1,
                    max_tokens=2000
                )
                self.quick_thinking_llm = self.deep_thinking_llm
            else:
                raise e
        
        self.toolkit = Toolkit(config=self.config)

        # Initialize memories (如果启用)
        memory_enabled = self.config.get("memory_enabled", True)
        if memory_enabled:
            # 使用单例ChromaDB管理器，避免并发创建冲突
            self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
            self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
            self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
            self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
            self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
        else:
            # 创建空的内存对象
            self.bull_memory = None
            self.bear_memory = None
            self.trader_memory = None
            self.invest_judge_memory = None
            self.risk_manager_memory = None

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.toolkit,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
            self.config,
            getattr(self, 'react_llm', None),
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources."""
        return {
            "market": ToolNode(
                [
                    # 统一工具
                    self.toolkit.get_stock_market_data_unified,
                    # online tools
                    self.toolkit.get_YFin_data_online,
                    self.toolkit.get_stockstats_indicators_report_online,
                    # offline tools
                    self.toolkit.get_YFin_data,
                    self.toolkit.get_stockstats_indicators_report,
                ]
            ),
            "social": ToolNode(
                [
                    # online tools
                    self.toolkit.get_stock_news_openai,
                    # offline tools
                    self.toolkit.get_reddit_stock_info,
                ]
            ),
            "news": ToolNode(
                [
                    # online tools
                    self.toolkit.get_global_news_openai,
                    self.toolkit.get_google_news,
                    # offline tools
                    self.toolkit.get_finnhub_news,
                    self.toolkit.get_reddit_news,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # 统一工具
                    self.toolkit.get_stock_fundamentals_unified,
                    # offline tools
                    self.toolkit.get_finnhub_company_insider_sentiment,
                    self.toolkit.get_finnhub_company_insider_transactions,
                    self.toolkit.get_simfin_balance_sheet,
                    self.toolkit.get_simfin_cashflow,
                    self.toolkit.get_simfin_income_stmt,
                ]
            ),
            "heat": ToolNode([]),  # 热度分析师使用内部工具，不需要外部工具节点
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        # 添加详细的接收日志
        logger.debug(f"🔍 [GRAPH DEBUG] ===== TradingAgentsGraph.propagate 接收参数 =====")
        logger.debug(f"🔍 [GRAPH DEBUG] 接收到的company_name: '{company_name}' (类型: {type(company_name)})")
        logger.debug(f"🔍 [GRAPH DEBUG] 接收到的trade_date: '{trade_date}' (类型: {type(trade_date)})")

        self.ticker = company_name
        logger.debug(f"🔍 [GRAPH DEBUG] 设置self.ticker: '{self.ticker}'")

        # Initialize state
        logger.debug(f"🔍 [GRAPH DEBUG] 创建初始状态，传递参数: company_name='{company_name}', trade_date='{trade_date}'")
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        logger.debug(f"🔍 [GRAPH DEBUG] 初始状态中的company_of_interest: '{init_agent_state.get('company_of_interest', 'NOT_FOUND')}'")
        logger.debug(f"🔍 [GRAPH DEBUG] 初始状态中的trade_date: '{init_agent_state.get('trade_date', 'NOT_FOUND')}'")
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"], company_name)

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "heat_report": final_state.get("heat_report", ""),
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal, stock_symbol=None):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal, stock_symbol)

    def switch_llm_model(self, model_key: str) -> bool:
        """
        动态切换LLM模型
        
        Args:
            model_key: 模型键值 (如 'dashscope_qwen_max', 'openai_gpt4o' 等)
            
        Returns:
            是否切换成功
        """
        try:
            logger.info(f"🔄 [动态LLM] 尝试切换模型: {model_key}")
            
            success = self.llm_manager.set_current_model(model_key)
            if success:
                # 更新LLM实例
                new_llm = self.llm_manager.get_current_llm()
                if new_llm:
                    self.deep_thinking_llm = new_llm
                    self.quick_thinking_llm = new_llm
                    
                    current_config = self.llm_manager.get_current_config()
                    logger.info(f"✅ [动态LLM] 模型切换成功: {current_config.display_name or current_config.model_name}")
                    return True
                else:
                    logger.error(f"❌ [动态LLM] 获取新模型实例失败")
                    return False
            else:
                logger.error(f"❌ [动态LLM] 模型切换失败: {model_key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [动态LLM] 模型切换异常: {e}")
            return False

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的模型列表"""
        try:
            return self.llm_manager.get_enabled_models()
        except Exception as e:
            logger.error(f"❌ [动态LLM] 获取可用模型失败: {e}")
            return {}

    def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """获取当前模型信息"""
        try:
            current_config = self.llm_manager.get_current_config()
            if current_config:
                return {
                    'provider': current_config.provider,
                    'model_name': current_config.model_name,
                    'display_name': current_config.display_name,
                    'description': current_config.description,
                    'temperature': current_config.temperature,
                    'max_tokens': current_config.max_tokens
                }
            return None
        except Exception as e:
            logger.error(f"❌ [动态LLM] 获取当前模型信息失败: {e}")
            return None

    def test_current_model(self) -> Dict[str, Any]:
        """测试当前模型连接"""
        try:
            current_config = self.llm_manager.get_current_config()
            if not current_config:
                return {'success': False, 'error': '无当前模型配置'}
            
            # 找到当前模型的键值
            for model_key, config in self.llm_manager.available_configs.items():
                if config == current_config:
                    return self.llm_manager.test_model(model_key)
            
            return {'success': False, 'error': '无法找到当前模型键值'}
            
        except Exception as e:
            logger.error(f"❌ [动态LLM] 测试模型失败: {e}")
            return {'success': False, 'error': str(e)}
