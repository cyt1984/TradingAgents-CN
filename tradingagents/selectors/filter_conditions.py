#!/usr/bin/env python3
"""
筛选条件数据结构定义
支持多种类型的筛选条件和逻辑组合
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import pandas as pd
from abc import ABC, abstractmethod

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class FilterOperator(Enum):
    """筛选操作符"""
    # 数值比较
    EQUAL = "=="          # 等于
    NOT_EQUAL = "!="      # 不等于
    GREATER = ">"         # 大于
    GREATER_EQUAL = ">="  # 大于等于
    LESS = "<"            # 小于
    LESS_EQUAL = "<="     # 小于等于
    BETWEEN = "between"   # 区间范围
    NOT_BETWEEN = "not_between"  # 非区间范围
    
    # 字符串匹配
    CONTAINS = "contains"     # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    STARTS_WITH = "starts_with"    # 开头匹配
    ENDS_WITH = "ends_with"        # 结尾匹配
    
    # 集合操作
    IN = "in"             # 在集合中
    NOT_IN = "not_in"     # 不在集合中
    
    # 特殊操作
    IS_NULL = "is_null"       # 为空
    IS_NOT_NULL = "is_not_null"  # 不为空


class FilterLogic(Enum):
    """筛选逻辑"""
    AND = "and"   # 与逻辑
    OR = "or"     # 或逻辑
    NOT = "not"   # 非逻辑


@dataclass
class FilterCondition(ABC):
    """筛选条件基类"""
    field_name: str                    # 字段名称
    field_display_name: str            # 字段显示名称
    operator: FilterOperator           # 操作符
    description: Optional[str] = None  # 描述信息
    
    @abstractmethod
    def validate_value(self, value: Any) -> bool:
        """验证值是否符合条件类型"""
        pass
    
    @abstractmethod
    def apply_filter(self, data: pd.DataFrame) -> pd.Series:
        """应用筛选条件到数据"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'field_name': self.field_name,
            'field_display_name': self.field_display_name,
            'operator': self.operator.value,
            'description': self.description,
            'type': self.__class__.__name__
        }


@dataclass
class NumericFilter(FilterCondition):
    """数值型筛选条件"""
    value: Union[float, int, Tuple[float, float]] = None  # 筛选值或范围
    min_value: Optional[float] = None                     # 最小值限制
    max_value: Optional[float] = None                     # 最大值限制
    decimal_places: int = 2                               # 小数位数
    
    def validate_value(self, value: Any) -> bool:
        """验证数值是否有效"""
        try:
            if self.operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]:
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    return False
                min_val, max_val = float(value[0]), float(value[1])
                return min_val <= max_val
            else:
                float(value)
                return True
        except (ValueError, TypeError):
            return False
    
    def apply_filter(self, data: pd.DataFrame) -> pd.Series:
        """应用数值筛选"""
        if self.field_name not in data.columns:
            logger.warning(f"字段 {self.field_name} 不存在于数据中")
            return pd.Series([False] * len(data))
        
        series = pd.to_numeric(data[self.field_name], errors='coerce')
        
        try:
            if self.operator == FilterOperator.EQUAL:
                return series == self.value
            elif self.operator == FilterOperator.NOT_EQUAL:
                return series != self.value
            elif self.operator == FilterOperator.GREATER:
                return series > self.value
            elif self.operator == FilterOperator.GREATER_EQUAL:
                return series >= self.value
            elif self.operator == FilterOperator.LESS:
                return series < self.value
            elif self.operator == FilterOperator.LESS_EQUAL:
                return series <= self.value
            elif self.operator == FilterOperator.BETWEEN:
                min_val, max_val = self.value
                return (series >= min_val) & (series <= max_val)
            elif self.operator == FilterOperator.NOT_BETWEEN:
                min_val, max_val = self.value
                return (series < min_val) | (series > max_val)
            elif self.operator == FilterOperator.IS_NULL:
                return series.isna()
            elif self.operator == FilterOperator.IS_NOT_NULL:
                return ~series.isna()
            else:
                logger.error(f"不支持的数值操作符: {self.operator}")
                return pd.Series([False] * len(data))
        except Exception as e:
            logger.error(f"应用数值筛选时出错: {e}")
            return pd.Series([False] * len(data))


