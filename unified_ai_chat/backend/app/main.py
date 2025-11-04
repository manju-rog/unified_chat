"""FastAPI entrypoint for the unified AI chat orchestrator - GEMINI FIRST APPROACH."""
from __future__ import annotations

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import re
import uuid
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import Settings, get_settings
from .gemini_client import ToolCall, gemini_client
from .models import ChatRequest, ChatResponse, ConfirmationButton, DisambiguationOption, SessionState
from .services.absence import absence_adapter
from .services.sow_direct import SowAdapter
from .services.intent_classifier import intent_classifier, IntentType
from .sow_components.models import SowState
from .session_manager import session_manager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# SOW globals
SOW_SESSIONS: dict[str, SowState] = {}
sow_adapter = SowAdapter(out_root=Path("generated_docs_sow"))

# SOW generation locks to prevent double-fires
_SOW_LOCKS: Dict[str, asyncio.Lock] = {}

def _lock_for(session_id: str) -> asyncio.Lock:
    """Get or create a lock for the given session"""
    if session_id not in _SOW_LOCKS:
        _SOW_LOCKS[session_id] = asyncio.Lock()
    return _SOW_LOCKS[session_id]

GENERIC_EMPLOYEE_TOKENS = {
    "someone", "somebody", "anyone", "anybody", "employee", "staff",
    "person", "people", "member", "team member", "them", "him", "her", "they",
}

EXIT_SOW_COMMANDS = {"exit sow", "exit", "quit", "cancel", "stop sow", "exit_sow"}


def _prompt_sow_confirmation(session: SessionState, project_overview: str) -> ChatResponse:
    session.metadata["pending_action"] = {
        "type": "start_sow",
        "data": {"project_overview": project_overview},
    }
    message = (
        "Do you want me to start the Statement of Work generation flow now?\n\n"
        "Once we begin, I'll switch to SOW mode (red theme) and collect the project details step by step."
    )
    confirmation_buttons = [
        ConfirmationButton(
            id="sow_confirm_yes",
            label="Yes, start SOW generation",
            value="yes start sow generation",
            style="primary",
        ),
        ConfirmationButton(
            id="sow_confirm_no",
            label="No, keep chatting",
            value="no",
            style="secondary",
        ),
    ]
    return ChatResponse(
        session_id=session.session_id,
        response=message,
        action_type="confirmation_needed",
        confirmation_buttons=confirmation_buttons,
    )





async def _start_sow_session(session: SessionState, project_overview: str | None = None) -> ChatResponse:
    state = SowState()
    
    # Only use project_overview if it's meaningful (not empty, not just "yes", etc.)
    meaningful_overview = False
    if project_overview:
        cleaned = project_overview.strip().lower()
        # Check if it's not just a confirmation word
        if cleaned and cleaned not in {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "start", "begin"}:
            state.data["project_info"] = project_overview.strip()
            state.stage = "services"
            meaningful_overview = True

    SOW_SESSIONS[session.session_id] = state
    session.metadata["active_sow"] = True

    if meaningful_overview:
        intro = (
            "🚀 **SOW session started!**\n\n"
            f"I captured your overview:\n> {project_overview}\n\n"
            "Now let's continue with the SOW wizard."
        )
        next_prompt = "Please select the type of services for this SOW:"
        hint = {
            "message": "Choose the services package below.",
            "confirmation_buttons": [
                {"id": "sow_service_standard", "label": "📦 Standard Package", "populate_input": "standard", "style": "primary"},
                {"id": "sow_service_custom", "label": "🛠️ Custom Services", "populate_input": "custom", "style": "secondary"},
            ],
        }
        state.stage = "services"
        response_text = f"{intro}\n\n{next_prompt}"
    else:
        # ALWAYS start with project info question
        question, hint = sow_adapter.start()
        response_text = question

    # Convert buttons to use populate_input instead of value
    confirmation_buttons = hint.get("confirmation_buttons", [])
    if confirmation_buttons:
        confirmation_buttons = [
            ConfirmationButton(
                id=btn["id"],
                label=btn["label"],
                populate_input=btn.get("populate_input", btn.get("value")),
                style=btn.get("style", "primary"),
            )
            for btn in confirmation_buttons
        ]
    else:
        confirmation_buttons = []

    # Ensure theme is set to SOW mode
    if not hint:
        hint = {}
    hint["theme"] = "sow"
    
    logger.info(f"Started SOW session for {session.session_id}, switching to SOW theme")
    
    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        action_type="sow_started",
        action_data=hint,
        confirmation_buttons=confirmation_buttons,
    )


async def _exit_sow_session(session: SessionState, message: Optional[str] = None) -> ChatResponse:
    # Clear ALL SOW-related state completely
    SOW_SESSIONS.pop(session.session_id, None)
    session.metadata.pop("active_sow", None)
    session.metadata.pop("sow_active", None)
    session.metadata.pop("pending_action", None)
    session.metadata.pop("waiting_for_reason", None)
    
    logger.info(f"Exited SOW session for {session.session_id}, returning to normal mode")
    
    response_text = message or (
        "✅ **Exited SOW mode.**\n\n"
        "I'm back to the unified assistant. Ask me anything about absence management or start a new SOW anytime."
    )
    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        action_type="sow_exit",
        action_data={"theme": "normal"}  # Explicitly set theme back to normal
    )


