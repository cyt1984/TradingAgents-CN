#!/usr/bin/env python3
"""
AI选股引擎调试和监控工具
提供AI系统的详细状态检查、性能监控和问题诊断功能
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import json

from ..utils.logging_manager import get_logger
from .stock_selector import get_stock_selector
from .ai_strategies.ai_strategy_manager import get_ai_strategy_manager

logger = get_logger('ai_debug')


class AIDebugTools:
    """AI引擎调试工具类"""
    
    def __init__(self):
        """初始化调试工具"""
        self.stock_selector = None
        self.ai_manager = None
        self.debug_history = []
        
        try:
            self.stock_selector = get_stock_selector()
            self.ai_manager = get_ai_strategy_manager()
            logger.info("✅ AI调试工具初始化成功")
        except Exception as e:
            logger.error(f"❌ AI调试工具初始化失败: {e}")
    
    def run_full_system_check(self) -> Dict[str, Any]:
        """执行完整系统检查"""
        logger.info("🔍 开始执行AI系统全面检查...")
        
        check_result = {
            'timestamp': datetime.now(),
            'overall_status': 'unknown',
            'components': {},
            'performance': {},
            'recommendations': []
        }
        
        try:
            # 1. 基础组件检查
            check_result['components'] = self._check_components()
            
            # 2. AI引擎状态检查
            ai_status = self._check_ai_engines()
            check_result['components']['ai_engines'] = ai_status
            
            # 3. 性能指标检查
            check_result['performance'] = self._check_performance()
            
            # 4. 功能测试
            function_test = self._test_basic_functions()
            check_result['components']['function_test'] = function_test
            
            # 5. 生成总体状态和建议
            check_result['overall_status'] = self._evaluate_overall_status(check_result)
            check_result['recommendations'] = self._generate_recommendations(check_result)
            
            # 记录检查历史
            self.debug_history.append(check_result)
            if len(self.debug_history) > 10:  # 保持最近10次检查记录
                self.debug_history.pop(0)
            
            logger.info(f"✅ 系统检查完成，总体状态: {check_result['overall_status']}")
            return check_result
            
        except Exception as e:
            logger.error(f"❌ 系统检查失败: {e}")
            check_result['overall_status'] = 'error'
            check_result['error'] = str(e)
            return check_result
    
    def _check_components(self) -> Dict[str, Any]:
        """检查基础组件状态"""
        components = {}
        
        # 选股引擎检查
        try:
            if self.stock_selector:
                components['stock_selector'] = {
                    'status': 'available',
                    'cache_enabled': self.stock_selector.cache_enabled,
                    'has_data_manager': hasattr(self.stock_selector, 'data_manager') and self.stock_selector.data_manager is not None,
                    'has_scoring_system': hasattr(self.stock_selector, 'scoring_system') and self.stock_selector.scoring_system is not None
                }
            else:
                components['stock_selector'] = {'status': 'unavailable'}
        except Exception as e:
            components['stock_selector'] = {'status': 'error', 'error': str(e)}
        
        return components
    
    def _check_ai_engines(self) -> Dict[str, Any]:
        """检查AI引擎状态"""
        if not self.ai_manager:
            return {'status': 'ai_manager_unavailable'}
        
        try:
            ai_status = self.ai_manager.get_performance_summary()
            
            engines_detail = {}
            for engine_name, is_available in ai_status.get('ai_engines_status', {}).items():
                engines_detail[engine_name] = {
                    'available': is_available,
                    'instance_exists': False
                }
                
                # 检查实例是否存在
                if engine_name == 'expert_committee':
                    engines_detail[engine_name]['instance_exists'] = self.ai_manager.expert_committee is not None
                elif engine_name == 'adaptive_engine':
                    engines_detail[engine_name]['instance_exists'] = self.ai_manager.adaptive_engine is not None
                elif engine_name == 'pattern_recognizer':
                    engines_detail[engine_name]['instance_exists'] = self.ai_manager.pattern_recognizer is not None
                elif engine_name == 'similarity_engine':
                    engines_detail[engine_name]['instance_exists'] = self.ai_manager.similarity_engine is not None
            
            return {
                'status': 'checked',
                'summary': ai_status,
                'engines_detail': engines_detail
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_performance(self) -> Dict[str, Any]:
        """检查性能指标"""
        performance = {}
        
        if self.ai_manager:
            try:
                ai_perf = self.ai_manager.get_performance_summary()
                performance['ai_manager'] = {
                    'total_analyses': ai_perf.get('total_analyses', 0),
                    'cache_hit_rate': ai_perf.get('cache_hit_rate', 0),
                    'average_processing_time': ai_perf.get('average_processing_time', 0),
                    'cache_size': ai_perf.get('cache_size', 0)
                }
            except Exception as e:
                performance['ai_manager'] = {'error': str(e)}
        
        return performance
    
    def _test_basic_functions(self) -> Dict[str, Any]:
        """测试基础功能"""
        test_results = {}
        
        # 测试股票列表获取
        try:
            if self.stock_selector:
                start_time = time.time()
                stock_list = self.stock_selector._get_stock_list()
                end_time = time.time()
                
                test_results['get_stock_list'] = {
                    'status': 'success' if not stock_list.empty else 'empty_result',
                    'count': len(stock_list) if not stock_list.empty else 0,
                    'execution_time': round(end_time - start_time, 3)
                }
            else:
                test_results['get_stock_list'] = {'status': 'selector_unavailable'}
        except Exception as e:
            test_results['get_stock_list'] = {'status': 'error', 'error': str(e)}
        
        # 测试AI分析功能（使用一个样本股票）
        if self.ai_manager and test_results.get('get_stock_list', {}).get('count', 0) > 0:
            try:
                # 获取一个测试股票
                stock_list = self.stock_selector._get_stock_list()
                test_symbol = stock_list.iloc[0]['ts_code'] if not stock_list.empty else '000001.SZ'
                
                start_time = time.time()
                sample_data = {'ts_code': test_symbol, 'name': '测试股票'}
                ai_result = self.ai_manager.analyze_stock_with_ai(test_symbol, sample_data)
                end_time = time.time()
                
                test_results['ai_analysis'] = {
                    'status': 'success' if ai_result else 'no_result',
                    'test_symbol': test_symbol,
                    'execution_time': round(end_time - start_time, 3),
                    'result_score': getattr(ai_result, 'overall_score', None) if ai_result else None
                }
            except Exception as e:
                test_results['ai_analysis'] = {'status': 'error', 'error': str(e)}
        
        return test_results
    
    def _evaluate_overall_status(self, check_result: Dict[str, Any]) -> str:
        """评估总体状态"""
        components = check_result.get('components', {})
        
        # 检查关键组件
        selector_status = components.get('stock_selector', {}).get('status')
        ai_engines = components.get('ai_engines', {})
        
        if selector_status == 'error':
            return 'critical_error'
        elif selector_status == 'unavailable':
            return 'service_unavailable'
        
        # 检查AI引擎
        if ai_engines.get('status') == 'error':
            return 'ai_system_error'
        
        ai_summary = ai_engines.get('summary', {})
        if not ai_summary.get('ai_enabled', False):
            return 'basic_mode'  # 基础模式，无AI增强
        
        availability_rate = ai_summary.get('engine_availability', {}).get('availability_rate', 0)
        if availability_rate >= 75:
            return 'fully_operational'
        elif availability_rate >= 50:
            return 'partially_operational'
        else:
            return 'limited_functionality'
    
    def _generate_recommendations(self, check_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        overall_status = check_result.get('overall_status')
        components = check_result.get('components', {})
        
        if overall_status == 'critical_error':
            recommendations.append("🚨 检测到严重错误，请检查系统配置和依赖")
        elif overall_status == 'service_unavailable':
            recommendations.append("⚠️ 选股服务不可用，请重启系统或检查配置")
        elif overall_status == 'ai_system_error':
            recommendations.append("🤖 AI系统出现错误，建议重新初始化AI引擎")
        elif overall_status == 'basic_mode':
            recommendations.append("📊 当前运行在基础模式，建议检查AI引擎配置")
        elif overall_status == 'limited_functionality':
            recommendations.append("🔧 AI功能受限，建议检查和修复失效的AI引擎")
        elif overall_status == 'partially_operational':
            recommendations.append("⚡ AI系统部分可用，可考虑重启AI引擎以获得完整功能")
        elif overall_status == 'fully_operational':
            recommendations.append("✅ 系统运行状态良好，所有功能正常")
        
        # 具体组件建议
        ai_engines = components.get('ai_engines', {})
        if ai_engines.get('status') == 'checked':
            engines_detail = ai_engines.get('engines_detail', {})
            for engine_name, engine_info in engines_detail.items():
                if engine_info.get('available') and not engine_info.get('instance_exists'):
                    recommendations.append(f"🔄 {engine_name} 状态不一致，建议重新初始化")
        
        # 性能建议
        performance = check_result.get('performance', {})
        ai_perf = performance.get('ai_manager', {})
        if isinstance(ai_perf, dict) and 'average_processing_time' in ai_perf:
            avg_time = ai_perf['average_processing_time']
            if avg_time > 5.0:
                recommendations.append("⏱️ AI分析平均耗时较长，建议清理缓存或优化配置")
            
            cache_hit_rate = ai_perf.get('cache_hit_rate', 0)
            if cache_hit_rate < 30:
                recommendations.append("💾 缓存命中率偏低，建议调整缓存策略")
        
        return recommendations
    
    def get_debug_report(self) -> str:
        """生成调试报告"""
        if not self.debug_history:
            return "📋 暂无调试历史记录，请先执行系统检查"
        
        latest_check = self.debug_history[-1]
        
        report = []
        report.append("🔍 AI选股系统调试报告")
        report.append("=" * 50)
        report.append(f"检查时间: {latest_check['timestamp']}")
        report.append(f"总体状态: {latest_check['overall_status']}")
        report.append("")
        
        # 组件状态
        report.append("📦 组件状态:")
        components = latest_check.get('components', {})
        for component_name, component_info in components.items():
            if isinstance(component_info, dict):
                status = component_info.get('status', 'unknown')
                report.append(f"  - {component_name}: {status}")
            else:
                report.append(f"  - {component_name}: {component_info}")
        
        report.append("")
        
        # AI引擎详情
        ai_engines = components.get('ai_engines', {})
        if ai_engines.get('status') == 'checked':
            report.append("🤖 AI引擎状态:")
            engines_detail = ai_engines.get('engines_detail', {})
            for engine_name, engine_info in engines_detail.items():
                available = "✅" if engine_info.get('available') else "❌"
                report.append(f"  - {engine_name}: {available}")
        
        report.append("")
        
        # 性能指标
        performance = latest_check.get('performance', {})
        if performance:
            report.append("📊 性能指标:")
            ai_perf = performance.get('ai_manager', {})
            if isinstance(ai_perf, dict):
                for metric, value in ai_perf.items():
                    if metric != 'error':
                        report.append(f"  - {metric}: {value}")
        
        report.append("")
        
        # 建议
        recommendations = latest_check.get('recommendations', [])
        if recommendations:
            report.append("💡 改进建议:")
            for rec in recommendations:
                report.append(f"  {rec}")
        
        return "\n".join(report)
    
    def benchmark_ai_performance(self, test_count: int = 5) -> Dict[str, Any]:
        """AI性能基准测试"""
        logger.info(f"🚀 开始AI性能基准测试，测试数量: {test_count}")
        
        if not self.ai_manager:
            return {'error': 'AI管理器不可用'}
        
        test_results = {
            'test_count': test_count,
            'timestamp': datetime.now(),
            'results': [],
            'statistics': {}
        }
        
        try:
            # 获取测试用股票列表
            stock_list = self.stock_selector._get_stock_list() if self.stock_selector else pd.DataFrame()
            if stock_list.empty:
                return {'error': '无法获取测试股票列表'}
            
            test_symbols = stock_list.head(test_count)['ts_code'].tolist()
            
            # 执行测试
            execution_times = []
            success_count = 0
            
            for i, symbol in enumerate(test_symbols):
                logger.info(f"🧪 测试进度: {i+1}/{test_count} - {symbol}")
                
                try:
                    start_time = time.time()
                    sample_data = {'ts_code': symbol, 'name': f'测试股票{i+1}'}
                    result = self.ai_manager.analyze_stock_with_ai(symbol, sample_data)
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    execution_times.append(execution_time)
                    
                    test_results['results'].append({
                        'symbol': symbol,
                        'execution_time': execution_time,
                        'success': result is not None,
                        'ai_score': getattr(result, 'overall_score', None) if result else None
                    })
                    
                    if result:
                        success_count += 1
                        
                except Exception as e:
                    test_results['results'].append({
                        'symbol': symbol,
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            # 计算统计数据
            if execution_times:
                test_results['statistics'] = {
                    'success_rate': success_count / test_count * 100,
                    'average_time': sum(execution_times) / len(execution_times),
                    'min_time': min(execution_times),
                    'max_time': max(execution_times),
                    'total_time': sum(execution_times)
                }
            
            logger.info(f"✅ 基准测试完成: {success_count}/{test_count} 成功")
            return test_results
            
        except Exception as e:
            logger.error(f"❌ 基准测试失败: {e}")
            test_results['error'] = str(e)
            return test_results
    
    def clear_ai_caches(self) -> Dict[str, Any]:
        """清理AI缓存"""
        logger.info("🧹 开始清理AI缓存...")
        
        result = {
            'timestamp': datetime.now(),
            'cleared_caches': []
        }
        
        try:
            if self.ai_manager:
                self.ai_manager.clear_cache()
                result['cleared_caches'].append('ai_manager')
                logger.info("✅ AI管理器缓存已清理")
            
            if self.stock_selector:
                # 清理股票选择器缓存
                self.stock_selector._stock_cache = {}
                self.stock_selector._cache_timestamp = None
                result['cleared_caches'].append('stock_selector')
                logger.info("✅ 选股器缓存已清理")
            
            logger.info(f"🧹 缓存清理完成: {result['cleared_caches']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 缓存清理失败: {e}")
            result['error'] = str(e)
            return result


# 全局调试工具实例
_debug_tools = None

def get_ai_debug_tools() -> AIDebugTools:
    """获取全局AI调试工具实例"""
    global _debug_tools
    if _debug_tools is None:
        _debug_tools = AIDebugTools()
    return _debug_tools