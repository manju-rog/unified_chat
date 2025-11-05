"""
Test full SOW generation flow with sample data
"""

import asyncio
import aiohttp
import json

# Test data
test_data = {
    "project_info": "SOW-2024-001, E-commerce Platform Migration, Migrate legacy system to cloud, improve performance 50%, reduce costs 30%, enhance security compliance",
    "services": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
    "deliverables": "DELIVERABLES: Technical Architecture Document, Migration Plan, Migrated Platform, Test Reports, Training Materials, Go-Live Support",
    "timeline": "TIMELINE: Start 2024-11-01, End 2025-04-30, 12 sprints of 2 weeks each",
    "resources": [
        {"role": "Project Manager", "count": 1},
        {"role": "Senior Developer", "count": 2},
        {"role": "DevOps Engineer", "count": 1},
        {"role": "QA Engineer", "count": 1},
        {"role": "Business Analyst", "count": 1}
    ],
    "contacts": {
        "name": "RetailCorp Ltd.",
        "contact_person": "Sarah Johnson",
        "designation": "IT Director",
        "department": "Technology",
        "email": "sarah.johnson@retailcorp.com",
        "phone": "+1-555-0456",
        "address": "456 Business Ave NY NY"
    },
    "budget": "BUDGET: Discovery $25k + $2k expenses, Migration $40k + $3.5k expenses, Development $120k + $8k expenses, Testing $30k + $2.5k expenses, Deployment $20k + $1.5k expenses"
}

async def test_sow_generation():
    """Test SOW generation via unified_ai_chat API"""
    
    print("=" * 80)
    print("TESTING FULL SOW GENERATION")
    print("=" * 80)
    print()
    
    # Convert resources to string format
    resources_str = ""
    for r in test_data["resources"]:
        role = r["role"]
        count = r["count"]
        resources_str += f"{role} - {count} person{'s' if count > 1 else ''} - 100% allocation\\n"
    
    # Convert contacts to string format
    contacts = test_data["contacts"]
    contacts_str = f"""Contractor Contact:
Name: Professional Services Team
Company: Professional Services Inc.
Role: Project Director
Email: pm@company.com
Phone: +1-555-0123
Address: 123 Business St, City, State

Client Contact:
Name: {contacts['contact_person']}
Company: {contacts['name']}
Role: {contacts['designation']}
Email: {contacts['email']}
Phone: {contacts['phone']}
Address: {contacts['address']}"""
    contacts_str = contacts_str.replace('\n', '\\n')
    
    # Prepare payload
    payload = {
        "template_path": "sample_sow_template.docx",
        "project_data": {
            "project_info": test_data["project_info"],
            "services": test_data["services"],
            "deliverables": test_data["deliverables"],
            "timeline": test_data["timeline"],
            "resources": resources_str,
            "contacts": contacts_str,
            "budget": test_data["budget"]
        },
        "session_id": "test_full_generation_001"
    }
    
    print("📤 Sending request to new_sow API...")
    print(f"   URL: http://localhost:8002/api/generate-direct")
    print(f"   Session ID: {payload['session_id']}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8002/api/generate-direct",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                print(f"📊 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print()
                    print("✅ SUCCESS! Document generated!")
                    print("=" * 80)
                    print(f"Session ID: {result.get('session_id')}")
                    print(f"Filename: {result.get('filename')}")
                    print(f"Download URL: {result.get('download_url')}")
                    print(f"Message: {result.get('message')}")
                    print()
                    
                    # Check if file exists
                    import os
                    filename = result.get('filename', '')
                    if filename:
                        file_path = f"use_sow/output/{filename}"
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path) / 1024
                            print(f"✅ File exists: {file_path}")
                            print(f"📊 File size: {file_size:.2f} KB")
                        else:
                            print(f"⚠️  File not found: {file_path}")
                    
                    print("=" * 80)
                    return True
                else:
                    error_text = await response.text()
                    print()
                    print("❌ FAILED!")
                    print("=" * 80)
                    print(f"Status: {response.status}")
                    print(f"Error: {error_text}")
                    print("=" * 80)
                    return False
                    
    except Exception as e:
        print()
        print("❌ ERROR!")
        print("=" * 80)
        print(f"Exception: {e}")
        print("=" * 80)
        return False

if __name__ == "__main__":
    print()
    print("🚀 Starting SOW Generation Test")
    print()
    
    success = asyncio.run(test_sow_generation())
    
    if success:
        print()
        print("✅ Test completed successfully!")
        print("📁 Check use_sow/output/ for the generated document")
    else:
        print()
        print("❌ Test failed!")
        print("💡 Make sure use_sow is running on port 8002")
    print()