async def _process_sow_message(session: SessionState, user_message: str) -> ChatResponse:
    state = SOW_SESSIONS.get(session.session_id)
    if state is None:
        return await _exit_sow_session(session, "SOW session was not active. I'm back to the main assistant.")

    # Quick-reply / text command → call the same function
    cleaned = user_message.strip().lower().replace(" ", "_")
    if cleaned == "generate_sow":
        return await do_generate_sow(session, state.data)

    state, hint = sow_adapter.process(state, user_message)
    SOW_SESSIONS[session.session_id] = state

    if hint.get("silent_update"):
        # Include confirmation buttons in silent updates
        confirmation_buttons = hint.get("confirmation_buttons", [])
        combined_buttons: List[ConfirmationButton] = []

        for btn in confirmation_buttons:
            combined_buttons.append(
                ConfirmationButton(
                    id=btn["id"],
                    label=btn["label"],
                    populate_input=btn.get("populate_input"),
                    style=btn.get("style", "primary"),
                )
            )
        
        # Ensure theme stays as SOW
        if not hint:
            hint = {}
        hint["theme"] = "sow"
        
        return ChatResponse(
            session_id=session.session_id,
            response="",
            action_type="sow_silent_update",
            action_data=hint,
            confirmation_buttons=combined_buttons,
        )

    confirmation_buttons = hint.get("confirmation_buttons", [])
    combined_buttons: List[ConfirmationButton] = []

    for btn in confirmation_buttons:
        combined_buttons.append(
            ConfirmationButton(
                id=btn["id"],
                label=btn["label"],
                populate_input=btn.get("populate_input"),  # Use populate_input for new behavior
                style=btn.get("style", "primary"),
            )
        )

    # Ensure theme stays as SOW
    if not hint:
        hint = {}
    hint["theme"] = "sow"

    return ChatResponse(
        session_id=session.session_id,
        response=hint.get("message", "Let's keep building the SOW."),
        action_type="sow_processing",
        action_data=hint,
        confirmation_buttons=combined_buttons,
    )


def _in_sow_session(session: SessionState) -> bool:
    return session.metadata.get("active_sow", False) and session.session_id in SOW_SESSIONS





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

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks = None,
    session: SessionState = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    logger.info("Processing chat message for session %s", session.session_id)
    
    user_message = request.message.strip()
    session.add_message("user", user_message)
    lowered = user_message.lower()

    pending_action = session.metadata.get("pending_action")
    if pending_action and pending_action.get("type") == "start_sow":
        if lowered in {"yes", "yes start sow generation", "y", "start sow", "yes, start sow generation"}:
            session.metadata.pop("pending_action", None)
            return await _start_sow_session(
                session, pending_action.get("data", {}).get("project_overview")
            )
        if lowered in {"no", "n", "nope", "not now"}:
            session.metadata.pop("pending_action", None)
            return ChatResponse(
                session_id=session.session_id,
                response="Okay, I won't start the SOW workflow right now. Let me know if you change your mind!",
                action_type="confirmation_cancelled",
            )

    # Handle SOW exit command at any point - even if session is not active
    # This handles the case where user says "exit sow" after generation completes
    if lowered in EXIT_SOW_COMMANDS:
        if _in_sow_session(session):
            return await _exit_sow_session(session)
        else:
            # User said exit but not in SOW - acknowledge and continue
            return ChatResponse(
                session_id=session.session_id,
                response="✅ You're already in normal mode. How can I help you with absence management or SOW generation?",
                action_type="already_in_normal_mode",
                action_data={"theme": "normal"}
            )

    # If we're actively in a SOW flow, keep the conversation there
    if _in_sow_session(session):
        return await _process_sow_message(session, user_message)

    # **GEMINI-FIRST APPROACH: Every message goes to Gemini with full context**
    context_parts = []
    
    # Add employee context for better name matching
    try:
        employees = await absence_adapter.get_employees()
        employee_entries = [
            f"{emp.get('name')}|{emp.get('id')}|{emp.get('department')}"
            for emp in employees
            if emp.get("name")
        ]
        if employee_entries:
            context_parts.append(
                "EMPLOYEE_DIRECTORY: "
                + "; ".join(employee_entries)
            )
    except Exception as e:
        logger.warning(f"Could not fetch employees: {e}")
    
    # Add conversation context
    pending_action = session.metadata.get("pending_action")
    if pending_action:
        action_type = pending_action.get("type", "")
        if action_type == "ask_reason":
            context_parts.append("CONTEXT: User was asked if they want to add a reason for marking absence")
        elif action_type == "ask_employee_name":
            context_parts.append("CONTEXT: User was asked to provide an employee name")
    
    full_context = " | ".join(context_parts) if context_parts else None
    
    # **ALWAYS SEND TO GEMINI - LET GEMINI DECIDE EVERYTHING**
    try:
        gemini_response = gemini_client.generate(session, user_message, full_context)
        parsed_response = gemini_client.parse_response(gemini_response)
        thinking = parsed_response.get("thinking")
        
        # Handle Gemini's tool calls
        if parsed_response["tool_calls"]:
            tool_call = parsed_response["tool_calls"][0]
            
            if tool_call.name == "absence_chat":
                response = await _handle_gemini_absence_call(session, tool_call, user_message)
                response.thinking = thinking
                return response
            elif tool_call.name == "start_sow_session":
                response = await _handle_sow_confirmation(session, tool_call, user_message)
                response.thinking = thinking
                return response
            elif tool_call.name == "provide_guidance":
                response = _handle_gemini_guidance(session, tool_call)
                response.thinking = thinking
                return response
        
        # If Gemini provided text response
        if parsed_response["text"]:
            session.add_message("assistant", parsed_response["text"])
            return ChatResponse(
                session_id=session.session_id,
                response=parsed_response["text"],
                action_type="gemini_text_response",
                thinking=thinking
            )
        
        # Gemini didn't return a tool call or text. Fall back to deterministic classifier
        fallback = await _attempt_classifier_fallback(session, user_message)
        if fallback:
            return fallback

        # Fallback message if both Gemini and classifier could not help
        return ChatResponse(
            session_id=session.session_id,
            response="I understand you want help. I can assist with absence management or SOW generation. What would you like to do?",
            action_type="clarification_needed"
        )
        
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        
        # Check if it's a quota/rate limit error
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "resource exhausted" in error_str:
            logger.warning("Gemini API quota exceeded, using fallback classifier")
            # Try fallback classifier
            try:
                fallback = await _attempt_classifier_fallback(session, user_message)
                if fallback:
                    return fallback
            except Exception as fallback_error:
                logger.error(f"Fallback classifier also failed: {fallback_error}")
            
            return ChatResponse(
                session_id=session.session_id,
                response="⚠️ AI service is temporarily unavailable (quota exceeded). Please try again in a moment, or rephrase your request.",
                action_type="quota_exceeded"
            )
        
        # Generic error
        return ChatResponse(
            session_id=session.session_id,
            response="I'm having trouble processing your request. Could you please rephrase it?",
            action_type="error_recovery"
        )


