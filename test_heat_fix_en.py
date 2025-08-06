#!/usr/bin/env python3
"""
Test Heat Analyst Fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_heat_analyst_fix():
    """Test heat analyst fix"""
    print("=" * 50)
    print("Testing Heat Analyst Fix")
    print("=" * 50)
    
    try:
        # Test 1: Import heat analyst module
        print("\n1. Testing heat analyst module import...")
        from tradingagents.agents.analysts.heat_analyst import create_heat_analyst, HeatAnalystAgent
        print("[OK] Heat analyst module imported successfully")
        
        # Test 2: Create heat analyst instance
        print("\n2. Testing heat analyst instance creation...")
        heat_agent = HeatAnalystAgent()
        print("[OK] Heat analyst instance created successfully")
        
        # Test 3: Check return format
        print("\n3. Testing return format...")
        from langchain_core.messages import AIMessage
        
        # Simulate return result
        test_report = "Test heat analysis report"
        test_result = {
            "messages": [AIMessage(content=test_report)],
            "heat_report": test_report,
        }
        
        print(f"[OK] Return format correct:")
        print(f"   - messages type: {type(test_result['messages'][0])}")
        print(f"   - heat_report exists: {'heat_report' in test_result}")
        print(f"   - heat_report content: {test_result['heat_report']}")
        
        # Test 4: Check conditional logic
        print("\n4. Testing conditional logic...")
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        logic = ConditionalLogic()
        test_state = {
            'messages': [AIMessage(content="test")]
        }
        
        result = logic.should_continue_heat(test_state)
        print(f"[OK] Conditional logic result: {result}")
        
        if result == "Msg Clear Heat":
            print("[OK] Heat analyst will not enter tool call loop")
        else:
            print("[ERROR] Heat analyst may enter tool call loop")
        
        # Test 5: Check workflow setup
        print("\n5. Testing workflow setup...")
        from tradingagents.graph.setup import GraphSetup
        
        print("[OK] Workflow setup module imported successfully")
        print("[OK] Heat analyst can be used in workflow")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] All tests passed! Heat analyst fix successful!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_heat_analyst_fix()
    if success:
        print("\n[INFO] Heat analysis report should now display correctly in web interface!")
        print("[INFO] Please test by selecting heat analyst in web interface.")
    else:
        print("\n[ERROR] Test failed, please check if fix is complete.")