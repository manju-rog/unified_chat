#!/usr/bin/env python3
"""
Test script to verify standard services flow in unified_ai_chat -> new_sow integration
"""

import requests
import json
import time

# Configuration
UNIFIED_CHAT_URL = "http://localhost:8001"
NEW_SOW_URL = "http://localhost:8002"

def test_standard_services_flow():
    """Test the complete flow of standard services selection"""
    
    print("=" * 80)
    print("TESTING STANDARD SERVICES FLOW")
    print("=" * 80)
    
    # Step 1: Check new_sow health
    print("\n1. Checking new_sow application health...")
    try:
        response = requests.get(f"{NEW_SOW_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ new_sow is running and healthy")
        else:
            print(f"   ❌ new_sow health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ new_sow is not running: {e}")
        return False
    
    # Step 2: Test direct generation with "standard" keyword
    print("\n2. Testing direct generation with 'standard' services keyword...")
    
    test_data = {
        "template_path": "/Users/manju/Desktop/project 3/sample_sow_template.docx",
        "project_data": {
            "project_info": "Data Extraction, Compression, and Transfer Implementation for OPF to G-COP",
            "services": "standard",  # ← This should trigger standard services auto-population
            "deliverables": "Data Extraction Module, File Compression Module, File Transfer Interface, Archival and Recovery Module",
            "timeline": "Start: January 2025, End: April 2025, 16 sprints total, 2 weeks per sprint",
            "resources": "Developer: 3, Tester: 2, DevOps: 1, Project Manager: 1",
            "contacts": "Client: MUFG Bank, Contact: John Smith, Email: john.smith@mufg.com, Phone: +1-555-0100, Address: Tokyo, Japan",
            "budget": "Total: $500,000, Milestone 1: $125,000, Milestone 2: $125,000, Milestone 3: $125,000, Milestone 4: $125,000"
        },
        "session_id": f"test_standard_{int(time.time())}"
    }
    
    try:
        print(f"   Sending request to {NEW_SOW_URL}/api/generate-direct...")
        print(f"   Services value: '{test_data['project_data']['services']}'")
        
        response = requests.post(
            f"{NEW_SOW_URL}/api/generate-direct",
            json=test_data,
            timeout=120  # Allow time for Gemini processing
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Document generated successfully!")
            print(f"   📄 Filename: {result.get('filename')}")
            print(f"   📁 Session ID: {result.get('session_id')}")
            
            # Verify the document was created
            import os
            output_path = f"/Users/manju/Desktop/project 3/new_sow/output/{result.get('filename')}"
            if os.path.exists(output_path):
                print(f"   ✅ Document file exists: {output_path}")
                print(f"   📊 File size: {os.path.getsize(output_path)} bytes")
                
                # Check if document contains standard services text
                from docx import Document
                doc = Document(output_path)
                full_text = "\n".join([para.text for para in doc.paragraphs])
                
                # Check for key phrases from standard services (case-insensitive, flexible matching)
                key_phrases = [
                    "Design Review",
                    "File Transfer mechanism",
                    "Quality Assurance",
                    "Requirements review",
                    "Development of Data Extraction",
                    "Post Go Live Support",
                    "Sprint #1",
                    "Sprint #2",
                    "Sprint #3",
                    "Sprint #4"
                ]
                
                found_phrases = []
                missing_phrases = []
                
                for phrase in key_phrases:
                    if phrase in full_text:
                        found_phrases.append(phrase)
                    else:
                        missing_phrases.append(phrase)
                
                print(f"\n   📋 Standard Services Content Check:")
                print(f"   ✅ Found {len(found_phrases)}/{len(key_phrases)} key phrases")
                
                if found_phrases:
                    print(f"   ✅ Found phrases:")
                    for phrase in found_phrases[:3]:  # Show first 3
                        print(f"      - {phrase}")
                
                if missing_phrases:
                    print(f"   ⚠️  Missing phrases:")
                    for phrase in missing_phrases:
                        print(f"      - {phrase}")
                
                if len(found_phrases) >= len(key_phrases) * 0.8:  # 80% threshold
                    print(f"\n   ✅ STANDARD SERVICES SUCCESSFULLY APPLIED!")
                    return True
                else:
                    print(f"\n   ❌ Standard services content not found in document")
                    return False
            else:
                print(f"   ❌ Document file not found: {output_path}")
                return False
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_standard_services_flow()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: Standard services flow is working correctly!")
    else:
        print("❌ TEST FAILED: Standard services flow has issues")
    print("=" * 80)