async def _handle_gemini_absence_call(session: SessionState, tool_call: ToolCall, user_message: str) -> ChatResponse:
    """Handle Gemini's absence_chat tool calls with full natural language understanding."""
    args = tool_call.arguments
    action = args.get("action")
    
    if action == "mark_absence":
        employee_name = args.get("employee_name", "").strip()
        status = args.get("status", "A")
        date_str = args.get("date", "today")
        reason = args.get("reason", "")
        
        # If employee name is generic or missing, ask for specific name
        if not employee_name or employee_name.lower() in GENERIC_EMPLOYEE_TOKENS:
            employees = await absence_adapter.get_employees()
            available_names = [emp.get("name", "") for emp in employees if emp.get("name")]
            
            session.metadata["pending_action"] = {
                "type": "ask_employee_name",
                "data": {"status": status, "dates": [_normalize_date_str(date_str)], "reason": reason}
            }
            
            status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, "absent")
            prompt_examples = (
                "Who do you want to mark absent, and on what date?\n\n"
                "You can try:\n"
                "• Mark Manju absent tomorrow\n"
                "• Mark Shreyas absent on 2025-10-16"
            )
            return ChatResponse(
                session_id=session.session_id,
                response=(
                    f"Which employee would you like to mark as {status_text}? Please provide a name.\n\n"
                    f"**Available employees:** {', '.join(available_names[:5])}{'...' if len(available_names) > 5 else ''}\n\n"
                    f"{prompt_examples}"
                ),
                action_type="employee_name_needed",
                action_data={"theme": "absence"}
            )
        
        # Try to match employee name
        employees = await absence_adapter.get_employees()
        matches = _find_employee_matches(employee_name, employees)
        
        if not matches:
            # Suggest similar names using fuzzy matching
            suggestions = []
            for emp in employees:
                if _calculate_name_similarity(employee_name.lower(), emp["name"].lower()) >= 0.6:
                    suggestions.append(emp["name"])
            
            response = f"I couldn't find '{employee_name}'."
            if suggestions:
                response += f" Did you mean: {', '.join(suggestions[:3])}?"
            return ChatResponse(
                session_id=session.session_id, 
                response=response, 
                action_type="employee_not_found",
                action_data={"theme": "absence"}
            )
        
        if len(matches) > 1:
            options = [DisambiguationOption(id=f"emp_{emp['id']}", label=emp['name'], value=emp['name']) for emp in matches]
            return ChatResponse(
                session_id=session.session_id,
                response=f"Multiple employees found for '{employee_name}'. Please select:",
                action_type="disambiguation_required",
                disambiguation_options=options
            )
        
        # Single match - proceed with marking
        matched_employee = matches[0]
        if matched_employee["name"].strip().lower() != employee_name.lower():
            option = DisambiguationOption(
                id=f"emp_{matched_employee['id']}",
                label=f"{matched_employee['name']} ({matched_employee.get('department', 'N/A')})",
                value=matched_employee['name'],
                metadata={
                    "employee_id": matched_employee['id'],
                    "action": action,
                    "status": status,
                    "date": _normalize_date_str(date_str),
                    "reason": reason,
                }
            )
            return ChatResponse(
                session_id=session.session_id,
                response=(
                    f"I couldn't find an exact match for '{employee_name}'. "
                    f"Did you mean **{matched_employee['name']}**?"
                ),
                action_type="employee_name_clarification",
                disambiguation_options=[option],
                action_data={"theme": "absence"}
            )

        normalized_date = _normalize_date_str(date_str)
        
        # If no reason provided, ask for it
        if not reason:
            session.metadata["pending_action"] = {
                "type": "ask_reason",
                "data": {"employee_name": matched_employee["name"], "status": status, "dates": [normalized_date], "reason": ""}
            }
            status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, "absent")
            return ChatResponse(
                session_id=session.session_id,
                response=f"Would you like to add a reason for marking {matched_employee['name']} as {status_text}?",
                action_type="reason_confirmation",
                confirmation_buttons=[
                    ConfirmationButton(id="reason_yes", label="Yes, add reason", value="yes", style="primary"),
                    ConfirmationButton(id="reason_no", label="No, skip", value="no", style="secondary")
                ],
                action_data={"theme": "absence"}
            )
        
        # Execute the marking
        result = await absence_adapter.mark_absence(
            employee_name=matched_employee["name"],
            status=status,
            dates=[normalized_date],
            reason=reason
        )
        
        session.add_message("assistant", result.get("message", "Absence marked successfully"))
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Absence marked successfully"),
            action_type="absence_marked",
            action_data={"theme": "absence"}
        )
    
    elif action == "query_absence":
        query_type = args.get("query_type", "all_absent")
        time_period = args.get("time_period")
        date_range = args.get("date_range")
        month = args.get("month")
        # ALWAYS use current year if not specified
        year = args.get("year", datetime.now().year)
        
        logger.info(f"Query absence - args: {args}, time_period: {time_period}, query_type: {query_type}, year: {year}")
        
        # Check for month FIRST before checking time_period
        if month:
            # Convert month name to number and use the provided year
            month_num = _month_name_to_number(month)
            month_str = f"{int(year)}-{month_num:02d}"
            logger.info(f"Querying month: {month_str} (month={month}, year={year})")
            result = await absence_adapter.query_absence(query_type="byMonth", month=month_str)
        elif date_range:
            start_raw = date_range.get("start") or ""
            end_raw = date_range.get("end") or ""
            start_date = _normalize_date_str(start_raw)
            end_date = _normalize_date_str(end_raw)
            logger.info(f"Date range: {start_date} to {end_date}")
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        elif time_period == "today":
            target_date = _normalize_date_str(args.get("date", "today"))
            logger.info(f"Querying by date: {target_date}")
            result = await absence_adapter.query_absence(query_type="byDate", dates=[target_date])
        elif time_period == "yesterday":
            result = await absence_adapter.query_absence(
                query_type="byDate", dates=[_normalize_date_str("yesterday")]
            )
        elif time_period == "tomorrow":
            result = await absence_adapter.query_absence(
                query_type="byDate", dates=[_normalize_date_str("tomorrow")]
            )
        elif time_period in {"this_week", "next_week", "last_week"}:
            start_date, end_date = _calculate_week_range(time_period)
            logger.info(f"Week range: {start_date} to {end_date}")
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        elif time_period in {"this_month", "next_month", "last_month"}:
            start_date, end_date = _calculate_month_range(time_period)
            logger.info(f"Month range: {start_date} to {end_date}")
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        else:
            # Default to today if nothing else matches
            target_date = _normalize_date_str(args.get("date", "today"))
            logger.info(f"Querying by date (default): {target_date}")
            result = await absence_adapter.query_absence(query_type="byDate", dates=[target_date])
        
        session.add_message("assistant", result.get("message", "Query completed"))
        
        # Pass details to action_data for frontend rendering
        action_data = {"theme": "absence"}
        if result.get("details"):
            action_data.update(result["details"])
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Query completed"),
            action_type="absence_query_result",
            action_data=action_data
        )
    
    elif action == "query_vacation":
        target_date = _normalize_date_str(args.get("date", "today"))
        result = await absence_adapter.query_absence(
            query_type="byStatus", status="V", dates=[target_date]
        )
        session.add_message("assistant", result.get("message", "Vacation query completed"))
        
        # Pass details to action_data for frontend rendering
        action_data = {"theme": "absence"}
        if result.get("details"):
            action_data.update(result["details"])
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Vacation query completed"),
            action_type="vacation_query_result",
            action_data=action_data
        )
    
    elif action == "check_employee_status":
        employee_name = args.get("employee_name", "")
        query_type = args.get("query_type", "specific_employee")
        date_str = args.get("date", "today")
        
        if not employee_name:
            return ChatResponse(
                session_id=session.session_id,
                response="Please specify which employee you'd like to check.",
                action_type="employee_name_needed",
                action_data={"theme": "absence"}
            )
        
        result = await absence_adapter.check_employee_status(
            employee_name=employee_name,
            date=_normalize_date_str(date_str),
            query_type=query_type
        )
        
        session.add_message("assistant", result.get("message", "Status check completed"))
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Status check completed"),
            action_type="employee_status_result",
            action_data={"theme": "absence"}
        )

    # Default fallback
    return ChatResponse(
        session_id=session.session_id,
        response="I understand you want help with absence management. Could you be more specific?",
        action_type="absence_clarification_needed",
        action_data={"theme": "absence"}
    )


