"""FastAPI entrypoint for the unified AI chat orchestrator."""
from __future__ import annotations

import logging
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import uuid

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import Settings, get_settings
from .gemini_client import ToolCall, gemini_client
from .models import ChatRequest, ChatResponse, ConfirmationButton, DisambiguationOption, SessionState
from .services.absence import absence_adapter
from .services.sow_direct import SowAdapter
from .sow_components.models import SowState
from .session_manager import session_manager

# SOW globals
SOW_SESSIONS: dict[str, SowState] = {}
sow_adapter = SowAdapter(out_root=Path("output"))

SOW_STATE_TO_SECTION = {
    "PROJECT_BASICS": "services",
    "SERVICES": "deliverables",
    "DELIVERABLES": "timeline",
    "TIMELINE": "resources",
    "RESOURCES": "contacts",
    "CONTACTS": "budget",
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Unified AI Chat Orchestrator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session(request: ChatRequest) -> SessionState:
    return session_manager.get_or_create(request.session_id)


def get_app_settings() -> Settings:
    return get_settings()


@app.get("/api/health")
async def health(settings: Settings = Depends(get_app_settings)) -> Dict[str, Any]:
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "absence_api": str(settings.absence_api_base),
        "sow_template": str(settings.sow_default_template),
    }

@app.get("/api/sow/documents/{session_id}/{filename}")
def get_sow_doc(session_id: str, filename: str):
    path = Path("output") / session_id / filename
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )





