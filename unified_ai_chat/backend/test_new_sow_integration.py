"""
Test script to verify new_sow integration with unified_ai_chat
Tests the conversion and generation with sample data
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.new_sow_adapter import new_sow_adapter
from app.sow_components.models import SowState

# Test data matching the user's input
test_data = {
    "project_info": "SOW-2024-001, E-commerce Platform Migration, Migrate legacy system to cloud, improve performance 50%, reduce costs 30%, enhance security compliance",
    
    "services": "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)",
    
    "deliverables": "Technical Architecture Document, Migration Plan, Migrated Platform, Test Reports, Training Materials, Go-Live Support",
    
    "timeline": "Start 2024-11-01, End 2025-04-30, 12 sprints of 2 weeks each",
    
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
    
    "budget": "Discovery $25k + $2k expenses, Migration $40k + $3.5k expenses, Development $120k + $8k expenses, Testing $30k + $2.5k expenses, Deployment $20k + $1.5k expenses. Total: $235k project fee + $17.5k expenses"
}

async def test_conversion():
    """Test the data conversion"""
    print("=" * 80)
    print("TESTING NEW_SOW INTEGRATION - DATA CONVERSION")
    print("=" * 80)
    print()
    
    # Convert data
    print("📋 Converting unified_chat data to new_sow format...")
    sow_context = new_sow_adapter._convert_to_new_sow_format(test_data)
    
    print("\n✅ CONVERSION RESULTS:")
    print("-" * 80)
    
    print("\n1️⃣  PROJECT INFO:")
    print(f"   Document Number: {sow_context['project_info']['document_number']}")
    print(f"   Project Name: {sow_context['project_info']['project_name']}")
    print(f"   Objectives: {len(sow_context['project_info']['objectives'])} items")
    
    print("\n2️⃣  SERVICES:")
    for idx, service in enumerate(sow_context['services'], 1):
        print(f"   {idx}. {service['name']} - {service['duration']}")
    
    print("\n3️⃣  DELIVERABLES:")
    for deliv in sow_context['deliverables']:
        print(f"   {deliv['id']}. {deliv['name']} (Sprints {deliv['sprint_start']}-{deliv['sprint_end']})")
    
    print("\n4️⃣  TIMELINE:")
    print(f"   Start: {sow_context['timeline']['start_date']}")
    print(f"   End: {sow_context['timeline']['end_date']}")
    print(f"   Total Sprints: {sow_context['timeline']['total_sprints']}")
    print(f"   Sprint Duration: {sow_context['timeline']['sprint_duration']}")
    
    print("\n5️⃣  RESOURCES:")
    for resource in sow_context['resources']:
        print(f"   • {resource['role']}: {resource['count']} person(s) @ {resource['allocation']}")
    
    print("\n6️⃣  CONTACTS:")
    print(f"   Contractor: {sow_context['contractor_contact']['name']} ({sow_context['contractor_contact']['email']})")
    print(f"   Client: {sow_context['client_contact']['name']} ({sow_context['client_contact']['email']})")
    
    print("\n7️⃣  BUDGET:")
    print(f"   Total Fee: ${sow_context['total_fee']:,.2f}")
    print(f"   Milestones:")
    for milestone in sow_context['milestones']:
        print(f"      {milestone['id']}. {milestone['name']}: ${milestone['fee']:,.2f}")
    
    print("\n" + "=" * 80)
    return sow_context

async def test_generation():
    """Test the full generation process"""
    print("\n" + "=" * 80)
    print("TESTING NEW_SOW INTEGRATION - DOCUMENT GENERATION")
    print("=" * 80)
    print()
    
    # Check if new_sow is running
    print("🔍 Checking if new_sow application is running...")
    is_healthy = await new_sow_adapter._check_new_sow_health()
    
    if not is_healthy:
        print("❌ new_sow application is NOT running on port 8002")
        print("\n💡 To start new_sow:")
        print("   cd new_sow")
        print("   python -m uvicorn app.main:app --port 8002 --reload")
        return None
    
    print("✅ new_sow application is running and healthy!")
    print()
    
    # Generate document
    print("📄 Generating SOW document via new_sow...")
    session_id = "test_integration_001"
    
    result = await new_sow_adapter.generate_sow_document(test_data, session_id)
    
    if result["success"]:
        print("\n✅ DOCUMENT GENERATED SUCCESSFULLY!")
        print("-" * 80)
        print(f"   Filename: {result['filename']}")
        print(f"   Download URL: {result['download_url']}")
        print(f"   Message: {result['message']}")
        print()
        
        # Check if file exists in generated_docs_sow
        project_root = Path(__file__).resolve().parents[2]
        doc_path = project_root / "generated_docs_sow" / result['filename']
        
        if doc_path.exists():
            file_size = doc_path.stat().st_size / 1024  # KB
            print(f"   ✅ File exists in generated_docs_sow/")
            print(f"   📊 File size: {file_size:.2f} KB")
            print(f"   📁 Full path: {doc_path}")
        else:
            print(f"   ⚠️  File not found in generated_docs_sow/")
            
            # Check new_sow/output
            new_sow_path = project_root / "new_sow" / "output" / result['filename']
            if new_sow_path.exists():
                print(f"   ℹ️  File found in new_sow/output/")
                print(f"   📁 Path: {new_sow_path}")
    else:
        print("\n❌ DOCUMENT GENERATION FAILED!")
        print("-" * 80)
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Message: {result.get('message', 'No message')}")
    
    print("\n" + "=" * 80)
    return result

async def main():
    """Run all tests"""
    print("\n🚀 Starting new_sow Integration Tests\n")
    
    # Test 1: Data conversion
    sow_context = await test_conversion()
    
    # Test 2: Document generation
    result = await test_generation()
    
    print("\n✅ All tests completed!")
    print("\nNext steps:")
    print("1. Check the generated document in generated_docs_sow/")
    print("2. Compare with documents from new_sow/output/")
    print("3. Verify all fields are properly populated")
    print()

if __name__ == "__main__":
    asyncio.run(main())
