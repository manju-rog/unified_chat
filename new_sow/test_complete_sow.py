#!/usr/bin/env python3
"""Test complete SOW generation with new_sow backend"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

# SOW Data
sow_data = {
    "project_info": {
        "project_id": "SOW-2024-001",
        "project_name": "E-commerce Platform Migration",
        "description": "Migrate legacy system to cloud, improve performance 50%, reduce costs 30%, enhance security compliance"
    },
    "services": [
        {"name": "Discovery & Planning", "duration": "3 weeks"},
        {"name": "Data Migration", "duration": "4 weeks"},
        {"name": "Application Development", "duration": "8 weeks"},
        {"name": "Testing & QA", "duration": "2 weeks"},
        {"name": "Deployment & Go-Live", "duration": "1 week"}
    ],
    "deliverables": [
        "Technical Architecture Document",
        "Migration Plan",
        "Migrated Platform",
        "Test Reports",
        "Training Materials",
        "Go-Live Support"
    ],
    "timeline": {
        "start_date": "2024-11-01",
        "end_date": "2025-04-30",
        "sprints": "12 sprints of 2 weeks each"
    },
    "resources": [
        {"role": "Project Manager", "count": 1, "allocation": "100%"},
        {"role": "Senior Developer", "count": 2, "allocation": "100%"},
        {"role": "DevOps Engineer", "count": 1, "allocation": "75%"},
        {"role": "QA Engineer", "count": 1, "allocation": "100%"},
        {"role": "Business Analyst", "count": 1, "allocation": "50%"}
    ],
    "contacts": {
        "contractor": {
            "name": "John Smith",
            "title": "Project Director",
            "company": "TechSolutions Inc.",
            "email": "john.smith@techsolutions.com",
            "phone": "+1-555-0123",
            "address": "123 Tech Street SF CA"
        },
        "client": {
            "name": "Sarah Johnson",
            "title": "IT Director",
            "company": "RetailCorp Ltd.",
            "email": "sarah.johnson@retailcorp.com",
            "phone": "+1-555-0456",
            "address": "456 Business Ave NY NY"
        }
    },
    "budget": {
        "discovery": {"cost": 25000, "expenses": 2000},
        "migration": {"cost": 40000, "expenses": 3500},
        "development": {"cost": 120000, "expenses": 8000},
        "testing": {"cost": 30000, "expenses": 2500},
        "deployment": {"cost": 20000, "expenses": 1500}
    }
}

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        print(f"✅ Root endpoint: {data['application']} v{data['version']}")
        print(f"   Available endpoints: {list(data['endpoints'].keys())}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_direct_generation():
    """Test direct SOW generation"""
    print("\n🔍 Testing direct SOW generation...")
    print("📝 Sending SOW data...")
    
    # Prepare request in the format expected by the API
    request_data = {
        "session_id": f"test_{int(time.time())}",
        "template_path": "sample_sow_template.docx",
        "project_data": {
            "project_info": f"Project ID: {sow_data['project_info']['project_id']}, Name: {sow_data['project_info']['project_name']}, Description: {sow_data['project_info']['description']}",
            "services": ", ".join([f"{s['name']} ({s['duration']})" for s in sow_data['services']]),
            "deliverables": ", ".join(sow_data['deliverables']),
            "timeline": f"Start: {sow_data['timeline']['start_date']}, End: {sow_data['timeline']['end_date']}, {sow_data['timeline']['sprints']}",
            "resources": ", ".join([f"{r['role']}: {r['count']} at {r['allocation']}" for r in sow_data['resources']]),
            "contacts": f"Contractor: {sow_data['contacts']['contractor']['name']}, {sow_data['contacts']['contractor']['title']}, {sow_data['contacts']['contractor']['company']}, {sow_data['contacts']['contractor']['email']}, {sow_data['contacts']['contractor']['phone']}, {sow_data['contacts']['contractor']['address']}. Client: {sow_data['contacts']['client']['name']}, {sow_data['contacts']['client']['title']}, {sow_data['contacts']['client']['company']}, {sow_data['contacts']['client']['email']}, {sow_data['contacts']['client']['phone']}, {sow_data['contacts']['client']['address']}",
            "budget": f"Discovery: ${sow_data['budget']['discovery']['cost']:,} + ${sow_data['budget']['discovery']['expenses']:,} expenses, Migration: ${sow_data['budget']['migration']['cost']:,} + ${sow_data['budget']['migration']['expenses']:,} expenses, Development: ${sow_data['budget']['development']['cost']:,} + ${sow_data['budget']['development']['expenses']:,} expenses, Testing: ${sow_data['budget']['testing']['cost']:,} + ${sow_data['budget']['testing']['expenses']:,} expenses, Deployment: ${sow_data['budget']['deployment']['cost']:,} + ${sow_data['budget']['deployment']['expenses']:,} expenses"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-direct",
            json=request_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation successful!")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Document: {result.get('document_path')}")
            print(f"   Status: {result.get('status')}")
            
            if result.get('download_url'):
                print(f"   Download URL: {result.get('download_url')}")
            
            return result
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None

def main():
    print("=" * 60)
    print("🚀 Testing new_sow Backend (Port 8002)")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Backend not responding. Make sure it's running on port 8002")
        return
    
    # Test root
    test_root()
    
    # Test direct generation
    print("\n" + "=" * 60)
    print("📄 SOW Generation Test")
    print("=" * 60)
    
    result = test_direct_generation()
    
    if result:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\n📥 Document generated successfully!")
        print(f"   Check the output directory for the generated SOW document")
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)

if __name__ == "__main__":
    main()
