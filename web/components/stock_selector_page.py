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
    st.markdown("基于多源数据融合和综合评分的多市场智能选股引擎")
    
    # 从session state获取侧边栏配置并应用到智能选股系统
    llm_provider = st.session_state.get('llm_provider')
    llm_model = st.session_state.get('llm_model')
    
    # 确保配置传递给后端LLM管理器
    if llm_provider and llm_model:
        try:
            from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
            llm_manager = get_llm_manager()
            
            # 根据侧边栏配置设置LLM模型
            model_mapping = {
                ("dashscope", "qwen-turbo"): "dashscope_qwen_turbo",
                ("dashscope", "qwen-plus-latest"): "dashscope_qwen_plus", 
                ("dashscope", "qwen-max"): "dashscope_qwen_max",
                ("deepseek", "deepseek-chat"): "deepseek_chat",
                ("kimi", "moonshot-v1-8k"): "kimi_chat",
                ("kimi", "moonshot-v1-32k"): "kimi_chat",
                ("kimi", "moonshot-v1-128k"): "kimi_chat",
                ("kimi", "kimi-k2-0711-preview"): "kimi_chat",
                ("kimi", "kimi-k2-turbo-preview"): "kimi_chat",
                ("google", "gemini-2.0-flash"): "google_gemini_pro",
                ("google", "gemini-1.5-pro"): "google_gemini_pro",
                ("google", "gemini-1.5-flash"): "google_gemini_pro",
                ("glm", "glm-4-plus"): "glm_chat",
                ("glm", "glm-4"): "glm_chat", 
                ("glm", "glm-4-air"): "glm_chat",
                ("glm", "glm-4-flash"): "glm_chat",
                ("openrouter", None): "openrouter_claude"  # OpenRouter使用自定义模型
            }
            
            # 查找匹配的模型键
            model_key = None
            for (provider, model), key in model_mapping.items():
                if provider == llm_provider and (model is None or model == llm_model):
                    model_key = key
                    break
            
            # 对于OpenRouter，使用实际的模型名称
            if llm_provider == "openrouter" and llm_model:
                # 创建一个OpenRouter的临时配置
                from tradingagents.llm_adapters.dynamic_llm_manager import LLMConfig
                openrouter_config = LLMConfig(
                    provider="openrouter",
                    model_name=llm_model,
                    base_url="https://openrouter.ai/api/v1",
                    display_name=f"OpenRouter - {llm_model}",
                    description=f"OpenRouter模型: {llm_model}"
                )
                # 添加到可用配置中
                llm_manager.available_configs["openrouter_custom"] = openrouter_config
                model_key = "openrouter_custom"
            
            if not model_key:
                model_key = "openai_gpt4o"  # 默认回退
                
            # 设置当前模型
            success = llm_manager.set_current_model(model_key)
            if success:
                logger.info(f"✅ [智能选股] AI模型已设置: {llm_provider} - {llm_model} -> {model_key}")
            else:
                logger.warning(f"⚠️ [智能选股] AI模型设置失败: {model_key}")
                
        except Exception as e:
            logger.error(f"❌ [智能选股] LLM配置应用失败: {e}")
    else:
        logger.warning("⚠️ [智能选股] 侧边栏LLM配置不完整")
    
    # 添加使用帮助
    render_selection_help()
    st.markdown("---")
    
    # 检查选股引擎可用性
    try:
        from tradingagents.selectors.stock_selector import get_stock_selector
        from tradingagents.selectors.filter_conditions import FilterOperator
        from tradingagents.selectors.ai_strategies.ai_strategy_manager import AIMode
        
        selector = get_stock_selector()
        ai_status = selector.get_ai_performance_summary()
        
        # 显示AI引擎详细状态
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if ai_status.get('ai_enabled', False):
                    availability = ai_status.get('engine_availability', {})
                    available_count = availability.get('available_count', 0)
                    total_count = availability.get('total_count', 4)
                    availability_rate = availability.get('availability_rate', 0)
                    
                    if availability_rate >= 75:
                        st.success(f"🚀 AI专家系统已就绪 ({available_count}/{total_count} 个引擎可用)")
                    elif availability_rate >= 50:
                        st.warning(f"⚡ AI系统部分可用 ({available_count}/{total_count} 个引擎可用)")
                    else:
                        st.warning(f"🔧 AI系统功能受限 ({available_count}/{total_count} 个引擎可用)")
                    
                    # 显示引擎状态详情
                    engines_status = ai_status.get('ai_engines_status', {})
                    status_text = []
                    if engines_status.get('expert_committee'):
                        status_text.append("👥 专家委员会")
                    if engines_status.get('adaptive_engine'):
                        status_text.append("🔄 自适应策略")
                    if engines_status.get('pattern_recognizer'):
                        status_text.append("📈 模式识别")
                    if engines_status.get('similarity_engine'):
                        status_text.append("🔍 相似性分析")
                    
                    if status_text:
                        st.info(f"🤖 可用AI功能：{' • '.join(status_text)}")
                else:
                    st.success("✅ 基础选股引擎已就绪")
                    st.warning("⚠️ AI增强功能不可用，使用基础选股模式")
            
            with col2:
                # AI模型选择和性能监控
                if ai_status.get('ai_enabled', False):
                    # AI模型选择
                    with st.expander("🤖 AI模型选择", expanded=False):
                        render_ai_model_selector(selector)
                    
                    with st.expander("📊 AI性能监控", expanded=False):
                        total_analyses = ai_status.get('total_analyses', 0)
                        cache_hit_rate = ai_status.get('cache_hit_rate', 0)
                        avg_time = ai_status.get('average_processing_time', 0)
                        
                        st.metric("已分析股票", f"{total_analyses}")
                        st.metric("缓存命中率", f"{cache_hit_rate:.1f}%")
                        st.metric("平均耗时", f"{avg_time:.2f}s")
                        
                        # AI调试工具
                        st.markdown("---")
                        st.markdown("**🔧 调试工具**")
                        
                        col_debug1, col_debug2 = st.columns(2)
                        
                        with col_debug1:
                            if st.button("🔍 系统检查", help="检查AI引擎状态"):
                                run_ai_system_check()
                        
                        with col_debug2:
                            if st.button("🧹 清理缓存", help="清理AI分析缓存"):
                                clear_ai_caches()
                else:
                    # 即使AI未启用，也显示模型选择（可能有助于启动AI）
                    with st.expander("🤖 AI模型设置", expanded=False):
                        st.info("⚠️ AI功能未启用，但您可以配置AI模型")
                        render_ai_model_selector(selector)
        
    except Exception as e:
        st.error(f"❌ 选股引擎初始化失败: {e}")
        st.info("💡 请检查系统配置和依赖")
        return
    
    # 添加市场选择
    st.markdown("### 🌍 市场选择")
    market_type = st.selectbox(
        "选择市场",
        ["A股", "美股", "港股"],
        index=0,
        help="选择要分析的股票市场"
    )
    
    # 创建两列布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📊 筛选条件设置")
        
        # 选股模式选择
        mode = st.selectbox(
            "选股模式",
            ["快速选股", "AI增强选股", "专家委员会", "自适应策略", "模式识别", "完整AI分析", "自定义筛选"],
            help="选择不同的选股策略，AI模式提供更智能的分析"
        )
        
        if mode == "快速选股":
            render_quick_selection_form()
        elif mode == "AI增强选股":
            render_ai_enhanced_form()
        elif mode == "专家委员会":
            render_expert_committee_form()
        elif mode == "自适应策略":
            render_adaptive_strategy_form()
        elif mode == "模式识别":
            render_pattern_based_form()
        elif mode == "完整AI分析":
            render_full_ai_form()
        else:
            render_custom_selection_form()
    
    with col2:
        st.markdown("### 📈 选股结果")
        
        # 选股按钮
        if st.button("🚀 开始选股", type="primary", use_container_width=True):
            with st.spinner("🔍 正在选股中..."):
                execute_stock_selection(selector, mode)
        
        # 保存市场类型到session state
        st.session_state.market_type = market_type
        
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

