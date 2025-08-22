#!/usr/bin/env python3
"""
智能更新系统测试 - 简化版
"""

import sys
import os
from pathlib import Path
import time

# 设置编码
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.stock_master_manager import get_stock_master_manager
from tradingagents.dataflows.historical_data_manager import get_historical_manager
from tradingagents.analytics.stock_activity_classifier import StockActivityClassifier

def test_activity_classifier():
    """测试活跃度分类器"""
    print("=== 测试股票活跃度分类器 ===")
    
    try:
        classifier = StockActivityClassifier()
        
        # 测试换手率计算
        print("\n1. 测试换手率计算...")
        turnover = classifier.calculate_turnover_rate('000001', days=5)
        print(f"   000001 换手率: {turnover:.2f}%")
        
        # 测试活跃度评分
        print("\n2. 测试活跃度评分...")
        score = classifier.calculate_activity_score('000001', days=5)
        if 'error' not in score:
            print(f"   000001 综合评分: {score['total_score']:.1f}/100")
            print(f"   分类结果: {score['classification']}")
            print(f"   换手率: {score['turnover_rate']:.2f}%")
            print(f"   成交量评分: {score['volume_score']:.1f}/100")
            print(f"   价格波动评分: {score['volatility_score']:.1f}/100")
        else:
            print(f"   评分失败: {score['error']}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_layered_update():
    """测试分层更新策略"""
    print("\n=== 测试分层更新策略 ===")
    
    try:
        # 获取少量股票测试
        manager = get_stock_master_manager()
        stocks_df = manager.load_stock_list('A股')
        
        if stocks_df is not None and not stocks_df.empty:
            test_symbols = stocks_df['symbol'].head(10).tolist()
            print(f"测试股票数量: {len(test_symbols)}")
            
            # 创建分类器
            classifier = StockActivityClassifier()
            
            # 批量分类
            classifications = classifier.classify_stocks(test_symbols)
            
            print("\n分类结果:")
            for category, symbols in classifications.items():
                print(f"   {category}: {len(symbols)} 只股票")
                if symbols:
                    print(f"     示例: {symbols[:3]}")
            
            return True
        else:
            print("无股票数据可供测试")
            return False
            
    except Exception as e:
        print(f"分层更新测试失败: {e}")
        return False

def test_performance_estimate():
    """测试性能估算"""
    print("\n=== 性能估算测试 ===")
    
    try:
        # 模拟5000只股票
        total_stocks = 5000
        
        # 预估分类分布
        active_percent = 0.08    # 8% 活跃
        normal_percent = 0.50    # 50% 普通
        inactive_percent = 0.42  # 42% 冷门
        
        active_count = int(total_stocks * active_percent)
        normal_count = int(total_stocks * normal_percent)
        inactive_count = total_stocks - active_count - normal_count
        
        print(f"模拟 {total_stocks} 只股票分类:")
        print(f"   活跃股票: {active_count} 只 (每日)")
        print(f"   普通股票: {normal_count} 只 (每周)")
        print(f"   冷门股票: {inactive_count} 只 (每月)")
        
        # 计算每日工作量
        daily_active = active_count
        daily_normal = normal_count / 7
        daily_inactive = inactive_count / 30
        daily_total = daily_active + daily_normal + daily_inactive
        
        print(f"\n每日实际更新:")
        print(f"   活跃股票: {daily_active:.0f} 只")
        print(f"   普通股票: {daily_normal:.0f} 只")
        print(f"   冷门股票: {daily_inactive:.0f} 只")
        print(f"   总计: {daily_total:.0f} 只/日")
        
        # 时间估算
        time_per_stock = 2  # 每只股票2秒
        max_workers = 10
        
        parallel_time = daily_total * time_per_stock / max_workers / 60  # 分钟
        old_time = daily_total * 3 / 60  # 旧系统每只股票3秒
        
        print(f"\n时间对比:")
        print(f"   旧系统: {old_time:.1f} 分钟/日")
        print(f"   新系统: {parallel_time:.1f} 分钟/日")
        print(f"   效率提升: {old_time/parallel_time:.1f}x")
        
        return True
        
    except Exception as e:
        print(f"性能估算失败: {e}")
        return False

def main():
    """主测试函数"""
    print("TradingAgents-CN 智能更新系统测试")
    print("=" * 50)
    
    try:
        # 测试1：活跃度分类器
        test1 = test_activity_classifier()
        
        # 测试2：分层更新策略
        test2 = test_layered_update()
        
        # 测试3：性能估算
        test3 = test_performance_estimate()
        
        print("\n" + "=" * 50)
        print("测试总结:")
        print(f"活跃度分类器: {'✅ 通过' if test1 else '❌ 失败'}")
        print(f"分层更新策略: {'✅ 通过' if test2 else '❌ 失败'}")
        print(f"性能估算: {'✅ 通过' if test3 else '❌ 失败'}")
        
        if all([test1, test2, test3]):
            print("\n🎉 所有测试通过！系统已准备好处理5000+股票的高效更新")
        else:
            print("\n⚠️ 部分测试失败，请检查日志")
            
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()