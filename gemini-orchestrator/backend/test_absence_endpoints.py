"""
Test script for Absence tool endpoints.
Verifies all endpoints work correctly.
"""

import asyncio
from datetime import datetime
from app.tools_absence import mark_absent, mark_present, get_absence_status, absence_storage
from app.models import AbsenceRequest, PresenceRequest


async def test_absence_endpoints():
    """Test all absence endpoints"""
    
    print("=" * 60)
    print("Testing Absence Tool Endpoints")
    print("=" * 60)
    
    # Clear storage
    absence_storage.clear()
    
    # Test 1: Mark employee absent
    print("\n1. Testing mark_absent endpoint...")
    request1 = AbsenceRequest(
        employee_id="manju",
        date="2025-10-05",
        reason="Sick leave"
    )
    result1 = await mark_absent(request1)
    print(f"   Result: {result1}")
    assert result1["ok"] == True
    assert "manju" in result1["message"]
    print("   ✓ mark_absent works correctly")
    
    # Test 2: Check absence status (should be absent)
    print("\n2. Testing get_absence_status endpoint (absent)...")
    result2 = await get_absence_status("manju", "2025-10-05")
    print(f"   Result: {result2}")
    assert result2["status"] == "absent"
    assert result2["reason"] == "Sick leave"
    print("   ✓ get_absence_status returns absent correctly")
    
    # Test 3: Mark employee present
    print("\n3. Testing mark_present endpoint...")
    request3 = PresenceRequest(
        employee_id="manju",
        date="2025-10-05"
    )
    result3 = await mark_present(request3)
    print(f"   Result: {result3}")
    assert result3["ok"] == True
    print("   ✓ mark_present works correctly")
    
    # Test 4: Check absence status (should be present now)
    print("\n4. Testing get_absence_status endpoint (present)...")
    result4 = await get_absence_status("manju", "2025-10-05")
    print(f"   Result: {result4}")
    assert result4["status"] == "present"
    print("   ✓ get_absence_status returns present correctly")
    
    # Test 5: Mark absent without reason
    print("\n5. Testing mark_absent without reason...")
    request5 = AbsenceRequest(
        employee_id="john",
        date="2025-10-06"
    )
    result5 = await mark_absent(request5)
    print(f"   Result: {result5}")
    assert result5["ok"] == True
    print("   ✓ mark_absent works without reason")
    
    # Test 6: Check status with default date (today)
    print("\n6. Testing get_absence_status with default date...")
    today = datetime.now().strftime("%Y-%m-%d")
    result6 = await get_absence_status("sarah", None)
    print(f"   Result: {result6}")
    assert result6["date"] == today
    assert result6["status"] == "present"
    print("   ✓ get_absence_status uses today's date by default")
    
    # Test 7: Verify storage state
    print("\n7. Verifying storage state...")
    print(f"   Storage contains {len(absence_storage)} records")
    for key, value in absence_storage.items():
        print(f"   - {key}: {value}")
    assert len(absence_storage) == 1  # Only john's record should remain
    print("   ✓ Storage state is correct")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_absence_endpoints())