@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    session: SessionState = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    logger.info("Processing chat message for session %s", session.session_id)
    
    user_message = request.message.strip()
    
    # Handle confirmation responses (yes/no) for pending actions
    user_lower = user_message.lower()
    is_yes_response = (user_lower in ["yes", "y", "yeah", "yep", "sure", "ok", "okay"] or 
                      "yes" in user_lower or "add reason" in user_lower)
    is_no_response = (user_lower in ["no", "n", "nope", "cancel", "skip"] or 
                     "no" in user_lower or "skip" in user_lower)
    
    if is_yes_response:
        pending_action = session.metadata.get("pending_action")
        if pending_action:
            action_type = pending_action.get("type")
            
            # If asking for reason, prompt for it
            if action_type == "ask_reason":
                session.add_message("user", user_message)
                session.metadata["waiting_for_reason"] = True
                return ChatResponse(
                    session_id=session.session_id,
                    response="Please state your reason:",
                    action_type="awaiting_reason",
                )
            
            # Execute the pending action
            session.add_message("user", user_message)
            result = await _execute_pending_action(session, pending_action)
            session.metadata.pop("pending_action", None)
            session.metadata.pop("pending_context", None)
            background_tasks.add_task(session_manager.cleanup_expired)
            return result
    elif is_no_response:
        pending_action = session.metadata.get("pending_action")
        if pending_action:
            action_type = pending_action.get("type")
            
            # If declining to add reason, execute without reason
            if action_type == "ask_reason":
                session.add_message("user", user_message)
                data = pending_action.get("data", {})
                data["reason"] = ""  # No reason
                pending_action["type"] = "mark_absence"
                result = await _execute_pending_action(session, pending_action)
                session.metadata.pop("pending_action", None)
                session.metadata.pop("pending_context", None)
                background_tasks.add_task(session_manager.cleanup_expired)
                return result
            
            # Cancel other pending actions
            session.metadata.pop("pending_action", None)
            session.metadata.pop("pending_context", None)
            session.add_message("user", user_message)
            return ChatResponse(
                session_id=session.session_id,
                response="Okay, cancelled. How else can I help you?",
            )
    
    # Handle reason input
    if session.metadata.get("waiting_for_reason"):
        session.metadata.pop("waiting_for_reason", None)
        pending_action = session.metadata.get("pending_action")
        if pending_action:
            session.add_message("user", user_message)
            # Add the reason to the pending action
            pending_action["data"]["reason"] = user_message
            pending_action["type"] = "mark_absence"
            result = await _execute_pending_action(session, pending_action)
            session.metadata.pop("pending_action", None)
            session.metadata.pop("pending_context", None)
            background_tasks.add_task(session_manager.cleanup_expired)
            return result
    
    # ---------- INTELLIGENT SOW MODE DETECTION ----------
    # Smart SOW triggers - more comprehensive and intelligent
    sow_triggers = {
        "create a sow", "start sow", "sow generation", "generate sow", "statement of work", 
        "create sow", "new sow", "sow document", "work statement", "project statement"
    }
    is_explicit_sow_trigger = any(trigger in user_message.lower() for trigger in sow_triggers)
    
    # Handle SOW mode with intelligent detection
    if session.active_domain == "sow" or is_explicit_sow_trigger:
        # Set SOW mode if explicitly triggered
        if is_explicit_sow_trigger and session.active_domain != "sow":
            session.active_domain = "sow"
        
        # Exit SOW mode
        if user_message.lower() in {"exit", "quit", "cancel", "abort", "/exit", "exit_sow", "exit sow"}:
            if session.session_id in SOW_SESSIONS:
                del SOW_SESSIONS[session.session_id]
            session.active_domain = None
            return ChatResponse(
                session_id=session.session_id,
                response="✅ **Exited SOW mode successfully!**\n\nI'm back to helping you with both absence management and SOW generation. What would you like to do next?",
                action_type="sow_exit",
                confirmation_buttons=[
                    ConfirmationButton(
                        id="absence_help",
                        label="Absence Management",
                        value="Who is absent today?",
                        style="primary"
                    ),
                    ConfirmationButton(
                        id="new_sow",
                        label="New SOW",
                        value="Create a SOW",
                        style="primary"
                    )
                ]
            )
        
        # Start SOW session
        if is_explicit_sow_trigger or session.session_id not in SOW_SESSIONS:
            SOW_SESSIONS[session.session_id] = SowState()
            q, hint = sow_adapter.start()
            return ChatResponse(
                session_id=session.session_id,
                response=q,
                action_type="sow_started",
                action_data=hint
            )
        
        # Generate document
        if user_message == "generate_sow":
            state = SOW_SESSIONS.get(session.session_id) or SowState()
            result = sow_adapter.finalize(state, session_id=session.session_id)
            return ChatResponse(
                session_id=session.session_id,
                response=result["message"],
                action_type="sow_generated",
                download_url=result["download_url"]
            )
        
        # Process SOW input
        state = SOW_SESSIONS.get(session.session_id) or SowState()
        state, hint = sow_adapter.process(state, user_message)
        SOW_SESSIONS[session.session_id] = state
        
        # Handle silent updates (for resource +/- clicks)
        if hint.get("silent_update"):
            return ChatResponse(
                session_id=session.session_id,
                response="",  # No message for silent updates
                action_type="sow_silent_update",
                action_data=hint
            )
        
        return ChatResponse(
            session_id=session.session_id,
            response=hint.get("message", "Processing..."),
            action_type="sow_processing",
            action_data=hint
        )

    session.add_message("user", user_message)

    # Early intent detection for better user experience
    user_lower = user_message.lower().strip()
    
    # Handle general/ambiguous queries before going to Gemini
    general_queries = [
        "what would you like to do today", "what can you do", "help", "hello", "hi",
        "what are your capabilities", "what do you help with", "options", "menu"
    ]
    
    mixed_intents = ["absence and sow", "sow and absence", "both", "everything"]
    
    # Check if user is asking for SOW but we're in absence mode or vice versa
    sow_keywords = ["sow", "statement of work", "document generation", "create document", "generate document"]
    absence_keywords = ["absent", "absence", "vacation", "leave", "present", "attendance"]
    
    is_sow_request = any(keyword in user_lower for keyword in sow_keywords)
    is_absence_request = any(keyword in user_lower for keyword in absence_keywords)
    
    # If in wrong mode, provide guidance to switch
    if session.active_domain == "absence" and is_sow_request and not is_absence_request:
        return ChatResponse(
            session_id=session.session_id,
            response="""*I'm currently in Absence Management mode.*

**To create a SOW document, I need to switch to SOW mode first.**

Would you like me to switch to SOW generation mode?""",
            action_type="mode_switch_needed",
            confirmation_buttons=[
                ConfirmationButton(
                    id="switch_to_sow",
                    label="Switch to SOW Mode",
                    value="Create a SOW",
                    style="primary"
                ),
                ConfirmationButton(
                    id="stay_absence",
                    label="Stay in Absence Mode",
                    value="Who is absent today?",
                    style="secondary"
                )
            ]
        )
    
    if session.active_domain == "sow" and is_absence_request and not is_sow_request:
        return ChatResponse(
            session_id=session.session_id,
            response="""*I'm currently in SOW Generation mode and focused exclusively on creating your Statement of Work.*

**To handle absence queries, please exit SOW mode first.**""",
            action_type="sow_mode_redirect",
            confirmation_buttons=[
                ConfirmationButton(
                    id="exit_sow",
                    label="Exit SOW Mode",
                    value="exit sow",
                    style="primary"
                ),
                ConfirmationButton(
                    id="continue_sow",
                    label="Continue SOW",
                    value="continue with SOW",
                    style="secondary"
                )
            ]
        )
    
    # Handle single word "sow" which is ambiguous
    if user_lower == "sow":
        return ChatResponse(
            session_id=session.session_id,
            response="""*The request "sow" is ambiguous. It could refer to starting a new Statement of Work or something else entirely.*

**I can help with both absence tracking and SOW generation. Which would you like to start with?**

**You can try:**
• Start SOW
• Check absence""",
            action_type="disambiguation_needed",
            confirmation_buttons=[
                ConfirmationButton(
                    id="absence_help",
                    label="Absence Management",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_help",
                    label="Create SOW", 
                    value="Create a SOW",
                    style="primary"
                )
            ]
        )
    
    if any(query in user_lower for query in general_queries):
        return ChatResponse(
            session_id=session.session_id,
            response="""*I'm here to help you with your daily operations!*

**I specialize in two main areas:**

🏢 **Absence Management**
- Check who's absent today
- Mark employees as absent, present, or on vacation
- View absence reports and history
- Track vacation days

📄 **SOW Generation** 
- Create professional Statement of Work documents
- Guided conversation to collect all requirements
- Generate downloadable documents

**What would you like to work on?**""",
            action_type="guidance_provided",
            confirmation_buttons=[
                ConfirmationButton(
                    id="absence_help",
                    label="Absence Management",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_help", 
                    label="Create SOW",
                    value="Create a SOW",
                    style="primary"
                )
            ]
        )
    
    if any(mixed in user_lower for mixed in mixed_intents):
        return ChatResponse(
            session_id=session.session_id,
            response="""*I can help with both absence management and SOW generation!*

**Which would you like to focus on first?**

I'll guide you through whichever option you choose, and you can always switch to the other later.""",
            action_type="disambiguation_needed",
            confirmation_buttons=[
                ConfirmationButton(
                    id="absence_first",
                    label="Start with Absence Management",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_first",
                    label="Start with SOW Generation", 
                    value="Create a SOW",
                    style="primary"
                )
            ]
        )

    # Check for SOW initiation request
    sow_keywords = ["sow", "statement of work", "document generation", "create document", "generate document"]
    if any(keyword in user_message.lower() for keyword in sow_keywords) and not hasattr(session, 'sow_session_id'):
        # Suggest SOW initiation with mode change warning
        return ChatResponse(
            session_id=session.session_id,
            response="""🔴 **SOW Generation Mode**

I can help you create a professional Statement of Work document! 

*Once we start, I'll focus exclusively on SOW generation until you exit or complete the document.*

**Ready to begin?**""",
            action_type="sow_initiation_suggested",
            confirmation_buttons=[
                ConfirmationButton(
                    id="sow_start",
                    label="Start SOW Generation",
                    value="Start SOW generation",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_cancel",
                    label="Not now",
                    value="no",
                    style="secondary"
                )
            ]
        )

    parsed: Dict[str, Any] = {"tool_calls": [], "text": ""}
    tool_calls: List[ToolCall] = []

    # Fetch employee list for context
    context = None
    employees = []
    try:
        employees = await absence_adapter.get_employees()
        if employees:
            employee_names = [emp.get("name", "") for emp in employees if emp.get("name")]
            context = f"Available employees in the system: {', '.join(employee_names)}"
            
            # Add conversation context if available
            pending_context = session.metadata.get("pending_context")
            if pending_context:
                context += f"\n\nPrevious context: {pending_context}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch employee list: %s", exc)

    # Check for direct routing first (SOW, absence keywords)
    direct_call = _maybe_route_without_llm(session, user_message)
    if direct_call:
        tool_calls = [direct_call]
    else:
        try:
            raw_response = gemini_client.generate(session, user_message, context=context)
            parsed = gemini_client.parse_response(raw_response)
            tool_calls = parsed.get("tool_calls", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Gemini processing failed: %s",
                exc,
                exc_info=True,
            )
            # Return error message instead of fallback
            return ChatResponse(
                session_id=session.session_id,
                response="I'm having trouble connecting to my AI brain right now. 🤖 Please try again in a moment!",
            intent="error",
            action_type="error",
        )

    assistant_responses: List[str] = []
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    disambiguation_options: Optional[List[DisambiguationOption]] = None
    confirmation_buttons: Optional[List[ConfirmationButton]] = None

    if tool_calls:
        for call in tool_calls:
            tool_result = await _execute_tool_call(session, call, settings)
            assistant_responses.append(tool_result["message"])
            action_type = tool_result.get("action_type") or action_type
            action_data = tool_result.get("action_data") or action_data
            disambiguation_options = tool_result.get("disambiguation_options") or disambiguation_options
            confirmation_buttons = tool_result.get("confirmation_buttons") or confirmation_buttons
            if tool_result.get("download_path"):
                download_url = f"/api/sow/documents/{session.session_id}/{tool_result['download_path']}"
                action_data = action_data or {}
                action_data["download_path"] = download_url
            session.add_message(
                "assistant",
                tool_result["message"],
                metadata={"actionType": tool_result.get("action_type"), "actionData": action_data},
            )
    elif parsed.get("text"):
        assistant_responses.append(parsed["text"])
        session.add_message("assistant", parsed["text"])
    else:
        # Better fallback with helpful guidance
        fallback_message = """*I'm not sure how to help with that specific request.*

**I can assist you with:**

🏢 **Absence Management** - Employee attendance and vacation tracking
📄 **SOW Generation** - Creating Statement of Work documents

**Could you try rephrasing your request, or let me know which area you'd like help with?**"""
        
        assistant_responses.append(fallback_message)
        session.add_message("assistant", fallback_message)
        
        # Add helpful buttons
        confirmation_buttons = [
            ConfirmationButton(
                id="absence_help",
                label="Absence Management",
                value="Who is absent today?",
                style="primary"
            ),
            ConfirmationButton(
                id="sow_help",
                label="Create SOW", 
                value="Create a SOW",
                style="primary"
            )
        ]

    background_tasks.add_task(session_manager.cleanup_expired)

    return ChatResponse(
        session_id=session.session_id,
        response="\n\n".join(assistant_responses),
        intent=action_type,
        action_type=action_type,
        action_data=action_data,
        download_url=download_url,
        disambiguation_options=disambiguation_options,
        confirmation_buttons=confirmation_buttons,
    )