@dataclass
class EnumFilter(FilterCondition):
    """枚举型筛选条件"""
    value: Union[str, List[str]] = None    # 筛选值或值列表
    allowed_values: List[str] = None       # 允许的值列表
    case_sensitive: bool = False           # 是否大小写敏感
    
    def validate_value(self, value: Any) -> bool:
        """验证枚举值是否有效"""
        if self.operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(value, (list, tuple)):
                return False
            values_to_check = value
        else:
            values_to_check = [value]
        
        if self.allowed_values:
            if self.case_sensitive:
                return all(v in self.allowed_values for v in values_to_check)
            else:
                allowed_lower = [v.lower() for v in self.allowed_values]
                return all(str(v).lower() in allowed_lower for v in values_to_check)
        return True
    
    def apply_filter(self, data: pd.DataFrame) -> pd.Series:
        """应用枚举筛选"""
        if self.field_name not in data.columns:
            logger.warning(f"字段 {self.field_name} 不存在于数据中")
            return pd.Series([False] * len(data))
        
        series = data[self.field_name].astype(str)
        if not self.case_sensitive:
            series = series.str.lower()
            if isinstance(self.value, str):
                compare_value = self.value.lower()
            elif isinstance(self.value, list):
                compare_value = [str(v).lower() for v in self.value]
            else:
                compare_value = self.value
        else:
            compare_value = self.value
        
        try:
            if self.operator == FilterOperator.EQUAL:
                return series == compare_value
            elif self.operator == FilterOperator.NOT_EQUAL:
                return series != compare_value
            elif self.operator == FilterOperator.CONTAINS:
                return series.str.contains(compare_value, na=False)
            elif self.operator == FilterOperator.NOT_CONTAINS:
                return ~series.str.contains(compare_value, na=False)
            elif self.operator == FilterOperator.STARTS_WITH:
                return series.str.startswith(compare_value, na=False)
            elif self.operator == FilterOperator.ENDS_WITH:
                return series.str.endswith(compare_value, na=False)
            elif self.operator == FilterOperator.IN:
                return series.isin(compare_value)
            elif self.operator == FilterOperator.NOT_IN:
                return ~series.isin(compare_value)
            elif self.operator == FilterOperator.IS_NULL:
                return data[self.field_name].isna()
            elif self.operator == FilterOperator.IS_NOT_NULL:
                return ~data[self.field_name].isna()
            else:
                logger.error(f"不支持的枚举操作符: {self.operator}")
                return pd.Series([False] * len(data))
        except Exception as e:
            logger.error(f"应用枚举筛选时出错: {e}")
            return pd.Series([False] * len(data))


@dataclass
class BooleanFilter(FilterCondition):
    """布尔型筛选条件"""
    value: bool = None  # 筛选值
    
    def validate_value(self, value: Any) -> bool:
        """验证布尔值是否有效"""
        return isinstance(value, (bool, int, str)) and str(value).lower() in ['true', 'false', '1', '0']
    
    def apply_filter(self, data: pd.DataFrame) -> pd.Series:
        """应用布尔筛选"""
        if self.field_name not in data.columns:
            logger.warning(f"字段 {self.field_name} 不存在于数据中")
            return pd.Series([False] * len(data))
        
        try:
            # 转换为布尔值
            series = data[self.field_name].astype(bool)
            
            if self.operator == FilterOperator.EQUAL:
                return series == self.value
            elif self.operator == FilterOperator.NOT_EQUAL:
                return series != self.value
            elif self.operator == FilterOperator.IS_NULL:
                return data[self.field_name].isna()
            elif self.operator == FilterOperator.IS_NOT_NULL:
                return ~data[self.field_name].isna()
            else:
                logger.error(f"不支持的布尔操作符: {self.operator}")
                return pd.Series([False] * len(data))
        except Exception as e:
            logger.error(f"应用布尔筛选时出错: {e}")
            return pd.Series([False] * len(data))


