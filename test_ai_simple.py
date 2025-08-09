#!/usr/bin/env python3
"""
Simple test to verify AI expert system is working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_system_status():
    """Test AI system status without Unicode output"""
    print("=" * 60)
    print("AI Expert System Status Check")
    print("=" * 60)
    
    try:
        # Test 1: Import AI modules
        print("\n1. Testing AI module imports...")
        from tradingagents.selectors.stock_selector import StockSelector, AIMode
        from tradingagents.selectors.ai_strategies.ai_strategy_manager import get_ai_strategy_manager
        print("   [OK] AI modules imported successfully")
        
        # Test 2: Initialize AI strategy manager
        print("\n2. Testing AI strategy manager...")
        ai_manager = get_ai_strategy_manager()
        ai_status = ai_manager.get_performance_summary()
        
        if ai_status.get('ai_enabled', False):
            availability = ai_status.get('engine_availability', {})
            available_count = availability.get('available_count', 0)
            total_count = availability.get('total_count', 4)
            print(f"   [OK] AI engines available: {available_count}/{total_count}")
        else:
            print("   [WARN] AI not enabled")
        
        # Test 3: Initialize stock selector
        print("\n3. Testing stock selector...")
        selector = StockSelector(cache_enabled=True)
        
        if selector.ai_strategy_manager:
            print("   [OK] Stock selector AI enhancement enabled")
        else:
            print("   [WARN] Stock selector AI enhancement not available")
        
        # Test 4: Quick select with AI
        print("\n4. Testing AI-enhanced stock selection...")
        try:
            result = selector.quick_select(
                min_score=65.0,
                min_market_cap=50.0,
                max_pe_ratio=30.0,
                grades=['A+', 'A'],
                limit=5
            )
            
            print(f"   [OK] AI selection completed")
            print(f"   [INFO] Found {len(result.symbols)} stocks")
            print(f"   [INFO] Execution time: {result.execution_time:.2f}s")
            
            # Check AI columns
            if hasattr(result, 'data') and not result.data.empty:
                ai_columns = [col for col in result.data.columns if 'ai_' in col]
                if ai_columns:
                    print(f"   [OK] AI analysis columns: {ai_columns}")
                else:
                    print(f"   [INFO] No AI columns found in results")
            
        except Exception as e:
            print(f"   [ERROR] AI selection failed: {str(e)}")
        
        # Test 5: Performance summary
        print("\n5. Testing performance monitoring...")
        try:
            performance = selector.get_ai_performance_summary()
            total_analyses = performance.get('total_analyses', 0)
            cache_hit_rate = performance.get('cache_hit_rate', 0)
            avg_time = performance.get('average_processing_time', 0)
            
            print(f"   [OK] Performance data retrieved")
            print(f"   [INFO] Total analyses: {total_analyses}")
            print(f"   [INFO] Cache hit rate: {cache_hit_rate:.1f}%")
            print(f"   [INFO] Avg processing time: {avg_time:.2f}s")
            
        except Exception as e:
            print(f"   [ERROR] Performance monitoring failed: {str(e)}")
        
        print("\n" + "=" * 60)
        print("AI Expert System Status Check Complete!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] AI system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_system_status()
    sys.exit(0 if success else 1)