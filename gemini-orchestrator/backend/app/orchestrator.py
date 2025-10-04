"""
Main orchestrator logic for coordinating Gemini calls, tool execution, and state management.
Requirements: 7.1, 7.2, 7.5
"""

import logging
from typing import Optional

from app.models import ChatResponse
from app.router import route_intent
from app.session_manager import get_session, update_session
from app.gemini_service import call_gemini
from app.tool_executor import execute_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def orchestrate(
    user_msg: str,
    session_id: Optional[str] = None
) -> ChatResponse:
    """
    Main orchestration function that coordinates the entire flow.
    
    Flow:
    1. Get or create session
    2. Route intent to determine domain
    3. Build context and call Gemini
    4. Execute tool call if present
    5. Update session state
    6. Return ChatResponse envelope
    
    Args:
        user_msg: User's message text
        session_id: Optional session identifier
    
    Returns:
        ChatResponse: Structured response envelope
    
    Requirements: 7.1, 7.2, 7.5
    """
    try:
        logger.info(f"Orchestrating message: {user_msg[:100]}...")
        
        # Step 1: Get or create session
        session = get_session(session_id)
        logger.info(f"Session {session.session_id}: mode={session.mode}")
        
        # Step 2: Route intent to determine domain
        new_mode = route_intent(user_msg, session.mode)
        logger.info(f"Routed to mode: {new_mode}")
        
        # Step 3: Build context and call Gemini
        gemini_response = await call_gemini(
            user_message=user_msg,
            session_mode=new_mode,
            session_slots=session.collected_slots,
            conversation_history=session.conversation_history
        )
        
        logger.info(f"Gemini response: mode={gemini_response.mode}, intent={gemini_response.intent}")
        
        # Step 4: Execute tool call if present
        tool_result = None
        if gemini_response.tool_call:
            tool_name = gemini_response.tool_call.get("name")
            tool_args = gemini_response.tool_call.get("args", {})
            
            logger.info(f"Executing tool: {tool_name}")
            tool_result = await execute_tool(tool_name, tool_args)
            
            # If tool execution failed, update message to user
            if not tool_result.get("ok", False):
                error_msg = tool_result.get("error", "Unknown error")
                gemini_response.message_to_user = f"Sorry, I couldn't complete that action: {error_msg}"
            else:
                # If tool succeeded, enhance message with result
                tool_data = tool_result.get("data", {})
                
                # Special handling for start_sow to capture sow_id
                if tool_name == "start_sow" and "sow_id" in tool_data:
                    session.active_sow_id = tool_data["sow_id"]
                    logger.info(f"Started SOW session: {session.active_sow_id}")
        
        # Step 5: Update session state
        # Add conversation turn
        conversation_turn = {
            "role": "user",
            "text": user_msg,
            "timestamp": session.updated_at.isoformat()
        }
        
        # Merge new slots with existing slots
        updated_slots = {**session.collected_slots, **gemini_response.slots}
        
        # Update session
        updated_session = update_session(
            session_id=session.session_id,
            mode=gemini_response.mode,
            active_sow_id=session.active_sow_id,
            collected_slots=updated_slots,
            conversation_turn=conversation_turn
        )
        
        # Add AI response to conversation history
        ai_turn = {
            "role": "assistant",
            "text": gemini_response.message_to_user,
            "timestamp": updated_session.updated_at.isoformat()
        }
        update_session(
            session_id=session.session_id,
            conversation_turn=ai_turn
        )
        
        logger.info(f"Session updated: mode={updated_session.mode}, slots={updated_slots}")
        
        # Step 6: Return ChatResponse envelope
        return gemini_response
    
    except Exception as e:
        logger.error(f"Error in orchestrate: {e}", exc_info=True)
        
        # Return error response
        return ChatResponse(
            mode="IDLE",
            intent=None,
            slots={},
            tool_call=None,
            message_to_user=f"Sorry, I encountered an error: {str(e)}"
        )
