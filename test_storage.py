#!/usr/bin/env python3
"""
简单测试脚本，验证持久化存储系统
"""

import sys
import os
import logging
from pathlib import Path

# 设置编码
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
from tradingagents.dataflows.stock_master_manager import get_stock_master_manager

def test_basic_functionality():
    """测试基本功能"""
    print("=== Testing Persistent Storage System ===")
    
    try:
        # 测试1: 获取增强数据管理器
        manager = get_enhanced_data_manager()
        print("Enhanced data manager initialized")
        
        # 测试2: 获取股票列表管理器
        stock_manager = get_stock_master_manager()
        print("Stock master manager initialized")
        
        # 测试3: 获取A股股票列表
        stocks = manager.get_stock_list('A')
        print(f"Retrieved A-share stock list: {len(stocks)} stocks")
        
        if stocks:
            print("First 5 stocks:")
            for i, stock in enumerate(stocks[:5]):
                print(f"  {i+1}. {stock['symbol']} - {stock['name']}")
        
        # 测试4: 获取单只股票信息
        if stocks:
            test_symbol = stocks[0]['symbol']
            info = manager.get_comprehensive_stock_info(test_symbol)
            print(f"Retrieved stock info for {test_symbol}")
            
        print("=== All tests passed ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality()