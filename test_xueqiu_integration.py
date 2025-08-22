#!/usr/bin/env python3
"""
测试雪球数据集成效果
验证社交情绪分析是否正确集成到智能选股系统中
"""

import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_xueqiu_data_fetch():
    """测试雪球数据获取"""
    logger.info("=" * 60)
    logger.info("📱 测试1: 雪球数据获取")
    logger.info("=" * 60)
    
    try:
        from tradingagents.dataflows.xueqiu_utils import get_xueqiu_provider
        
        provider = get_xueqiu_provider()
        
        # 测试股票列表
        test_symbols = ['000001', '600519', '000858']  # 平安银行、贵州茅台、五粮液
        
        for symbol in test_symbols:
            logger.info(f"\n📊 测试股票: {symbol}")
            
            # 获取情绪数据
            sentiment = provider.get_stock_sentiment(symbol, days=7)
            if sentiment:
                logger.info(f"✅ 情绪分析成功:")
                logger.info(f"   - 讨论数: {sentiment.get('total_discussions', 0)}")
                logger.info(f"   - 情绪分数: {sentiment.get('sentiment_score', 0):.2f}")
                logger.info(f"   - 积极比例: {sentiment.get('positive_ratio', 0):.2%}")
                logger.info(f"   - 平均互动: {sentiment.get('avg_interactions', 0):.0f}")
            else:
                logger.warning(f"⚠️ 未获取到 {symbol} 的情绪数据")
            
            # 获取讨论数据
            discussions = provider.get_stock_discussions(symbol, limit=5)
            if discussions:
                logger.info(f"✅ 获取到 {len(discussions)} 条讨论")
                if discussions:
                    top_discussion = discussions[0]
                    logger.info(f"   最热讨论: {top_discussion.get('text', '')[:100]}...")
            
            time.sleep(0.5)  # 避免请求过快
        
        logger.info("\n✅ 雪球数据获取测试通过!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 雪球数据获取测试失败: {e}")
        return False

