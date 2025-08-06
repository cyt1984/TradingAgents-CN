#!/usr/bin/env python3
"""
同花顺iFinD配置文件
包含API密钥、配额管理、接口配置等
"""

import os
from typing import Dict, Any

class TongHuaShunConfig:
    """同花顺iFinD配置管理"""
    
    def __init__(self):
        # API基础配置
        self.api_enabled = os.getenv('TONGHUASHUN_API_ENABLED', 'false').lower() == 'true'
        self.username = os.getenv('TONGHUASHUN_USERNAME', '')
        self.password = os.getenv('TONGHUASHUN_PASSWORD', '')
        
        # 配额管理配置
        self.max_requests_per_month = int(os.getenv('TONGHUASHUN_MAX_REQUESTS_MONTH', '1000'))
        self.max_requests_per_day = int(os.getenv('TONGHUASHUN_MAX_REQUESTS_DAY', '100'))
        self.request_interval = float(os.getenv('TONGHUASHUN_REQUEST_INTERVAL', '1.0'))  # 秒
        
        # 接口配置
        self.timeout = int(os.getenv('TONGHUASHUN_TIMEOUT', '30'))  # 超时时间(秒)
        self.retry_attempts = int(os.getenv('TONGHUASHUN_RETRY_ATTEMPTS', '3'))
        
        # 研报接口特定配置
        self.research_report_fields = [
            'ths_report_title_research',      # 研报标题
            'ths_report_institution_research', # 发布机构
            'ths_report_analyst_research',    # 分析师
            'ths_report_publish_date_research', # 发布日期
            'ths_rating_latest_research',     # 最新评级
            'ths_target_price_research',      # 目标价
            'ths_report_abstract_research',   # 研报摘要
        ]
        
        # 数据质量配置
        self.min_report_title_length = 5
        self.max_report_summary_length = 500
        self.confidence_base_score = 0.75  # 同花顺基础可信度评分
        
    def is_enabled(self) -> bool:
        """检查是否启用同花顺API"""
        return self.api_enabled and self.username and self.password
    
    def get_quota_config(self) -> Dict[str, Any]:
        """获取配额配置"""
        return {
            'max_requests_per_month': self.max_requests_per_month,
            'max_requests_per_day': self.max_requests_per_day,
            'request_interval': self.request_interval
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'username': self.username,
            'password': self.password,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts
        }

# 全局配置实例
tonghuashun_config = TongHuaShunConfig()