async def _execute_tool_call(
    session: SessionState, call: ToolCall, settings: Settings
) -> Dict[str, Any]:
    name = call.name
    args = call.arguments

    if name == "absence_chat":
        session.active_domain = "absence"
        action = args.get("action")
        employee_name = args.get("employee_name")
        
        try:
            # Check for multiple employee matches
            if employee_name:
                employees = await absence_adapter.get_employees()
                matches = _find_employee_matches(employee_name, employees)
                
                if len(matches) > 1:
                    # Multiple matches - return disambiguation options
                    options = [
                        DisambiguationOption(
                            id=f"emp_{emp['id']}",
                            label=f"{emp['name']} ({emp.get('department', 'N/A')})",
                            value=emp['name'],
                            metadata={
                                "employee_id": emp['id'],
                                "action": action,
                                "status": args.get("status"),
                                "date": args.get("date"),
                                "date_range": args.get("date_range"),
                                "reason": args.get("reason"),
                            }
                        )
                        for emp in matches
                    ]
                    
                    # Store the pending action
                    session.metadata["pending_disambiguation"] = {
                        "action": action,
                        "matches": [emp['name'] for emp in matches],
                        "original_args": args,
                    }
                    
                    return {
                        "message": f"I found {len(matches)} employees matching '{employee_name}'. Please select one:",
                        "action_type": "disambiguation_required",
                        "disambiguation_options": options,
                    }
                elif len(matches) == 0:
                    # No match - ask for clarification
                    session.metadata["pending_context"] = f"User asked about employee '{employee_name}' but no exact match found"
                    return {
                        "message": f"I couldn't find an employee named '{employee_name}'. Could you check the spelling or provide more details?",
                        "action_type": "clarification_needed",
                    }
                else:
                    # Exact match - use it
                    employee_name = matches[0]['name']
            
            if action == "mark_absence":
                status = args.get("status", "A")
                date_str = args.get("date", _today())
                if date_str == "today":
                    date_str = _today()
                elif date_str == "yesterday":
                    date_str = (date.today() - timedelta(days=1)).isoformat()
                elif date_str == "tomorrow":
                    date_str = (date.today() + timedelta(days=1)).isoformat()
                    
                reason = args.get("reason", "")
                
                # If no reason provided, ask politely
                if not reason:
                    status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
                    
                    # Store pending action
                    session.metadata["pending_action"] = {
                        "type": "ask_reason",
                        "data": {
                            "employee_name": employee_name,
                            "status": status,
                            "dates": [date_str],
                            "reason": "",
                        }
                    }
                    
                    # Return with Yes/No buttons
                    confirmation_buttons = [
                        ConfirmationButton(
                            id="reason_yes",
                            label="Yes, add reason",
                            value="yes",
                            style="primary"
                        ),
                        ConfirmationButton(
                            id="reason_no",
                            label="No, skip",
                            value="no",
                            style="secondary"
                        )
                    ]
                    
                    return {
                        "message": f"Would you like to add a reason for marking {employee_name} as {status_text}?",
                        "action_type": "reason_confirmation",
                        "confirmation_buttons": confirmation_buttons,
                    }
                
                # If reason is provided, mark directly
                result = await absence_adapter.mark_absence(
                    employee_name, [date_str], status, reason
                )
                status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
                if result.get("success"):
                    reason_text = f" Reason: {reason}" if reason else ""
                    return {
                        "message": f"✅ Marked {employee_name} as {status_text} for {date_str}.{reason_text}",
                        "action_type": "absence_mark",
                        "action_data": result.get("details"),
                    }
                else:
                    return {
                        "message": result.get("message", "Could not mark absence."),
                        "action_type": "absence_error",
                    }
                    
            elif action == "query_absence":
                date_str = args.get("date")
                date_range = args.get("date_range")
                
                if date_range:
                    start = date_range.get("start")
                    end = date_range.get("end")
                    result = await absence_adapter.query_absence(
                        query_type="byDateRange",
                        dates=[start, end],
                        employee_name=employee_name,
                    )
                elif date_str:
                    if date_str == "today":
                        date_str = _today()
                    elif date_str == "yesterday":
                        date_str = (date.today() - timedelta(days=1)).isoformat()
                    elif date_str == "tomorrow":
                        date_str = (date.today() + timedelta(days=1)).isoformat()
                    result = await absence_adapter.query_absence(
                        query_type="byDate",
                        dates=[date_str],
                        employee_name=employee_name,
                    )
                else:
                    # Default to today
                    result = await absence_adapter.query_absence(
                        query_type="byDate",
                        dates=[_today()],
                        employee_name=employee_name,
                    )
                    
                return {
                    "message": result.get("message", "Could not retrieve absence information."),
                    "action_type": "absence_query" if result.get("success") else "absence_error",
                    "action_data": result.get("details"),
                }
                
        except Exception as exc:  # noqa: BLE001
            logger.warning("Absence operation failed: %s", exc, exc_info=True)
            return {
                "message": f"Error processing absence request: {str(exc)}",
                "action_type": "absence_error",
            }
            
        return {
            "message": "I couldn't understand that absence request.",
            "action_type": "absence_error",
        }

    if name == "start_sow_session":
        overview = args.get("projectOverview", "")
        result = intelligent_sow_adapter.start_session(session, overview)
        
        # Set SOW mode
        session.active_domain = "sow"
        
        # Always include exit button for SOW responses
        base_buttons = [
            ConfirmationButton(
                id="sow_exit",
                label="Exit SOW Mode",
                value="exit sow",
                style="secondary"
            )
        ]
        
        # Check if we need to show service selection buttons
        if result.get("success") and result.get("next_step") == "services":
            service_buttons = [
                ConfirmationButton(
                    id="service_standard",
                    label="Standard Service Package",
                    value="standard",
                    style="primary"
                ),
                ConfirmationButton(
                    id="service_custom", 
                    label="Custom Services",
                    value="custom",
                    style="secondary"
                )
            ]
            return {
                "message": result.get("message", "Let's begin the SOW workflow."),
                "action_type": "sow_start",
                "action_data": {"next_step": result.get("next_step")},
                "confirmation_buttons": service_buttons + base_buttons
            }
        
        return {
            "message": result.get("message", "Let's begin the SOW workflow."),
            "action_type": "sow_start" if result.get("success") else "sow_error",
            "action_data": {"next_step": result.get("next_step")},
            "confirmation_buttons": base_buttons if result.get("success") else None
        }

    if name == "update_sow_section":
        section = args.get("section")
        content = args.get("content", "")
        result = await intelligent_sow_adapter.process_user_input(session, content)
        
        payload: Dict[str, Any] = {"next_step": result.get("next_step")}
        if result.get("download_path"):
            payload["download_path"] = result.get("download_path")
        
        # Always include exit button
        base_buttons = [
            ConfirmationButton(
                id="sow_exit",
                label="Exit SOW Mode",
                value="exit sow",
                style="secondary"
            )
        ]
        
        # Check if we need to show service selection buttons
        confirmation_buttons = base_buttons
        if result.get("show_service_buttons"):
            service_buttons = [
                ConfirmationButton(
                    id="service_standard",
                    label="Standard Service Package",
                    value="standard",
                    style="primary"
                ),
                ConfirmationButton(
                    id="service_custom",
                    label="Custom Services", 
                    value="custom",
                    style="secondary"
                )
            ]
            confirmation_buttons = service_buttons + base_buttons
        
        # Check if we can generate document
        if result.get("can_generate"):
            generate_buttons = [
                ConfirmationButton(
                    id="generate_sow",
                    label="Generate SOW Document",
                    value="generate",
                    style="primary"
                )
            ]
            confirmation_buttons = generate_buttons + base_buttons
        
        return {
            "message": result.get("message", "Section updated."),
            "action_type": "sow_update" if result.get("success") else "sow_error",
            "action_data": payload,
            "download_path": result.get("download_path"),
            "confirmation_buttons": confirmation_buttons,
        }

    if name == "finalize_sow":
        result = intelligent_sow_adapter.finalize(session)
        payload: Dict[str, Any] = {}
        if result.get("download_path"):
            payload["download_path"] = result.get("download_path")
        return {
            "message": result.get("message", "Processing your SOW."),
            "action_type": "sow_finalize" if result.get("success") else "sow_error",
            "action_data": payload,
            "download_path": result.get("download_path"),
        }

    if name == "provide_guidance":
        guidance_type = args.get("guidance_type", "help")
        explanation = args.get("explanation", "")
        main_response = args.get("main_response", "")
        suggested_actions = args.get("suggested_actions", [])
        
        # Format the response with styling
        formatted_response = ""
        if explanation:
            formatted_response += f"*{explanation}*\n\n"
        
        formatted_response += main_response
        
        if suggested_actions:
            formatted_response += "\n\n**You can try:**\n"
            for action in suggested_actions:
                formatted_response += f"• {action}\n"
        
        # Add quick action buttons based on guidance type
        confirmation_buttons = None
        if guidance_type in ["capabilities", "help", "disambiguation"]:
            confirmation_buttons = [
                ConfirmationButton(
                    id="absence_help",
                    label="Absence Management",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_help",
                    label="Create SOW",
                    value="Create a SOW",
                    style="primary"
                )
            ]
        
        return {
            "message": formatted_response,
            "action_type": "guidance_provided",
            "action_data": {"guidance_type": guidance_type},
            "confirmation_buttons": confirmation_buttons
        }

    logger.warning("Received unsupported tool call: %s", name)
    return {
        "message": "I am not sure how to handle that request right now.",
        "action_type": "unknown_tool",
    }


