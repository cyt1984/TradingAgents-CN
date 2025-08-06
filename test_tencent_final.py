import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test Tencent integration
try:
    from tradingagents.dataflows.tencent_utils import get_tencent_stock_info
    
    result = get_tencent_stock_info('000001')
    if result:
        print("SUCCESS: Tencent integration working")
        print("Symbol:", result.get('symbol'))
        print("Current Price:", result.get('current_price'))
        print("Change %:", result.get('change_pct'))
        
        # Test K-line data
        from tradingagents.dataflows.tencent_utils import get_tencent_kline
        kline = get_tencent_kline('000001', count=3)
        if kline is not None:
            print("K-line data retrieved:", len(kline), "records")
            print("Tencent integration complete")
        else:
            print("K-line data failed")
    else:
        print("FAILED: No data from Tencent")
        
except Exception as e:
    print("ERROR testing Tencent:", str(e))
    import traceback
    traceback.print_exc()