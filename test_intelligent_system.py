#!/usr/bin/env python3
"""Test the enhanced intelligent system with smart reasoning"""

import requests
import json

def test_intelligent_system():
    """Test intelligent system with various edge cases"""
    print("🧠 Testing Intelligent System with AI Reasoning")
    print("=" * 60)
    
    base_url = "http://localhost:8001/api"
    
    # Test cases that should show intelligent behavior
    test_cases = [
        {
            "query": "Show this month's absences",
            "expected": "Should show October 2025 absences with reasoning"
        },
        {
            "query": "Who is absent today?", 
            "expected": "Should show today's (2025-10-14) absences"
        },
        {
            "query": "Current month absence report",
            "expected": "Should interpret as October 2025"
        },
        {
            "query": "Create a SOW",
            "expected": "Should switch to SOW mode with red theme"
        },
        {
            "query": "Help me with both absence and SOW",
            "expected": "Should provide intelligent guidance"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test['query']}'")
        print(f"   Expected: {test['expected']}")
        
        payload = {
            "message": test['query'],
            "session_id": f"intelligent_test_{i}"
        }
        
        try:
            response = requests.post(f"{base_url}/chat", json=payload, timeout=15)
            data = response.json()
            
            response_text = data.get('response', '')
            action_type = data.get('action_type', 'None')
            
            print(f"   Response: {response_text[:150]}...")
            print(f"   Action: {action_type}")
            
            # Check for intelligent features
            has_reasoning = '💭' in response_text or '*' in response_text
            has_mode_indicator = '🔵' in response_text or '🔴' in response_text
            
            if has_reasoning:
                print("   ✅ Shows AI reasoning")
            if has_mode_indicator:
                print("   ✅ Has mode indicator")
            if 'October 2025' in response_text or '2025-10' in response_text:
                print("   ✅ Smart date interpretation")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Intelligent System Test Complete!")

if __name__ == "__main__":
    test_intelligent_system()