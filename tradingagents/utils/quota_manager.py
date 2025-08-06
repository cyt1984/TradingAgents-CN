#!/usr/bin/env python3
"""
配额管理器
用于管理API调用频率和次数限制
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('quota_manager')

class QuotaManager:
    """API配额管理器"""
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.max_requests_per_month = config.get('max_requests_per_month', 1000)
        self.max_requests_per_day = config.get('max_requests_per_day', 100)
        self.request_interval = config.get('request_interval', 1.0)
        
        # 配额记录文件
        self.quota_file = Path(f"quota_{service_name}.json")
        self.last_request_time = 0
        
        # 加载现有配额记录
        self.quota_data = self._load_quota_data()
    
    def _load_quota_data(self) -> Dict[str, Any]:
        """加载配额数据"""
        try:
            if self.quota_file.exists():
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"加载配额数据: {self.service_name}")
                    return data
        except Exception as e:
            logger.warning(f"加载配额数据失败: {e}")
        
        # 返回默认结构
        return {
            'monthly_requests': {},
            'daily_requests': {},
            'last_reset': datetime.now().isoformat()
        }
    
    def _save_quota_data(self):
        """保存配额数据"""
        try:
            with open(self.quota_file, 'w', encoding='utf-8') as f:
                json.dump(self.quota_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存配额数据失败: {e}")
    
    def _get_current_month_key(self) -> str:
        """获取当前月份键"""
        return datetime.now().strftime('%Y-%m')
    
    def _get_current_day_key(self) -> str:
        """获取当前日期键"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _cleanup_old_records(self):
        """清理过期记录"""
        current_time = datetime.now()
        
        # 清理月度记录(保留最近3个月)
        month_keys_to_remove = []
        for month_key in self.quota_data['monthly_requests'].keys():
            try:
                month_date = datetime.strptime(month_key, '%Y-%m')
                if (current_time - month_date).days > 90:  # 3个月
                    month_keys_to_remove.append(month_key)
            except:
                month_keys_to_remove.append(month_key)
        
        for key in month_keys_to_remove:
            del self.quota_data['monthly_requests'][key]
        
        # 清理日度记录(保留最近30天)
        day_keys_to_remove = []
        for day_key in self.quota_data['daily_requests'].keys():
            try:
                day_date = datetime.strptime(day_key, '%Y-%m-%d')
                if (current_time - day_date).days > 30:
                    day_keys_to_remove.append(day_key)
            except:
                day_keys_to_remove.append(day_key)
        
        for key in day_keys_to_remove:
            del self.quota_data['daily_requests'][key]
        
        if month_keys_to_remove or day_keys_to_remove:
            logger.debug(f"清理过期配额记录: {len(month_keys_to_remove)} 月度, {len(day_keys_to_remove)} 日度")
    
    def can_make_request(self) -> Dict[str, Any]:
        """检查是否可以发起请求"""
        try:
            self._cleanup_old_records()
            
            current_month = self._get_current_month_key()
            current_day = self._get_current_day_key()
            
            # 检查月度配额
            monthly_count = self.quota_data['monthly_requests'].get(current_month, 0)
            if monthly_count >= self.max_requests_per_month:
                return {
                    'can_request': False,
                    'reason': 'monthly_quota_exceeded',
                    'monthly_used': monthly_count,
                    'monthly_limit': self.max_requests_per_month
                }
            
            # 检查日度配额
            daily_count = self.quota_data['daily_requests'].get(current_day, 0)
            if daily_count >= self.max_requests_per_day:
                return {
                    'can_request': False,
                    'reason': 'daily_quota_exceeded',
                    'daily_used': daily_count,
                    'daily_limit': self.max_requests_per_day
                }
            
            # 检查请求间隔
            current_time = time.time()
            if current_time - self.last_request_time < self.request_interval:
                wait_time = self.request_interval - (current_time - self.last_request_time)
                return {
                    'can_request': False,
                    'reason': 'rate_limit',
                    'wait_time': wait_time
                }
            
            return {
                'can_request': True,
                'monthly_used': monthly_count,
                'monthly_limit': self.max_requests_per_month,
                'daily_used': daily_count,
                'daily_limit': self.max_requests_per_day
            }
            
        except Exception as e:
            logger.error(f"配额检查失败: {e}")
            return {'can_request': False, 'reason': 'check_error', 'error': str(e)}
    
    def record_request(self):
        """记录一次请求"""
        try:
            current_month = self._get_current_month_key()
            current_day = self._get_current_day_key()
            
            # 更新月度计数
            self.quota_data['monthly_requests'][current_month] = \
                self.quota_data['monthly_requests'].get(current_month, 0) + 1
            
            # 更新日度计数
            self.quota_data['daily_requests'][current_day] = \
                self.quota_data['daily_requests'].get(current_day, 0) + 1
            
            # 更新最后请求时间
            self.last_request_time = time.time()
            
            # 保存数据
            self._save_quota_data()
            
            logger.debug(f"记录请求: {self.service_name}, 月度: {self.quota_data['monthly_requests'][current_month]}/{self.max_requests_per_month}")
            
        except Exception as e:
            logger.error(f"记录请求失败: {e}")
    
    def get_quota_status(self) -> Dict[str, Any]:
        """获取配额状态"""
        try:
            current_month = self._get_current_month_key()
            current_day = self._get_current_day_key()
            
            monthly_used = self.quota_data['monthly_requests'].get(current_month, 0)
            daily_used = self.quota_data['daily_requests'].get(current_day, 0)
            
            return {
                'service_name': self.service_name,
                'monthly': {
                    'used': monthly_used,
                    'limit': self.max_requests_per_month,
                    'remaining': max(0, self.max_requests_per_month - monthly_used),
                    'usage_rate': monthly_used / self.max_requests_per_month if self.max_requests_per_month > 0 else 0
                },
                'daily': {
                    'used': daily_used,
                    'limit': self.max_requests_per_day,
                    'remaining': max(0, self.max_requests_per_day - daily_used),
                    'usage_rate': daily_used / self.max_requests_per_day if self.max_requests_per_day > 0 else 0
                },
                'request_interval': self.request_interval
            }
            
        except Exception as e:
            logger.error(f"获取配额状态失败: {e}")
            return {'error': str(e)}
    
    def wait_if_needed(self):
        """如果需要等待，则等待"""
        quota_check = self.can_make_request()
        
        if not quota_check['can_request']:
            if quota_check['reason'] == 'rate_limit':
                wait_time = quota_check['wait_time']
                logger.info(f"⏳ 请求频率限制，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            elif quota_check['reason'] == 'daily_quota_exceeded':
                logger.warning(f"⚠️ 日度配额已用完: {quota_check['daily_used']}/{quota_check['daily_limit']}")
                return False
            elif quota_check['reason'] == 'monthly_quota_exceeded':
                logger.warning(f"⚠️ 月度配额已用完: {quota_check['monthly_used']}/{quota_check['monthly_limit']}")
                return False
            else:
                logger.warning(f"⚠️ 配额检查失败: {quota_check.get('reason', 'unknown')}")
                return False
        
        return True