async def _handle_confirmation_yes(session: SessionState, intent_result) -> ChatResponse:
    pending_action = session.metadata.get("pending_action")
    if not pending_action:
        return ChatResponse(
            session_id=session.session_id,
            response="I don't have any pending actions to confirm. How else can I help you?",
            action_type="no_pending_action",
        )

    action_type = pending_action.get("type")

    if action_type == "ask_reason":
        session.metadata["waiting_for_reason"] = True
        return ChatResponse(
            session_id=session.session_id,
            response="Please provide the reason:",
            action_type="awaiting_reason",
            action_data={"theme": "absence"}
        )
    if action_type == "start_sow":
        session.metadata.pop("pending_action", None)
        return await _start_sow_session(
            session, pending_action.get("data", {}).get("project_overview")
        )

    pending_action["type"] = "mark_absence"
    return await _execute_pending_action(session, pending_action)


async def _handle_confirmation_no(session: SessionState, intent_result) -> ChatResponse:
    pending_action = session.metadata.get("pending_action")
    if pending_action and pending_action.get("type") == "ask_reason":
        pending_action["data"]["reason"] = pending_action["data"].get("reason") or "Not provided"
        pending_action["type"] = "mark_absence"
        session.metadata.pop("waiting_for_reason", None)
        return await _execute_pending_action(session, pending_action)
    if pending_action and pending_action.get("type") == "start_sow":
        session.metadata.pop("pending_action", None)
        return ChatResponse(
            session_id=session.session_id,
            response="Okay, I won't start the SOW workflow right now. Let me know if you change your mind!",
            action_type="confirmation_cancelled",
        )

    session.metadata.pop("pending_action", None)
    session.metadata.pop("waiting_for_reason", None)
    return ChatResponse(
        session_id=session.session_id,
        response="Okay, cancelled. What would you like to do next?",
        action_type="action_cancelled",
    )


async def _handle_reason_provided(session: SessionState, intent_result) -> ChatResponse:
    pending_action = session.metadata.get("pending_action")
    if not pending_action:
        return ChatResponse(
            session_id=session.session_id,
            response="Thanks for the information. How else can I help you?",
            action_type="reason_acknowledged",
            action_data={"theme": "unified"}
        )

    pending_action["data"]["reason"] = intent_result.extracted_data.get("reason", "")
    pending_action["type"] = "mark_absence"
    return await _execute_pending_action(session, pending_action)


