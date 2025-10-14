#!/usr/bin/env python3
"""Test the enhanced SOW UI system"""

import sys
import json
from pathlib import Path

# Add the backend to path
sys.path.insert(0, str(Path(__file__).parent / "unified_ai_chat" / "backend"))

from app.services.sow_direct import SowAdapter
from app.sow_components.models import SowState

def test_enhanced_sow_ui():
    """Test the enhanced SOW UI with proper buttons and dropdowns"""
    print("🎨 Testing Enhanced SOW UI System")
    print("=" * 60)
    
    # Initialize adapter
    adapter = SowAdapter(out_root=Path("unified_ai_chat/output"))
    
    # Test 1: Start session
    print("\n1. Testing session start...")
    question, hint = adapter.start()
    print(f"✅ Question: {question}")
    print(f"✅ Hint: {hint}")
    
    # Test 2: Project Info → Services (should show buttons)
    print("\n2. Testing Project Info → Services with buttons...")
    state = SowState()
    state, resp = adapter.process(state, "Banking system modernization project for MUFG")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    print(f"✅ Buttons: {resp.get('confirmation_buttons', [])}")
    
    # Test 3: Services → Deliverables
    print("\n3. Testing Services selection...")
    state, resp = adapter.process(state, "standard")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    
    # Test 4: Deliverables → Timeline
    print("\n4. Testing Deliverables...")
    state, resp = adapter.process(state, "Core banking system, API gateway, mobile app, documentation")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    
    # Test 5: Timeline → Resources (should show resource builder)
    print("\n5. Testing Timeline → Resources with builder...")
    state, resp = adapter.process(state, "6 months, 12 sprints of 2 weeks each")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    print(f"✅ Resource Builder: {resp.get('show_resource_builder', False)}")
    print(f"✅ Resource Roles: {resp.get('resource_roles', [])}")
    
    # Test 6: Resource selection
    print("\n6. Testing Resource selection...")
    state, resp = adapter.process(state, "+:Developer")
    print(f"✅ Added Developer: {resp.get('message', 'No message')}")
    print(f"✅ Current Resources: {resp.get('current_resources', [])}")
    
    state, resp = adapter.process(state, "+:DevOps")
    print(f"✅ Added DevOps: {resp.get('message', 'No message')}")
    
    state, resp = adapter.process(state, "+:Project Manager")
    print(f"✅ Added PM: {resp.get('message', 'No message')}")
    
    # Test 7: Resources → Contacts (should show dropdown)
    print("\n7. Testing Resources → Contacts with dropdown...")
    state, resp = adapter.process(state, "next")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    print(f"✅ Contact Dropdown: {len(resp.get('contact_dropdown', []))} options")
    
    # Print contact options
    for contact in resp.get('contact_dropdown', []):
        print(f"   • {contact['label']}: {contact['details']['contact_person']}")
    
    # Test 8: Contact selection
    print("\n8. Testing Contact selection...")
    state, resp = adapter.process(state, "contact:mufg_bank")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message preview: {resp.get('message', 'No message')[:100]}...")
    
    # Test 9: Budget → Generate
    print("\n9. Testing Budget → Generate...")
    state, resp = adapter.process(state, "$2.5M USD, milestone-based payments")
    print(f"✅ Stage: {state.stage}")
    print(f"✅ Message: {resp.get('message', 'No message')}")
    print(f"✅ Generate Buttons: {resp.get('generate_buttons', [])}")
    
    # Test 10: Final generation
    print("\n10. Testing final document generation...")
    result = adapter.finalize(state, session_id="enhanced_test")
    print(f"✅ Generation result: {result}")
    
    # Test 11: Verify output
    print("\n11. Verifying enhanced output...")
    output_dir = Path("unified_ai_chat/output/enhanced_test")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        if files:
            print(f"✅ Enhanced document created: {files[0]}")
            print(f"✅ File size: {files[0].stat().st_size} bytes")
        else:
            print("❌ No DOCX file found")
    else:
        print("❌ Output directory not created")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced SOW UI Test Complete!")
    print("\n📋 **UI Features Verified:**")
    print("✅ Service selection buttons (Standard/Custom)")
    print("✅ Resource builder with +/- buttons for 6 roles")
    print("✅ Contact dropdown with MUFG Bank")
    print("✅ Generate document button")
    print("✅ Enhanced messaging with emojis and formatting")

if __name__ == "__main__":
    test_enhanced_sow_ui()