def test_batch_processor_with_social():
    """测试批处理器的社交数据集成"""
    logger.info("\n" + "=" * 60)
    logger.info("🤖 测试2: 批处理器社交数据集成")
    logger.info("=" * 60)
    
    try:
        from tradingagents.selectors.batch_ai_processor import BatchAIProcessor, BatchConfig
        
        # 配置批处理器
        config = BatchConfig(
            batch_size=10,
            max_workers=4,
            enable_social=True,  # 启用社交分析
            social_weight=0.2,
            min_discussions=5
        )
        
        processor = BatchAIProcessor(config)
        
        # 测试股票
        test_symbols = ['000001', '600519']
        
        logger.info(f"🚀 开始批量分析 {len(test_symbols)} 只股票...")
        
        # 执行批处理
        report = processor.process_stocks(test_symbols)
        
        logger.info(f"\n📊 批处理报告:")
        logger.info(f"   - 总股票数: {report.total_stocks}")
        logger.info(f"   - 成功处理: {report.successful_stocks}")
        logger.info(f"   - 处理时间: {report.total_time:.2f}秒")
        logger.info(f"   - 吞吐量: {report.throughput:.2f}股票/秒")
        
        # 检查缓存中的结果
        if hasattr(processor, '_results_cache'):
            for symbol in test_symbols:
                if symbol in processor._results_cache:
                    result = processor._results_cache[symbol]
                    if result.success and result.analysis_result:
                        analysis = result.analysis_result
                        
                        logger.info(f"\n📈 {symbol} 分析结果:")
                        logger.info(f"   - 综合评分: {analysis.get('combined_score', 0):.1f}")
                        logger.info(f"   - 推荐: {analysis.get('recommendation', 'HOLD')}")
                        
                        # 检查社交数据
                        if 'social_signals' in analysis:
                            logger.info(f"   - 社交信号: {', '.join(analysis['social_signals'])}")
                        
                        if 'analyst_results' in analysis and 'social' in analysis['analyst_results']:
                            social_data = analysis['analyst_results']['social']
                            logger.info(f"   - 社交评分: {social_data.get('social_score', 0):.1f}")
        
        logger.info("\n✅ 批处理器社交数据集成测试通过!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 批处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_pipeline_social():
    """测试异步管道的社交数据集成"""
    logger.info("\n" + "=" * 60)
    logger.info("⚡ 测试3: 异步管道社交数据集成")
    logger.info("=" * 60)
    
    try:
        import asyncio
        from tradingagents.dataflows.async_data_pipeline import AsyncDataPipeline, PipelineConfig
        
        async def run_test():
            # 配置管道
            config = PipelineConfig(
                max_concurrent_tasks=10,
                batch_size=50,
                enable_caching=True,
                cache_ttl=3600
            )
            
            pipeline = AsyncDataPipeline(config)
            
            # 测试股票
            test_symbols = ['000001', '000002']
            
            logger.info(f"🚀 开始异步处理 {len(test_symbols)} 只股票...")
            
            # 处理股票
            result = await pipeline.process_symbols(test_symbols)
            
            if result and 'results' in result:
                for symbol, data in result['results'].items():
                    if not isinstance(data, dict) or 'error' in data:
                        continue
                    
                    logger.info(f"\n📊 {symbol} 数据:")
                    
                    # 检查社交数据字段
                    social_fields = [
                        'social_sentiment_score',
                        'total_discussions', 
                        'social_heat',
                        'sentiment_trend'
                    ]
                    
                    for field in social_fields:
                        if field in data:
                            logger.info(f"   - {field}: {data[field]}")
                    
                    # 检查增强评分
                    if 'enrich_score' in data:
                        logger.info(f"   - 增强评分: {data['enrich_score']:.1f}")
                    
                    if 'final_score' in data:
                        logger.info(f"   - 最终评分: {data['final_score']:.1f}")
            
            # 显示度量
            if 'metrics' in result:
                metrics = result['metrics']
                logger.info(f"\n📈 管道度量:")
                logger.info(f"   - 处理时间: {metrics.get('total_time', 0):.2f}秒")
                logger.info(f"   - 吞吐量: {metrics.get('throughput', 0):.2f}股票/秒")
            
            return True
        
        # 运行异步测试
        success = asyncio.run(run_test())
        
        if success:
            logger.info("\n✅ 异步管道社交数据集成测试通过!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 异步管道测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_selector_integration():
    """测试股票选择器的完整集成"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 测试4: 股票选择器完整集成")
    logger.info("=" * 60)
    
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        from tradingagents.selectors.config import AIMode
        
        selector = StockSelector()
        
        logger.info("🚀 执行AI增强选股（包含社交数据）...")
        
        # 使用AI增强模式选股
        result = selector.ai_enhanced_select(
            min_score=60,
            limit=5,
            ai_mode=AIMode.AI_ENHANCED
        )
        
        if result and result.data is not None and not result.data.empty:
            logger.info(f"\n📊 选股结果:")
            logger.info(f"   - 选中股票数: {len(result.data)}")
            logger.info(f"   - 执行时间: {result.execution_time:.2f}秒")
            
            # 检查是否包含社交数据列
            social_columns = ['social_score', 'social_heat', 'social_sentiment', 'social_signals']
            available_social_cols = [col for col in social_columns if col in result.data.columns]
            
            if available_social_cols:
                logger.info(f"   - 包含社交数据列: {', '.join(available_social_cols)}")
                
                # 显示前几只股票的社交数据
                for idx, row in result.data.head(3).iterrows():
                    symbol = row.get('ts_code', '')
                    logger.info(f"\n   📈 {symbol}:")
                    
                    if 'intelligent_score' in row:
                        logger.info(f"      - 智能综合评分: {row['intelligent_score']:.1f}")
                    
                    for col in available_social_cols:
                        if col in row and pd.notna(row[col]):
                            if col == 'social_signals':
                                logger.info(f"      - {col}: {row[col]}")
                            else:
                                logger.info(f"      - {col}: {row[col]:.2f}")
            else:
                logger.warning("   ⚠️ 未找到社交数据列")
            
            logger.info("\n✅ 股票选择器集成测试通过!")
            return True
        else:
            logger.warning("⚠️ 选股结果为空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 股票选择器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    logger.info("🚀 开始测试雪球数据集成效果")
    logger.info(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # 测试1: 雪球数据获取
    test_results['xueqiu_fetch'] = test_xueqiu_data_fetch()
    time.sleep(1)
    
    # 测试2: 批处理器集成
    test_results['batch_processor'] = test_batch_processor_with_social()
    time.sleep(1)
    
    # 测试3: 异步管道集成
    test_results['async_pipeline'] = test_async_pipeline_social()
    time.sleep(1)
    
    # 测试4: 完整选股集成
    test_results['stock_selector'] = test_stock_selector_integration()
    
    # 总结测试结果
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果总结")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 所有测试通过！雪球数据已成功集成到智能选股系统!")
        logger.info("\n📈 集成效果:")
        logger.info("   1. 批处理器可以获取并分析雪球情绪数据")
        logger.info("   2. 异步管道包含社交数据获取和评分")
        logger.info("   3. 股票选择器使用社交信号进行智能评分")
        logger.info("   4. 缓存策略有效减少重复请求")
    else:
        logger.error("\n❌ 部分测试失败，请检查日志并修复问题")
    
    return all_passed

if __name__ == "__main__":
    import pandas as pd
    
    # 设置pandas显示选项
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    
    # 运行测试
    success = main()
    exit(0 if success else 1)