#!/usr/bin/env python3
"""
智能选股系统
基于多源数据融合的A股智能筛选模块
"""

from .stock_selector import StockSelector, SelectionCriteria, SelectionResult
from .filter_conditions import (
    FilterCondition, 
    NumericFilter, 
    EnumFilter, 
    BooleanFilter,
    FilterOperator,
    FilterLogic,
    FilterGroup
)

__all__ = [
    'StockSelector',
    'SelectionCriteria',
    'SelectionResult',
    'FilterCondition',
    'NumericFilter', 
    'EnumFilter', 
    'BooleanFilter',
    'FilterOperator',
    'FilterLogic',
    'FilterGroup'
]

__version__ = '1.0.0'