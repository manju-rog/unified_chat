"""
Test script for Gemini integration.
Verifies that all components are properly initialized and can work together.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_gemini_client():
    """Test Gemini client initialization."""
    print("Testing Gemini client initialization...")
    
    try:
        from app.gemini_client import get_gemini_client
        
        client = get_gemini_client()
        print(f"✓ Gemini client initialized successfully")
        print(f"  Model: {client.model_name}")
        print(f"  Temperature: {client.generation_config.temperature}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Gemini client: {e}")
        return False


async def test_system_prompt():
    """Test system prompt generation."""
    print("\nTesting system prompt...")
    
    try:
        from app.system_prompt import get_system_prompt, get_response_schema
        
        prompt = get_system_prompt()
        schema = get_response_schema()
        
        print(f"✓ System prompt generated successfully")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"  Response schema fields: {list(schema['properties'].keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to generate system prompt: {e}")
        return False


async def test_tool_definitions():
    """Test tool definitions."""
    print("\nTesting tool definitions...")
    
    try:
        from app.tool_definitions import get_absence_tools, get_sow_tools, get_all_tools
        
        absence_tools = get_absence_tools()
        sow_tools = get_sow_tools()
        all_tools = get_all_tools()
        
        print(f"✓ Tool definitions created successfully")
        print(f"  Absence tools: {len(absence_tools)} tool(s)")
        print(f"  SOW tools: {len(sow_tools)} tool(s)")
        print(f"  Total tools: {len(all_tools)} tool(s)")
        
        # List function names
        for tool in all_tools:
            func_names = [f.name for f in tool.function_declarations]
            print(f"  Functions: {', '.join(func_names)}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create tool definitions: {e}")
        return False


async def test_gemini_service():
    """Test Gemini service (without actual API call)."""
    print("\nTesting Gemini service...")
    
    try:
        from app.gemini_service import call_gemini
        
        print(f"✓ Gemini service module loaded successfully")
        print(f"  call_gemini function available: {callable(call_gemini)}")
        
        # Note: We don't make actual API calls in this test to avoid using API quota
        print("  (Skipping actual API call to preserve quota)")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load Gemini service: {e}")
        return False


async def test_integration():
    """Test full integration (optional, requires API key)."""
    print("\nTesting full integration...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠ Skipping integration test (no valid API key)")
        return True
    
    try:
        from app.gemini_service import call_gemini
        
        print("  Making test API call...")
        response = await call_gemini(
            user_message="Hello, can you help me?",
            session_mode="IDLE"
        )
        
        print(f"✓ Integration test successful")
        print(f"  Response mode: {response.mode}")
        print(f"  Message: {response.message_to_user[:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Gemini Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_gemini_client())
    results.append(await test_system_prompt())
    results.append(await test_tool_definitions())
    results.append(await test_gemini_service())
    results.append(await test_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
    else:
        print(f"✗ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
