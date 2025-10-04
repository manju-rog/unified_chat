"""Simple test script for router module."""
from app.router import route_intent, IDLE, ABSENCE, SOW

def test_router():
    """Test the domain router with various inputs."""
    
    print("Testing Domain Router")
    print("=" * 50)
    
    # Test absence keywords
    test_cases = [
        # (user_text, current_mode, expected_result, description)
        ("mark manju absent today", IDLE, ABSENCE, "Absence keyword from IDLE"),
        ("is john present?", IDLE, ABSENCE, "Presence keyword from IDLE"),
        ("check leave status", IDLE, ABSENCE, "Leave keyword from IDLE"),
        ("sick day for sarah", IDLE, ABSENCE, "Sick keyword from IDLE"),
        
        # Test SOW keywords
        ("generate sow for project", IDLE, SOW, "SOW keyword from IDLE"),
        ("create statement of work", IDLE, SOW, "Statement of work from IDLE"),
        ("add deliverables", IDLE, SOW, "Deliverable keyword from IDLE"),
        ("what are the milestones?", IDLE, SOW, "Milestone keyword from IDLE"),
        
        # Test mode persistence
        ("yes, that's correct", ABSENCE, ABSENCE, "Maintain ABSENCE mode"),
        ("the reason is sick", ABSENCE, ABSENCE, "Maintain ABSENCE mode with context"),
        ("yes, continue", SOW, SOW, "Maintain SOW mode"),
        ("the project name is AI System", SOW, SOW, "Maintain SOW mode with context"),
        
        # Test mode switching
        ("now generate a sow", ABSENCE, SOW, "Switch from ABSENCE to SOW"),
        ("mark someone absent", SOW, ABSENCE, "Switch from SOW to ABSENCE"),
        
        # Test exit commands
        ("exit", ABSENCE, IDLE, "Exit from ABSENCE mode"),
        ("cancel", SOW, IDLE, "Cancel from SOW mode"),
        ("finish", SOW, IDLE, "Finish from SOW mode"),
        
        # Test out-of-scope
        ("what's the weather?", IDLE, IDLE, "Out of scope stays IDLE"),
        ("hello", IDLE, IDLE, "Generic greeting stays IDLE"),
    ]
    
    passed = 0
    failed = 0
    
    for user_text, current_mode, expected, description in test_cases:
        result = route_intent(user_text, current_mode)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {description}")
        print(f"  Input: '{user_text}' | Mode: {current_mode}")
        print(f"  Expected: {expected} | Got: {result}")
        print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = test_router()
    exit(0 if success else 1)
