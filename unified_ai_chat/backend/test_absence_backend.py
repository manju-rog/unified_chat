"""Test script to verify absence backend is working."""
import asyncio
import httpx
from datetime import date

async def test_backend():
    """Test if the absence backend is responding correctly."""
    base_url = "http://localhost:8010/api"
    
    print("🔍 Testing Absence Backend Connection...")
    print(f"Base URL: {base_url}\n")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Test 1: Get employees
        print("1️⃣ Testing GET /ai/employees")
        try:
            response = await client.get("/ai/employees")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                employees = data.get("data", [])
                print(f"   ✅ Found {len(employees)} employees")
                if employees:
                    print(f"   Sample: {employees[0].get('name')} (ID: {employees[0].get('id')})")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
        
        print()
        
        # Test 2: Mark absence
        print("2️⃣ Testing POST /ai/mark-absence")
        try:
            payload = {
                "employeeId": 3,  # Ganesh
                "dates": [date.today().isoformat()],
                "status": "A",
                "reason": "Test absence"
            }
            print(f"   Payload: {payload}")
            response = await client.post("/ai/mark-absence", json=payload)
            print(f"   Status: {response.status_code}")
            if response.status_code < 400:
                data = response.json()
                print(f"   ✅ Response: {data}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        
        # Test 3: Query today's absences
        print("3️⃣ Testing GET /absences/calendar/day-details")
        try:
            today = date.today().isoformat()
            response = await client.get("/absences/calendar/day-details", params={"date": today})
            print(f"   Date: {today}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response: {data}")
                employees = data.get("employees", {})
                absent = employees.get("A", [])
                if absent:
                    print(f"   📊 Absent today: {[emp.get('name') for emp in absent]}")
                else:
                    print(f"   📊 No absences recorded for today")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        print("=" * 60)
        print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_backend())
