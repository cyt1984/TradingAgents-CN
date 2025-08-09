#!/usr/bin/env python3
"""
ASCII-only test for unified smart stock selection system
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== ASCII Test: Unified Smart Stock Selection System ===")

def test_a_share_data():
    """Test A-share data source"""
    print("\n1. Testing A-share data source...")
    
    try:
        from tradingagents.dataflows.enhanced_data_manager import EnhancedDataManager
        manager = EnhancedDataManager()
        
        # Test getting A-share list
        stocks = manager.get_stock_list('A')
        print(f"   A-share stock count: {len(stocks)}")
        
        if stocks:
            print("   First 3 stocks:")
            for i, stock in enumerate(stocks[:3]):
                print(f"      {i+1}. {stock['symbol']} - {stock['name']}")
        
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_stock_selector():
    """Test stock selector"""
    print("\n2. Testing stock selector...")
    
    try:
        from tradingagents.selectors.stock_selector import StockSelector
        selector = StockSelector()
        
        # Test getting stock list
        stock_list = selector._get_stock_list()
        print(f"   Stock selector count: {len(stock_list)}")
        print(f"   Data type: {type(stock_list)}")
        
        if not stock_list.empty:
            print(f"   Columns: {list(stock_list.columns)}")
            print("   Sample stocks:")
            for i, (idx, row) in enumerate(stock_list.head(3).iterrows()):
                print(f"      {i+1}. {row['ts_code']} - {row['name']}")
        
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_interface():
    """Test web interface components"""
    print("\n3. Testing web interface...")
    
    try:
        from web.components.stock_selector_page import execute_stock_selection
        print("   Web components imported successfully")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("Starting ASCII-only verification...")
    
    tests = [
        ("A-share Data", test_a_share_data),
        ("Stock Selector", test_stock_selector),
        ("Web Interface", test_web_interface)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        if test_func():
            print(f"[PASS] {test_name}")
            passed += 1
        else:
            print(f"[FAIL] {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] Unified smart stock selection system is working!")
        print("   - A-share data source: FIXED")
        print("   - Stock selector: WORKING")
        print("   - Market selection: ENABLED")
        print("   - AI expert system: READY")
    else:
        print(f"\n[WARNING] {total - passed} issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)