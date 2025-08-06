#!/usr/bin/env python3
"""
增强缓存策略
减少API调用，提升响应速度
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import os

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('cache')

class EnhancedCache:
    """增强缓存管理器"""
    
    def __init__(self):
        self.cache_dir = Path("./cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 分层缓存配置
        self.cache_durations = {
            'price': 60,           # 1分钟
            'volume': 300,         # 5分钟
            'news': 1800,          # 30分钟
            'fundamentals': 86400, # 24小时
            'sentiment': 3600,     # 1小时
            'technical': 900,      # 15分钟
        }
        
        logger.info("✅ 增强缓存管理器初始化完成")
    
    def _get_cache_key(self, data_type: str, symbol: str, **kwargs) -> str:
        """生成缓存键"""
        content = f"{data_type}_{symbol}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, data_type: str, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        cache_key = self._get_cache_key(data_type, symbol, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # 检查是否过期
            created_at = datetime.fromisoformat(cached.get('created_at', ''))
            duration = self.cache_durations.get(data_type, 300)
            
            if datetime.now() - created_at > timedelta(seconds=duration):
                cache_path.unlink(missing_ok=True)
                return None
            
            logger.debug(f"⚡ 命中缓存: {data_type}_{symbol}")
            return cached.get('data')
            
        except Exception as e:
            logger.error(f"缓存读取失败: {e}")
            return None
    
    def set(self, data_type: str, symbol: str, data: Dict[str, Any], **kwargs):
        """设置缓存数据"""
        cache_key = self._get_cache_key(data_type, symbol, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'data': data,
                'created_at': datetime.now().isoformat(),
                'data_type': data_type,
                'symbol': symbol,
                'kwargs': kwargs
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"💾 缓存设置: {data_type}_{symbol}")
            
        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
    
    def is_valid(self, data_type: str, symbol: str, **kwargs) -> bool:
        """检查缓存是否有效"""
        cache_key = self._get_cache_key(data_type, symbol, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            created_at = datetime.fromisoformat(cached.get('created_at', ''))
            duration = self.cache_durations.get(data_type, 300)
            
            return datetime.now() - created_at <= timedelta(seconds=duration)
            
        except:
            return False
    
    def get_or_set(self, data_type: str, symbol: str, fetch_func, **kwargs) -> Dict[str, Any]:
        """获取或设置缓存数据"""
        # 先尝试获取缓存
        cached = self.get(data_type, symbol, **kwargs)
        if cached is not None:
            return cached
        
        # 获取新数据
        try:
            data = fetch_func()
            self.set(data_type, symbol, data, **kwargs)
            return data
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return {}
    
    def clear_expired(self):
        """清理过期缓存"""
        expired_count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                
                created_at = datetime.fromisoformat(cached.get('created_at', ''))
                data_type = cached.get('data_type', 'price')
                duration = self.cache_durations.get(data_type, 300)
                
                if datetime.now() - created_at > timedelta(seconds=duration):
                    cache_file.unlink()
                    expired_count += 1
                    
            except Exception:
                continue
        
        logger.info(f"清理了 {expired_count} 个过期缓存")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        stats = defaultdict(int)
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                
                data_type = cached.get('data_type', 'unknown')
                stats[data_type] += 1
                
            except:
                continue
        
        return dict(stats)

class CacheManager:
    """缓存管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = EnhancedCache()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> EnhancedCache:
        """获取缓存实例"""
        return cls()

# 全局缓存实例
def get_cache() -> EnhancedCache:
    """获取全局缓存实例"""
    return CacheManager.get_instance()

# 便捷函数
def cached_data(data_type: str, symbol: str, fetch_func, **kwargs):
    """装饰器式缓存获取"""
    cache = get_cache()
    return cache.get_or_set(data_type, symbol, fetch_func, **kwargs)