def _maybe_route_without_llm(session: SessionState, message: str) -> Optional[ToolCall]:
    if not message:
        return None

    lower = message.lower()

    # DISABLED: Let absence queries go through Gemini for proper parsing
    # absence_keywords = [
    #     "absent",
    #     "absence", 
    #     "vacation",
    #     "leave",
    #     "present",
    #     "attendance",
    #     "sick",
    #     "time off",
    #     "who is off",
    # ]
    # if any(keyword in lower for keyword in absence_keywords):
    #     return ToolCall(name="absence_chat", arguments={"message": message})

    if (
        "statement of work" in lower
        or "create a sow" in lower
        or lower.startswith("sow")
        or " need a sow" in lower
    ):
        return ToolCall(name="start_sow_session", arguments={"projectOverview": message})

    sow_state = session.sow_state
    if sow_state:
        current_state = sow_state.generator.conversation_state
        next_section = SOW_STATE_TO_SECTION.get(current_state)
        if next_section:
            return ToolCall(
                name="update_sow_section",
                arguments={"section": next_section, "content": message},
            )
        if current_state == "BUDGET":
            return ToolCall(name="finalize_sow", arguments={})

    return None


async def _attempt_absence_fallback(session: SessionState, message: str) -> Optional[Dict[str, Any]]:
    employees = await absence_adapter.get_employees()
    parsed = _parse_absence_message(message, employees)
    if not parsed:
        return None

    if parsed["type"] == "mark":
        result = await absence_adapter.mark_absence(
            parsed["employee"], parsed["dates"], parsed["status"], parsed.get("reason")
        )
        if not result.get("success"):
            return {
                "message": result.get("message", "I couldn't update the attendance."),
                "action_type": "absence_mark_failed",
                "action_data": result.get("details"),
            }
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(parsed["status"], parsed["status"])
        date_text = ", ".join(parsed["dates"])
        return {
            "message": f"Marked {parsed['employee']} as {status_text} for {date_text}.",
            "action_type": "absence_mark",
            "action_data": result.get("details"),
        }

    if parsed["type"] == "query":
        result = await absence_adapter.query_absence(
            query_type=parsed["query_type"],
            dates=parsed.get("dates"),
            employee_name=parsed.get("employee"),
            month=parsed.get("month"),
        )
        msg = result.get("message", "I could not retrieve the absence information.")
        action = "absence_query" if result.get("success") else "absence_query_failed"
        return {
            "message": msg,
            "action_type": action,
            "action_data": result.get("details"),
        }

    return None


