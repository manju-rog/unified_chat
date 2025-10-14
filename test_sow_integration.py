#!/usr/bin/env python3
"""Test the SOW integration system"""

import sys
import json
from pathlib import Path

# Add the backend to path
sys.path.insert(0, str(Path(__file__).parent / "unified_ai_chat" / "backend"))

from app.services.sow_direct import SowAdapter
from app.sow_components.models import SowState

def test_sow_flow():
    """Test the complete SOW flow"""
    print("🧪 Testing SOW Integration System")
    print("=" * 50)
    
    # Initialize adapter
    adapter = SowAdapter(out_root=Path("unified_ai_chat/output"))
    
    # Test 1: Start session
    print("\n1. Testing session start...")
    question, hint = adapter.start()
    print(f"✅ Question: {question}")
    print(f"✅ Hint: {hint}")
    
    # Test 2: Process through stages
    print("\n2. Testing stage progression...")
    state = SowState()
    
    # Project info
    state, resp = adapter.process(state, "E-commerce platform development for retail client")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Services
    state, resp = adapter.process(state, "standard")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Deliverables
    state, resp = adapter.process(state, "Web application, API documentation, deployment guide")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Timeline
    state, resp = adapter.process(state, "3 months, 6 sprints of 2 weeks each")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Resources
    state, resp = adapter.process(state, "+:Developer")
    print(f"✅ Resources added, Response: {resp.get('message', 'No message')}")
    state, resp = adapter.process(state, "+:Tester")
    print(f"✅ Resources added, Response: {resp.get('message', 'No message')}")
    state, resp = adapter.process(state, "next")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Contacts
    state, resp = adapter.process(state, "client:Acme Corp,contractor:StellarSoft Solutions")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Budget
    state, resp = adapter.process(state, "$50,000 USD, Net 30 payment terms")
    print(f"✅ Stage: {state.stage}, Response: {resp.get('message', 'No message')}")
    
    # Test 3: Generate document
    print("\n3. Testing document generation...")
    result = adapter.finalize(state, session_id="test_session")
    print(f"✅ Generation result: {result}")
    
    # Test 4: Check output
    print("\n4. Checking output...")
    output_dir = Path("unified_ai_chat/output/test_session")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        if files:
            print(f"✅ Document created: {files[0]}")
            print(f"✅ File size: {files[0].stat().st_size} bytes")
        else:
            print("❌ No DOCX file found")
    else:
        print("❌ Output directory not created")
    
    print("\n" + "=" * 50)
    print("🎉 SOW Integration Test Complete!")

if __name__ == "__main__":
    test_sow_flow()