@dataclass
class FilterGroup:
    """筛选条件组"""
    conditions: List[Union[FilterCondition, 'FilterGroup']]  # 条件列表
    logic: FilterLogic = FilterLogic.AND                     # 逻辑关系
    description: Optional[str] = None                        # 描述信息
    
    def apply_filter(self, data: pd.DataFrame) -> pd.Series:
        """应用条件组筛选"""
        if not self.conditions:
            return pd.Series([True] * len(data))
        
        results = []
        for condition in self.conditions:
            try:
                result = condition.apply_filter(data)
                results.append(result)
            except Exception as e:
                logger.error(f"应用筛选条件时出错: {e}")
                results.append(pd.Series([False] * len(data)))
        
        if not results:
            return pd.Series([True] * len(data))
        
        # 应用逻辑操作
        final_result = results[0]
        for result in results[1:]:
            if self.logic == FilterLogic.AND:
                final_result = final_result & result
            elif self.logic == FilterLogic.OR:
                final_result = final_result | result
        
        if self.logic == FilterLogic.NOT:
            final_result = ~final_result
        
        return final_result
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'conditions': [c.to_dict() if hasattr(c, 'to_dict') else str(c) for c in self.conditions],
            'logic': self.logic.value,
            'description': self.description,
            'type': 'FilterGroup'
        }


# 常用的股票筛选字段定义
STOCK_FILTER_FIELDS = {
    # 基本信息
    'symbol': {'name': '股票代码', 'type': 'enum', 'description': '股票代码筛选'},
    'name': {'name': '股票名称', 'type': 'enum', 'description': '股票名称筛选'},
    'industry': {'name': '所属行业', 'type': 'enum', 'description': '行业分类筛选'},
    'sector': {'name': '所属板块', 'type': 'enum', 'description': '板块分类筛选'},
    
    # 价格相关
    'current_price': {'name': '最新价', 'type': 'numeric', 'description': '当前股价'},
    'change_percent': {'name': '涨跌幅(%)', 'type': 'numeric', 'description': '当日涨跌幅'},
    'change_amount': {'name': '涨跌额', 'type': 'numeric', 'description': '当日涨跌额'},
    
    # 市场指标
    'market_cap': {'name': '总市值', 'type': 'numeric', 'description': '总市值(亿元)'},
    'pe_ratio': {'name': '市盈率', 'type': 'numeric', 'description': '动态市盈率'},
    'pb_ratio': {'name': '市净率', 'type': 'numeric', 'description': '市净率'},
    'volume': {'name': '成交量', 'type': 'numeric', 'description': '成交量'},
    'turnover': {'name': '换手率(%)', 'type': 'numeric', 'description': '换手率'},
    
    # 财务指标
    'roe': {'name': 'ROE(%)', 'type': 'numeric', 'description': '净资产收益率'},
    'roa': {'name': 'ROA(%)', 'type': 'numeric', 'description': '总资产收益率'},
    'gross_margin': {'name': '毛利率(%)', 'type': 'numeric', 'description': '毛利率'},
    'debt_ratio': {'name': '资产负债率(%)', 'type': 'numeric', 'description': '资产负债率'},
    'current_ratio': {'name': '流动比率', 'type': 'numeric', 'description': '流动比率'},
    
    # 评分相关
    'overall_score': {'name': '综合评分', 'type': 'numeric', 'description': '系统综合评分'},
    'technical_score': {'name': '技术面评分', 'type': 'numeric', 'description': '技术分析评分'},
    'fundamental_score': {'name': '基本面评分', 'type': 'numeric', 'description': '基本面分析评分'},
    'sentiment_score': {'name': '情绪面评分', 'type': 'numeric', 'description': '情绪分析评分'},
    'quality_score': {'name': '数据质量评分', 'type': 'numeric', 'description': '数据质量评分'},
    'risk_score': {'name': '风险评分', 'type': 'numeric', 'description': '风险评分'},
    'grade': {'name': '投资等级', 'type': 'enum', 'description': '投资等级评定', 
              'allowed_values': ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D']},
}