def render_ai_enhanced_form():
    """渲染AI增强选股表单"""
    st.markdown("#### 🤖 AI增强选股")
    st.info("🎆 使用AI专家委员会、自适应策略、模式识别等多种AI技术")
    
    # AI评分要求
    min_ai_score = st.slider(
        "AI最小综合评分",
        min_value=0,
        max_value=100,
        value=75,
        step=5,
        help="AI综合分析后的最低评分要求"
    )
    
    # 置信度要求
    min_confidence = st.slider(
        "最小置信度",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="AI分析结果的最低置信度要求"
    )
    
    # 风险承受度
    risk_tolerance = st.selectbox(
        "风险承受度",
        options=["低风险", "中等风险", "中高风险", "高风险"],
        index=1,
        help="选择可接受的风险水平"
    )
    
    # 结果数量
    limit = st.selectbox(
        "返回数量",
        options=[10, 20, 30, 50],
        index=2,
        help="AI推荐股票数量"
    )
    
    # 保存参数
    st.session_state.ai_enhanced_params = {
        'min_ai_score': min_ai_score,
        'min_confidence': min_confidence,
        'risk_tolerance': risk_tolerance,
        'limit': limit
    }

def render_expert_committee_form():
    """渲染专家委员会表单"""
    st.markdown("#### 💼 专家委员会决策")
    st.info("👥 5名专家分析师：市场、基本面、新闻、社交媒体、热度分析")
    
    # 专家评分要求
    min_expert_score = st.slider(
        "专家委员会最低评分",
        min_value=0,
        max_value=100,
        value=80,
        step=5,
        help="专家委员会综合评分要求"
    )
    
    # 一致性要求
    consensus_level = st.selectbox(
        "一致性要求",
        options=["意见分化", "存在分歧", "基本一致", "高度一致"],
        index=2,
        help="专家意见的一致性要求"
    )
    
    # 结果数量
    limit = st.selectbox(
        "返回数量",
        options=[10, 15, 25, 30],
        index=2,
        help="专家委员会推荐股票数量"
    )
    
    st.session_state.expert_committee_params = {
        'min_expert_score': min_expert_score,
        'consensus_level': consensus_level,
        'limit': limit
    }

