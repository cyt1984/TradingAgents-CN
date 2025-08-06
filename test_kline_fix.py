import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test K-line data specifically
try:
    from tradingagents.dataflows.tencent_utils import get_tencent_kline
    import json
    
    print("Testing K-line API...")
    
    # Test with debug
    symbol = '000001'
    
    # Try different periods
    periods = ['day', 'week']
    for period in periods:
        print(f"\nTesting {period} K-line...")
        try:
            kline = get_tencent_kline(symbol, period=period, count=5)
            if kline is not None and not kline.empty:
                print(f"SUCCESS: {period} K-line - {len(kline)} records")
                print("Columns:", list(kline.columns))
                print("Latest:", kline.iloc[-1].to_dict())
            else:
                print(f"FAILED: {period} K-line - no data")
        except Exception as e:
            print(f"ERROR in {period}: {e}")
            
except Exception as e:
    print("ERROR:", str(e))
    import traceback
    traceback.print_exc()