#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tencent():
    try:
        from tradingagents.dataflows.tencent_utils import get_tencent_stock_info
        
        result = get_tencent_stock_info('000001')
        if result:
            print("SUCCESS: Tencent data retrieved")
            print(f"Symbol: {result.get('symbol')}")
            print(f"Name: {result.get('name')}")
            print(f"Price: {result.get('current_price')}")
            print(f"Change: {result.get('change_pct')}%")
            return True
        else:
            print("FAILED: No data returned")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_tencent()