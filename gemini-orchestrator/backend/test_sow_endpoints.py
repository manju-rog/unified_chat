"""
Test script for SOW tool endpoints.
Run with: python test_sow_endpoints.py
"""

import asyncio
from app.tools_sow import start_sow, update_sow, generate_sow
from app.models import SowStart, SowUpdate, ContactInfo, ServiceItem, DeliverableItem


async def test_sow_endpoints():
    """Test all SOW endpoints"""
    
    print("=" * 60)
    print("Testing SOW Tool Endpoints")
    print("=" * 60)
    
    # Test 1: Start SOW
    print("\n1. Testing start_sow endpoint...")
    start_request = SowStart(project_name="Predictive Maintenance System")
    start_result = await start_sow(start_request)
    print(f"Result: {start_result}")
    
    if not start_result.get("ok"):
        print("❌ Failed to start SOW")
        return
    
    sow_id = start_result.get("sow_id")
    print(f"✅ SOW started with ID: {sow_id}")
    
    # Test 2: Update SOW
    print("\n2. Testing update_sow endpoint...")
    
    oracle_rep = ContactInfo(
        name="John Smith",
        email="john.smith@oracle.com",
        phone="+1-555-0100",
        address="500 Oracle Parkway, Redwood City, CA"
    )
    
    billing_contact = ContactInfo(
        name="Jane Doe",
        email="jane.doe@company.com",
        phone="+1-555-0200"
    )
    
    services = [
        ServiceItem(
            name="AI Model Development",
            description="Develop and train predictive maintenance models using machine learning"
        ),
        ServiceItem(
            name="System Integration",
            description="Integrate AI models with existing maintenance management systems"
        )
    ]
    
    deliverables = [
        DeliverableItem(
            name="Trained ML Models",
            description="Production-ready machine learning models for predictive maintenance"
        ),
        DeliverableItem(
            name="Integration Documentation",
            description="Complete technical documentation for system integration"
        )
    ]
    
    acceptance_criteria = "All models must achieve 95% accuracy on test data and integrate seamlessly with existing systems."
    
    update_request = SowUpdate(
        sow_id=sow_id,
        oracle_rep=oracle_rep,
        billing_contact=billing_contact,
        services=services,
        deliverables=deliverables,
        acceptance=acceptance_criteria
    )
    
    update_result = await update_sow(update_request)
    print(f"Result: {update_result}")
    
    if update_result.get("ok"):
        print("✅ SOW updated successfully")
    else:
        print("❌ Failed to update SOW")
        return
    
    # Test 3: Generate SOW
    print("\n3. Testing generate_sow endpoint...")
    generate_result = await generate_sow(sow_id)
    print(f"Result: {generate_result}")
    
    if generate_result.get("ok"):
        print(f"✅ SOW document generated: {generate_result.get('url')}")
        print(f"   File location: /tmp/{sow_id}.docx")
    else:
        print(f"❌ Failed to generate SOW: {generate_result.get('reason')}")
    
    # Test 4: Test error handling - invalid SOW ID
    print("\n4. Testing error handling with invalid SOW ID...")
    invalid_update = SowUpdate(
        sow_id="invalid-id-12345",
        oracle_rep=oracle_rep
    )
    error_result = await update_sow(invalid_update)
    print(f"Result: {error_result}")
    
    if not error_result.get("ok"):
        print("✅ Error handling works correctly")
    else:
        print("❌ Error handling failed")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sow_endpoints())