async def _execute_pending_action(session: SessionState, pending_action: Dict[str, Any]) -> ChatResponse:
    action_type = pending_action.get("type")
    data = pending_action.get("data", {})

    if action_type == "mark_absence":
        employee_name = data.get("employee_name")
        status = data.get("status", "A")
        dates = data.get("dates", [_today()])
        reason = data.get("reason", "") or "Not provided"

        normalized_dates = [_normalize_date_str(value) for value in dates]
        result = await absence_adapter.mark_absence(employee_name, normalized_dates, status, reason)

        session.metadata.pop("pending_action", None)
        session.metadata.pop("waiting_for_reason", None)

        if result.get("success"):
            session.add_message("assistant", result.get("message", "Absence updated."))
            details = result.get("details", {})
            if not isinstance(details, dict):
                details = {}
            details["theme"] = "absence"
            return ChatResponse(
                session_id=session.session_id,
                response=result.get("message", "Absence updated."),
                action_type="absence_mark",
                action_data=details,
            )
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Unable to update absence."),
            action_type="absence_error",
            action_data={"theme": "absence"}
        )

    return ChatResponse(
        session_id=session.session_id,
        response="I couldn't execute that action.",
        action_type="error",
    )


async def _handle_gemini_sow_call(session: SessionState, tool_call: ToolCall) -> ChatResponse:
    """Handle SOW session start from Gemini."""
    args = tool_call.arguments
    project_overview = args.get("projectOverview", "")

    if _in_sow_session(session):
        return ChatResponse(
            session_id=session.session_id,
            response="We are already in the SOW workflow. Please continue answering the prompts or type 'exit sow' to leave.",
            action_type="sow_processing",
            confirmation_buttons=[_build_exit_button()],
        )

    return _prompt_sow_confirmation(session, project_overview)


async def _attempt_classifier_fallback(session: SessionState, user_message: str) -> Optional[ChatResponse]:
    """Use the deterministic classifier when Gemini does not produce a tool call."""
    session_context = {
        "pending_action": session.metadata.get("pending_action"),
        "waiting_for_reason": session.metadata.get("waiting_for_reason", False),
        "session_history": session.recent_history(3),
    }
    
    intent_result = intent_classifier.classify_intent(user_message, session_context)
    
    # Handle confirmations and reasons immediately
    if intent_result.intent_type == IntentType.CONFIRMATION_YES:
        return await _handle_confirmation_yes(session, intent_result)
    if intent_result.intent_type == IntentType.CONFIRMATION_NO:
        return await _handle_confirmation_no(session, intent_result)
    if intent_result.intent_type == IntentType.REASON_PROVIDED:
        return await _handle_reason_provided(session, intent_result)
    
    absence_intents = {
        IntentType.MARK_ABSENCE,
        IntentType.MARK_MULTIPLE_ABSENCE,
        IntentType.QUERY_ABSENCE_TODAY,
        IntentType.QUERY_ABSENCE_MONTH,
        IntentType.QUERY_ABSENCE_SPECIFIC_MONTH,
        IntentType.QUERY_ABSENCE_WEEK,
        IntentType.QUERY_ABSENCE_DATE_RANGE,
        IntentType.QUERY_VACATION,
        IntentType.CHECK_EMPLOYEE_SPECIFIC_DAY,
        IntentType.CHECK_EMPLOYEE_LEAVE,
    }

    if intent_result.intent_type in absence_intents:
        tool_args = _build_tool_args_from_intent(intent_result)
        if tool_args:
            tool_call = ToolCall(name="absence_chat", arguments=tool_args)
            return await _handle_gemini_absence_call(session, tool_call, user_message)

    sow_intents = {
        IntentType.CREATE_SOW,
        IntentType.GENERATE_SOW,
        IntentType.SOW_REPORT,
        IntentType.PROJECT_DETAILS_SOW,
    }

    if intent_result.intent_type in sow_intents:
        overview = intent_result.extracted_data.get("project_overview") if intent_result.extracted_data else None
        return _prompt_sow_confirmation(session, overview or user_message)

    return None


def _build_tool_args_from_intent(intent_result) -> Optional[Dict[str, Any]]:
    """Translate an intent classification into absence_chat tool arguments."""
    data = intent_result.extracted_data or {}

    if intent_result.intent_type == IntentType.MARK_ABSENCE:
        return {
            "action": "mark_absence",
            "employee_name": data.get("employee_name", ""),
            "status": data.get("status", "A"),
            "date": data.get("date", "today"),
        }

    if intent_result.intent_type == IntentType.MARK_MULTIPLE_ABSENCE:
        names = data.get("employee_names") or []
        if not names:
            return None
        return {
            "action": "mark_multiple_absence",
            "employee_names": names,
            "status": data.get("status", "A"),
            "date": data.get("date", "today"),
        }

    if intent_result.intent_type == IntentType.QUERY_ABSENCE_TODAY:
        return {"action": "query_absence", "time_period": "today"}

    if intent_result.intent_type == IntentType.QUERY_ABSENCE_MONTH:
        return {"action": "query_absence", "time_period": "this_month"}

    if intent_result.intent_type == IntentType.QUERY_ABSENCE_SPECIFIC_MONTH:
        return {
            "action": "query_absence",
            "month": data.get("month"),
            "year": data.get("year", datetime.now().year),
        }

    if intent_result.intent_type == IntentType.QUERY_ABSENCE_WEEK:
        return {
            "action": "query_absence",
            "time_period": data.get("week_type", "this_week"),
        }

    if intent_result.intent_type == IntentType.QUERY_ABSENCE_DATE_RANGE:
        date_range = data.get("date_range")
        if date_range and len(date_range) >= 2:
            return {
                "action": "query_absence",
                "date_range": {"start": date_range[0], "end": date_range[1]},
            }
        month_range = data.get("month_range")
        day_range = data.get("day_range")
        if month_range and day_range and len(day_range) >= 2:
            start = f"{month_range[0]} {day_range[0]}"
            end = f"{month_range[-1]} {day_range[1]}"
            return {
                "action": "query_absence",
                "date_range": {"start": start, "end": end},
            }
        return {
            "action": "query_absence",
            "time_period": "today",
        }

    if intent_result.intent_type == IntentType.QUERY_VACATION:
        return {"action": "query_vacation"}

    if intent_result.intent_type == IntentType.CHECK_EMPLOYEE_SPECIFIC_DAY:
        return {
            "action": "check_employee_status",
            "employee_name": data.get("employee_name", ""),
            "date": data.get("day", "today"),
            "query_type": "specific_employee",
        }

    if intent_result.intent_type == IntentType.CHECK_EMPLOYEE_LEAVE:
        return {
            "action": "check_employee_status",
            "employee_name": data.get("employee_name", ""),
            "date": data.get("day", "today"),
            "query_type": "leave_status",
        }

    return None


