#!/usr/bin/env python3
"""
GLM-4.5 模型适配器
支持智谱 GLM-4.5 模型的适配器实现
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


class ChatGLM(OpenAICompatibleBase):
    """
    GLM-4.5 模型适配器
    基于 OpenAI 兼容接口实现
    """
    
    def __init__(
        self,
        model: str = "glm-4-plus",
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        temperature: float = 0.1,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ):
        """
        初始化 GLM-4.5 适配器
        
        Args:
            model: 模型名称，默认 "glm-4-plus"
            api_key: API密钥，如不提供则从环境变量 GLM_API_KEY 获取
            base_url: API基础URL
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        """
        
        # 从环境变量获取API密钥
        if api_key is None:
            api_key = os.getenv("GLM_API_KEY")
            if not api_key:
                raise ValueError(
                    "GLM API密钥未提供。请设置环境变量 GLM_API_KEY 或在初始化时提供 api_key 参数。"
                )
        
        # 调用基类初始化
        super().__init__(
            provider_name="GLM",
            model=model,
            api_key_env_var="GLM_API_KEY",
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # GLM特定配置
        self.supports_system_message = True
        self.supports_function_calling = True
        self.context_window = 128000  # GLM-4.5 支持128K上下文
        self.max_output_tokens = 4096
        
        logger.info(f"✅ GLM-4.5 适配器初始化成功")
        logger.info(f"   模型: {self.model_name}")
        logger.info(f"   基础URL: {self.openai_api_base}")
        logger.info(f"   上下文窗口: {self.context_window:,} tokens")
    
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
                    provider="GLM",
                    model=self.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )
                
                logger.debug(f"🎯 GLM token使用: 输入={input_tokens}, 输出={output_tokens}, 总计={total_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 创建GLM聊天结果失败: {e}")
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
            logger.debug(f"🚀 开始GLM-4.5生成，消息数量: {len(messages)}")
            
            # 调用基类方法
            result = super()._generate(messages, stop, run_manager, **kwargs)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            logger.info(f"✅ GLM-4.5生成完成，耗时: {generation_time:.2f}秒")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            generation_time = end_time - start_time
            
            logger.error(f"❌ GLM-4.5生成失败，耗时: {generation_time:.2f}秒，错误: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            "provider": "GLM",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": self.context_window,
            "supports_function_calling": self.supports_function_calling,
            "supports_system_message": self.supports_system_message,
            "base_url": self.openai_api_base
        }
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """
        获取可用的 GLM 模型列表
        """
        return [
            "glm-4-plus",         # GLM-4.5 主模型  
            "glm-4-0520",         # GLM-4 标准版
            "glm-4-air",          # GLM-4 轻量版
            "glm-4-airx",         # GLM-4 增强版
            "glm-4-flash",        # GLM-4 快速版
            "glm-4",              # GLM-4 通用版
            "glm-3-turbo"         # GLM-3 加速版
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        估算使用成本（人民币）
        基于 GLM 的定价策略
        """
        # GLM-4.5 定价 (参考价格，实际价格请查看官网)
        # GLM-4-Plus: 输入 ¥0.05/1K tokens, 输出 ¥0.15/1K tokens
        # GLM-4: 输入 ¥0.01/1K tokens, 输出 ¥0.03/1K tokens
        
        if "plus" in self.model_name.lower():
            # GLM-4-Plus 定价
            input_cost = (input_tokens / 1000) * 0.05
            output_cost = (output_tokens / 1000) * 0.15
        elif "flash" in self.model_name.lower():
            # GLM-4-Flash 定价（更便宜）
            input_cost = (input_tokens / 1000) * 0.001
            output_cost = (output_tokens / 1000) * 0.002
        else:
            # 标准 GLM-4 定价
            input_cost = (input_tokens / 1000) * 0.01
            output_cost = (output_tokens / 1000) * 0.03
        
        total_cost = input_cost + output_cost
        return total_cost


def create_glm_adapter(
    model: str = "glm-4-plus",
    temperature: float = 0.1,
    max_tokens: Optional[int] = 4096,
    **kwargs
) -> ChatGLM:
    """
    创建 GLM 适配器的便捷函数
    
    Args:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大输出token数
        **kwargs: 其他参数
    
    Returns:
        ChatGLM: GLM适配器实例
    """
    return ChatGLM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


# 为了兼容性，提供多个别名
ChatZhipu = ChatGLM  # 智谱别名
create_zhipu_adapter = create_glm_adapter  # 智谱别名


def get_glm_adapter(
    model: str = "glm-4-plus",
    temperature: float = 0.1,
    max_tokens: Optional[int] = 4096
) -> ChatGLM:
    """
    获取 GLM 适配器实例
    
    Args:
        model: 模型名称，默认 "glm-4-plus"
        temperature: 温度参数，默认 0.1
        max_tokens: 最大输出token数，默认 4096
    
    Returns:
        ChatGLM: GLM适配器实例
    """
    try:
        adapter = create_glm_adapter(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"✅ GLM适配器创建成功: {model}")
        return adapter
        
    except Exception as e:
        logger.error(f"❌ GLM适配器创建失败: {e}")
        raise


if __name__ == "__main__":
    # 测试代码
    try:
        # 创建适配器
        glm = create_glm_adapter()
        
        # 显示模型信息
        info = glm.get_model_info()
        print("GLM 模型信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 显示可用模型
        models = glm.get_available_models()
        print(f"\n可用模型: {', '.join(models)}")
        
        # 成本估算示例
        cost = glm.estimate_cost(1000, 500)
        print(f"\n成本估算 (1000输入+500输出tokens): ¥{cost:.4f}")
        
    except Exception as e:
        print(f"测试失败: {e}")