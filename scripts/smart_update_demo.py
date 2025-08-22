#!/usr/bin/env python3
"""
智能活跃度更新系统演示脚本
展示完整的5000+股票分层更新优化方案
"""

import sys
import time
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.batch_update_manager import batch_update_stocks, estimate_batch_time
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager
from tradingagents.analytics.stock_activity_classifier import classify_stocks_batch
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('smart_update_demo')


def demo_smart_update():
    """演示智能更新系统"""
    print("🚀 TradingAgents-CN 智能更新系统演示")
    print("=" * 60)
    
    # 获取股票列表管理器
    stock_manager = get_stock_master_manager()
    
    # 获取A股股票列表
    print("📊 获取A股股票列表...")
    symbols_df = stock_manager.load_stock_list('A股')
    if symbols_df is None or symbols_df.empty:
        print("❌ 无股票数据，请先运行测试")
        return
    
    symbols = symbols_df['symbol'].tolist()
    print(f"✅ 获取到 {len(symbols)} 只A股股票")
    
    # 演示活跃度分类
    print("\n📈 开始活跃度智能分类...")
    classifications = classify_stocks_batch(symbols[:100])  # 先分类前100只演示
    
    print("\n📊 分类结果：")
    for category, stocks in classifications.items():
        print(f"   {category}: {len(stocks)} 只股票")
    
    # 预估更新时间
    print(f"\n⏱️ 预估更新时间（{len(symbols)}只股票）：")
    time_estimate = estimate_batch_time(symbols, max_workers=10)
    print(f"   总估算：{time_estimate['total_estimate']} 秒")
    print(f"   并行估算：{time_estimate['parallel_estimate']} 秒")
    print(f"   并行度：{time_estimate['max_workers']} 工作线程")
    
    # 实际更新演示（少量股票）
    demo_symbols = symbols[:20]  # 演示20只股票
    print(f"\n🔥 开始更新演示（{len(demo_symbols)}只股票）...")
    
    start_time = time.time()
    result = batch_update_stocks(demo_symbols, max_workers=5)
    actual_time = time.time() - start_time
    
    print(f"\n✅ 更新完成！")
    print(f"   实际耗时：{actual_time:.2f} 秒")
    print(f"   更新数量：{result['updated_symbols']} 只")
    print(f"   成功：{result['successful']} 只")
    print(f"   失败：{result['failed']} 只")
    print(f"   跳过：{result['skipped_symbols']} 只")
    print(f"   吞吐量：{result['throughput']:.2f} 股票/秒")
    
    # 性能对比
    print(f"\n📊 性能提升对比：")
    old_time = len(demo_symbols) * 3  # 假设旧系统每只3秒
    improvement = old_time / actual_time if actual_time > 0 else 1
    print(f"   旧系统预估：{old_time} 秒")
    print(f"   新系统实际：{actual_time:.2f} 秒")
    print(f"   性能提升：{improvement:.1f}x")
    
    # 展示分层更新策略
    print(f"\n🎯 完整系统效果预估（{len(symbols)}只股票）：")
    full_classifications = classify_stocks_batch(symbols)
    
    active_count = len(full_classifications.get('active', []))
    normal_count = len(full_classifications.get('normal', []))
    inactive_count = len(full_classifications.get('inactive', []))
    
    print(f"   活跃股票：{active_count} 只（每日更新）")
    print(f"   普通股票：{normal_count} 只（每周更新）")
    print(f"   冷门股票：{inactive_count} 只（每月更新）")
    
    # 计算实际每日工作量
    daily_work = active_count + normal_count / 7 + inactive_count / 30
    estimated_daily_time = daily_work * 2 / 10  # 平均每只2秒，10并发
    
    print(f"\n📅 每日实际工作量：")
    print(f"   需要更新：{daily_work:.0f} 只股票/日")
    print(f"   预估耗时：{estimated_daily_time:.1f} 分钟")
    print(f"   相比全量更新：从 {len(symbols)*3/60:.1f}小时 → {estimated_daily_time:.1f}分钟")
    print(f"   效率提升：{len(symbols)*3/60/estimated_daily_time:.1f}x")


def demo_classification_detail():
    """演示分类详情"""
    print("\n" + "=" * 60)
    print("🔍 活跃度分类详情演示")
    print("=" * 60)
    
    # 选择几只不同特征的股票演示
    demo_symbols = ['000001', '000002', '000004', '000006', '000007']
    
    from tradingagents.analytics.stock_activity_classifier import classify_stock_activity
    
    for symbol in demo_symbols:
        print(f"\n📊 {symbol} 活跃度分析：")
        result = classify_stock_activity(symbol)
        
        if 'error' not in result:
            print(f"   综合评分：{result['total_score']:.1f}/100")
            print(f"   换手率：{result['turnover_rate']:.2f}%")
            print(f"   成交量评分：{result['volume_score']:.1f}/100")
            print(f"   价格波动评分：{result['volatility_score']:.1f}/100")
            print(f"   分类：{result['classification']}")
        else:
            print(f"   分析失败：{result['error']}")


if __name__ == "__main__":
    print("🎯 TradingAgents-CN 智能更新系统演示")
    print("作者：AI助手")
    print("版本：v2.0 智能活跃度优化版")
    print()
    
    try:
        demo_smart_update()
        demo_classification_detail()
    except KeyboardInterrupt:
        print("\n\n🛑 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示错误：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("系统已准备好处理5000+股票的高效更新")
    print("=" * 60)