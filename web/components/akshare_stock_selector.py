#!/usr/bin/env python3
"""
基于AkShare的A股选股组件
无需API token的免费A股选股方案
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

@st.cache_data(ttl=300)  # 缓存5分钟
def get_akshare_stock_data():
    """获取AkShare股票数据并缓存"""
    try:
        import akshare as ak
        
        # 获取A股实时数据
        stock_data = ak.stock_zh_a_spot_em()
        
        if not stock_data.empty:
            # 数据清理和标准化
            cleaned_data = stock_data.copy()
            
            # 重命名列 - 先保留原始列，再添加新列
            if '代码' in cleaned_data.columns:
                cleaned_data['code'] = cleaned_data['代码']
            if '名称' in cleaned_data.columns:
                cleaned_data['name'] = cleaned_data['名称']  # 保持字符串类型
            
            # 数值列映射
            numeric_column_mapping = {
                '最新价': 'price', 
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '市盈率-动态': 'pe_ratio',
                '市净率': 'pb_ratio'
            }
            
            for old_col, new_col in numeric_column_mapping.items():
                if old_col in cleaned_data.columns:
                    cleaned_data[new_col] = pd.to_numeric(cleaned_data[old_col], errors='coerce')
            
            # 添加计算字段
            cleaned_data['market_cap'] = cleaned_data.get('price', 0) * 100  # 简化的市值计算
            cleaned_data['ts_code'] = cleaned_data.get('code', '')
            
            # 确保name列不为空
            if 'name' not in cleaned_data.columns and '名称' in cleaned_data.columns:
                cleaned_data['name'] = cleaned_data['名称']
            
            # 调试输出
            print(f"数据处理完成，列名: {list(cleaned_data.columns)}")
            if 'name' in cleaned_data.columns:
                print(f"name列样本: {cleaned_data['name'].head(3).tolist()}")
            
            return cleaned_data
        else:
            return pd.DataFrame()
            
    except ImportError:
        st.error("❌ 需要安装AkShare: pip install akshare")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ 获取股票数据失败: {e}")
        return pd.DataFrame()

def calculate_stock_score(row):
    """计算股票综合评分"""
    score = 50  # 基础分
    
    try:
        # 价格因子 (10分)
        if pd.notna(row.get('price')):
            price = row['price']
            if 5 <= price <= 100:
                score += 10
            elif 3 <= price <= 200:
                score += 5
        
        # 市盈率因子 (20分)
        if pd.notna(row.get('pe_ratio')):
            pe = row['pe_ratio']
            if 0 < pe <= 15:
                score += 20
            elif 15 < pe <= 25:
                score += 15
            elif 25 < pe <= 40:
                score += 10
        
        # 涨跌幅因子 (15分)
        if pd.notna(row.get('pct_change')):
            pct_change = row['pct_change']
            if -2 <= pct_change <= 5:
                score += 15
            elif -5 <= pct_change <= 8:
                score += 10
        
        # 成交额因子 (5分)
        if pd.notna(row.get('amount')):
            amount = row['amount']
            if amount >= 50000000:  # 5000万以上
                score += 5
                
    except Exception:
        pass
    
    return min(max(score, 0), 100)

def get_investment_grade(score):
    """根据评分获得投资等级"""
    if score >= 85:
        return 'A+'
    elif score >= 75:
        return 'A'
    elif score >= 65:
        return 'A-'
    elif score >= 55:
        return 'B+'
    elif score >= 45:
        return 'B'
    elif score >= 35:
        return 'B-'
    else:
        return 'C'

def render_akshare_stock_selector():
    """渲染AkShare A股选股页面"""
    st.markdown("# 🇨🇳 A股智能选股 (AkShare)")
    st.markdown("基于AkShare免费数据的A股选股系统，无需API token")
    
    # 使用帮助
    with st.expander("❓ 使用说明", expanded=False):
        st.markdown("""
        ### 🎯 功能特色
        - ✅ **完全免费** - 无需任何API token
        - ✅ **实时数据** - 基于AkShare实时A股数据  
        - ✅ **智能评分** - 多维度股票评分系统
        - ✅ **灵活筛选** - 支持多种筛选条件
        
        ### 📊 评分体系
        - **价格合理性** (10分): 合理价格区间加分
        - **估值水平** (20分): 市盈率合理性评估
        - **表现稳定性** (15分): 涨跌幅稳定性
        - **活跃度** (5分): 成交额活跃度
        - **基础分** (50分): 所有股票基础分
        
        ### 🏆 投资等级
        - **A+级**: 85分以上，优质投资标的
        - **A级**: 75-84分，良好投资机会  
        - **B级**: 45-74分，一般投资标的
        - **C级**: 45分以下，谨慎投资
        """)
    
    st.markdown("---")
    
    # 获取股票数据
    with st.spinner("📊 正在获取A股数据..."):
        stock_data = get_akshare_stock_data()
    
    if stock_data.empty:
        st.error("❌ 无法获取股票数据，请稍后重试")
        return
    
    st.success(f"✅ 成功获取 {len(stock_data)} 只A股数据")
    
    # 调试信息
    with st.expander("🔍 数据列信息 (调试用)", expanded=False):
        st.write(f"数据列: {list(stock_data.columns)}")
        if not stock_data.empty:
            st.write("前3行样本数据:")
            sample_cols = ['code', 'name', 'price', 'pct_change']
            available_cols = [col for col in sample_cols if col in stock_data.columns]
            if available_cols:
                st.dataframe(stock_data[available_cols].head(3))
            else:
                st.write("原始列名:")
                st.write(stock_data.head(3))
    
    # 创建两列布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🔍 筛选条件")
        
        # 价格范围
        price_range = st.slider(
            "股价范围 (元)",
            min_value=0.0,
            max_value=500.0,
            value=(3.0, 100.0),
            step=1.0,
            help="设置股价筛选范围"
        )
        
        # 市盈率范围
        pe_range = st.slider(
            "市盈率范围",
            min_value=0,
            max_value=100,
            value=(5, 30),
            step=1,
            help="设置市盈率筛选范围"
        )
        
        # 涨跌幅范围
        pct_change_range = st.slider(
            "涨跌幅范围 (%)",
            min_value=-10.0,
            max_value=10.0,
            value=(-5.0, 5.0),
            step=0.5,
            help="设置涨跌幅筛选范围"
        )
        
        # 最小成交额
        min_amount = st.number_input(
            "最小成交额 (万元)",
            min_value=0,
            max_value=1000000,
            value=1000,
            step=500,
            help="设置最小成交额要求"
        )
        
        # 最小评分
        min_score = st.slider(
            "最小综合评分",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
            help="设置最小综合评分要求"
        )
        
        # 结果数量
        result_limit = st.selectbox(
            "返回股票数量",
            [10, 20, 50, 100],
            index=1,
            help="选择返回的股票数量"
        )
        
        # 排序方式
        sort_by = st.selectbox(
            "排序方式",
            ["综合评分", "涨跌幅", "成交额", "市盈率"],
            index=0,
            help="选择排序字段"
        )
    
    with col2:
        st.markdown("### 🎯 选股结果")
        
        if st.button("🚀 开始A股选股", type="primary", use_container_width=True):
            with st.spinner("🔍 正在分析筛选..."):
                # 执行选股
                result = execute_akshare_selection(
                    stock_data, price_range, pe_range, pct_change_range, 
                    min_amount, min_score, result_limit, sort_by
                )
                
                if result is not None and not result.empty:
                    st.session_state.akshare_result = result
                    st.success(f"✅ 选股完成! 找到 {len(result)} 只优质A股")
                else:
                    st.warning("😔 未找到符合条件的股票，请调整筛选条件")
        
        # 显示选股结果
        display_akshare_results()

def execute_akshare_selection(data, price_range, pe_range, pct_change_range, 
                             min_amount, min_score, limit, sort_by):
    """执行AkShare选股筛选"""
    try:
        # 复制数据
        filtered_data = data.copy()
        original_count = len(filtered_data)
        
        # 计算综合评分
        filtered_data['overall_score'] = filtered_data.apply(calculate_stock_score, axis=1)
        filtered_data['grade'] = filtered_data['overall_score'].apply(get_investment_grade)
        
        # 应用筛选条件
        
        # 1. 价格筛选
        if 'price' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['price'] >= price_range[0]) & 
                (filtered_data['price'] <= price_range[1]) &
                (filtered_data['price'].notna())
            ]
        
        # 2. 市盈率筛选
        if 'pe_ratio' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['pe_ratio'] >= pe_range[0]) & 
                (filtered_data['pe_ratio'] <= pe_range[1]) &
                (filtered_data['pe_ratio'].notna()) &
                (filtered_data['pe_ratio'] > 0)
            ]
        
        # 3. 涨跌幅筛选
        if 'pct_change' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['pct_change'] >= pct_change_range[0]) & 
                (filtered_data['pct_change'] <= pct_change_range[1]) &
                (filtered_data['pct_change'].notna())
            ]
        
        # 4. 成交额筛选
        if 'amount' in filtered_data.columns:
            min_amount_value = min_amount * 10000  # 万元转元
            filtered_data = filtered_data[
                (filtered_data['amount'] >= min_amount_value) &
                (filtered_data['amount'].notna())
            ]
        
        # 5. 综合评分筛选
        filtered_data = filtered_data[filtered_data['overall_score'] >= min_score]
        
        # 排序
        sort_column_map = {
            "综合评分": "overall_score",
            "涨跌幅": "pct_change", 
            "成交额": "amount",
            "市盈率": "pe_ratio"
        }
        
        sort_column = sort_column_map.get(sort_by, "overall_score")
        if sort_column in filtered_data.columns:
            ascending = False if sort_by in ["综合评分", "涨跌幅", "成交额"] else True
            filtered_data = filtered_data.sort_values(sort_column, ascending=ascending)
        
        # 限制结果数量
        result = filtered_data.head(limit)
        
        logger.info(f"A股选股完成: {original_count} -> {len(result)} 只股票")
        return result
        
    except Exception as e:
        logger.error(f"A股选股失败: {e}")
        return pd.DataFrame()

def display_akshare_results():
    """显示AkShare选股结果"""
    if 'akshare_result' not in st.session_state:
        st.info("👈 请设置条件并执行选股")
        return
    
    result = st.session_state.akshare_result
    
    if result.empty:
        st.warning("😔 未找到符合条件的股票")
        return
    
    # 基本统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("筛选结果", f"{len(result)}只")
    with col2:
        avg_score = result['overall_score'].mean()
        st.metric("平均评分", f"{avg_score:.1f}分")
    with col3:
        avg_pe = result['pe_ratio'].mean()
        st.metric("平均市盈率", f"{avg_pe:.1f}倍")
    with col4:
        avg_change = result['pct_change'].mean()
        st.metric("平均涨跌幅", f"{avg_change:+.2f}%")
    
    st.markdown("---")
    
    # 股票列表
    st.markdown("### 📋 推荐股票列表")
    
    # 准备显示数据
    display_data = result.copy()
    display_columns = ['code', 'name', 'price', 'pct_change', 'pe_ratio', 'overall_score', 'grade']
    
    # 确保所有列存在，如果没有name列，尝试使用原始列名
    for col in display_columns:
        if col not in display_data.columns:
            if col == 'name' and '名称' in display_data.columns:
                display_data[col] = display_data['名称']
            elif col == 'code' and '代码' in display_data.columns:
                display_data[col] = display_data['代码']
            else:
                display_data[col] = 'N/A'
    
    # 重命名列
    column_names = {
        'code': '股票代码',
        'name': '股票名称', 
        'price': '最新价(元)',
        'pct_change': '涨跌幅(%)',
        'pe_ratio': '市盈率',
        'overall_score': '综合评分',
        'grade': '投资等级'
    }
    
    display_df = display_data[display_columns].rename(columns=column_names)
    
    # 格式化数据
    if '最新价(元)' in display_df.columns:
        display_df['最新价(元)'] = display_df['最新价(元)'].apply(lambda x: f"¥{x:.2f}" if pd.notna(x) else 'N/A')
    if '涨跌幅(%)' in display_df.columns:
        display_df['涨跌幅(%)'] = display_df['涨跌幅(%)'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else 'N/A')
    if '市盈率' in display_df.columns:
        display_df['市盈率'] = display_df['市盈率'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else 'N/A')
    if '综合评分' in display_df.columns:
        display_df['综合评分'] = display_df['综合评分'].apply(lambda x: f"{x:.0f}分" if pd.notna(x) else 'N/A')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # 导出功能
    if st.button("📄 导出结果为CSV"):
        try:
            csv_data = result.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 下载CSV文件",
                data=csv_data,
                file_name=f"A股选股结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"导出失败: {e}")

if __name__ == "__main__":
    render_akshare_stock_selector()