def render_adaptive_strategy_form():
    """渲染自适应策略表单"""
    st.markdown("#### 🔄 自适应策略")
    st.info("🌡️ 根据市场环境自动调整：牛市/熊市/震荡/高波动/复苏")
    
    # 策略偏好
    strategy_preference = st.selectbox(
        "策略偏好",
        options=["自动适应", "成长型", "价值型", "动量型", "质量型", "防御型", "进攻型"],
        index=0,
        help="策略类型偏好，选择自动适应将根据市场环境选择最优策略"
    )
    
    # 风险偏好
    risk_preference = st.slider(
        "风险偏好",
        min_value=0.1,
        max_value=1.0,
        value=0.6,
        step=0.1,
        help="0.1=保守，1.0=激进"
    )
    
    # 结果数量
    limit = st.selectbox(
        "返回数量",
        options=[15, 25, 40, 50],
        index=2,
        help="自适应策略推荐股票数量"
    )
    
    st.session_state.adaptive_strategy_params = {
        'strategy_preference': strategy_preference,
        'risk_preference': risk_preference,
        'limit': limit
    }

def render_pattern_based_form():
    """渲染模式识别表单"""
    st.markdown("#### 📈 模式识别选股")
    st.info("🤓 识别12种技术模式：趋势、突破、反转、动量、成交量等")
    
    # 模式类型选择
    pattern_types = st.multiselect(
        "期望模式类型",
        options=["看涨趋势", "向上突破", "看涨反转", "强势动量", "成交量异常", "低波动率"],
        default=["看涨趋势", "向上突破"],
        help="选择希望找到的技术模式"
    )
    
    # 模式评分要求
    min_pattern_score = st.slider(
        "最小模式评分",
        min_value=50,
        max_value=100,
        value=75,
        step=5,
        help="模式识别的最低评分要求"
    )
    
    # 置信度要求
    min_pattern_confidence = st.slider(
        "模式置信度",
        min_value=0.5,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="模式识别的最低置信度"
    )
    
    # 结果数量
    limit = st.selectbox(
        "返回数量",
        options=[15, 25, 35, 50],
        index=2,
        help="模式驱动选股结果数量"
    )
    
    st.session_state.pattern_based_params = {
        'pattern_types': pattern_types,
        'min_pattern_score': min_pattern_score,
        'min_pattern_confidence': min_pattern_confidence,
        'limit': limit
    }

def render_full_ai_form():
    """渲染完整AI表单"""
    st.markdown("#### 🎆 完整AI分析")
    st.warning("⚠️ 完整AI分析需要更长时间，但提供最全面的智能分析")
    
    # 综合评分要求
    min_overall_score = st.slider(
        "AI综合评分",
        min_value=60,
        max_value=100,
        value=85,
        step=5,
        help="完整AI分析的最高评分要求"
    )
    
    # 置信度要求
    min_confidence = st.slider(
        "最高置信度",
        min_value=0.6,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="AI分析的最高置信度要求"
    )
    
    # 风险承受度
    risk_tolerance = st.selectbox(
        "风险承受度",
        options=["低风险", "中等风险", "中高风险"],
        index=1,
        help="完整AI分析的风险承受度"
    )
    
    # 结果数量
    limit = st.selectbox(
        "精选数量",
        options=[5, 10, 15, 20],
        index=3,
        help="完整AI分析的精选股票数量"
    )
    
    st.session_state.full_ai_params = {
        'min_overall_score': min_overall_score,
        'min_confidence': min_confidence,
        'risk_tolerance': risk_tolerance,
        'limit': limit
    }

