"""
热度分析Web界面组件
集成免费热度分析到Streamlit Web界面
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# 导入热度分析模块
from tradingagents.analytics import HeatAnalyzer, SocialMediaAPI, VolumeAnomalyDetector, SentimentAnalyzer
from tradingagents.analytics.integration import HeatAnalysisIntegration

class HeatAnalysisUI:
    """热度分析Web界面类"""
    
    def __init__(self):
        self.heat_integration = HeatAnalysisIntegration()
        self.heat_analyzer = HeatAnalyzer()
        self.social_api = SocialMediaAPI()
        self.volume_detector = VolumeAnomalyDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def render_heat_analysis_page(self):
        """渲染热度分析主页面"""
        st.title("🔥 股票热度分析")
        st.markdown("---")
        
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 综合热度分析", 
            "📱 社交媒体热度", 
            "📊 成交量异动", 
            "😊 情绪分析"
        ])
        
        # 侧边栏配置
        with st.sidebar:
            st.header("⚙️ 分析配置")
            
            # 股票代码输入
            symbol = st.text_input("股票代码", placeholder="如: 000001, 600519")
            
            # 市场类型选择
            market_type = st.selectbox("市场类型", ["A股", "美股", "港股"])
            
            # 分析天数
            days = st.slider("分析天数", min_value=1, max_value=30, value=7)
            
            # 开始分析按钮
            analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
        
        if analyze_button and symbol:
            self._run_heat_analysis(symbol, market_type, days, tab1, tab2, tab3, tab4)
        elif analyze_button:
            st.error("请输入股票代码")
        else:
            self._show_welcome_guide()
    
    def _run_heat_analysis(self, symbol: str, market_type: str, days: int, *tabs):
        """运行热度分析并显示结果"""
        with st.spinner(f"正在分析 {symbol} 的热度数据..."):
            try:
                # 运行综合热度分析
                heat_result = self.heat_integration.analyze_with_heat(symbol)
                
                # 分别获取各模块数据
                social_result = self.social_api.get_social_heat(symbol)
                volume_result = self.volume_detector.detect_anomaly(symbol, days)
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(symbol)
                
                # 在对应标签页显示结果
                with tabs[0]:
                    self._display_comprehensive_heat(heat_result)
                
                with tabs[1]:
                    self._display_social_heat(social_result)
                
                with tabs[2]:
                    self._display_volume_anomaly(volume_result)
                
                with tabs[3]:
                    self._display_sentiment_analysis(sentiment_result)
                    
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
    
    def _display_comprehensive_heat(self, result: Dict):
        """显示综合热度分析"""
        st.header("📊 综合热度分析")
        
        heat_score = result.get('heat_score', 0)
        heat_level = result.get('heat_level', '未知')
        
        # 创建热力指标卡片
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("热度分数", f"{heat_score:.1f}/100", 
                     delta=f"{heat_score - 50:.1f}" if heat_score > 50 else None)
        
        with col2:
            st.metric("热度等级", heat_level)
        
        with col3:
            risk_level = result.get('risk_assessment', {}).get('risk_level', '未知')
            st.metric("风险等级", risk_level.upper())
        
        # 热度趋势图
        st.subheader("📈 热度趋势")
        trend_data = result.get('heat_analysis', {}).get('trend', {})
        if trend_data:
            self._create_trend_chart(trend_data)
        
        # 预警信息
        alerts = result.get('alerts', [])
        if alerts:
            st.subheader("⚠️ 预警信息")
            for alert in alerts:
                level = alert.get('level', 'info')
                message = alert.get('message', '')
                
                if level == 'high':
                    st.error(f"🔴 {message}")
                elif level == 'medium':
                    st.warning(f"🟡 {message}")
                else:
                    st.info(f"🔵 {message}")
        
        # 操作建议
        recommendations = result.get('action_recommendations', [])
        if recommendations:
            st.subheader("💡 操作建议")
            for rec in recommendations:
                st.info(rec)
    
    def _display_social_heat(self, result: Dict):
        """显示社交媒体热度"""
        st.header("📱 社交媒体热度")
        
        score = result.get('score', 0)
        platforms = result.get('platforms', {})
        
        # 平台热度对比
        platform_data = []
        for platform, data in platforms.items():
            if isinstance(data, dict) and 'score' in data:
                platform_data.append({
                    '平台': platform,
                    '热度': data.get('score', 0)
                })
        
        if platform_data:
            df = pd.DataFrame(platform_data)
            fig = px.bar(df, x='平台', y='热度', title='各平台热度对比')
            st.plotly_chart(fig, use_container_width=True)
        
        # 趋势分析
        trend = result.get('trend', {})
        if trend:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("24小时变化", f"{trend.get('change_24h', 0):.1f}%")
            with col2:
                st.metric("趋势方向", trend.get('direction', '稳定'))
    
    def _display_volume_anomaly(self, result: Dict):
        """显示成交量异动分析"""
        st.header("📊 成交量异动分析")
        
        score = result.get('anomaly_score', 0)
        level = result.get('anomaly_level', '正常')
        
        # 异动评分
        st.metric("异动评分", f"{score:.1f}/100", level)
        
        # 成交量分析
        volume_analysis = result.get('volume_analysis', {})
        if volume_analysis:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ratio = volume_analysis.get('volume_ratio_5', 0)
                st.metric("成交量比率", f"{ratio:.1f}x")
            
            with col2:
                trend = volume_analysis.get('trend_direction', '未知')
                st.metric("趋势方向", trend)
            
            with col3:
                strength = volume_analysis.get('trend_strength', 0)
                st.metric("趋势强度", f"{strength:.2f}")
        
        # 资金流向
        money_flow = result.get('money_flow', {})
        if money_flow:
            st.subheader("💰 资金流向")
            
            main_inflow = money_flow.get('main_net_inflow', 0)
            retail_inflow = money_flow.get('small_net_inflow', 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("主力净流入", f"{main_inflow:,.0f}万")
            with col2:
                st.metric("散户净流入", f"{retail_inflow:,.0f}万")
            
            # 散户-机构博弈
            if money_flow.get('is_divergence', False):
                st.warning("⚠️ 检测到散户-机构资金流向背离")
    
    def _display_sentiment_analysis(self, result: Dict):
        """显示情绪分析"""
        st.header("😊 市场情绪分析")
        
        overall = result.get('overall_sentiment', {})
        sentiment_score = overall.get('sentiment_score', 0)
        sentiment_label = overall.get('sentiment_label', '未知')
        
        # 综合情绪指标
        col1, col2 = st.columns(2)
        with col1:
            st.metric("情绪得分", f"{sentiment_score:.1f}")
        with col2:
            st.metric("情绪状态", sentiment_label)
        
        # 各平台情绪分布
        platforms = ['social_sentiment', 'news_sentiment', 'forum_sentiment']
        sentiments = []
        
        for platform in platforms:
            data = result.get(platform, {})
            if data:
                sentiments.append({
                    '平台': platform.replace('_sentiment', '').title(),
                    '情绪得分': data.get('sentiment_score', 0),
                    '正面比例': data.get('positive_ratio', 0),
                    '负面比例': data.get('negative_ratio', 0)
                })
        
        if sentiments:
            df = pd.DataFrame(sentiments)
            fig = px.bar(df, x='平台', y=['正面比例', '负面比例'], 
                        title='各平台情绪分布', barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        
        # 散户-机构博弈
        battle = result.get('retail_institutional', {})
        if battle:
            st.subheader("⚔️ 散户-机构博弈")
            
            battle_score = battle.get('battle_score', 0)
            battle_direction = battle.get('battle_direction', '未知')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("博弈得分", f"{battle_score:.1f}")
            with col2:
                st.metric("博弈状态", battle_direction)
            
            # 资金对比图
            main_flow = battle.get('main_inflow', 0)
            retail_flow = battle.get('retail_inflow', 0)
            
            flow_data = pd.DataFrame({
                '类型': ['主力', '散户'],
                '资金流入': [main_flow, retail_flow]
            })
            
            fig = px.bar(flow_data, x='类型', y='资金流入', 
                        title='资金流向对比', color='类型')
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_trend_chart(self, trend_data: Dict):
        """创建趋势图表"""
        # 模拟趋势数据
        dates = [datetime.now() - timedelta(days=i) for i in range(7)]
        values = [50 + i*5 + (i%3)*10 for i in range(7)]
        
        df = pd.DataFrame({
            '日期': dates,
            '热度值': values
        })
        
        fig = px.line(df, x='日期', y='热度值', title='7天热度趋势')
        st.plotly_chart(fig, use_container_width=True)
    
    def render_heat_ranking(self, symbols: List[str]):
        """渲染热度排行榜"""
        st.header("🏆 热度排行榜")
        
        if st.button("刷新排行榜"):
            with st.spinner("正在计算热度排名..."):
                try:
                    rankings = self.heat_analyzer.get_heat_ranking(symbols, limit=10)
                    
                    if rankings:
                        # 创建DataFrame
                        df = pd.DataFrame([
                            {
                                '股票代码': r['symbol'],
                                '热度分数': r.get('heat_score', 0),
                                '热度等级': r.get('heat_analysis', {}).get('heat_level', '未知')
                            }
                            for r in rankings
                        ])
                        
                        # 显示排行榜
                        st.dataframe(df, use_container_width=True)
                        
                        # 可视化
                        fig = px.bar(df, x='股票代码', y='热度分数', 
                                    title='股票热度排行榜', color='热度等级')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无数据")
                        
                except Exception as e:
                    st.error(f"获取排行榜失败: {str(e)}")
    
    def _show_welcome_guide(self):
        """显示欢迎指南"""
        st.markdown("""
        ## 🎯 欢迎使用股票热度分析系统
        
        ### 🔥 功能介绍
        
        **综合热度分析**: 整合社交媒体、成交量、情绪等多维度数据
        
        **社交媒体热度**: 微博、雪球、股吧等平台讨论热度
        
        **成交量异动**: 成交量、换手率、资金流向异常检测
        
        **情绪分析**: 市场情绪、散户机构博弈分析
        
        ### 📊 使用步骤
        
        1. 在左侧输入股票代码（如：000001）
        2. 选择市场类型（A股/美股/港股）
        3. 设置分析天数（1-30天）
        4. 点击"开始分析"按钮
        5. 查看各维度分析结果
        
        ### 💡 提示
        
        - **A股**: 使用6位数字代码（如：000001, 600519）
        - **美股**: 使用股票代码（如：AAPL, TSLA）
        - **港股**: 使用5位数字代码（如：00700, 09988）
        
        **系统基于免费API构建，无需额外费用**
        """)

# 创建全局实例
heat_ui = HeatAnalysisUI()

def render_heat_analysis():
    """主函数，供Web界面调用"""
    heat_ui.render_heat_analysis_page()

if __name__ == "__main__":
    render_heat_analysis()