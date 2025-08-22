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
            # 分层数据源策略 - 解决速度问题的核心配置
            'tiered_strategy': {
                'enable_tiered': True,              # 启用分层数据获取
                'batch_preferred': True,            # 批量数据源优先
                'intelligent_fallback': True,       # 智能降级
                'performance_monitoring': True,     # 性能监控
            },
            
            # 批量数据源优先级 - 高效批量下载
            'batch_sources': [
                'baostock',     # BaoStock - 完全免费批量下载
                'akshare',      # AKShare - 免费批量API
                'tushare',      # Tushare - 高质量批量数据（付费）
            ],
            
            # 实时数据源优先级 - 精准单点获取
            'realtime_sources': [
                'eastmoney',    # 东方财富 - 实时行情
                'tencent',      # 腾讯财经 - 实时免费
                'sina',         # 新浪财经 - 稳定免费
                'xueqiu',       # 雪球 - 社交+价格
            ],
            
            # 传统优先级（保持向后兼容）
            'priority_order': [
                'baostock',     # 批量优先
                'akshare',      # 批量优先
                'eastmoney',    # 实时补充
                'tencent',      # 实时补充
                'sina',         # 实时补充
                'xueqiu',       # 实时补充
            ],
            
            # 各数据源可用性配置
            'availability': {
                'baostock': True,      # 批量数据源
                'akshare': True,       # 批量数据源  
                'tushare': False,      # 批量数据源（需token）
                'eastmoney': True,     # 实时数据源
                'tencent': True,       # 实时数据源
                'sina': True,          # 实时数据源
                'xueqiu': True,        # 实时数据源
            },
            
            # 数据获取策略
            'strategy': {
                'enable_multi_source': True,        # 启用多数据源
                'enable_data_fusion': True,         # 启用数据融合
                'enable_quality_check': True,       # 启用质量检查
                'enable_auto_fallback': True,       # 启用自动降级
                'max_retry_per_source': 3,          # 每个数据源最大重试次数
                'timeout_per_request': 30,          # 每个请求超时时间(秒)
                
                # 批量优化策略
                'batch_size_optimization': True,    # 批量大小优化
                'concurrent_batch_requests': 8,     # 并发批量请求数
                'batch_request_delay': 0.1,         # 批量请求间隔（秒）
                'intelligent_scheduling': True,     # 智能调度
                'cache_integration': True,          # 缓存集成
                
                # 实时补充策略
                'realtime_fallback_timeout': 5,     # 实时降级超时（秒）
                'realtime_max_concurrent': 3,       # 实时最大并发数
                'realtime_retry_delay': 1,          # 实时重试延迟（秒）
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
    
    def get_tiered_strategy_config(self) -> Dict[str, Any]:
        """获取分层策略配置"""
        return self.config.get('tiered_strategy', {}).copy()
    
    def get_batch_sources(self) -> List[str]:
        """获取批量数据源列表"""
        return [source for source in self.config.get('batch_sources', [])
                if self.is_source_enabled(source)]
    
    def get_realtime_sources(self) -> List[str]:
        """获取实时数据源列表"""
        return [source for source in self.config.get('realtime_sources', [])
                if self.is_source_enabled(source)]
    
    def is_batch_preferred(self) -> bool:
        """是否优先使用批量数据源"""
        return self.config.get('tiered_strategy', {}).get('batch_preferred', True)
    
    def is_tiered_enabled(self) -> bool:
        """是否启用分层数据获取"""
        return self.config.get('tiered_strategy', {}).get('enable_tiered', True)
    
    def get_batch_config(self) -> Dict[str, Any]:
        """获取批量数据源配置"""
        strategy = self.config.get('strategy', {})
        return {
            'concurrent_requests': strategy.get('concurrent_batch_requests', 8),
            'request_delay': strategy.get('batch_request_delay', 0.1),
            'size_optimization': strategy.get('batch_size_optimization', True),
            'intelligent_scheduling': strategy.get('intelligent_scheduling', True),
        }
    
    def get_realtime_config(self) -> Dict[str, Any]:
        """获取实时数据源配置"""
        strategy = self.config.get('strategy', {})
        return {
            'fallback_timeout': strategy.get('realtime_fallback_timeout', 5),
            'max_concurrent': strategy.get('realtime_max_concurrent', 3),
            'retry_delay': strategy.get('realtime_retry_delay', 1),
        }

# 全局配置实例
_data_source_config = None

def get_data_source_config():
    """获取数据源配置实例"""
    global _data_source_config
    if _data_source_config is None:
        _data_source_config = DataSourceConfig()
    return _data_source_config