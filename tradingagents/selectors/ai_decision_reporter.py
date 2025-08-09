#!/usr/bin/env python3
"""
AI决策报告生成器
生成详细的AI选股决策过程报告
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('ai_reports')

class AIDecisionReporter:
    """AI决策报告生成器"""
    
    def __init__(self):
        self.report_data = {}
        
    def generate_stock_analysis_report(self, symbol: str, ai_result: Dict[str, Any], 
                                      stock_data: Dict[str, Any] = None) -> str:
        """生成单只股票的AI分析报告"""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"🤖 AI选股决策报告 - {symbol}")
        report_lines.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        # 基础信息
        report_lines.append("\n📊 基础分析信息")
        report_lines.append("-" * 40)
        report_lines.append(f"股票代码: {symbol}")
        report_lines.append(f"AI综合评分: {ai_result.get('overall_score', 0):.1f}")
        report_lines.append(f"投资建议: {ai_result.get('recommendation', '未知')}")
        report_lines.append(f"风险评估: {ai_result.get('risk_assessment', '未评估')}")
        report_lines.append(f"置信度: {ai_result.get('confidence_level', 0):.2f}")
        report_lines.append(f"分析耗时: {ai_result.get('processing_time', 0):.2f}秒")
        
        # AI引擎贡献
        report_lines.append("\n🤖 AI引擎分析贡献")
        report_lines.append("-" * 40)
        
        if ai_result.get('expert_committee_score') is not None:
            report_lines.append(f"专家委员会评分: {ai_result['expert_committee_score']:.1f}")
        
        if ai_result.get('adaptive_strategy_score') is not None:
            report_lines.append(f"自适应策略评分: {ai_result['adaptive_strategy_score']:.1f}")
            report_lines.append(f"市场环境识别: {ai_result.get('market_regime', '未知')}")
        
        if ai_result.get('pattern_recognition_score') is not None:
            report_lines.append(f"模式识别评分: {ai_result['pattern_recognition_score']:.1f}")
        
        # 专家委员会详情
        if ai_result.get('expert_analysis'):
            report_lines.append("\n👥 专家委员会决策详情")
            report_lines.append("-" * 40)
            
            expert_analysis = ai_result['expert_analysis']
            committee_decision = expert_analysis.get('committee_decision', {})
            
            report_lines.append(f"委员会综合评分: {committee_decision.get('score', 0):.1f}")
            report_lines.append(f"专家一致性: {committee_decision.get('consensus_level', '未知')}")
            report_lines.append(f"决策置信度: {committee_decision.get('confidence', 0):.2f}")
            
            # 各专家意见
            expert_opinions = expert_analysis.get('expert_opinions', {})
            if expert_opinions:
                report_lines.append("\n👨‍💼 各专家详细意见:")
                for expert_name, opinion in expert_opinions.items():
                    score = opinion.get('score', 0)
                    recommendation = opinion.get('recommendation', '观望')
                    confidence = opinion.get('confidence', 0)
                    reasoning = opinion.get('reasoning', '')
                    
                    report_lines.append(f"\n  📝 {expert_name}:")
                    report_lines.append(f"     评分: {score:.1f}")
                    report_lines.append(f"     建议: {recommendation}")
                    report_lines.append(f"     置信度: {confidence:.2f}")
                    if reasoning:
                        report_lines.append(f"     分析理由: {reasoning[:100]}...")
            
            # 决策因素
            decision_factors = committee_decision.get('decision_factors', [])
            if decision_factors:
                report_lines.append(f"\n🔑 关键决策因素:")
                for factor in decision_factors[:5]:
                    report_lines.append(f"   • {factor}")
        
        # 关键因素分析
        if ai_result.get('key_factors'):
            report_lines.append("\n🎯 关键决策因素")
            report_lines.append("-" * 40)
            for factor in ai_result['key_factors'][:5]:
                report_lines.append(f"   • {factor}")
        
        # 风险因素
        if ai_result.get('risk_factors'):
            report_lines.append("\n⚠️ 风险因素分析")
            report_lines.append("-" * 40)
            for risk in ai_result['risk_factors'][:5]:
                report_lines.append(f"   • {risk}")
        
        # 机会因素
        if ai_result.get('opportunity_factors'):
            report_lines.append("\n🌟 机会因素分析")
            report_lines.append("-" * 40)
            for opportunity in ai_result['opportunity_factors'][:5]:
                report_lines.append(f"   • {opportunity}")
        
        # 模式识别结果
        if ai_result.get('detected_patterns'):
            report_lines.append("\n📈 技术模式识别")
            report_lines.append("-" * 40)
            patterns = ai_result['detected_patterns']
            if isinstance(patterns, str):
                try:
                    # 尝试解析字符串格式的列表
                    patterns = patterns.replace('[', '').replace(']', '').replace("'", '').split(', ')
                    patterns = [p.strip() for p in patterns if p.strip()]
                except:
                    patterns = [patterns]
            
            for pattern in patterns[:5]:
                report_lines.append(f"   • {pattern}")
        
        # 投资建议详解
        report_lines.append("\n💡 投资建议详解")
        report_lines.append("-" * 40)
        report_lines.append(f"总体建议: {ai_result.get('recommendation', '未知')}")
        report_lines.append(f"风险等级: {ai_result.get('risk_assessment', '未评估')}")
        report_lines.append(f"建议置信度: {ai_result.get('confidence_level', 0):.2f}")
        
        # 基于评分的建议解释
        score = ai_result.get('overall_score', 0)
        confidence = ai_result.get('confidence_level', 0)
        
        if score >= 80 and confidence >= 0.8:
            report_lines.append("✅ 该股票获得AI系统高度评价，建议重点关注")
        elif score >= 70 and confidence >= 0.6:
            report_lines.append("🟡 该股票获得AI系统较好评价，可适当关注")
        elif score >= 60:
            report_lines.append("⚪ 该股票AI评价一般，建议谨慎观察")
        else:
            report_lines.append("🔴 该股票AI评价较低，建议回避或谨慎对待")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("🤖 报告生成完成 - AI选股系统")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def generate_batch_analysis_report(self, results: List[Dict[str, Any]], 
                                     mode: str = "AI增强选股") -> str:
        """生成批量分析的AI决策报告"""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"🤖 批量AI选股决策报告")
        report_lines.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"📋 选股模式: {mode}")
        report_lines.append(f"📊 分析股票数量: {len(results)}")
        report_lines.append("=" * 80)
        
        # 统计分析
        valid_results = [r for r in results if r.get('overall_score', 0) > 0]
        
        if valid_results:
            scores = [r.get('overall_score', 0) for r in valid_results]
            confidences = [r.get('confidence_level', 0) for r in valid_results]
            
            report_lines.append("\n📊 AI分析统计摘要")
            report_lines.append("-" * 40)
            report_lines.append(f"成功分析股票数: {len(valid_results)}")
            report_lines.append(f"AI平均评分: {sum(scores) / len(scores):.1f}")
            report_lines.append(f"AI最高评分: {max(scores):.1f}")
            report_lines.append(f"AI最低评分: {min(scores):.1f}")
            report_lines.append(f"平均置信度: {sum(confidences) / len(confidences):.2f}")
            
            # 评分分布
            high_score_count = len([s for s in scores if s >= 80])
            medium_score_count = len([s for s in scores if 60 <= s < 80])
            low_score_count = len([s for s in scores if s < 60])
            
            report_lines.append(f"\n📈 AI评分分布:")
            report_lines.append(f"   优秀(≥80分): {high_score_count}只 ({high_score_count/len(scores)*100:.1f}%)")
            report_lines.append(f"   良好(60-79分): {medium_score_count}只 ({medium_score_count/len(scores)*100:.1f}%)")
            report_lines.append(f"   一般(<60分): {low_score_count}只 ({low_score_count/len(scores)*100:.1f}%)")
            
            # 推荐分布
            recommendations = {}
            for result in valid_results:
                rec = result.get('recommendation', '未知')
                recommendations[rec] = recommendations.get(rec, 0) + 1
            
            if recommendations:
                report_lines.append(f"\n💡 AI推荐分布:")
                for rec, count in sorted(recommendations.items(), key=lambda x: x[1], reverse=True):
                    report_lines.append(f"   {rec}: {count}只 ({count/len(scores)*100:.1f}%)")
            
            # 风险分布
            risk_assessments = {}
            for result in valid_results:
                risk = result.get('risk_assessment', '未评估')
                risk_assessments[risk] = risk_assessments.get(risk, 0) + 1
            
            if risk_assessments:
                report_lines.append(f"\n⚠️ 风险评估分布:")
                for risk, count in sorted(risk_assessments.items(), key=lambda x: x[1], reverse=True):
                    report_lines.append(f"   {risk}: {count}只 ({count/len(scores)*100:.1f}%)")
        
        # AI引擎贡献统计
        report_lines.append("\n🤖 AI引擎贡献统计")
        report_lines.append("-" * 40)
        
        expert_scores = [r.get('expert_committee_score') for r in valid_results if r.get('expert_committee_score') is not None]
        adaptive_scores = [r.get('adaptive_strategy_score') for r in valid_results if r.get('adaptive_strategy_score') is not None]
        pattern_scores = [r.get('pattern_recognition_score') for r in valid_results if r.get('pattern_recognition_score') is not None]
        
        if expert_scores:
            report_lines.append(f"专家委员会: 平均{sum(expert_scores)/len(expert_scores):.1f}分 (参与{len(expert_scores)}只)")
        if adaptive_scores:
            report_lines.append(f"自适应策略: 平均{sum(adaptive_scores)/len(adaptive_scores):.1f}分 (参与{len(adaptive_scores)}只)")
        if pattern_scores:
            report_lines.append(f"模式识别: 平均{sum(pattern_scores)/len(pattern_scores):.1f}分 (参与{len(pattern_scores)}只)")
        
        # 排名前10的股票
        if valid_results:
            report_lines.append("\n🏆 AI评分排名前10的股票")
            report_lines.append("-" * 40)
            
            sorted_results = sorted(valid_results, key=lambda x: x.get('overall_score', 0), reverse=True)[:10]
            
            for i, result in enumerate(sorted_results, 1):
                symbol = result.get('symbol', '未知')
                score = result.get('overall_score', 0)
                recommendation = result.get('recommendation', '未知')
                confidence = result.get('confidence_level', 0)
                
                report_lines.append(f"{i:2d}. {symbol:8s} - {score:5.1f}分 - {recommendation} (置信度: {confidence:.2f})")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("🤖 批量分析报告生成完成")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report_to_file(self, report_content: str, filename: str = None) -> str:
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ai_decision_report_{timestamp}.txt"
        
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        report_path = report_dir / filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"AI决策报告已保存到: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"保存AI决策报告失败: {e}")
            return None
    
    def generate_html_report(self, results: List[Dict[str, Any]], mode: str = "AI增强选股") -> str:
        """生成HTML格式的AI决策报告"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI选股决策报告</title>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
                .stock-item {{ padding: 10px; margin: 5px 0; background: #fff; border-left: 4px solid #007bff; }}
                .high-score {{ border-left-color: #28a745; }}
                .medium-score {{ border-left-color: #ffc107; }}
                .low-score {{ border-left-color: #dc3545; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI选股决策报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>选股模式: {mode} | 分析股票数量: {len(results)}</p>
            </div>
        """
        
        if results:
            valid_results = [r for r in results if r.get('overall_score', 0) > 0]
            
            if valid_results:
                scores = [r.get('overall_score', 0) for r in valid_results]
                
                html_content += f"""
                <div class="section">
                    <h2>📊 AI分析统计</h2>
                    <div class="metric">平均评分: {sum(scores)/len(scores):.1f}</div>
                    <div class="metric">最高评分: {max(scores):.1f}</div>
                    <div class="metric">最低评分: {min(scores):.1f}</div>
                    <div class="metric">分析股票数: {len(valid_results)}</div>
                </div>
                """
                
                html_content += """
                <div class="section">
                    <h2>🏆 AI评分排名</h2>
                    <table>
                        <tr><th>排名</th><th>股票代码</th><th>AI评分</th><th>投资建议</th><th>置信度</th><th>风险评估</th></tr>
                """
                
                sorted_results = sorted(valid_results, key=lambda x: x.get('overall_score', 0), reverse=True)[:20]
                
                for i, result in enumerate(sorted_results, 1):
                    symbol = result.get('symbol', '未知')
                    score = result.get('overall_score', 0)
                    recommendation = result.get('recommendation', '未知')
                    confidence = result.get('confidence_level', 0)
                    risk = result.get('risk_assessment', '未评估')
                    
                    score_class = 'high-score' if score >= 80 else 'medium-score' if score >= 60 else 'low-score'
                    
                    html_content += f"""
                    <tr class="stock-item {score_class}">
                        <td>{i}</td>
                        <td>{symbol}</td>
                        <td>{score:.1f}</td>
                        <td>{recommendation}</td>
                        <td>{confidence:.2f}</td>
                        <td>{risk}</td>
                    </tr>
                    """
                
                html_content += """
                    </table>
                </div>
                """
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content


# 全局报告生成器实例
_ai_reporter = None

def get_ai_reporter() -> AIDecisionReporter:
    """获取全局AI报告生成器实例"""
    global _ai_reporter
    if _ai_reporter is None:
        _ai_reporter = AIDecisionReporter()
    return _ai_reporter

def generate_ai_decision_report(symbol: str, ai_result: Dict[str, Any], 
                               stock_data: Dict[str, Any] = None) -> str:
    """生成AI决策报告的便捷函数"""
    reporter = get_ai_reporter()
    return reporter.generate_stock_analysis_report(symbol, ai_result, stock_data)

def generate_batch_ai_report(results: List[Dict[str, Any]], mode: str = "AI增强选股") -> str:
    """生成批量AI决策报告的便捷函数"""
    reporter = get_ai_reporter()
    return reporter.generate_batch_analysis_report(results, mode)

if __name__ == "__main__":
    # 测试报告生成功能
    test_result = {
        'symbol': 'TEST001',
        'overall_score': 75.5,
        'confidence_level': 0.8,
        'recommendation': '推荐',
        'risk_assessment': '中等风险',
        'expert_committee_score': 78.2,
        'adaptive_strategy_score': 72.8,
        'key_factors': ['基本面良好', '技术面突破', '市场环境有利'],
        'risk_factors': ['行业竞争激烈'],
        'opportunity_factors': ['政策支持', '业绩增长预期'],
        'processing_time': 2.5
    }
    
    reporter = AIDecisionReporter()
    report = reporter.generate_stock_analysis_report('TEST001', test_result)
    print(report)
    
    # 保存报告
    saved_path = reporter.save_report_to_file(report, "test_ai_report.txt")
    print(f"报告已保存到: {saved_path}")