def _handle_gemini_guidance(session: SessionState, tool_call: ToolCall) -> ChatResponse:
    """Handle guidance responses from Gemini with personality and humor."""
    args = tool_call.arguments
    guidance_type = args.get("guidance_type", "help")
    explanation = args.get("explanation", "")
    main_response = args.get("main_response", "")
    suggested_actions = args.get("suggested_actions", [])
    
    # Format response with personality
    response_parts = []
    
    # Add emoji based on guidance type
    emoji_map = {
        "greeting": "👋",
        "capabilities": "🤖",
        "confused": "🤔",
        "incomplete": "🧩",
        "out_of_context": "🎯",
        "ambiguous": "❓",
        "help": "💡"
    }
    emoji = emoji_map.get(guidance_type, "💬")
    
    # Add explanation if provided (in italics)
    if explanation:
        response_parts.append(f"*{explanation}*\n")
    
    # Add main response with emoji
    if main_response:
        response_parts.append(f"{emoji} {main_response}")
    
    # Add suggested actions in a friendly format
    if suggested_actions:
        if guidance_type in ["confused", "incomplete", "ambiguous"]:
            response_parts.append("\n**Here are some things I can help with:**")
        else:
            response_parts.append("\n**You can try:**")
        
        for action in suggested_actions:
            response_parts.append(f"• {action}")
    
    response_text = "\n".join(response_parts)
    
    # Add helpful buttons based on guidance type
    buttons = []
    if guidance_type in ["capabilities", "greeting", "help"]:
        buttons = [
            ConfirmationButton(
                id="absence_help", 
                label="📅 Check Absences", 
                populate_input="Who is absent today?", 
                style="primary"
            ),
            ConfirmationButton(
                id="sow_help", 
                label="📄 Create SOW", 
                populate_input="Create a statement of work", 
                style="primary"
            )
        ]
    elif guidance_type in ["confused", "incomplete", "ambiguous", "out_of_context"]:
        # Provide quick action buttons for confused users
        buttons = [
            ConfirmationButton(
                id="quick_absence", 
                label="📅 Absence Management", 
                populate_input="Show me today's absences", 
                style="secondary"
            ),
            ConfirmationButton(
                id="quick_sow", 
                label="📄 SOW Generation", 
                populate_input="I want to create a SOW", 
                style="secondary"
            ),
            ConfirmationButton(
                id="quick_help", 
                label="❓ What can you do?", 
                populate_input="What can you help me with?", 
                style="secondary"
            )
        ]
    
    session.add_message("assistant", response_text)
    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        action_type=f"guidance_{guidance_type}",
        confirmation_buttons=buttons
    )


async def _execute_tool_call(session: SessionState, call: ToolCall, settings: Settings) -> Dict[str, Any]:
    """
    Backwards-compatible helper used by legacy tests to trigger tool execution without Gemini.
    """
    if call.name == "absence_chat":
        response = await _handle_gemini_absence_call(session, call, "")
    elif call.name == "start_sow_session":
        response = await _handle_gemini_sow_call(session, call)
    elif call.name == "provide_guidance":
        response = _handle_gemini_guidance(session, call)
    else:
        raise ValueError(f"Unsupported tool call: {call.name}")

    return {
        "message": response.response,
        "action_type": response.action_type,
        "action_data": response.action_data,
        "confirmation_buttons": response.confirmation_buttons,
        "disambiguation_options": response.disambiguation_options,
        "download_path": response.download_url,
    }


# Utility functions
def _today() -> str:
    return date.today().isoformat()

