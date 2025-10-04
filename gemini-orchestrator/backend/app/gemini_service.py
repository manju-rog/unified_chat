"""
Gemini service for AI-powered orchestration.
Handles context building, API calls, and response parsing.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.gemini_client import get_gemini_client
from app.system_prompt import get_system_prompt
from app.tool_definitions import get_all_tools
from app.models import ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def call_gemini(
    user_message: str,
    session_mode: str = "IDLE",
    session_slots: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> ChatResponse:
    """
    Call Gemini API with context, tools, and response schema.
    
    Args:
        user_message: The user's message text
        session_mode: Current session mode (IDLE, ABSENCE, SOW)
        session_slots: Collected information from conversation
        conversation_history: Recent conversation turns
    
    Returns:
        ChatResponse: Structured response envelope
    
    Requirements: 7.3, 7.4
    """
    try:
        # Get Gemini client
        client = get_gemini_client()
        model = client.get_model()
        
        # Build context
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = get_system_prompt(current_date)
        
        # Prepare session context
        session_slots = session_slots or {}
        conversation_history = conversation_history or []
        
        # Build context message
        context_parts = [
            system_prompt,
            f"\n\nCURRENT SESSION STATE:",
            f"- Mode: {session_mode}",
            f"- Collected slots: {json.dumps(session_slots)}",
        ]
        
        # Add conversation history if available
        if conversation_history:
            context_parts.append("\n\nRECENT CONVERSATION:")
            for turn in conversation_history[-5:]:  # Last 5 turns
                role = turn.get("role", "user")
                text = turn.get("text", "")
                context_parts.append(f"{role}: {text}")
        
        context_parts.append(f"\n\nUSER MESSAGE: {user_message}")
        context_parts.append("\n\nRespond with valid JSON following the ChatResponse schema.")
        
        full_context = "\n".join(context_parts)
        
        # Get all tools
        tools = get_all_tools()
        
        # Call Gemini API with tools
        logger.info(f"Calling Gemini API with mode={session_mode}")
        
        # Create chat with tools
        chat = model.start_chat(history=[])
        
        # Send message with tools (tools parameter expects list of Tool objects or dicts)
        response = chat.send_message(
            full_context,
            tools=tools
        )
        
        # Parse response
        response_text = response.text
        logger.info(f"Gemini response: {response_text[:200]}...")
        
        # Try to parse JSON response
        try:
            # Clean response text (remove markdown code blocks if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            response_data = json.loads(cleaned_text)
            
            # Validate and create ChatResponse
            chat_response = ChatResponse(
                mode=response_data.get("mode", session_mode),
                intent=response_data.get("intent"),
                slots=response_data.get("slots", {}),
                tool_call=response_data.get("tool_call"),
                message_to_user=response_data.get("message_to_user", response_text)
            )
            
            return chat_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            
            # Return fallback response
            return ChatResponse(
                mode=session_mode,
                intent=None,
                slots={},
                tool_call=None,
                message_to_user=response_text
            )
    
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        
        # Return error fallback response
        return ChatResponse(
            mode="IDLE",
            intent=None,
            slots={},
            tool_call=None,
            message_to_user=f"Sorry, I encountered an error: {str(e)}"
        )


async def call_gemini_with_function_calling(
    user_message: str,
    session_mode: str = "IDLE",
    session_slots: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Alternative implementation using Gemini's native function calling.
    Returns raw response with potential function calls.
    
    Args:
        user_message: The user's message text
        session_mode: Current session mode
        session_slots: Collected information
        conversation_history: Recent conversation turns
    
    Returns:
        Dict with response data and function calls
    """
    try:
        client = get_gemini_client()
        model = client.get_model()
        
        # Build context
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = get_system_prompt(current_date)
        
        session_slots = session_slots or {}
        conversation_history = conversation_history or []
        
        # Build prompt
        context_parts = [
            system_prompt,
            f"\nCurrent mode: {session_mode}",
            f"Collected info: {json.dumps(session_slots)}",
            f"\nUser: {user_message}"
        ]
        
        full_prompt = "\n".join(context_parts)
        
        # Get tools
        tools = get_all_tools()
        
        # Call with function calling
        chat = model.start_chat(history=[])
        response = chat.send_message(
            full_prompt,
            tools=tools
        )
        
        # Check for function calls
        function_calls = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    function_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args)
                    })
        
        return {
            "text": response.text if not function_calls else "",
            "function_calls": function_calls,
            "mode": session_mode
        }
        
    except Exception as e:
        logger.error(f"Error in function calling: {e}", exc_info=True)
        return {
            "text": f"Error: {str(e)}",
            "function_calls": [],
            "mode": "IDLE"
        }
