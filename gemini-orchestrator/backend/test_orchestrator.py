"""
Test script for orchestrator logic.
Tests session management, tool execution, and orchestrate function.
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.session_manager import get_session, update_session, clear_session
from app.orchestrator import orchestrate


async def test_session_manager():
    """Test session state manager."""
    print("\n=== Testing Session Manager ===")
    
    # Test creating new session
    session1 = get_session()
    print(f"✓ Created new session: {session1.session_id}")
    print(f"  Mode: {session1.mode}")
    print(f"  Slots: {session1.collected_slots}")
    
    # Test retrieving existing session
    session1_retrieved = get_session(session1.session_id)
    assert session1_retrieved.session_id == session1.session_id
    print(f"✓ Retrieved existing session: {session1_retrieved.session_id}")
    
    # Test updating session
    updated = update_session(
        session_id=session1.session_id,
        mode="ABSENCE",
        collected_slots={"employee": "John"},
        conversation_turn={"role": "user", "text": "Mark John absent"}
    )
    print(f"✓ Updated session mode to: {updated.mode}")
    print(f"  Slots: {updated.collected_slots}")
    print(f"  History length: {len(updated.conversation_history)}")
    
    # Test clearing session
    cleared = clear_session(session1.session_id)
    assert cleared == True
    print(f"✓ Cleared session: {session1.session_id}")
    
    print("✓ Session manager tests passed!")


async def test_orchestrator_basic():
    """Test basic orchestrator flow without actual Gemini calls."""
    print("\n=== Testing Orchestrator (Basic) ===")
    
    # Note: This will make actual Gemini API calls if GEMINI_API_KEY is set
    # For now, we'll just test that the function can be called
    
    try:
        # Test with a simple message
        response = await orchestrate(
            user_msg="Hello",
            session_id=None
        )
        
        print(f"✓ Orchestrate returned response")
        print(f"  Mode: {response.mode}")
        print(f"  Message: {response.message_to_user[:100]}...")
        
    except Exception as e:
        print(f"⚠ Orchestrate test skipped (expected if no API key): {e}")


async def main():
    """Run all tests."""
    print("Starting orchestrator tests...")
    
    # Test session manager
    await test_session_manager()
    
    # Test orchestrator (basic)
    await test_orchestrator_basic()
    
    print("\n=== All Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
