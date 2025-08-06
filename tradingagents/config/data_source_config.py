#!/usr/bin/env python3
"""
数据源配置管理
配置多数据源的优先级和使用策略
"""

import os
from typing import Dict, List, Any
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('config')

class DataSourceConfig:
    """数据源配置管理器"""
    
    def __init__(self):
        """初始化数据源配置"""
        self.config = {
            # 数据源优先级 - 无API限制优先
            'priority_order': [
                'eastmoney',    # 东方财富 - 全面免费
                'tencent',      # 腾讯财经 - 实时免费
                'sina',         # 新浪财经 - 稳定免费
                'baostock',     # 宝通数据 - 免费基本面
                'xueqiu',       # 雪球 - 社交+价格
                'tushare',      # Tushare - 降级备用
                'akshare',      # AKShare - 最后备用
            ],
            
            # 各数据源可用性配置
            'availability': {
                'eastmoney': True,
                'tencent': True,
                'sina': True,
                'xueqiu': True,
                'tushare': True,
                'akshare': True,
            },
            
            # 数据获取策略
            'strategy': {
                'enable_multi_source': True,        # 启用多数据源
                'enable_data_fusion': True,         # 启用数据融合
                'enable_quality_check': True,       # 启用质量检查
                'enable_auto_fallback': True,       # 启用自动降级
                'max_retry_per_source': 3,          # 每个数据源最大重试次数
                'timeout_per_request': 30,          # 每个请求超时时间(秒)
            },
            
            # 数据质量阈值
            'quality_thresholds': {
                'min_data_points': 3,               # 最少数据点
                'max_price_deviation': 0.05,        # 最大价格偏差(5%)
                'max_volume_deviation': 0.10,       # 最大成交量偏差(10%)
            },
            
            # 缓存配置
            'cache': {
                'enable_cache': True,
                'cache_duration_minutes': {
                    'price_data': 5,                # 价格数据缓存5分钟
                    'news_data': 30,                # 新闻数据缓存30分钟
                    'financial_data': 1440,         # 财务数据缓存24小时
                    'sentiment_data': 60,           # 情绪数据缓存1小时
                },
            }
        }
        
        # 从环境变量覆盖配置
        self._load_from_env()
        
        logger.info("✅ 数据源配置初始化完成")
        logger.info(f"   数据源优先级: {self.config['priority_order']}")
        logger.info(f"   多数据源模式: {self.config['strategy']['enable_multi_source']}")
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 数据源开关
        for source in self.config['availability']:
            env_key = f"ENABLE_{source.upper()}"
            if os.getenv(env_key):
                self.config['availability'][source] = os.getenv(env_key).lower() == 'true'
        
        # 策略开关
        strategy_keys = [
            'enable_multi_source',
            'enable_data_fusion', 
            'enable_quality_check',
            'enable_auto_fallback'
        ]
        
        for key in strategy_keys:
            env_key = f"DATA_{key.upper()}"
            if os.getenv(env_key):
                self.config['strategy'][key] = os.getenv(env_key).lower() == 'true'
    
    def get_priority_order(self) -> List[str]:
        """获取数据源优先级"""
        return [source for source in self.config['priority_order'] 
                if self.config['availability'].get(source, True)]
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def is_source_enabled(self, source: str) -> bool:
        """检查数据源是否启用"""
        return self.config['availability'].get(source, True)
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.config['strategy'].copy()
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.config['cache'].copy()

# 全局配置实例
_data_source_config = None

def get_data_source_config():
    """获取数据源配置实例"""
    global _data_source_config
    if _data_source_config is None:
        _data_source_config = DataSourceConfig()
    return _data_source_config