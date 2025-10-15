"""FastAPI entrypoint for the unified AI chat orchestrator - GEMINI FIRST APPROACH."""
from __future__ import annotations

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
sow_adapter = SowAdapter(out_root=Path("output"))

GENERIC_EMPLOYEE_TOKENS = {
    "someone", "somebody", "anyone", "anybody", "employee", "staff", 
    "person", "people", "member", "team member", "them", "him", "her", "they",
}

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
        
        # Handle Gemini's tool calls
        if parsed_response["tool_calls"]:
            tool_call = parsed_response["tool_calls"][0]
            
            if tool_call.name == "absence_chat":
                return await _handle_gemini_absence_call(session, tool_call, user_message)
            elif tool_call.name == "start_sow_session":
                return await _handle_gemini_sow_call(session, tool_call)
            elif tool_call.name == "provide_guidance":
                return _handle_gemini_guidance(session, tool_call)
        
        # If Gemini provided text response
        if parsed_response["text"]:
            session.add_message("assistant", parsed_response["text"])
            return ChatResponse(
                session_id=session.session_id,
                response=parsed_response["text"],
                action_type="gemini_text_response"
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
                action_type="employee_name_needed"
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
            return ChatResponse(session_id=session.session_id, response=response, action_type="employee_not_found")
        
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
                disambiguation_options=[option]
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
                ]
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
            action_type="absence_marked"
        )
    
    elif action == "query_absence":
        query_type = args.get("query_type", "all_absent")
        time_period = args.get("time_period")
        date_range = args.get("date_range")
        month = args.get("month")
        year = args.get("year", 2025)
        
        if time_period in {"today", None}:
            target_date = _normalize_date_str(args.get("date", "today"))
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
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        elif time_period in {"this_month", "next_month", "last_month"}:
            start_date, end_date = _calculate_month_range(time_period)
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        elif month:
            month_str = f"{year}-{_month_name_to_number(month):02d}"
            result = await absence_adapter.query_absence(query_type="byMonth", month=month_str)
        elif date_range:
            start_raw = date_range.get("start") or ""
            end_raw = date_range.get("end") or ""
            start_date = _normalize_date_str(start_raw)
            end_date = _normalize_date_str(end_raw)
            result = await absence_adapter.query_absence(
                query_type="byDateRange", dates=[start_date, end_date]
            )
        else:
            result = await absence_adapter.query_absence(
                query_type="byDate", dates=[_today()]
            )
        
        session.add_message("assistant", result.get("message", "Query completed"))
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Query completed"),
            action_type="absence_query_result"
        )
    
    elif action == "query_vacation":
        target_date = _normalize_date_str(args.get("date", "today"))
        result = await absence_adapter.query_absence(
            query_type="byStatus", status="V", dates=[target_date]
        )
        session.add_message("assistant", result.get("message", "Vacation query completed"))
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Vacation query completed"),
            action_type="vacation_query_result"
        )
    
    elif action == "check_employee_status":
        employee_name = args.get("employee_name", "")
        query_type = args.get("query_type", "specific_employee")
        date_str = args.get("date", "today")
        
        if not employee_name:
            return ChatResponse(
                session_id=session.session_id,
                response="Please specify which employee you'd like to check.",
                action_type="employee_name_needed"
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
        action_type="employee_status_result"
    )

    # Default fallback
    return ChatResponse(
        session_id=session.session_id,
        response="I understand you want help with absence management. Could you be more specific?",
        action_type="absence_clarification_needed"
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
            return ChatResponse(
                session_id=session.session_id,
                response=result.get("message", "Absence updated."),
                action_type="absence_mark",
                action_data=result.get("details"),
            )
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Unable to update absence."),
            action_type="absence_error",
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
    
    # Initialize SOW session
    if session.session_id not in SOW_SESSIONS:
        SOW_SESSIONS[session.session_id] = SowState()
    
    sow_state = SOW_SESSIONS[session.session_id]
    sow_state.project_overview = project_overview
    sow_state.current_section = "services"
    
    session.add_message("assistant", "Starting SOW creation process...")
    return ChatResponse(
        session_id=session.session_id,
        response="Great! I'll help you create a professional Statement of Work. Let's start with the services section.\n\nWhat services will be provided in this project?",
        action_type="sow_section_prompt"
    )


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
    """Handle guidance responses from Gemini."""
    args = tool_call.arguments
    guidance_type = args.get("guidance_type")
    explanation = args.get("explanation", "")
    main_response = args.get("main_response")
    suggested_actions = args.get("suggested_actions", [])
    
    # Format response
    response_parts = []
    if explanation:
        response_parts.append(f"*{explanation}*\n")
    
    response_parts.append(main_response)
    
    if suggested_actions:
        response_parts.append("\n**You can try:**")
        for action in suggested_actions:
            response_parts.append(f"• {action}")
    
    response_text = "\n".join(response_parts)
    
    # Add helpful buttons for common guidance types
    buttons = []
    if guidance_type in ["capabilities", "greeting", "help"]:
        buttons = [
            ConfirmationButton(id="absence_help", label="Absence Management", value="Who is absent today?", style="primary"),
            ConfirmationButton(id="sow_help", label="SOW Generation", value="Create a SOW", style="primary")
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
    """Convert month name to number."""
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    return months.get(month_name.lower(), 10)


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