def _needs_absence_fallback(message: Optional[str]) -> bool:
    if not message:
        return True
    lower = message.lower()
    return "trouble connecting" in lower or "could not" in lower


def _parse_absence_message(message: str, employees: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    lower = message.lower()
    employee_name = _match_employee(lower, employees)

    status_map = {"absent": "A", "present": "P", "vacation": "V", "holiday": "V"}
    status = None
    for key, value in status_map.items():
        if key in lower:
            status = value
            break

    if any(word in lower for word in ["mark", "set", "make", "put"]) and status:
        dates = _extract_mark_dates(lower)
        if not dates:
            dates = [_today()]
        if employee_name:
            return {
                "type": "mark",
                "employee": employee_name,
                "status": status,
                "dates": dates,
            }

    if any(word in lower for word in ["who", "show", "list", "get", "report"]):
        query = _extract_query_details(lower)
        if not query.get("dates") and query.get("query_type") == "byDate":
            query["dates"] = [_today()]
        return query

    return None


def _match_employee(lower_message: str, employees: List[Dict[str, Any]]) -> Optional[str]:
    padded = f" {lower_message} "
    for emp in employees:
        name = emp.get("name", "")
        if not name:
            continue
        if name.lower() in lower_message:
            return name
    for emp in employees:
        name = emp.get("name", "")
        if not name:
            continue
        first = name.split()[0].lower()
        if re.search(rf"\b{re.escape(first)}\b", lower_message):
            return name
    return None


def _extract_mark_dates(lower_message: str) -> List[str]:
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", lower_message)
    if dates:
        return dates
    if "today" in lower_message:
        return [_today()]
    if "tomorrow" in lower_message:
        return [(date.today() + timedelta(days=1)).isoformat()]
    if "yesterday" in lower_message:
        return [(date.today() - timedelta(days=1)).isoformat()]
    return []


def _extract_query_details(lower_message: str) -> Dict[str, Any]:
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    if "today" in lower_message:
        return {"type": "query", "query_type": "byDate", "dates": [_today()]}
    if "yesterday" in lower_message:
        return {
            "type": "query",
            "query_type": "byDate",
            "dates": [(date.today() - timedelta(days=1)).isoformat()],
        }
    if "tomorrow" in lower_message:
        return {
            "type": "query",
            "query_type": "byDate",
            "dates": [(date.today() + timedelta(days=1)).isoformat()],
        }
    if "this week" in lower_message:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return {
            "type": "query",
            "query_type": "byDateRange",
            "dates": [start.isoformat(), end.isoformat()],
        }
    if "this month" in lower_message:
        today = date.today()
        start = today.replace(day=1)
        if today.month == 12:
            next_month = start.replace(year=today.year + 1, month=1)
        else:
            next_month = start.replace(month=today.month + 1)
        end = next_month - timedelta(days=1)
        return {
            "type": "query",
            "query_type": "byMonth",
            "month": start.strftime("%Y-%m"),
            "dates": [start.isoformat(), end.isoformat()],
        }
    for name, number in months.items():
        if name in lower_message:
            year = date.today().year
            match = re.search(rf"{name} (\d{{4}})", lower_message)
            if match:
                year = int(match.group(1))
            start = date(year, number, 1)
            if number == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, number + 1, 1)
            end = next_month - timedelta(days=1)
            return {
                "type": "query",
                "query_type": "byMonth",
                "month": start.strftime("%Y-%m"),
                "dates": [start.isoformat(), end.isoformat()],
            }
    return {"type": "query", "query_type": "byDate"}


