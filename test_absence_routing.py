#!/usr/bin/env python3
"""Test absence routing specifically"""

import requests
import json

def test_absence_routing():
    """Test that absence queries are routed correctly"""
    print("🧪 Testing Absence Routing")
    print("=" * 40)
    
    base_url = "http://localhost:8001/api"
    
    # Test absence queries
    absence_queries = [
        "Who is absent today?",
        "Show me absence report",
        "Mark John as absent",
        "Who is on vacation?",
        "Check attendance"
    ]
    
    for i, query in enumerate(absence_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        
        payload = {
            "message": query,
            "session_id": f"test_absence_{i}"
        }
        
        try:
            response = requests.post(f"{base_url}/chat", json=payload, timeout=10)
            data = response.json()
            
            print(f"   Response: {data.get('response', 'No response')[:100]}...")
            print(f"   Action Type: {data.get('action_type', 'None')}")
            print(f"   Intent: {data.get('intent', 'None')}")
            
            # Check if it's properly routed to absence
            if data.get('action_type') and 'absence' in data.get('action_type', ''):
                print("   ✅ Properly routed to absence system")
            elif 'absence_error' in data.get('intent', ''):
                print("   ❌ Absence error - routing failed")
            else:
                print("   ⚠️  Unclear routing")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 40)
    print("Absence routing test complete")

if __name__ == "__main__":
    test_absence_routing()