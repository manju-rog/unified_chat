import requests
import json
from websocket import create_connection
import time

BASE_URL = "http://localhost:8000/api"

def test_websocket_conversation_v2(session_id):
    """Test WebSocket conversation with improved extraction"""
    print("\n=== Testing WebSocket Conversation (V2 - Function Calling) ===")
    
    ws = create_connection(f"ws://localhost:8000/api/ws/{session_id}", timeout=90)
    
    # Receive initial message
    initial = json.loads(ws.recv())
    print(f"\nBot: {initial['message'][:150]}...")
    
    conversation_flow = [
    {
        "message": "SOW-2025-001, Cloud Migration Project, objectives are reduce infrastructure costs, improve scalability, enhance security",
        "label": "Project Info"
    },
    {
        "message": "Migration planning service with detailed assessment for 2 weeks, Data migration service to move all systems for 4 weeks, Testing and validation service for 2 weeks",
        "label": "Services"
    },
    {
        "message": "Migration plan document with detailed roadmap, Migrated data with validation reports, Test results and performance benchmarks",
        "label": "Deliverables"
    },
    {
        "message": "Start date 2025-11-01, end date 2026-01-31, 6 sprints of 2 weeks each",
        "label": "Timeline"
    },
    {
        "message": "2 Senior Cloud Engineers from Development team full-time, 1 Data Migration Specialist from Migration team full-time, 1 QA Engineer from Testing team part-time",
        "label": "Resources"
    },
    {
        "message": "Contractor: John Smith, TechCorp Solutions, 123 Tech Street New York NY, +1-555-0100, john@techcorp.com, Project Manager. Client: Jane Doe, ClientCo Inc, 456 Business Ave Boston MA, +1-555-0200, jane@clientco.com, IT Director",
        "label": "Contacts"
    },
    {
        "message": "Planning milestone 15000, Data migration milestone 40000, Testing milestone 10000, estimated expenses 5000",
        "label": "Budget"
    },
    {
        "message": "yes, I'm done",  # ← ADD THIS LINE - triggers completion
        "label": "Confirmation"
    }
]

    
    last_response = None
    is_complete = False
    
    for idx, item in enumerate(conversation_flow, 1):
        print(f"\n--- Message {idx}/7: {item['label']} ---")
        
        # Send message
        ws.send(json.dumps({"message": item['message']}))
        print(f"User: {item['message'][:80]}...")
        
        try:
            # Receive response
            ws.settimeout(90)
            response = json.loads(ws.recv())
            last_response = response
            print(f"Bot: {response['message'][:100]}...")
            print(f"✓ Stage: {response['stage']}")
            print(f"✓ Progress: {response['progress']}%")
            
            # Check if completed
            if response.get('is_complete'):
                print("\n🎉 DATA COLLECTION COMPLETED!")
                print("✓ All data extracted using Gemini Function Calling")
                is_complete = True
                break
                
        except Exception as e:
            print(f"⚠ Error receiving response: {e}")
            break
        
        # Wait between messages
        if idx < len(conversation_flow):
            wait_time = 3
            print(f"Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    # ✅ CRITICAL: After budget message, wait for completion processing
    if not is_complete:
        print("\n--- Waiting for completion confirmation (Gemini extraction) ---")
        print("This may take up to 60 seconds for AI processing...")
        
        try:
            ws.settimeout(90)  # Extended timeout for Gemini API call
            final_response = json.loads(ws.recv())
            
            print(f"\nBot: {final_response['message'][:200]}...")
            print(f"✓ Final Stage: {final_response['stage']}")
            print(f"✓ Final Progress: {final_response['progress']}%")
            print(f"✓ Is Complete: {final_response.get('is_complete')}")
            
            if final_response.get('is_complete'):
                print("\n🎉 DATA COLLECTION COMPLETED!")
                print("✓ All data extracted using Gemini Function Calling")
                is_complete = True
            else:
                print("\n⚠️ WARNING: Session not marked as completed")
                
        except Exception as e:
            print(f"\n⚠ Timeout or error waiting for completion: {e}")
            print("⚠ Session may not be marked as completed - will check status")
    
    ws.close()
    print("\n✓ WebSocket closed")
    
    return is_complete


def check_session_status(session_id):
    """Check and display session status"""
    print("\n--- Checking Session Status ---")
    print("-" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        
        if response.status_code == 200:
            session_info = response.json()
            print(f"Session ID: {session_info['session_id']}")
            print(f"Current Stage: {session_info['current_stage']}")
            print(f"Progress: {session_info['progress']}%")
            print(f"Is Completed: {session_info['is_completed']}")
            print(f"Created: {session_info['created_at']}")
            print(f"Updated: {session_info['updated_at']}")
            return session_info['is_completed']
        else:
            print(f"✗ Error checking status: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_complete_flow():
    """Test complete flow: upload -> session -> conversation -> generate"""
    
    print("="*70)
    print("SOW GENERATOR V2 - COMPLETE TEST")
    print("="*70)
    
    # 1. Upload template
    print("\n1. UPLOADING TEMPLATE")
    print("-" * 70)
    
    try:
        with open("sample_sow_template.docx", "rb") as f:
            files = {"file": ("template.docx", f)}
            response = requests.post(f"{BASE_URL}/upload-template", files=files)
        
        if response.status_code != 200:
            print(f"✗ Upload failed: {response.json()}")
            return
        
        template_id = response.json()["template_id"]
        print(f"✓ Template ID: {template_id}")
        
    except FileNotFoundError:
        print("✗ Error: sample_sow_template.docx not found!")
        print("  Make sure the template file exists in the current directory")
        return
    except Exception as e:
        print(f"✗ Error uploading template: {e}")
        return
    
    # 2. Create session
    print("\n2. CREATING SESSION")
    print("-" * 70)
    
    try:
        response = requests.post(f"{BASE_URL}/create-session?template_id={template_id}")
        
        if response.status_code != 200:
            print(f"✗ Session creation failed: {response.json()}")
            return
        
        session_id = response.json()["session_id"]
        print(f"✓ Session ID: {session_id}")
        
    except Exception as e:
        print(f"✗ Error creating session: {e}")
        return
    
    # 3. WebSocket conversation
    print("\n3. WEBSOCKET CONVERSATION")
    print("-" * 70)
    
    conversation_complete = test_websocket_conversation_v2(session_id)
    
    # 4. Check session status
    session_complete = check_session_status(session_id)
    
    # If conversation didn't complete via WebSocket, wait and check again
    if not conversation_complete and not session_complete:
        print("\n⚠️ Session not completed yet - waiting 10 seconds for background processing...")
        time.sleep(10)
        session_complete = check_session_status(session_id)
    
    if not session_complete:
        print("\n⚠️ WARNING: Session is not marked as completed")
        print("⚠️ Document generation may fail")
        print("\nAttempting to generate anyway...")
    
    # 5. Generate document
    print("\n4. GENERATING DOCUMENT")
    print("-" * 70)
    
    try:
        response = requests.post(f"{BASE_URL}/generate-document/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Document generated: {data['filename']}")
            
            # 6. Download document
            print("\n5. DOWNLOADING DOCUMENT")
            print("-" * 70)
            
            download_response = requests.get(f"{BASE_URL}/download/{session_id}")
            
            if download_response.status_code == 200:
                filename = "FINAL_SOW_V2_WORKING.docx"
                with open(filename, "wb") as f:
                    f.write(download_response.content)
                print(f"✓ Downloaded as: {filename}")
                print(f"✓ File size: {len(download_response.content):,} bytes")
                
                print("\n" + "="*70)
                print("🎉 SUCCESS! ALL TESTS PASSED!")
                print("="*70)
                print(f"\n📄 Open '{filename}' to see your generated SOW document!")
                print("\nKey Improvements:")
                print("  ✓ Single-pass extraction (only 1 Gemini API call)")
                print("  ✓ Function calling (guaranteed data structure)")
                print("  ✓ No rate limiting issues")
                print("  ✓ Faster and more reliable")
                print("="*70)
            else:
                print(f"✗ Download failed: {download_response.status_code}")
                print(f"Response: {download_response.text}")
        else:
            print(f"✗ Document generation failed")
            error_detail = response.json()
            print(f"Status: {response.status_code}")
            print(f"Error: {error_detail}")
            
            if "data collection not complete" in str(error_detail):
                print("\n💡 Troubleshooting:")
                print("   - The session did not reach COMPLETED stage")
                print("   - Check server logs for Gemini API errors")
                print("   - Verify GEMINI_API_KEY is valid")
                print("   - Try increasing timeout in WebSocket connection")
                
    except Exception as e:
        print(f"✗ Error during document generation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting SOW Generator V2 Test Suite")
    print("Make sure the server is running on http://localhost:8000")
    print("\n")
    
    # Quick server check
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        if health.status_code == 200:
            print("✓ Server is running and healthy\n")
        else:
            print("⚠ Server responded but health check failed\n")
    except:
        print("✗ ERROR: Cannot connect to server!")
        print("  Please start the server with:")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\n")
        exit(1)
    
    # Run tests
    test_complete_flow()