def _today() -> str:
    return date.today().isoformat()


def _find_employee_matches(name: str, employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find all employees matching the given name (case-insensitive, partial match)."""
    if not name:
        return []
    
    name_lower = name.strip().lower()
    matches = []
    
    # First try exact match
    for emp in employees:
        emp_name = emp.get("name", "").strip()
        if emp_name.lower() == name_lower:
            return [emp]  # Exact match, return immediately
    
    # Then try partial match (contains)
    for emp in employees:
        emp_name = emp.get("name", "").strip()
        if name_lower in emp_name.lower():
            matches.append(emp)
    
    return matches


async def _execute_pending_action(session: SessionState, pending_action: Dict[str, Any]) -> ChatResponse:
    """Execute a pending action that was confirmed by the user."""
    action_type = pending_action.get("type")
    data = pending_action.get("data", {})
    
    if action_type == "mark_absence":
        employee_name = data.get("employee_name")
        status = data.get("status", "A")
        dates = data.get("dates", [_today()])
        reason = data.get("reason", "")
        
        result = await absence_adapter.mark_absence(employee_name, dates, status, reason)
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        
        if result.get("success"):
            return ChatResponse(
                session_id=session.session_id,
                response=f"✅ Marked {employee_name} as {status_text} for {', '.join(dates)}.",
                action_type="absence_mark",
                action_data=result.get("details"),
            )
        else:
            return ChatResponse(
                session_id=session.session_id,
                response=result.get("message", "Could not mark absence."),
                action_type="absence_error",
            )
    
    return ChatResponse(
        session_id=session.session_id,
        response="I couldn't execute that action.",
        action_type="error",
    )


@app.post("/api/chat/select-option")
async def select_disambiguation_option(
    request: Dict[str, Any],
    session: SessionState = Depends(get_session),
) -> ChatResponse:
    """Handle user selection from disambiguation options."""
    option_metadata = request.get("metadata", {})
    selected_name = request.get("value")
    
    action = option_metadata.get("action")
    
    if action == "mark_absence":
        status = option_metadata.get("status", "A")
        date_str = option_metadata.get("date", _today())
        if date_str == "today":
            date_str = _today()
        elif date_str == "yesterday":
            date_str = (date.today() - timedelta(days=1)).isoformat()
        elif date_str == "tomorrow":
            date_str = (date.today() + timedelta(days=1)).isoformat()
            
        reason = option_metadata.get("reason", "")
        result = await absence_adapter.mark_absence(selected_name, [date_str], status, reason)
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        
        if result.get("success"):
            session.add_message("assistant", f"✅ Marked {selected_name} as {status_text} for {date_str}.")
            return ChatResponse(
                session_id=session.session_id,
                response=f"✅ Marked {selected_name} as {status_text} for {date_str}.",
                action_type="absence_mark",
                action_data=result.get("details"),
            )
    
    elif action == "query_absence":
        date_str = option_metadata.get("date")
        date_range = option_metadata.get("date_range")
        
        if date_range:
            start = date_range.get("start")
            end = date_range.get("end")
            result = await absence_adapter.query_absence(
                query_type="byDateRange",
                dates=[start, end],
                employee_name=selected_name,
            )
        elif date_str:
            if date_str == "today":
                date_str = _today()
            result = await absence_adapter.query_absence(
                query_type="byDate",
                dates=[date_str],
                employee_name=selected_name,
            )
        else:
            result = await absence_adapter.query_absence(
                query_type="byDate",
                dates=[_today()],
                employee_name=selected_name,
            )
        
        session.add_message("assistant", result.get("message", ""))
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Could not retrieve absence information."),
            action_type="absence_query" if result.get("success") else "absence_error",
            action_data=result.get("details"),
        )
    
    return ChatResponse(
        session_id=session.session_id,
        response="I couldn't process that selection.",
        action_type="error",
    )


@app.get("/api/sow/documents/{session_id}/{filename}")
async def download_sow_document(session_id: str, filename: str, settings: Settings = Depends(get_app_settings)) -> Response:
    path = settings.sow_output_dir / session_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path, filename=filename)
