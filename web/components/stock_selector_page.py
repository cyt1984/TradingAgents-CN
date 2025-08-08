#!/usr/bin/env python3
"""
选股页面组件
提供智能选股功能的完整Web界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('web')

def render_selection_help():
    """渲染选股帮助信息"""
    with st.expander("❓ 使用帮助", expanded=False):
        st.markdown("""
        ### 🎯 快速选股
        - **综合评分**: 0-100分，推荐≥70分
        - **市值**: 建议≥50亿，过滤小盘股风险
        - **市盈率**: 建议≤30倍，避免高估值风险  
        - **投资等级**: A+/A级为优质股票
        
        ### 🔧 自定义筛选
        - 可设置多个筛选条件
        - 支持数值比较操作
        - 可自定义排序字段
        - 结果数量可调整
        
        ### 📊 结果说明
        - **候选总数**: 系统中所有可用股票数量
        - **筛选结果**: 符合条件的股票数量
        - **成功率**: 筛选通过率
        - **执行时间**: 选股耗时
        """)

def render_stock_selector_page():
    """渲染选股页面"""
    st.markdown("# 🎯 智能选股系统")
    st.markdown("基于多源数据融合和综合评分的A股智能选股引擎")
    
    # 添加使用帮助
    render_selection_help()
    st.markdown("---")
    
    # 检查选股引擎可用性
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        from tradingagents.selectors.filter_conditions import FilterOperator
        
        selector = get_stock_selector()
        st.success("✅ 选股引擎已就绪")
        
    except Exception as e:
        st.error(f"❌ 选股引擎初始化失败: {e}")
        st.info("💡 请检查系统配置和依赖")
        return
    
    # 创建两列布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📊 筛选条件设置")
        
        # 选股模式选择
        mode = st.selectbox(
            "选股模式",
            ["快速选股", "自定义筛选"],
            help="快速选股使用预设条件，自定义筛选可设置详细参数"
        )
        
        if mode == "快速选股":
            render_quick_selection_form()
        else:
            render_custom_selection_form()
    
    with col2:
        st.markdown("### 📈 选股结果")
        
        # 选股按钮
        if st.button("🚀 开始选股", type="primary", use_container_width=True):
            with st.spinner("🔍 正在选股中..."):
                execute_stock_selection(selector, mode)
        
        # 显示选股结果
        display_selection_results()

def render_quick_selection_form():
    """渲染快速选股表单"""
    st.markdown("#### 🎯 快速选股参数")
    
    # 综合评分
    min_score = st.slider(
        "最小综合评分",
        min_value=0,
        max_value=100,
        value=70,
        step=5,
        help="选择综合评分最低要求"
    )
    
    # 市值要求
    min_market_cap = st.number_input(
        "最小市值 (亿元)",
        min_value=0.0,
        max_value=10000.0,
        value=50.0,
        step=10.0,
        help="设置市值门槛"
    )
    
    # 市盈率上限
    max_pe_ratio = st.number_input(
        "最大市盈率",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=5.0,
        help="设置市盈率上限"
    )
    
    # 投资等级
    grades = st.multiselect(
        "投资等级",
        options=['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-'],
        default=['A+', 'A'],
        help="选择期望的投资等级"
    )
    
    # 结果数量
    limit = st.selectbox(
        "返回数量",
        options=[10, 20, 50, 100],
        index=1,
        help="选择返回的股票数量"
    )
    
    # 保存到session state
    st.session_state.quick_params = {
        'min_score': min_score,
        'min_market_cap': min_market_cap,
        'max_pe_ratio': max_pe_ratio,
        'grades': grades,
        'limit': limit
    }

def render_custom_selection_form():
    """渲染自定义筛选表单"""
    st.markdown("#### 🔧 自定义筛选参数")
    
    # 获取可用字段
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        selector = get_stock_selector()
        fields = selector.get_available_fields()
        
        # 数值类型字段
        numeric_fields = {k: v for k, v in fields.items() if v.get('type') == 'numeric'}
        
        st.markdown("##### 📊 数值条件")
        conditions = []
        
        # 动态添加筛选条件
        num_conditions = st.number_input("筛选条件数量", 1, 5, 2)
        
        for i in range(int(num_conditions)):
            with st.expander(f"条件 {i+1}", expanded=True):
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    field = st.selectbox(
                        "字段",
                        options=list(numeric_fields.keys()),
                        format_func=lambda x: numeric_fields.get(x, {}).get('name', x),
                        key=f"field_{i}"
                    )
                
                with col_b:
                    operator = st.selectbox(
                        "条件",
                        options=['>=', '<=', '=', '!='],
                        key=f"op_{i}"
                    )
                
                with col_c:
                    value = st.number_input(
                        "数值",
                        value=0.0,
                        key=f"val_{i}"
                    )
                
                conditions.append({
                    'field': field,
                    'operator': operator,
                    'value': value
                })
        
        # 排序设置
        st.markdown("##### 📈 排序设置")
        sort_field = st.selectbox(
            "排序字段",
            options=['overall_score'] + list(numeric_fields.keys())[:10],
            format_func=lambda x: fields.get(x, {}).get('name', x) if x in fields else x
        )
        
        sort_desc = st.checkbox("降序排列", value=True)
        
        # 结果数量
        limit = st.number_input("结果数量", 1, 200, 50)
        
        # 保存到session state
        st.session_state.custom_params = {
            'conditions': conditions,
            'sort_field': sort_field,
            'sort_desc': sort_desc,
            'limit': limit
        }
        
    except Exception as e:
        st.error(f"获取字段信息失败: {e}")

def execute_stock_selection(selector, mode):
    """执行选股操作"""
    try:
        if mode == "快速选股":
            params = st.session_state.get('quick_params', {})
            result = selector.quick_select(
                min_score=params.get('min_score', 70),
                min_market_cap=params.get('min_market_cap', 50),
                max_pe_ratio=params.get('max_pe_ratio', 30),
                grades=params.get('grades', ['A+', 'A']),
                limit=params.get('limit', 20)
            )
        else:
            # 自定义筛选逻辑
            from tradingagents.selectors.stock_selector import SelectionCriteria
            from tradingagents.selectors.filter_conditions import FilterOperator
            
            params = st.session_state.get('custom_params', {})
            conditions = params.get('conditions', [])
            
            # 构建筛选器
            filters = []
            for cond in conditions:
                if cond['operator'] == '>=':
                    op = FilterOperator.GREATER_EQUAL
                elif cond['operator'] == '<=':
                    op = FilterOperator.LESS_EQUAL
                elif cond['operator'] == '=':
                    op = FilterOperator.EQUAL
                else:  # !=
                    op = FilterOperator.NOT_EQUAL
                
                filter_obj = selector.create_numeric_filter(
                    cond['field'], op, cond['value']
                )
                filters.append(filter_obj)
            
            criteria = SelectionCriteria(
                filters=filters,
                sort_by=params.get('sort_field', 'overall_score'),
                sort_ascending=not params.get('sort_desc', True),
                limit=params.get('limit', 50),
                include_scores=True,
                include_basic_info=True
            )
            
            result = selector.select_stocks(criteria)
        
        # 保存结果到session state
        st.session_state.selection_result = result
        
        # 显示成功消息
        st.success(f"✅ 选股完成! 找到 {len(result.symbols)} 只股票")
        logger.info(f"📊 [选股成功] 找到 {len(result.symbols)} 只股票")
        
    except Exception as e:
        st.error(f"❌ 选股失败: {e}")
        logger.error(f"❌ [选股失败] {e}")

def display_selection_results():
    """显示选股结果"""
    if 'selection_result' not in st.session_state:
        st.info("👈 请在左侧设置条件并执行选股")
        return
    
    result = st.session_state.selection_result
    
    if not result.symbols:
        st.warning("😔 未找到符合条件的股票，请调整筛选条件")
        return
    
    # 显示基本统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("候选总数", result.total_candidates)
    with col2:
        st.metric("筛选结果", result.filtered_count)
    with col3:
        st.metric("成功率", f"{result.summary.get('success_rate', 0):.1f}%")
    with col4:
        st.metric("执行时间", f"{result.execution_time:.2f}s")
    
    st.markdown("---")
    
    # 显示股票列表
    st.markdown("### 📋 选股结果")
    
    if not result.data.empty:
        # 准备显示数据
        display_data = result.data.copy()
        
        # 选择要显示的列
        display_columns = []
        if 'ts_code' in display_data.columns:
            display_columns.append('ts_code')
        if 'name' in display_data.columns:
            display_columns.append('name')
        if 'overall_score' in display_data.columns:
            display_columns.append('overall_score')
        if 'grade' in display_data.columns:
            display_columns.append('grade')
        if 'market_cap' in display_data.columns:
            display_columns.append('market_cap')
        if 'pe_ratio' in display_data.columns:
            display_columns.append('pe_ratio')
        
        # 显示表格
        if display_columns:
            st.dataframe(
                display_data[display_columns].head(50),
                use_container_width=True,
                hide_index=True
            )
        else:
            # 如果没有预期的列，显示所有数据
            st.dataframe(display_data.head(50), use_container_width=True)
    else:
        # 只显示股票代码列表
        symbols_df = pd.DataFrame({
            '序号': range(1, len(result.symbols) + 1),
            '股票代码': result.symbols
        })
        st.dataframe(symbols_df, use_container_width=True, hide_index=True)
    
    # 显示统计信息
    if 'statistics' in result.summary:
        with st.expander("📊 详细统计信息", expanded=False):
            stats = result.summary['statistics']
            
            for field, stat_data in list(stats.items())[:5]:  # 显示前5个统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{field} 平均", f"{stat_data.get('mean', 0):.2f}")
                with col2:
                    st.metric(f"{field} 最大", f"{stat_data.get('max', 0):.2f}")
                with col3:
                    st.metric(f"{field} 最小", f"{stat_data.get('min', 0):.2f}")
    
    # 导出功能
    if st.button("📄 导出结果", help="导出选股结果到CSV文件"):
        try:
            csv_data = result.data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 下载CSV文件",
                data=csv_data,
                file_name=f"选股结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"导出失败: {e}")

if __name__ == "__main__":
    render_stock_selector_page()