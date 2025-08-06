#!/usr/bin/env python3
"""
Kimi K2 模型适配器
支持月之暗面 Kimi K2 模型的适配器实现
"""

import os
import time
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun

# 导入基类
from .openai_compatible_base import OpenAICompatibleBase

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入token跟踪器
try:
    from tradingagents.config.config_manager import token_tracker
    TOKEN_TRACKING_ENABLED = True
except ImportError:
    TOKEN_TRACKING_ENABLED = False


class ChatKimi(OpenAICompatibleBase):
    """
    Kimi K2 模型适配器
    基于 OpenAI 兼容接口实现
    """
    
    def __init__(
        self,
        model: str = "moonshot-v1-8k",
        api_key: Optional[str] = None,
        base_url: str = "https://api.moonshot.cn/v1",
        temperature: float = 0.1,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ):
        """
        初始化 Kimi K2 适配器
        
        Args:
            model: 模型名称，默认 "moonshot-v1-8k"
            api_key: API密钥，如不提供则从环境变量 KIMI_API_KEY 获取
            base_url: API基础URL
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        """
        
        # 从环境变量获取API密钥
        if api_key is None:
            api_key = os.getenv("KIMI_API_KEY")
            if not api_key:
                raise ValueError(
                    "Kimi API密钥未提供。请设置环境变量 KIMI_API_KEY 或在初始化时提供 api_key 参数。"
                )
        
        # 调用基类初始化
        super().__init__(
            provider_name="kimi",
            model=model,
            api_key_env_var="KIMI_API_KEY",
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Kimi特定配置
        self.supports_system_message = True
        self.supports_function_calling = True
        self.context_window = 200000  # Kimi K2 支持20万token上下文
        self.max_output_tokens = max_tokens or 4096
        
        logger.info(f"[SUCCESS] Kimi K2 adapter initialized successfully")
        logger.info(f"   Model: {self.model_name}")
        logger.info(f"   Base URL: {self.openai_api_base}")
        logger.info(f"   Context window: {self.context_window:,} tokens")
    
    def _create_chat_result(self, response: Any) -> ChatResult:
        """
        创建聊天结果，包含token使用统计
        """
        try:
            result = super()._create_chat_result(response)
            
            # 记录token使用情况
            if TOKEN_TRACKING_ENABLED and hasattr(response, 'usage'):
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', input_tokens + output_tokens)
                
                # 记录到token跟踪器
                token_tracker.record_usage(
                    provider="Kimi",
                    model=self.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )
                
                logger.debug(f"Kimi token usage: input={input_tokens}, output={output_tokens}, total={total_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 创建Kimi聊天结果失败: {e}")
            raise
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成聊天回复
        """
        start_time = time.time()
        
        try:
            logger.debug(f"🚀 开始Kimi K2生成，消息数量: {len(messages)}")
            
            # 调用基类方法
            result = super()._generate(messages, stop, run_manager, **kwargs)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            logger.info(f"✅ Kimi K2生成完成，耗时: {generation_time:.2f}秒")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            generation_time = end_time - start_time
            
            logger.error(f"❌ Kimi K2生成失败，耗时: {generation_time:.2f}秒，错误: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            "provider": "kimi",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": self.context_window,
            "supports_function_calling": self.supports_function_calling,
            "supports_system_message": self.supports_system_message,
            "base_url": str(getattr(self, 'openai_api_base', getattr(self, 'base_url', 'https://api.moonshot.cn/v1')))
        }
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """
        获取可用的 Kimi 模型列表
        """
        return [
            "moonshot-v1-8k",          # Kimi 8K上下文版本
            "moonshot-v1-32k",         # Kimi 32K上下文版本
            "moonshot-v1-128k",        # Kimi 128K上下文版本
            "kimi-k2-0711-preview",    # Kimi K2 0711预览版
            "kimi-k2-turbo-preview"    # Kimi K2 Turbo预览版
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        估算使用成本（人民币）
        基于 Kimi 的定价策略
        """
        # 根据模型类型设置不同的定价
        model_pricing = {
            "moonshot-v1-8k": {"input": 0.012, "output": 0.012},
            "moonshot-v1-32k": {"input": 0.024, "output": 0.024},
            "moonshot-v1-128k": {"input": 0.06, "output": 0.06},
            "kimi-k2-0711-preview": {"input": 0.06, "output": 0.06},
            "kimi-k2-turbo-preview": {"input": 0.03, "output": 0.03}
        }
        
        # 获取当前模型的定价
        pricing = model_pricing.get(self.model_name, {"input": 0.01, "output": 0.03})
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return total_cost


def create_kimi_adapter(
    model: str = "moonshot-v1-8k",
    temperature: float = 0.1,
    max_tokens: Optional[int] = 4096,
    **kwargs
) -> ChatKimi:
    """
    创建 Kimi 适配器的便捷函数
    
    Args:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大输出token数
        **kwargs: 其他参数
    
    Returns:
        ChatKimi: Kimi适配器实例
    """
    return ChatKimi(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


# 为了兼容性，提供多个别名
ChatMoonshot = ChatKimi  # 月之暗面别名
create_moonshot_adapter = create_kimi_adapter  # 月之暗面别名


def get_kimi_adapter(
    model: str = "moonshot-v1-8k",
    temperature: float = 0.1,
    max_tokens: Optional[int] = 4096
) -> ChatKimi:
    """
    获取 Kimi 适配器实例
    
    Args:
        model: 模型名称，默认 "moonshot-v1-8k"
        temperature: 温度参数，默认 0.1
        max_tokens: 最大输出token数，默认 4096
    
    Returns:
        ChatKimi: Kimi适配器实例
    """
    try:
        adapter = create_kimi_adapter(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"✅ Kimi适配器创建成功: {model}")
        return adapter
        
    except Exception as e:
        logger.error(f"❌ Kimi适配器创建失败: {e}")
        raise


if __name__ == "__main__":
    # 测试代码
    try:
        # 创建适配器
        kimi = create_kimi_adapter()
        
        # 显示模型信息
        info = kimi.get_model_info()
        print("Kimi 模型信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 显示可用模型
        models = kimi.get_available_models()
        print(f"\n可用模型: {', '.join(models)}")
        
        # 成本估算示例
        cost = kimi.estimate_cost(1000, 500)
        print(f"\n成本估算 (1000输入+500输出tokens): ¥{cost:.4f}")
        
    except Exception as e:
        print(f"测试失败: {e}")