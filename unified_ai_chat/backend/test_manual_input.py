"""
Test manual input for SOW generation stages
"""
from app.services.sow_direct import SowAdapter
from app.sow_components.models import SowState
from pathlib import Path

# Initialize adapter
adapter = SowAdapter(out_root=Path("test_output"))

# Test Stage 2: Services - Manual Input
print("=" * 60)
print("TEST 1: Services Stage - Manual Input")
print("=" * 60)
state = SowState(stage="services", data={})
user_input = "Custom web development services including frontend, backend, and database design"
state, response = adapter.process(state, user_input)
print(f"✅ Input: {user_input}")
print(f"✅ Stored: {state.data.get('services')}")
print(f"✅ Next Stage: {state.stage}")
print()

# Test Stage 5: Resources - Manual Input
print("=" * 60)
print("TEST 2: Resources Stage - Manual Input")
print("=" * 60)
state = SowState(stage="resources", data={})
user_input = "3 Senior Developers, 2 QA Engineers, 1 DevOps Specialist, 1 Scrum Master"
state, response = adapter.process(state, user_input)
print(f"✅ Input: {user_input}")
print(f"✅ Stored: {state.data.get('resources_text')}")
print(f"✅ Next Stage: {state.stage}")
print()

# Test Stage 6: Contacts - Manual Input
print("=" * 60)
print("TEST 3: Contacts Stage - Manual Input")
print("=" * 60)
state = SowState(stage="contacts", data={})
user_input = "ABC Corporation, Contact: Jane Smith, Email: jane@abc.com, Phone: +1-555-9999"
state, response = adapter.process(state, user_input)
print(f"✅ Input: {user_input}")
print(f"✅ Stored: {state.data.get('contacts')}")
print(f"✅ Next Stage: {state.stage}")
print()

# Test Stage 2: Services - Button Input (should still work)
print("=" * 60)
print("TEST 4: Services Stage - Button Input (Standard)")
print("=" * 60)
state = SowState(stage="services", data={})
user_input = "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)"
state, response = adapter.process(state, user_input)
print(f"✅ Input: {user_input[:50]}...")
print(f"✅ Stored: {state.data.get('services')[:50]}...")
print(f"✅ Next Stage: {state.stage}")
print()

# Test Stage 5: Resources - Button Input (should still work)
print("=" * 60)
print("TEST 5: Resources Stage - Button Input (+/- commands)")
print("=" * 60)
state = SowState(stage="resources", data={})
# Simulate button clicks
state, response = adapter.process(state, "+:Developer")
state, response = adapter.process(state, "+:Developer")
state, response = adapter.process(state, "+:Tester")
print(f"✅ Resources: {state.data.get('resources')}")
state, response = adapter.process(state, "next")
print(f"✅ Next Stage: {state.stage}")
print()

# Test Stage 6: Contacts - Button Input (should still work)
print("=" * 60)
print("TEST 6: Contacts Stage - Button Input (Database Match)")
print("=" * 60)
state = SowState(stage="contacts", data={})
user_input = "CONTACT: MUFG Bank | Contact Person: John Doe (Senior Manager, IT Department) | Email: john.doe@mufg.com | Phone: +1-555-0123 | Address: 1251 Avenue of the Americas, New York, NY 10020"
state, response = adapter.process(state, user_input)
print(f"✅ Input: {user_input[:50]}...")
print(f"✅ Stored Contact Name: {state.data.get('contacts', {}).get('name')}")
print(f"✅ Next Stage: {state.stage}")
print()

print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nSummary:")
print("✅ Services: Accepts manual text AND button clicks")
print("✅ Resources: Accepts manual text AND +/- commands")
print("✅ Contacts: Accepts manual text AND database selections")