def execute_stock_selection(selector, mode):
    """执行选股操作"""
    try:
        # 获取市场类型
        market_type = st.session_state.get('market_type', 'A股')
        
        # 创建进度显示容器
        progress_container = st.container()
        with progress_container:
            # 检查是否是AI模式
            is_ai_mode = mode in ["AI增强选股", "专家委员会", "自适应策略", "模式识别", "完整AI分析"]
            
            if is_ai_mode:
                st.info(f"🤖 正在启动{market_type}AI专家系统...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 显示AI分析步骤
                ai_steps = [
                    f"🔍 获取{market_type}股票基础数据",
                    "🤖 启动AI专家委员会",
                    "📊 执行多维度分析",
                    "⚖️ 融合专家意见",
                    "🎯 生成智能推荐"
                ]
                
                for i, step in enumerate(ai_steps):
                    status_text.text(step)
                    progress_bar.progress((i + 1) * 20)
                    import time
                    time.sleep(0.5)  # 模拟分析过程
        
        if mode == "快速选股":
            params = st.session_state.get('quick_params', {})
            result = selector.quick_select(
                min_score=params.get('min_score', 70),
                min_market_cap=params.get('min_market_cap', 50),
                max_pe_ratio=params.get('max_pe_ratio', 30),
                grades=params.get('grades', ['A+', 'A']),
                limit=params.get('limit', 20)
            )
        elif mode == "AI增强选股":
            params = st.session_state.get('ai_enhanced_params', {})
            result = selector.ai_enhanced_select(
                min_ai_score=params.get('min_ai_score', 75),
                min_confidence=params.get('min_confidence', 0.7),
                max_risk_level=params.get('risk_tolerance', '中等风险'),
                limit=params.get('limit', 30)
            )
        elif mode == "专家委员会":
            params = st.session_state.get('expert_committee_params', {})
            result = selector.expert_committee_select(
                min_expert_score=params.get('min_expert_score', 80),
                min_consensus=params.get('consensus_level', '基本一致'),
                limit=params.get('limit', 25)
            )
        elif mode == "自适应策略":
            params = st.session_state.get('adaptive_strategy_params', {})
            result = selector.adaptive_strategy_select(
                limit=params.get('limit', 40)
            )
        elif mode == "模式识别":
            params = st.session_state.get('pattern_based_params', {})
            result = selector.pattern_based_select(
                pattern_types=params.get('pattern_types', []),
                min_pattern_score=params.get('min_pattern_score', 75),
                limit=params.get('limit', 35)
            )
        elif mode == "完整AI分析":
            params = st.session_state.get('full_ai_params', {})
            result = selector.full_ai_select(
                min_overall_score=params.get('min_overall_score', 85),
                min_confidence=params.get('min_confidence', 0.8),
                risk_tolerance=params.get('risk_tolerance', '中等风险'),
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
        
        # 清理进度显示
        if is_ai_mode:
            progress_container.empty()
        
        # 保存结果到session state
        st.session_state.selection_result = result
        st.session_state.selection_mode = mode  # 保存选股模式
        
        # 获取市场类型
        market_type = st.session_state.get('market_type', 'A股')
        
        # 显示成功消息和AI分析摘要
        success_col1, success_col2 = st.columns([2, 1])
        with success_col1:
            st.success(f"✅ {market_type}选股完成! 找到 {len(result.symbols)} 只股票")
            
        with success_col2:
            if is_ai_mode and hasattr(result, 'data') and not result.data.empty:
                # 显示AI分析摘要
                if 'ai_overall_score' in result.data.columns:
                    avg_ai_score = result.data['ai_overall_score'].mean()
                    st.metric("AI平均评分", f"{avg_ai_score:.1f}")
                
        # 显示AI决策过程摘要
        if is_ai_mode and hasattr(result, 'data') and not result.data.empty:
            with st.expander("🤖 AI决策过程详情", expanded=True):
                st.markdown(f"**📋 选股模式**: {mode}")
                st.markdown(f"**🌍 市场类型**: {market_type}")
                st.markdown(f"**🎯 AI参与程度**: 深度智能分析")
                
                # 显示AI引擎状态
                if 'ai_overall_score' in result.data.columns:
                    ai_scores = result.data['ai_overall_score'].dropna()
                    if len(ai_scores) > 0:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("AI平均评分", f"{ai_scores.mean():.1f}")
                        with col2:
                            st.metric("AI最高评分", f"{ai_scores.max():.1f}")
                        with col3:
                            st.metric("AI最低评分", f"{ai_scores.min():.1f}")
                        with col4:
                            high_score_count = len(ai_scores[ai_scores >= 80])
                            st.metric("优质股票", f"{high_score_count}只")
                
                # 显示AI引擎贡献
                engine_contributions = []
                if 'expert_committee_score' in result.data.columns:
                    expert_scores = result.data['expert_committee_score'].dropna()
                    if len(expert_scores) > 0:
                        engine_contributions.append(f"专家委员会: {expert_scores.mean():.1f}")
                
                if 'adaptive_strategy_score' in result.data.columns:
                    adaptive_scores = result.data['adaptive_strategy_score'].dropna()
                    if len(adaptive_scores) > 0:
                        engine_contributions.append(f"自适应策略: {adaptive_scores.mean():.1f}")
                
                if 'pattern_recognition_score' in result.data.columns:
                    pattern_scores = result.data['pattern_recognition_score'].dropna()
                    if len(pattern_scores) > 0:
                        engine_contributions.append(f"模式识别: {pattern_scores.mean():.1f}")
                
                if engine_contributions:
                    st.markdown("**🤖 AI引擎贡献**:")
                    for contribution in engine_contributions:
                        st.write(f"   • {contribution}")
                
                # 显示置信度分析
                if 'ai_confidence' in result.data.columns:
                    confidence_data = result.data['ai_confidence'].dropna()
                    if len(confidence_data) > 0:
                        st.markdown("**📊 AI置信度分析**:")
                        high_conf = len(confidence_data[confidence_data >= 0.8])
                        med_conf = len(confidence_data[(confidence_data >= 0.6) & (confidence_data < 0.8)])
                        low_conf = len(confidence_data[confidence_data < 0.6])
                        avg_conf = confidence_data.mean()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("高置信度", f"{high_conf}只")
                        with col2:
                            st.metric("中置信度", f"{med_conf}只")
                        with col3:
                            st.metric("低置信度", f"{low_conf}只")
                        with col4:
                            st.metric("平均置信度", f"{avg_conf:.2f}")
                
                # 显示推荐分布
                if 'ai_recommendation' in result.data.columns:
                    recommendations = result.data['ai_recommendation'].dropna().value_counts()
                    if len(recommendations) > 0:
                        st.markdown("**💡 AI推荐分布**:")
                        for rec, count in recommendations.head(5).items():
                            st.write(f"   • {rec}: {count}只")
                
                # 显示风险评估
                if 'ai_risk_assessment' in result.data.columns:
                    risk_data = result.data['ai_risk_assessment'].dropna().value_counts()
                    if len(risk_data) > 0:
                        st.markdown("**⚠️ 风险评估分布**:")
                        for risk, count in risk_data.head(5).items():
                            st.write(f"   • {risk}: {count}只")
                
                # 显示市场环境分析
                if 'market_regime' in result.data.columns:
                    regime_data = result.data['market_regime'].dropna().value_counts()
                    if len(regime_data) > 0:
                        st.markdown("**🌡️ 市场环境分析**:")
                        for regime, count in regime_data.items():
                            if regime and regime != '未知':
                                st.write(f"   • {regime}: {count}只")
                
                # 显示模式识别结果
                if 'detected_patterns' in result.data.columns:
                    patterns_data = result.data['detected_patterns'].dropna()
                    if len(patterns_data) > 0:
                        st.markdown("**📈 模式识别结果**:")
                        all_patterns = []
                        for patterns_str in patterns_data:
                            try:
                                if isinstance(patterns_str, str) and patterns_str != '[]':
                                    patterns = patterns_str.replace('[', '').replace(']', '').replace("'", '').split(', ')
                                    all_patterns.extend([p.strip() for p in patterns if p.strip()])
                            except:
                                continue
                        
                        if all_patterns:
                            from collections import Counter
                            pattern_counts = Counter(all_patterns).most_common(5)
                            for pattern, count in pattern_counts:
                                st.write(f"   • {pattern}: {count}次")
        
        logger.info(f"📊 [选股成功] {mode}模式找到 {len(result.symbols)} 只股票")
        
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
        
        # AI增强列优先显示
        if 'ai_overall_score' in display_data.columns:
            display_columns.append('ai_overall_score')
        if 'ai_recommendation' in display_data.columns:
            display_columns.append('ai_recommendation')
        if 'ai_confidence' in display_data.columns:
            display_columns.append('ai_confidence')
        if 'ai_risk_assessment' in display_data.columns:
            display_columns.append('ai_risk_assessment')
            
        # 传统列
        if 'overall_score' in display_data.columns:
            display_columns.append('overall_score')
        if 'grade' in display_data.columns:
            display_columns.append('grade')
        if 'market_cap' in display_data.columns:
            display_columns.append('market_cap')
        if 'pe_ratio' in display_data.columns:
            display_columns.append('pe_ratio')
            
        # 专业列
        if 'expert_committee_score' in display_data.columns:
            display_columns.append('expert_committee_score')
        if 'adaptive_strategy_score' in display_data.columns:
            display_columns.append('adaptive_strategy_score')
        if 'pattern_recognition_score' in display_data.columns:
            display_columns.append('pattern_recognition_score')
        if 'market_regime' in display_data.columns:
            display_columns.append('market_regime')
        
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
    
    # 显示AI洞察面板
    if not result.data.empty:
        display_ai_insights(result.data)
    
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

def display_ai_insights(data: pd.DataFrame):
    """显示AI洞察面板"""
    if data.empty:
        return
        
    # 检查是否有AI相关列
    ai_columns = ['ai_overall_score', 'ai_confidence', 'ai_recommendation', 'ai_risk_assessment',
                 'expert_committee_score', 'adaptive_strategy_score', 'pattern_recognition_score',
                 'market_regime', 'detected_patterns', 'key_factors']
    
    has_ai_data = any(col in data.columns for col in ai_columns)
    
    if not has_ai_data:
        return
    
    with st.expander("🤖 AI分析洞察", expanded=True):
        
        # 显示选股模式和AI参与程度
        selection_mode = st.session_state.get('selection_mode', '未知')
        if selection_mode in ["AI增强选股", "专家委员会", "自适应策略", "模式识别", "完整AI分析"]:
            st.info(f"📋 选股模式: {selection_mode} | 🤖 AI专家系统深度参与")
        else:
            st.info(f"📋 选股模式: {selection_mode} | 📊 传统筛选 + AI智能排序")
        
        # AI评分分布
        if 'ai_overall_score' in data.columns:
            st.markdown("##### 🎯 AI综合评分分析")
            
            col1, col2, col3, col4 = st.columns(4)
            ai_scores = data['ai_overall_score'].dropna()
            
            if not ai_scores.empty:
                with col1:
                    st.metric("AI平均评分", f"{ai_scores.mean():.1f}")
                with col2:
                    st.metric("AI最高评分", f"{ai_scores.max():.1f}")
                with col3:
                    high_score_count = len(ai_scores[ai_scores >= 80])
                    st.metric("优质股票 (≥80)", high_score_count)
                with col4:
                    # 计算智能评分（如果存在）
                    if 'intelligent_score' in data.columns:
                        intelligent_scores = data['intelligent_score'].dropna()
                        if not intelligent_scores.empty:
                            st.metric("智能评分", f"{intelligent_scores.mean():.1f}")
                    else:
                        st.metric("分析完成", f"{len(ai_scores)}只")
                
                # 评分分布图
                score_ranges = {
                    '90-100分 (卓越)': len(ai_scores[ai_scores >= 90]),
                    '80-89分 (优秀)': len(ai_scores[(ai_scores >= 80) & (ai_scores < 90)]),
                    '70-79分 (良好)': len(ai_scores[(ai_scores >= 70) & (ai_scores < 80)]),
                    '60-69分 (一般)': len(ai_scores[(ai_scores >= 60) & (ai_scores < 70)]),
                    '低于60分': len(ai_scores[ai_scores < 60])
                }
                
                # 只显示有数据的范围
                filtered_ranges = {k: v for k, v in score_ranges.items() if v > 0}
                if filtered_ranges:
                    st.markdown("**📊 AI评分分布**")
                    import pandas as pd
                    score_df = pd.DataFrame(list(filtered_ranges.items()), columns=['评分范围', '股票数量'])
                    score_df = score_df.set_index('评分范围')
                    st.bar_chart(score_df)
        
        # 置信度分析
        if 'ai_confidence' in data.columns:
            st.markdown("##### 🎯 AI置信度分布")
            confidence_data = data['ai_confidence'].dropna()
            if not confidence_data.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    high_conf = len(confidence_data[confidence_data >= 0.8])
                    st.metric("高置信度 (≥0.8)", high_conf)
                with col2:
                    med_conf = len(confidence_data[(confidence_data >= 0.6) & (confidence_data < 0.8)])
                    st.metric("中置信度 (0.6-0.8)", med_conf)
                with col3:
                    low_conf = len(confidence_data[confidence_data < 0.6])
                    st.metric("低置信度 (<0.6)", low_conf)
                with col4:
                    avg_conf = confidence_data.mean()
                    st.metric("平均置信度", f"{avg_conf:.2f}")
        
        # AI推荐分布
        if 'ai_recommendation' in data.columns:
            st.markdown("##### 📊 AI推荐分布")
            recommendations = data['ai_recommendation'].dropna().value_counts()
            if not recommendations.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    for rec, count in recommendations.head(3).items():
                        st.metric(f"🔸 {rec}", count)
                
                with col2:
                    # 简单的柱状图
                    st.bar_chart(recommendations.head(5))
        
        # 风险评估分布
        if 'ai_risk_assessment' in data.columns:
            st.markdown("##### ⚠️ 风险评估分布")
            risk_data = data['ai_risk_assessment'].dropna().value_counts()
            if not risk_data.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    low_risk = risk_data.get('低风险', 0)
                    st.metric("�︢ 低风险", low_risk)
                with col2:
                    med_risk = risk_data.get('中等风险', 0) + risk_data.get('中高风险', 0)
                    st.metric("😐 中等风险", med_risk)
                with col3:
                    high_risk = risk_data.get('高风险', 0)
                    st.metric("😱 高风险", high_risk)
        
        # 市场环境分析
        if 'market_regime' in data.columns:
            st.markdown("##### 🌡️ 市场环境分析")
            regime_data = data['market_regime'].dropna().value_counts()
            if not regime_data.empty:
                st.write("当前识别到的市场环境:")
                for regime, count in regime_data.items():
                    if regime and regime != '未知':
                        st.info(f"📈 {regime}: {count} 只股票")
        
        # 模式识别结果
        if 'detected_patterns' in data.columns:
            st.markdown("##### 📈 模式识别结果")
            patterns_data = data['detected_patterns'].dropna()
            if not patterns_data.empty:
                all_patterns = []
                for patterns_str in patterns_data:
                    try:
                        if isinstance(patterns_str, str) and patterns_str != '[]':
                            # 简单解析列表字符串
                            patterns = patterns_str.replace('[', '').replace(']', '').replace('\'', '').split(', ')
                            all_patterns.extend([p.strip() for p in patterns if p.strip()])
                    except:
                        continue
                
                if all_patterns:
                    pattern_counts = pd.Series(all_patterns).value_counts().head(5)
                    for pattern, count in pattern_counts.items():
                        st.write(f"• {pattern}: {count} 次")
        
        # AI引擎性能对比
        if any(col in data.columns for col in ['expert_committee_score', 'adaptive_strategy_score', 'pattern_recognition_score']):
            st.markdown("##### 🚀 AI引擎性能对比")
            
            performance_data = {}
            if 'expert_committee_score' in data.columns:
                expert_scores = data['expert_committee_score'].dropna()
                if not expert_scores.empty:
                    performance_data['专家委员会'] = expert_scores.mean()
            
            if 'adaptive_strategy_score' in data.columns:
                adaptive_scores = data['adaptive_strategy_score'].dropna()
                if not adaptive_scores.empty:
                    performance_data['自适应策略'] = adaptive_scores.mean()
            
            if 'pattern_recognition_score' in data.columns:
                pattern_scores = data['pattern_recognition_score'].dropna()
                if not pattern_scores.empty:
                    performance_data['模式识别'] = pattern_scores.mean()
            
            if performance_data:
                # 显示性能对比
                performance_df = pd.DataFrame(list(performance_data.items()), 
                                            columns=['引擎', '平均评分'])
                performance_df = performance_df.set_index('引擎')
                st.bar_chart(performance_df)
        
        # 关键因子分析
        if 'key_factors' in data.columns:
            st.markdown("##### 🔑 关键因子分析")
            factors_data = data['key_factors'].dropna()
            if not factors_data.empty:
                all_factors = []
                for factors_str in factors_data:
                    try:
                        if isinstance(factors_str, str) and factors_str != '[]':
                            # 简单解析列表字符串
                            factors = factors_str.replace('[', '').replace(']', '').replace('\'', '').split(', ')
                            all_factors.extend([f.strip() for f in factors if f.strip()])
                    except:
                        continue
                
                if all_factors:
                    factor_counts = pd.Series(all_factors).value_counts().head(8)
                    cols = st.columns(2)
                    for i, (factor, count) in enumerate(factor_counts.items()):
                        with cols[i % 2]:
                            st.write(f"• {factor}: {count} 次")

def run_ai_system_check():
    """运行AI系统检查"""
    try:
        with st.spinner("🔍 正在检查AI系统状态..."):
            from tradingagents.selectors.ai_debug_tools import get_ai_debug_tools
            debug_tools = get_ai_debug_tools()
            check_result = debug_tools.run_full_system_check()
        
        overall_status = check_result.get('overall_status', 'unknown')
        
        # 显示检查结果
        if overall_status == 'fully_operational':
            st.success("✅ AI系统运行状态：完全正常")
        elif overall_status == 'partially_operational':
            st.warning("⚡ AI系统运行状态：部分可用")
        elif overall_status == 'limited_functionality':
            st.warning("🔧 AI系统运行状态：功能受限")
        elif overall_status == 'basic_mode':
            st.info("📊 AI系统运行状态：基础模式")
        else:
            st.error("❌ AI系统运行状态：存在问题")
        
        # 显示详细报告
        with st.expander("📋 详细检查报告", expanded=False):
            report = debug_tools.get_debug_report()
            st.text(report)
        
        # 显示建议
        recommendations = check_result.get('recommendations', [])
        if recommendations:
            st.markdown("**💡 系统建议:**")
            for rec in recommendations:
                st.write(f"• {rec}")
                
    except Exception as e:
        st.error(f"❌ 系统检查失败: {e}")

def clear_ai_caches():
    """清理AI缓存"""
    try:
        with st.spinner("🧹 正在清理AI缓存..."):
            from tradingagents.selectors.ai_debug_tools import get_ai_debug_tools
            debug_tools = get_ai_debug_tools()
            result = debug_tools.clear_ai_caches()
        
        cleared_caches = result.get('cleared_caches', [])
        if cleared_caches:
            st.success(f"✅ 缓存清理完成: {', '.join(cleared_caches)}")
        else:
            st.warning("⚠️ 没有发现可清理的缓存")
            
    except Exception as e:
        st.error(f"❌ 缓存清理失败: {e}")

def render_ai_model_selector(selector):
    """渲染AI模型选择器 - 复用股票分析的侧边栏配置"""
    try:
        st.markdown("**🧠 AI模型配置**")
        st.info("💡 **提示**: 智能选股使用与股票分析相同的AI模型配置，请在左侧侧边栏中选择AI模型")
        
        # 从session state获取当前配置
        llm_provider = st.session_state.get('llm_provider')
        llm_model = st.session_state.get('llm_model')
        
        if llm_provider and llm_model:
            st.markdown("**🎯 当前AI模型:**")
            col1, col2 = st.columns(2)
            with col1:
                # 显示侧边栏配置的模型信息
                provider_display = {
                    'dashscope': '🇨🇳 阿里云DashScope',
                    'deepseek': '🚀 DeepSeek V3',
                    'kimi': '🌙 月之暗面Kimi',
                    'google': '🌟 Google AI',
                    'openrouter': '🌐 OpenRouter',
                    'glm': '🧠 智谱GLM'
                }.get(llm_provider, llm_provider.upper())
                
                st.success(f"**{llm_model}**")
                st.caption(f"供应商: {provider_display}")
            with col2:
                # 显示配置状态
                try:
                    # 验证模型是否正确配置
                    current_model_info = selector.get_current_ai_model_info()
                    if current_model_info:
                        st.metric("状态", "✅ 已配置")
                        if 'temperature' in current_model_info:
                            st.metric("温度参数", f"{current_model_info.get('temperature', 0.7):.1f}")
                    else:
                        st.metric("状态", "⚠️ 待同步")
                except:
                    st.metric("状态", "🔄 加载中")
        else:
            st.warning("⚠️ 未检测到当前AI模型，请在左侧侧边栏配置")
            st.markdown("**请按以下步骤配置AI模型：**")
            st.markdown("1. 在左侧侧边栏找到 **🧠 AI模型配置**")
            st.markdown("2. 选择 **LLM提供商** (如：🇨🇳 阿里百炼)")
            st.markdown("3. 选择 **模型版本** (如：Plus - 平衡)")
            st.markdown("4. 配置完成后，智能选股将自动使用该模型")
        
        # 获取可用模型统计
        available_models = selector.get_available_ai_models()
        if available_models:
            # 按供应商分组统计
            providers = {}
            for model_key, model_info in available_models.items():
                provider = model_info.get('provider', 'unknown')
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append((model_key, model_info))
            
            # 显示统计信息
            with st.expander("📊 可用模型概览", expanded=False):
                st.write(f"**总计**: {len(available_models)} 个模型，来自 {len(providers)} 个供应商")
                
                provider_names = {
                    'openai': '🌐 OpenAI',
                    'dashscope': '🇨🇳 阿里云DashScope', 
                    'deepseek': '🚀 DeepSeek',
                    'google': '🔍 Google AI',
                    'anthropic': '🧠 Anthropic',
                    'openrouter': '🌍 OpenRouter',
                    'kimi': '🌙 月之暗面Kimi'
                }
                
                for provider, models in providers.items():
                    provider_display = provider_names.get(provider, provider.title())
                    enabled_count = sum(1 for _, info in models if info.get('enabled') and info.get('has_api_key'))
                    total_count = len(models)
                    
                    if enabled_count > 0:
                        st.success(f"✅ **{provider_display}**: {enabled_count}/{total_count} 个模型可用")
                    else:
                        st.error(f"❌ **{provider_display}**: 需要配置API密钥")
        
        st.markdown("---")
        st.markdown("**📝 说明**:")
        st.markdown("- 智能选股的所有AI模式将使用您在侧边栏中选择的AI模型")
        st.markdown("- 包括：AI增强选股、专家委员会选股、自适应策略选股等")
        st.markdown("- 如需更换模型，请在左侧侧边栏的 **🧠 AI模型配置** 中选择")
    
    except Exception as e:
        st.error(f"❌ AI模型选择器加载失败: {e}")
        st.markdown("请检查系统配置或联系管理员")

def get_api_key_name(provider: str) -> str:
    """获取API密钥环境变量名"""
    key_map = {
        'openai': 'OPENAI_API_KEY',
        'dashscope': 'DASHSCOPE_API_KEY', 
        'deepseek': 'DEEPSEEK_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY',
        'kimi': 'KIMI_API_KEY'
    }
    return key_map.get(provider.lower(), f'{provider.upper()}_API_KEY')

def switch_ai_model(selector, model_key: str, model_info: Dict[str, Any]):
    """切换AI模型"""
    try:
        with st.spinner(f"🔄 正在切换到 {model_info.get('display_name', model_key)}..."):
            success = selector.switch_ai_model(model_key)
        
        if success:
            st.success(f"✅ 成功切换到: {model_info.get('display_name', model_key)}")
            st.info("💡 AI模型已更新，新的选股分析将使用此模型")
            
            # 记录到session state以便后续使用
            st.session_state.current_ai_model = model_key
            
            # 建议用户清理缓存
            if st.button("🧹 清理AI缓存", help="清理旧模型的分析缓存"):
                clear_ai_caches()
            
        else:
            st.error(f"❌ 模型切换失败: {model_key}")
            
    except Exception as e:
        st.error(f"❌ 模型切换异常: {e}")
        logger.error(f"模型切换失败: {e}")

def test_ai_model(selector, model_key: str):
    """测试AI模型连接"""
    try:
        with st.spinner("🧪 正在测试模型连接..."):
            # 尝试通过选股器测试模型
            available_models = selector.get_available_ai_models()
            model_info = available_models.get(model_key, {})
            
            if not model_info.get('has_api_key'):
                st.error("❌ 模型测试失败: API密钥未配置")
                return
            
            # 简单的连接测试
            try:
                from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
                llm_manager = get_llm_manager()
                test_result = llm_manager.test_model(model_key)
                
                if test_result.get('success'):
                    st.success("✅ 模型连接测试成功")
                    
                    # 显示测试详情
                    with st.expander("📋 测试详情", expanded=False):
                        st.write(f"**模型**: {test_result.get('model', 'N/A')}")
                        st.write(f"**提供商**: {test_result.get('provider', 'N/A')}")
                        
                        response = test_result.get('response', '')
                        if response:
                            st.write(f"**测试响应**: {response[:200]}...")
                else:
                    st.error(f"❌ 模型连接测试失败: {test_result.get('error', '未知错误')}")
                    
            except Exception as e:
                st.error(f"❌ 模型测试异常: {e}")
                
    except Exception as e:
        st.error(f"❌ 测试过程失败: {e}")
        logger.error(f"模型测试失败: {e}")

if __name__ == "__main__":
    render_stock_selector_page()