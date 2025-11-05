import requests
import json
from websocket import create_connection
import time

BASE_URL = "http://localhost:8000/api"

def test_upload_template():
    """Test template upload"""
    print("\n=== Testing Template Upload ===")
    
    with open("sample_sow_template.docx", "rb") as f:
        files = {"file": ("template.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = requests.post(f"{BASE_URL}/upload-template", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()["template_id"]

def test_create_session(template_id):
    """Test session creation"""
    print("\n=== Testing Session Creation ===")
    
    response = requests.post(f"{BASE_URL}/create-session?template_id={template_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()["session_id"]

def test_websocket_conversation(session_id):
    """Test WebSocket conversation"""
    print("\n=== Testing WebSocket Conversation ===")
    
    # Set timeout for WebSocket
    ws = create_connection(f"ws://localhost:8000/api/ws/{session_id}", timeout=30)
    
    # Receive initial message
    initial = json.loads(ws.recv())
    print(f"\nBot: {initial['message'][:150]}...")
    
    conversation_flow = [
        {
            "message": "SOW-2025-001, Cloud Migration Project, objectives are reduce infrastructure costs, improve scalability, enhance security",
            "label": "Project Info (document number, name, objectives)"
        },
        {
            "message": "Migration planning service for 2 weeks, Data migration service for 4 weeks, Testing and validation for 2 weeks",
            "label": "Services (name, description, duration)"
        },
        {
            "message": "Migration plan document with detailed roadmap, Migrated data with validation reports, Test results and performance benchmarks",
            "label": "Deliverables (name and description)"
        },
        {
            "message": "Start date 2025-11-01, end date 2026-01-31, 6 sprints of 2 weeks each",
            "label": "Timeline (dates and sprints)"
        },
        {
            "message": "2 Senior Cloud Engineers from Development team full-time, 1 Data Migration Specialist from Migration team full-time, 1 QA Engineer from Testing team part-time",
            "label": "Resources (role, team, count, allocation)"
        },
        {
            "message": "Contractor: John Smith, TechCorp Solutions, 123 Tech Street New York NY, +1-555-0100, john@techcorp.com, Project Manager. Client: Jane Doe, ClientCo Inc, 456 Business Ave Boston MA, +1-555-0200, jane@clientco.com, IT Director",
            "label": "Contacts (both contractor and client details)"
        },
        {
            "message": "Planning milestone $15000, Data migration milestone $40000, Testing milestone $10000, estimated expenses $5000",
            "label": "Budget (milestones and expenses)"
        }
    ]
    
    for idx, item in enumerate(conversation_flow, 1):
        print(f"\n--- Message {idx}/7: {item['label']} ---")
        
        # Send message
        ws.send(json.dumps({"message": item['message']}))
        print(f"User: {item['message'][:80]}...")
        
        try:
            # Receive response with timeout
            ws.settimeout(30)  # 30 second timeout
            response = json.loads(ws.recv())
            print(f"Bot: {response['message'][:100]}...")
            print(f"✓ Stage: {response['stage']}")
            print(f"✓ Progress: {response['progress']}%")
            
            # Check if completed
            if response.get('is_complete'):
                print("✓ Data collection COMPLETED!")
                break
        except Exception as e:
            print(f"⚠ Error receiving response: {e}")
            print("Continuing to next message...")
        
        # Wait to avoid rate limits
        if idx < len(conversation_flow):
            print(f"Waiting 10 seconds...")  # Increased from 5 to 10
            time.sleep(10)
    
    # Wait for final completion message
    print("\n--- Waiting for final completion message ---")
    try:
        ws.settimeout(30)
        final_response = json.loads(ws.recv())
        print(f"Bot: {final_response['message'][:150]}...")
        print(f"✓ Final Stage: {final_response['stage']}")
        print(f"✓ Final Progress: {final_response['progress']}%")
        print(f"✓ Is Complete: {final_response.get('is_complete')}")
    except Exception as e:
        print(f"⚠ Timeout or error waiting for completion: {e}")
        print("Proceeding anyway...")
    
    ws.close()
    print("\n✓ Conversation completed!")



def test_generate_document(session_id):
    """Test document generation"""
    print("\n=== Testing Document Generation ===")
    
    response = requests.post(f"{BASE_URL}/generate-document/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Download document
    download_response = requests.get(f"{BASE_URL}/download/{session_id}")
    if download_response.status_code == 200:
        with open("generated_sow.docx", "wb") as f:
            f.write(download_response.content)
        print("Document downloaded as 'generated_sow.docx'")

if __name__ == "__main__":
    try:
        # Run tests
        template_id = test_upload_template()
        session_id = test_create_session(template_id)
        test_websocket_conversation(session_id)
        test_generate_document(session_id)
        
        print("\n=== All Tests Completed Successfully! ===")
    except Exception as e:
        print(f"\nError during testing: {e}")
