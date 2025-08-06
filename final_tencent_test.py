import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_final():
    """Final test of Tencent integration"""
    
    print("=== Tencent Data Integration Final Test ===")
    
    # Test real-time price
    try:
        from tradingagents.dataflows.tencent_utils import get_tencent_stock_info
        
        result = get_tencent_stock_info('000001')
        if result and result.get('current_price'):
            print("SUCCESS: Real-time price working")
            print(f"  Price: {result['current_price']}")
            print(f"  Change: {result['change_pct']}%")
            
            # Test batch
            from tradingagents.dataflows.tencent_utils import get_tencent_multiple_stocks
            batch = get_tencent_multiple_stocks(['000001', '600519'])
            if batch:
                print(f"SUCCESS: Batch working - {len(batch)} stocks")
                
                # Test enhanced manager
                from tradingagents.dataflows.enhanced_data_manager import get_enhanced_data_manager
                manager = get_enhanced_data_manager()
                data = manager.get_comprehensive_stock_info('000001')
                if data:
                    print("SUCCESS: Enhanced manager integrated")
                    print(f"  Sources: {data.get('sources', [])}")
                    print("\n=== STAGE 1 COMPLETE ===")
                    print("Tencent integration verified and working")
                    return True
    except Exception as e:
        print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    test_final()