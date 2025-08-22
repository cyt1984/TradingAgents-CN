#!/usr/bin/env python3
"""
股票活跃度智能分类系统
基于换手率、成交量、价格波动、新闻热度和资金流向的5维度综合评分
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import sqlite3
from pathlib import Path

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager

logger = get_logger('activity_classifier')


class StockActivityClassifier:
    """股票活跃度智能分类器"""
    
    def __init__(self):
        """初始化分类器"""
        self.historical_manager = get_historical_manager()
        self.stock_manager = get_stock_master_manager()
        
        # 权重配置
        self.weights = {
            'turnover_rate': 0.25,      # 换手率 25%
            'volume': 0.25,             # 成交量 25%
            'price_volatility': 0.25,   # 价格波动 25%
            'news_heat': 0.15,          # 新闻热度 15%
            'fund_flow': 0.10           # 资金流向 10%
        }
        
        # 分类阈值
        self.thresholds = {
            'active': 85,      # 活跃股票
            'normal': 45,      # 普通股票
            'inactive': 0      # 冷门股票
        }
        
        logger.info("📊 股票活跃度分类器初始化完成")
    
    def calculate_turnover_rate(self, symbol: str, days: int = 5) -> float:
        """
        计算股票换手率
        
        Args:
            symbol: 股票代码
            days: 计算天数
            
        Returns:
            平均换手率（百分比）
        """
        try:
            # 获取历史数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)  # 多取一些避免周末
            
            data = self.historical_manager.load_historical_data(
                symbol, "daily", 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data is None or data.empty:
                return 0.0
            
            # 获取最近days天的数据
            data = data.tail(days)
            
            if len(data) < days * 0.7:  # 至少70%的数据
                return 0.0
            
            # 获取股票基础信息
            stock_info = self.stock_manager.get_stock_info(symbol)
            if not stock_info or 'outstanding_shares' not in stock_info:
                # 估算流通股本
                avg_volume = data['volume'].mean()
                outstanding_shares = avg_volume * 100  # 粗略估算
            else:
                outstanding_shares = stock_info.get('outstanding_shares', 100000000)
            
            # 计算换手率 = 成交量 / 流通股本 * 100%
            turnovers = (data['volume'] / outstanding_shares) * 100
            avg_turnover = turnovers.mean()
            
            return max(0.0, avg_turnover)
            
        except Exception as e:
            logger.debug(f"计算{symbol}换手率失败: {e}")
            return 0.0
    
    def calculate_volume_score(self, symbol: str, days: int = 5) -> float:
        """计算成交量活跃度分数"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)
            
            data = self.historical_manager.load_historical_data(
                symbol, "daily",
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data is None or data.empty:
                return 0.0
            
            data = data.tail(days)
            if len(data) < days * 0.7:
                return 0.0
            
            # 计算平均成交额（万元）
            avg_amount = (data['volume'] * data['close']).mean() / 10000
            
            # 标准化到0-100分
            if avg_amount >= 10000:  # 1亿元以上
                return 100.0
            elif avg_amount >= 1000:  # 1000万-1亿元
                return 80.0 + 20.0 * (avg_amount - 1000) / 9000
            elif avg_amount >= 100:   # 100万-1000万
                return 50.0 + 30.0 * (avg_amount - 100) / 900
            elif avg_amount >= 10:    # 10万-100万
                return 20.0 + 30.0 * (avg_amount - 10) / 90
            else:                     # 10万以下
                return 0.0 + 20.0 * avg_amount / 10
                
        except Exception as e:
            logger.debug(f"计算{symbol}成交量分数失败: {e}")
            return 0.0
    
    def calculate_price_volatility(self, symbol: str, days: int = 5) -> float:
        """计算价格波动活跃度分数"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)
            
            data = self.historical_manager.load_historical_data(
                symbol, "daily",
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data is None or data.empty:
                return 0.0
            
            data = data.tail(days)
            if len(data) < days * 0.7:
                return 0.0
            
            # 计算平均涨跌幅绝对值
            volatility = data['change_pct'].abs().mean()
            
            # 标准化到0-100分
            if volatility >= 5:      # 5%以上
                return 100.0
            elif volatility >= 3:    # 3-5%
                return 80.0 + 20.0 * (volatility - 3) / 2
            elif volatility >= 1:    # 1-3%
                return 50.0 + 30.0 * (volatility - 1) / 2
            elif volatility >= 0.5:  # 0.5-1%
                return 20.0 + 30.0 * (volatility - 0.5) / 0.5
            else:                    # 0.5%以下
                return 0.0 + 20.0 * volatility / 0.5
                
        except Exception as e:
            logger.debug(f"计算{symbol}价格波动分数失败: {e}")
            return 0.0
    
    def calculate_news_heat_score(self, symbol: str) -> float:
        """计算新闻热度分数（简化版）"""
        # 这里简化处理，实际需要从新闻数据源获取
        # 暂时返回一个基础分数，后续可扩展
        return 50.0
    
    def calculate_fund_flow_score(self, symbol: str) -> float:
        """计算资金流向分数（简化版）"""
        # 这里简化处理，实际需要从资金流向数据获取
        # 暂时返回一个基础分数，后续可扩展
        return 50.0
    
    def calculate_activity_score(self, symbol: str, days: int = 5) -> Dict[str, float]:
        """
        计算股票活跃度综合分数
        
        Args:
            symbol: 股票代码
            days: 计算天数
            
        Returns:
            活跃度评分详情
        """
        try:
            logger.info(f"📊 计算{symbol}活跃度评分...")
            
            # 计算各维度分数
            turnover_score = self.calculate_turnover_rate(symbol, days)
            volume_score = self.calculate_volume_score(symbol, days)
            volatility_score = self.calculate_price_volatility(symbol, days)
            news_score = self.calculate_news_heat_score(symbol)
            fund_score = self.calculate_fund_flow_score(symbol)
            
            # 标准化换手率分数
            turnover_normalized = min(100.0, turnover_score * 10)  # 10%换手率为满分
            
            # 综合评分
            total_score = (
                turnover_normalized * self.weights['turnover_rate'] +
                volume_score * self.weights['volume'] +
                volatility_score * self.weights['price_volatility'] +
                news_score * self.weights['news_heat'] +
                fund_score * self.weights['fund_flow']
            )
            
            result = {
                'symbol': symbol,
                'total_score': round(total_score, 2),
                'turnover_rate': round(turnover_score, 2),
                'turnover_score': round(turnover_normalized, 2),
                'volume_score': round(volume_score, 2),
                'volatility_score': round(volatility_score, 2),
                'news_score': round(news_score, 2),
                'fund_score': round(fund_score, 2),
                'classification': self._classify_by_score(total_score),
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {symbol}活跃度评分: {total_score:.2f}分 - {result['classification']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 计算{symbol}活跃度评分失败: {e}")
            return {
                'symbol': symbol,
                'total_score': 0.0,
                'classification': 'unknown',
                'error': str(e)
            }
    
    def _classify_by_score(self, score: float) -> str:
        """根据分数分类"""
        if score >= self.thresholds['active']:
            return 'active'      # 活跃股票
        elif score >= self.thresholds['normal']:
            return 'normal'      # 普通股票
        else:
            return 'inactive'    # 冷门股票
    
    def classify_stocks(self, symbols: List[str], days: int = 5) -> Dict[str, List[str]]:
        """
        批量分类股票
        
        Args:
            symbols: 股票代码列表
            days: 计算天数
            
        Returns:
            分类结果字典
        """
        logger.info(f"📊 开始批量分类{len(symbols)}只股票...")
        
        results = {
            'active': [],      # 活跃股票
            'normal': [],      # 普通股票
            'inactive': [],    # 冷门股票
            'unknown': []      # 未知分类
        }
        
        for symbol in symbols:
            try:
                score_result = self.calculate_activity_score(symbol, days)
                classification = score_result['classification']
                
                if classification in results:
                    results[classification].append(symbol)
                else:
                    results['unknown'].append(symbol)
                    
            except Exception as e:
                logger.error(f"❌ 分类{symbol}失败: {e}")
                results['unknown'].append(symbol)
        
        # 统计结果
        total = sum(len(v) for v in results.values())
        logger.info(f"📈 分类完成：活跃{len(results['active'])}只，普通{len(results['normal'])}只，冷门{len(results['inactive'])}只，未知{len(results['unknown'])}只")
        
        return results
    
    def get_update_frequency(self, classification: str) -> str:
        """获取更新频率"""
        frequency_map = {
            'active': 'daily',      # 每日更新
            'normal': 'weekly',     # 每周更新
            'inactive': 'monthly',  # 每月更新
            'unknown': 'weekly'     # 默认每周
        }
        return frequency_map.get(classification, 'weekly')


# 全局实例
_activity_classifier = None


def get_activity_classifier() -> StockActivityClassifier:
    """获取活跃度分类器实例"""
    global _activity_classifier
    if _activity_classifier is None:
        _activity_classifier = StockActivityClassifier()
    return _activity_classifier


# 便捷函数
def classify_stock_activity(symbol: str, days: int = 5) -> Dict[str, float]:
    """单个股票活跃度分类"""
    return get_activity_classifier().calculate_activity_score(symbol, days)


def classify_stocks_batch(symbols: List[str], days: int = 5) -> Dict[str, List[str]]:
    """批量股票活跃度分类"""
    return get_activity_classifier().classify_stocks(symbols, days)