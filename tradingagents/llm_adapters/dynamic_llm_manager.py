#!/usr/bin/env python3
"""
动态LLM管理器
支持用户在运行时选择和切换不同的AI模型提供商
解决固定OpenAI模型的问题，支持多种LLM提供商
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from tradingagents.llm_adapters import ChatDashScope, ChatDashScopeOpenAI

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('llm_manager')


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    KIMI = "kimi"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str                          # 提供商
    model_name: str                        # 模型名称
    api_key: Optional[str] = None          # API密钥
    base_url: Optional[str] = None         # 基础URL
    max_tokens: int = 4000                 # 最大token数
    temperature: float = 0.7               # 温度参数
    enabled: bool = True                   # 是否启用
    display_name: Optional[str] = None     # 显示名称
    description: Optional[str] = None      # 描述


class DynamicLLMManager:
    """动态LLM管理器"""
    
    def __init__(self, config_file: str = "config/llm_models.json"):
        """
        初始化LLM管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 当前活跃的LLM配置
        self.current_config = None
        self.current_llm = None
        
        # 可用的LLM配置
        self.available_configs = {}
        
        # 初始化默认配置
        self._init_default_configs()
        
        # 加载配置文件
        self._load_configs()
        
        logger.info("🤖 动态LLM管理器初始化完成")
        logger.info(f"   可用模型: {len(self.available_configs)} 个")

    def _init_default_configs(self):
        """初始化默认LLM配置"""
        self.default_configs = {
            # OpenAI系列
            "openai_gpt4o": LLMConfig(
                provider="openai",
                model_name="gpt-4o",
                base_url="https://api.openai.com/v1",
                display_name="GPT-4o",
                description="OpenAI最新的多模态模型"
            ),
            "openai_gpt4o_mini": LLMConfig(
                provider="openai", 
                model_name="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                display_name="GPT-4o Mini",
                description="OpenAI经济型模型"
            ),
            
            # DashScope系列
            "dashscope_qwen_max": LLMConfig(
                provider="dashscope",
                model_name="qwen-max",
                display_name="Qwen Max",
                description="阿里云通义千问最强模型"
            ),
            "dashscope_qwen_plus": LLMConfig(
                provider="dashscope",
                model_name="qwen-plus", 
                display_name="Qwen Plus",
                description="阿里云通义千问平衡模型"
            ),
            "dashscope_qwen_turbo": LLMConfig(
                provider="dashscope",
                model_name="qwen-turbo",
                display_name="Qwen Turbo",
                description="阿里云通义千问高速模型"
            ),
            
            # DeepSeek系列
            "deepseek_chat": LLMConfig(
                provider="deepseek",
                model_name="deepseek-chat",
                base_url="https://api.deepseek.com/v1",
                display_name="DeepSeek Chat",
                description="DeepSeek对话模型"
            ),
            "deepseek_coder": LLMConfig(
                provider="deepseek", 
                model_name="deepseek-coder",
                base_url="https://api.deepseek.com/v1",
                display_name="DeepSeek Coder",
                description="DeepSeek代码模型"
            ),
            
            # Google系列
            "google_gemini_pro": LLMConfig(
                provider="google",
                model_name="gemini-pro",
                display_name="Gemini Pro",
                description="Google Gemini专业版"
            ),
            
            # OpenRouter系列
            "openrouter_claude": LLMConfig(
                provider="openrouter",
                model_name="anthropic/claude-3-sonnet",
                base_url="https://openrouter.ai/api/v1",
                display_name="Claude 3 Sonnet",
                description="OpenRouter的Claude模型"
            ),
            
            # Kimi系列
            "kimi_chat": LLMConfig(
                provider="kimi",
                model_name="moonshot-v1-8k",
                base_url="https://api.moonshot.cn/v1",
                display_name="Kimi Chat",
                description="月之暗面Kimi模型"
            ),
            
            # GLM系列
            "glm_chat": LLMConfig(
                provider="glm",
                model_name="glm-4-plus",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                display_name="GLM-4 Plus",
                description="智谱AI GLM-4 Plus模型"
            )
        }

    def _load_configs(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载自定义配置
                for key, config_dict in data.get('custom_configs', {}).items():
                    self.available_configs[key] = LLMConfig(**config_dict)
                
                # 设置当前配置
                current_key = data.get('current_config')
                if current_key and current_key in self.available_configs:
                    self.current_config = self.available_configs[current_key]
                    
            except Exception as e:
                logger.warning(f"⚠️ 加载LLM配置文件失败: {e}")
        
        # 合并默认配置
        for key, config in self.default_configs.items():
            if key not in self.available_configs:
                # 从环境变量获取API密钥
                config.api_key = self._get_api_key_from_env(config.provider)
                config.enabled = bool(config.api_key)  # 有API密钥才启用
                self.available_configs[key] = config

    def _get_api_key_from_env(self, provider: str) -> Optional[str]:
        """从环境变量获取API密钥"""
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "dashscope": "DASHSCOPE_API_KEY", 
            "deepseek": "DEEPSEEK_API_KEY",
            "google": "GOOGLE_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "kimi": "MOONSHOT_API_KEY",
            "glm": "GLM_API_KEY"
        }
        
        env_key = env_key_map.get(provider)
        return os.getenv(env_key) if env_key else None

    def save_configs(self):
        """保存配置到文件"""
        try:
            # 只保存自定义配置
            custom_configs = {}
            for key, config in self.available_configs.items():
                if key not in self.default_configs:
                    custom_configs[key] = asdict(config)
            
            data = {
                'custom_configs': custom_configs,
                'current_config': self._get_current_config_key()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 LLM配置已保存到: {self.config_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存LLM配置失败: {e}")

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的模型列表"""
        models = {}
        for key, config in self.available_configs.items():
            models[key] = {
                'provider': config.provider,
                'model_name': config.model_name,
                'display_name': config.display_name or config.model_name,
                'description': config.description or f"{config.provider} {config.model_name}",
                'enabled': config.enabled,
                'has_api_key': bool(config.api_key)
            }
        return models

    def get_enabled_models(self) -> Dict[str, Dict[str, Any]]:
        """获取已启用的模型列表"""
        models = self.get_available_models()
        return {k: v for k, v in models.items() if v['enabled'] and v['has_api_key']}

    def set_current_model(self, model_key: str) -> bool:
        """
        设置当前使用的模型
        
        Args:
            model_key: 模型键值
            
        Returns:
            是否设置成功
        """
        if model_key not in self.available_configs:
            logger.error(f"❌ 模型 {model_key} 不存在")
            return False
        
        config = self.available_configs[model_key]
        
        if not config.enabled or not config.api_key:
            logger.error(f"❌ 模型 {model_key} 未启用或缺少API密钥")
            return False
        
        try:
            # 创建LLM实例
            llm = self._create_llm_instance(config)
            
            self.current_config = config
            self.current_llm = llm
            
            logger.info(f"✅ 已切换到模型: {config.display_name or config.model_name}")
            
            # 保存配置
            self.save_configs()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 切换模型失败: {e}")
            return False

    def _create_llm_instance(self, config: LLMConfig):
        """创建LLM实例"""
        provider = config.provider
        
        if provider == "openai":
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "dashscope":
            return ChatDashScope(
                model=config.model_name,
                dashscope_api_key=config.api_key,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "deepseek":
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                google_api_key=config.api_key,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "anthropic":
            return ChatAnthropic(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "openrouter":
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "kimi":
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        elif provider == "glm":
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")

    def get_current_llm(self):
        """获取当前LLM实例"""
        if self.current_llm is None:
            # 尝试自动选择一个可用的模型
            enabled_models = self.get_enabled_models()
            if enabled_models:
                first_model = list(enabled_models.keys())[0]
                logger.info(f"🔄 自动选择模型: {first_model}")
                self.set_current_model(first_model)
        
        return self.current_llm

    def get_current_config(self) -> Optional[LLMConfig]:
        """获取当前配置"""
        return self.current_config

    def _get_current_config_key(self) -> Optional[str]:
        """获取当前配置的键值"""
        if not self.current_config:
            return None
        
        for key, config in self.available_configs.items():
            if config == self.current_config:
                return key
        return None

    def add_custom_model(self, key: str, config: LLMConfig) -> bool:
        """
        添加自定义模型配置
        
        Args:
            key: 配置键值
            config: LLM配置
            
        Returns:
            是否添加成功
        """
        try:
            self.available_configs[key] = config
            self.save_configs()
            logger.info(f"✅ 已添加自定义模型: {key}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加自定义模型失败: {e}")
            return False

    def remove_custom_model(self, key: str) -> bool:
        """
        删除自定义模型配置
        
        Args:
            key: 配置键值
            
        Returns:
            是否删除成功
        """
        if key in self.default_configs:
            logger.error(f"❌ 无法删除默认配置: {key}")
            return False
        
        if key not in self.available_configs:
            logger.error(f"❌ 配置不存在: {key}")
            return False
        
        try:
            del self.available_configs[key]
            
            # 如果删除的是当前配置，重置
            if self.current_config == self.available_configs.get(key):
                self.current_config = None
                self.current_llm = None
            
            self.save_configs()
            logger.info(f"✅ 已删除自定义模型: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除自定义模型失败: {e}")
            return False

    def test_model(self, model_key: str) -> Dict[str, Any]:
        """
        测试模型连接
        
        Args:
            model_key: 模型键值
            
        Returns:
            测试结果
        """
        if model_key not in self.available_configs:
            return {
                'success': False,
                'error': f"模型 {model_key} 不存在"
            }
        
        config = self.available_configs[model_key]
        
        try:
            # 创建临时LLM实例
            llm = self._create_llm_instance(config)
            
            # 发送测试消息
            response = llm.invoke("Hello, this is a test message. Please respond with 'Test successful'.")
            
            return {
                'success': True,
                'model': config.display_name or config.model_name,
                'provider': config.provider,
                'response': str(response.content) if hasattr(response, 'content') else str(response)
            }
            
        except Exception as e:
            return {
                'success': False,
                'model': config.display_name or config.model_name,
                'provider': config.provider,
                'error': str(e)
            }


# 全局实例
_llm_manager = None

def get_llm_manager() -> DynamicLLMManager:
    """获取LLM管理器单例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = DynamicLLMManager()
    return _llm_manager


# 便捷函数
def get_current_llm():
    """获取当前LLM实例"""
    return get_llm_manager().get_current_llm()

def set_current_model(model_key: str) -> bool:
    """设置当前模型"""
    return get_llm_manager().set_current_model(model_key)

def get_available_models() -> Dict[str, Dict[str, Any]]:
    """获取可用模型列表"""
    return get_llm_manager().get_available_models()

def get_enabled_models() -> Dict[str, Dict[str, Any]]:
    """获取已启用模型列表"""
    return get_llm_manager().get_enabled_models()


if __name__ == "__main__":
    # 测试代码
    manager = get_llm_manager()
    
    print("可用模型:")
    for key, info in manager.get_available_models().items():
        status = "✅" if info['enabled'] and info['has_api_key'] else "❌"
        print(f"  {status} {key}: {info['display_name']} ({info['provider']})")
    
    # 测试模型切换
    enabled_models = manager.get_enabled_models()
    if enabled_models:
        first_model = list(enabled_models.keys())[0]
        print(f"\n测试切换到: {first_model}")
        success = manager.set_current_model(first_model)
        print(f"切换结果: {'成功' if success else '失败'}")
        
        if success:
            current = manager.get_current_config()
            print(f"当前模型: {current.display_name} ({current.provider})")