def _normalize_date_str(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD format."""
    if not date_str:
        return _today()

    if date_str.lower() == "today":
        return _today()
    elif date_str.lower() == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    elif date_str.lower() == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    
    cleaned = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            parsed_date = datetime.strptime(cleaned, fmt).date()
            return parsed_date.isoformat()
        except ValueError:
            continue

    month_day_match = re.match(r"([A-Za-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?", cleaned)
    if month_day_match:
        month_num = _month_name_to_number(month_day_match.group(1))
        day = int(month_day_match.group(2))
        year = int(month_day_match.group(3)) if month_day_match.group(3) else datetime.now().year
        try:
            return date(year, month_num, day).isoformat()
        except ValueError:
            return _today()

    return _today()

def _find_employee_matches(name: str, employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find employee matches by name with fuzzy matching."""
    if not name:
        return []
    
    name_lower = name.lower().strip()
    exact_matches = []
    fuzzy_matches = []
    
    for emp in employees:
        emp_name = emp.get("name", "").lower().strip()
        if emp_name == name_lower:
            exact_matches.append(emp)
        elif name_lower in emp_name or emp_name in name_lower:
            fuzzy_matches.append(emp)
        elif _calculate_name_similarity(name_lower, emp_name) >= 0.7:
            fuzzy_matches.append(emp)
    
    return exact_matches or fuzzy_matches

def _calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names."""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

def _month_name_to_number(month_name: str) -> int:
    """Convert month name to number. Returns current month if not found."""
    months = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    return months.get(month_name.lower(), datetime.now().month)


def _calculate_week_range(week_type: str) -> Tuple[str, str]:
    """Return ISO date range for week descriptors relative to today."""
    today = date.today()
    if week_type == "this_week":
        start = today - timedelta(days=today.weekday())
    elif week_type == "next_week":
        start = today + timedelta(days=(7 - today.weekday()))
    else:  # last_week
        start = today - timedelta(days=today.weekday() + 7)
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _calculate_month_range(month_type: str) -> Tuple[str, str]:
    """Return ISO date range for month descriptors relative to today."""
    today = date.today()
    if month_type == "this_month":
        start = today.replace(day=1)
    elif month_type == "next_month":
        if today.month == 12:
            start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            start = today.replace(month=today.month + 1, day=1)
    else:  # last_month
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            start = today.replace(month=today.month - 1, day=1)

    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1, day=1)
    else:
        next_month = start.replace(month=start.month + 1, day=1)

    end = next_month - timedelta(days=1)
    return start.isoformat(), end.isoformat()

# SOW Session Management
from .services.sow_session import sow_session_manager, SOWStage
from .services.sow_generator import sow_generator

async def _handle_sow_confirmation(session: SessionState, tool_call: ToolCall, user_message: str) -> ChatResponse:
    """Handle SOW intent with seamless transition"""
    
    # Check if there's a pending absence action - offer seamless transition
    pending_action = session.metadata.get("pending_action")
    if pending_action and pending_action.get("type") not in ["start_sow"]:
        # Clear pending absence action and transition to SOW
        session.metadata.pop("pending_action", None)
        session.metadata.pop("waiting_for_reason", None)
        logger.info(f"Seamlessly transitioning from absence to SOW for session {session.session_id}")
    
    # Set pending action for SOW confirmation (compatible with existing system)
    project_overview = tool_call.arguments.get("projectOverview", "")
    session.metadata["pending_action"] = {
        "type": "start_sow",
        "data": {"project_overview": project_overview}
    }
    
    # Ask for confirmation before starting SOW session
    return ChatResponse(
        session_id=session.session_id,
        response="🔴 **SOW Generation Request Detected**\n\nDo you want to start the SOW (Statement of Work) generation process?\n\n⚠️ **Note**: This will switch to SOW mode with a red theme and collect information step by step. You can exit anytime by typing 'exit sow'.",
        action_type="sow_confirmation_needed",
        confirmation_buttons=[
            ConfirmationButton(id="start_sow", label="Yes, Start SOW Generation", value="yes", style="primary"),
            ConfirmationButton(id="cancel_sow", label="No, Stay in Normal Mode", value="no", style="secondary")
        ]
    )

async def _handle_sow_session_input(session: SessionState, user_message: str) -> ChatResponse:
    """Handle input during active SOW session"""
    
    # Check for exit command
    if user_message.lower().strip() in ["exit sow", "exit", "quit sow", "cancel sow"]:
        result = sow_session_manager.exit_sow_session(session.session_id)
        session.metadata.pop("sow_active", None)
        
        return ChatResponse(
            session_id=session.session_id,
            response=result["message"],
            action_type="sow_exited"
        )
    
    # Check for SOW confirmation responses
    if user_message.lower().strip() == "start_sow_confirmed":
        result = sow_session_manager.start_sow_session(session.session_id)
        session.metadata["sow_active"] = True
        
        return ChatResponse(
            session_id=session.session_id,
            response=result["message"],
            action_type="sow_started",
            action_data={
                "theme": "sow",
                "show_exit": True,
                "progress": result.get("progress", 1),
                "total_steps": result.get("total_steps", 8)
            }
        )
    
    elif user_message.lower().strip() == "cancel_sow":
        return ChatResponse(
            session_id=session.session_id,
            response="✅ Staying in normal mode. How can I help you with absence management?",
            action_type="sow_cancelled"
        )
    
    # Process SOW input
    result = sow_session_manager.process_sow_input(session.session_id, user_message)
    
    if "error" in result:
        return ChatResponse(
            session_id=session.session_id,
            response=f"❌ Error: {result['error']}",
            action_type="sow_error"
        )
    
    # Check if document generation was requested
    if result.get("action") == "generate_document":
        return await do_generate_sow(session, result["session_data"])
    
    # Return SOW response
    response_data = {
        "theme": result.get("theme", "sow"),
        "show_exit": result.get("show_exit", True),
        "progress": result.get("progress", 1),
        "total_steps": result.get("total_steps", 8)
    }
    
    # Add buttons if present
    if "buttons" in result:
        response_data["confirmation_buttons"] = [
            ConfirmationButton(
                id=btn["id"], 
                label=btn["label"], 
                value=btn["value"],
                style=btn.get("style", "secondary")
            ) for btn in result["buttons"]
        ]
    
    return ChatResponse(
        session_id=session.session_id,
        response=result["message"],
        action_type="sow_step_completed",
        action_data=response_data
    )

async def do_generate_sow(session: SessionState, collected_data: Dict[str, Any]) -> ChatResponse:
    """Single entry point for SOW generation - prevents dual triggers"""
    async with _lock_for(session.session_id):
        try:
            # Check state machine - prevent invalid transitions
            current_phase = collected_data.get("sow_phase", "ready_to_generate")
            if current_phase == "generating":
                return ChatResponse(
                    session_id=session.session_id,
                    response="⏳ SOW generation already in progress. Please wait...",
                    action_type="info"
                )
            elif current_phase == "generated":
                return ChatResponse(
                    session_id=session.session_id,
                    response="✅ SOW already generated. Start a new SOW if needed.",
                    action_type="info"
                )
            
            # Set generating state
            collected_data["sow_phase"] = "generating"
            
            logger.info(f"[SOW] START generate -> session={session.session_id}")
            
            # Progress bubble (non-action)
            session.add_message("assistant", "🤖 Generating your SOW… please wait.")
            logger.info(f"[SOW] progress bubble -> session={session.session_id}")
            
            # Call new_sow application directly via HTTP API (port 8002)
            # new_sow now has /api/generate-direct endpoint with Gemini AI processing
            import aiohttp
            
            # Prepare payload for new_sow
            new_sow_url = "http://localhost:8002/api/generate-direct"
            
            # Convert resources list to string format
            resources_list = collected_data.get("resources", [])
            resources_str = ""
            if isinstance(resources_list, list):
                resource_lines = []
                for r in resources_list:
                    role = r.get("role", "Team Member")
                    count = r.get("count", 1)
                    resource_lines.append(f"{role} - {count} person{'s' if count > 1 else ''} - 100% allocation")
                resources_str = "\\n".join(resource_lines)
            else:
                resources_str = str(resources_list)
            
            # Convert contacts dict to string format
            contacts_dict = collected_data.get("contacts", {})
            contacts_str = ""
            if isinstance(contacts_dict, dict) and contacts_dict:
                contacts_str = f"""Contractor Contact:
Name: Professional Services Team
Company: Professional Services Inc.
Role: Project Director
Email: pm@company.com
Phone: +1-555-0123
Address: 123 Business St, City, State

Client Contact:
Name: {contacts_dict.get('contact_person', 'Client Representative')}
Company: {contacts_dict.get('name', 'Client Organization')}
Role: {contacts_dict.get('designation', 'Project Sponsor')}
Email: {contacts_dict.get('email', 'client@company.com')}
Phone: {contacts_dict.get('phone', '+1-555-0456')}
Address: {contacts_dict.get('address', 'Client Address')}"""
                contacts_str = contacts_str.replace('\n', '\\n')
            
            # Convert collected_data to new_sow format
            payload = {
                "template_path": "sample_sow_template.docx",
                "project_data": {
                    "project_info": collected_data.get("project_info", ""),
                    "services": collected_data.get("services", ""),
                    "deliverables": collected_data.get("deliverables", ""),
                    "timeline": collected_data.get("timeline", ""),
                    "resources": resources_str,
                    "contacts": contacts_str,
                    "budget": collected_data.get("budget", "")
                },
                "session_id": session.session_id
            }
            
            logger.info(f"[SOW] Calling new_sow API at {new_sow_url}")
            
            try:
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.post(new_sow_url, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as response:
                        if response.status == 200:
                            res = await response.json()
                            logger.info(f"[SOW] new_sow API success: {res}")
                            res["success"] = True
                        else:
                            error_text = await response.text()
                            logger.error(f"[SOW] new_sow API error: {response.status} - {error_text}")
                            res = {"success": False, "error": f"API error: {response.status}"}
            except Exception as e:
                logger.error(f"[SOW] new_sow API call failed: {e}")
                res = {"success": False, "error": str(e)}
            
            if not res.get("success"):
                collected_data["sow_phase"] = "error"
                logger.error(f"[SOW] FAILED -> session={session.session_id} error={res.get('error')}")
                return ChatResponse(
                    session_id=session.session_id,
                    response=f"❌ SOW failed: {res.get('error')}",
                    action_type="error"
                )
            
            # Mark SOW session as completed - CLEAR ALL SOW STATE
            if hasattr(sow_session_manager, 'exit_sow_session'):
                sow_session_manager.exit_sow_session(session.session_id)
            
            # Clear all SOW-related metadata and session data
            session.metadata.pop("sow_active", None)
            session.metadata.pop("active_sow", None)
            session.metadata.pop("pending_action", None)
            SOW_SESSIONS.pop(session.session_id, None)
            
            # Emit the ONLY success action here
            filename = res.get("filename", "SOW_document.docx")
            # Construct proper download URL for unified chat backend
            download_url = f"http://localhost:8001/api/sow/download/{filename}"
            
            btn = {
                "label": "⬇️ Download SOW", 
                "action": "open_url",
                "url": download_url, 
                "style": "primary"
            }
            
            # Set generated state
            collected_data["sow_phase"] = "generated"
            
            logger.info(f"[SOW] SUCCESS card EMIT -> session={session.session_id} url={download_url}")
            
            return ChatResponse(
                session_id=session.session_id,
                response="✅ **SOW Document Generated Successfully!**\n\nYour document is ready and will download automatically.",
                action_type="sow_document_ready",
                download_url=download_url,
                action_data={
                    "buttons": [btn], 
                    "filename": filename,
                    "theme": "normal",
                    "loading": False,
                    "auto_download": True,
                    "download_url": download_url
                }
            )
                
        except Exception as e:
            collected_data["sow_phase"] = "error"
            logger.error(f"[SOW] ERROR -> session={session.session_id} error={e}")
            return ChatResponse(
                session_id=session.session_id,
                response=f"❌ Failed to generate SOW document: {str(e)}",
                action_type="sow_generation_error",
                action_data={"theme": "sow", "show_exit": True}
            )

# Add SOW download endpoints
@app.get("/api/sow/download/{filename}")
async def download_sow_document(filename: str):
    """Download generated SOW document"""
    try:
        # Check generated_docs_sow folder at project root
        project_root = Path(__file__).resolve().parents[2]
        file_path = project_root / "generated_docs_sow" / filename
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filename.endswith('.docx') else "text/plain",
                filename=filename
            )
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sow/documents/{session_id}/{filename}")
async def download_sow_document_by_session(session_id: str, filename: str):
    """Download generated SOW document by session"""
    try:
        # Check generated_docs_sow folder at project root
        project_root = Path(__file__).resolve().parents[2]
        file_path = project_root / "generated_docs_sow" / filename
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filename.endswith('.docx') else "text/plain",
                filename=filename
            )
        
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SOW generation is now handled immediately in the chat endpoint