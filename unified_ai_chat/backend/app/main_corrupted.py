"""FastAPI entrypoint for the unified AI chat orchestrator."""
from __future__ import annotations

import logging
import re
import uuid
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Tokens that indicate the user has not yet supplied a concrete employee name.
GENERIC_EMPLOYEE_TOKENS = {
    "someone",
    "somebody",
    "anyone",
    "anybody",
    "employee",
    "staff",
    "person",
    "people",
    "member",
    "team member",
    "them",
    "him",
    "her",
    "they",
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


async def _handle_gemini_absence_call(session: SessionState, tool_call: ToolCall, user_message: str) -> ChatResponse:
    """Handle Gemini's absence_chat tool calls with full natural language understanding."""
    args = tool_call.arguments
    action = args.get("action")
    
    if action == "mark_absence":
        return await _handle_gemini_mark_absence(session, args, user_message)
    elif action == "mark_multiple_absence":
        return await _handle_gemini_mark_multiple_absence(session, args)
    elif action == "query_absence":
        return await _handle_gemini_query_absence(session, args)
    elif action == "query_vacation":
        return await _handle_gemini_query_vacation(session, args)
    elif action == "check_employee_status":
        return await _handle_gemini_check_employee_status(session, args)
    else:
        return ChatResponse(
            session_id=session.session_id,
            response="I understand you want help with absence management. Could you be more specific about what you need?",
            action_type="absence_clarification_needed"
        )


async def _handle_gemini_mark_absence(session: SessionState, args: Dict[str, Any], user_message: str) -> ChatResponse:
    """Handle marking absence based on Gemini's understanding."""
    employee_name = args.get("employee_name", "").strip()
    status = args.get("status", "A")
    date_str = args.get("date", "today")
    reason = args.get("reason", "")
    
    # Normalize date
    normalized_date = _normalize_date_str(date_str)
    
    # Get employees for matching
    employees = await absence_adapter.get_employees()
    available_names = [emp.get("name", "") for emp in employees if emp.get("name")]
    
    # Handle generic employee names or missing names
    if not employee_name or employee_name.lower() in GENERIC_EMPLOYEE_TOKENS:
        session.metadata["pending_action"] = {
            "type": "ask_employee_name",
            "data": {
                "status": status,
                "dates": [normalized_date],
                "reason": reason,
                "available_employees": available_names,
            }
        }
        
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        preview = ", ".join(available_names[:5])
        more = f" (and {len(available_names) - 5} more)" if len(available_names) > 5 else ""
        
        return ChatResponse(
            session_id=session.session_id,
            response=f"Which employee would you like to mark as {status_text}? Please provide a name.\n\n**Available employees:** {preview}{more}",
            action_type="employee_name_needed",
        )
    
    # Try to match employee name
    matches = _find_employee_matches(employee_name, employees)
    
    if not matches:
        # No matches - suggest similar names
        suggestions = []
        for emp in employees:
            name = emp.get("name", "")
            if name and _calculate_name_similarity(employee_name.lower(), name.lower()) >= 0.6:
                suggestions.append(name)
        
        suggestion_text = f"I couldn't find an employee named '{employee_name}'."
        if suggestions:
            suggestion_text += f"\n\n**Did you mean:** {', '.join(suggestions[:3])}?"
        elif available_names:
            suggestion_text += f"\n\n**Available employees:** {', '.join(available_names[:5])}"
            if len(available_names) > 5:
                suggestion_text += f" (and {len(available_names) - 5} more)"
        
        return ChatResponse(
            session_id=session.session_id,
            response=suggestion_text,
            action_type="employee_name_clarification",
        )
    
    if len(matches) > 1:
        # Multiple matches - disambiguate
        options = [
            DisambiguationOption(
                id=f"emp_{emp['id']}",
                label=f"{emp['name']} ({emp.get('department', 'N/A')})",
                value=emp['name'],
                metadata={
                    "employee_id": emp['id'],
                    "action": "mark_absence",
                    "status": status,
                    "date": normalized_date,
                    "reason": reason,
                },
            )
            for emp in matches
        ]
        
        return ChatResponse(
            session_id=session.session_id,
            response=f"I found {len(matches)} employees matching '{employee_name}'. Please select one:",
            action_type="disambiguation_required",
            disambiguation_options=options,
        )
    
    # Single match found
    matched_employee = matches[0]
    employee_name = matched_employee["name"]
    
    # Check if it's a fuzzy match and confirm
    if matched_employee["name"].strip().lower() != employee_name.lower():
        option = DisambiguationOption(
            id=f"emp_{matched_employee['id']}",
            label=f"{matched_employee['name']} ({matched_employee.get('department', 'N/A')})",
            value=matched_employee['name'],
            metadata={
                "employee_id": matched_employee['id'],
                "action": "mark_absence",
                "status": status,
                "date": normalized_date,
                "reason": reason,
            },
        )
        
        return ChatResponse(
            session_id=session.session_id,
            response=f"Did you mean **{matched_employee['name']}**?",
            action_type="employee_name_clarification",
            disambiguation_options=[option],
        )
    
    # Perfect match - check if we need reason
    if not reason:
        session.metadata["pending_action"] = {
            "type": "ask_reason",
            "data": {
                "employee_name": employee_name,
                "status": status,
                "dates": [normalized_date],
                "reason": "",
            },
        }
        
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        return ChatResponse(
            session_id=session.session_id,
            response=f"Would you like to add a reason for marking {employee_name} as {status_text}?",
            action_type="reason_confirmation",
            confirmation_buttons=[
                ConfirmationButton(
                    id="reason_yes",
                    label="Yes, add reason",
                    value="yes",
                    style="primary",
                ),
                ConfirmationButton(
                    id="reason_no",
                    label="No, skip",
                    value="no",
                    style="secondary",
                ),
            ],
        )
    
    # Execute the absence marking
    try:
        result = await absence_adapter.mark_absence(
            employee_name=employee_name,
            status=status,
            dates=[normalized_date],
            reason=reason,
        )
        
        session.add_message("assistant", result.get("message", "Absence marked successfully"))
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Absence marked successfully"),
            action_type="absence_marked",
            action_data=result.get("details"),
        )
    except Exception as e:
        logger.error(f"Error marking absence: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response=f"Sorry, I couldn't mark the absence. Error: {str(e)}",
            action_type="absence_error",
        )


async def _handle_gemini_query_absence(session: SessionState, args: Dict[str, Any]) -> ChatResponse:
    """Handle absence queries based on Gemini's understanding."""
    time_period = args.get("time_period")
    date_range = args.get("date_range")
    month = args.get("month")
    year = args.get("year", 2025)
    query_type = args.get("query_type", "all_absent")
    
    try:
        if time_period == "today":
            result = await absence_adapter.query_absence(
                query_type="byDate",
                dates=[_today()],
            )
        elif time_period in ["this_week", "next_week", "last_week"]:
            # Handle week queries
            result = await absence_adapter.query_absence(
                query_type="byWeek",
                week_type=time_period,
            )
        elif time_period == "this_month" or month:
            # Handle month queries
            if month:
                month_mapping = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month_num = month_mapping.get(month.lower(), 10)  # Default to current month
                month_str = f"{year}-{month_num:02d}"
            else:
                month_str = datetime.now().strftime("%Y-%m")
            
            result = await absence_adapter.query_absence(
                query_type="byMonth",
                month=month_str,
            )
        elif date_range:
            # Handle date range queries
            start_date = _normalize_date_str(date_range.get("start", ""))
            end_date = _normalize_date_str(date_range.get("end", ""))
            result = await absence_adapter.query_absence(
                query_type="byDateRange",
                start_date=start_date,
                end_date=end_date,
            )
        else:
            # Default to today
            result = await absence_adapter.query_absence(
                query_type="byDate",
                dates=[_today()],
            )
        
        session.add_message("assistant", result.get("message", "Query completed"))
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Query completed"),
            action_type="absence_query_result",
            action_data=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"Error querying absence: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response=f"Sorry, I couldn't retrieve the absence information. Error: {str(e)}",
            action_type="absence_query_error",
        )


async def _handle_gemini_query_vacation(session: SessionState, args: Dict[str, Any]) -> ChatResponse:
    """Handle vacation queries."""
    try:
        result = await absence_adapter.query_absence(
            query_type="byStatus",
            status="V",  # Vacation status
        )
        
        session.add_message("assistant", result.get("message", "Vacation query completed"))
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Vacation query completed"),
            action_type="vacation_query_result",
            action_data=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"Error querying vacation: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response=f"Sorry, I couldn't retrieve vacation information. Error: {str(e)}",
            action_type="vacation_query_error",
        )


async def _handle_gemini_check_employee_status(session: SessionState, args: Dict[str, Any]) -> ChatResponse:
    """Handle checking specific employee status."""
    employee_name = args.get("employee_name", "").strip()
    query_type = args.get("query_type", "specific_employee")
    date_str = args.get("date", "today")
    
    if not employee_name:
        return ChatResponse(
            session_id=session.session_id,
            response="Please specify which employee you'd like to check.",
            action_type="employee_name_needed"
        )
    
    try:
        normalized_date = _normalize_date_str(date_str)
        
        if query_type == "leave_status":
            # Check if employee is on leave
            result = await absence_adapter.check_employee_leave_status(
                employee_name=employee_name,
                date=normalized_date,
            )
        else:
            # Check specific employee absence
            result = await absence_adapter.check_employee_status(
                employee_name=employee_name,
                date=normalized_date,
            )
        
        session.add_message("assistant", result.get("message", "Employee status checked"))
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Employee status checked"),
            action_type="employee_status_result",
            action_data=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"Error checking employee status: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response=f"Sorry, I couldn't check the employee status. Error: {str(e)}",
            action_type="employee_status_error",
        )


async def _handle_gemini_mark_multiple_absence(session: SessionState, args: Dict[str, Any]) -> ChatResponse:
    """Handle marking multiple employees absent."""
    employee_names = args.get("employee_names", [])
    status = args.get("status", "A")
    date_str = args.get("date", "today")
    reason = args.get("reason", "")
    
    if not employee_names:
        return ChatResponse(
            session_id=session.session_id,
            response="Please specify which employees you'd like to mark absent.",
            action_type="employee_names_needed"
        )
    
    try:
        normalized_date = _normalize_date_str(date_str)
        
        result = await absence_adapter.mark_multiple_absence(
            employee_names=employee_names,
            status=status,
            dates=[normalized_date],
            reason=reason,
        )
        
        session.add_message("assistant", result.get("message", "Multiple absences marked"))
        
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Multiple absences marked"),
            action_type="multiple_absence_marked",
            action_data=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"Error marking multiple absences: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response=f"Sorry, I couldn't mark multiple absences. Error: {str(e)}",
            action_type="multiple_absence_error",
        )


async def _handle_gemini_sow_call(session: SessionState, tool_call: ToolCall) -> ChatResponse:
    """Handle SOW session start from Gemini."""
    args = tool_call.arguments
    project_overview = args.get("projectOverview", "")
    
    # Start SOW session
    if session.session_id not in SOW_SESSIONS:
        SOW_SESSIONS[session.session_id] = SowState()
    
    sow_state = SOW_SESSIONS[session.session_id]
    sow_state.project_overview = project_overview
    sow_state.current_section = "services"
    
    session.add_message("assistant", "Starting SOW creation process...")
    
    return ChatResponse(
        session_id=session.session_id,
        response="Great! I'll help you create a professional Statement of Work. Let's start with the services section.\n\nWhat services will be provided in this project?",
        action_type="sow_services_needed",
    )


async def _handle_gemini_sow_update(session: SessionState, tool_call: ToolCall) -> ChatResponse:
    """Handle SOW section updates from Gemini."""
    args = tool_call.arguments
    section = args.get("section")
    content = args.get("content")
    
    if session.session_id not in SOW_SESSIONS:
        return ChatResponse(
            session_id=session.session_id,
            response="No active SOW session. Would you like to start creating a new SOW?",
            action_type="sow_session_needed"
        )
    
    sow_state = SOW_SESSIONS[session.session_id]
    
    # Update the section
    if section == "services":
        sow_state.services = content
        sow_state.current_section = "deliverables"
        next_prompt = "What are the key deliverables for this project?"
    elif section == "deliverables":
        sow_state.deliverables = content
        sow_state.current_section = "timeline"
        next_prompt = "What's the timeline for this project?"
    elif section == "timeline":
        sow_state.timeline = content
        sow_state.current_section = "resources"
        next_prompt = "What resources will be needed?"
    elif section == "resources":
        sow_state.resources = content
        sow_state.current_section = "contacts"
        next_prompt = "Who are the key contacts for this project?"
    elif section == "contacts":
        sow_state.contacts = content
        sow_state.current_section = "budget"
        next_prompt = "What's the budget information?"
    elif section == "budget":
        sow_state.budget = content
        sow_state.current_section = "complete"
        next_prompt = "All sections complete! Ready to generate the SOW document?"
    else:
        next_prompt = "Please provide the next section information."
    
    session.add_message("assistant", f"Updated {section} section. {next_prompt}")
    
    return ChatResponse(
        session_id=session.session_id,
        response=next_prompt,
        action_type=f"sow_{sow_state.current_section}_needed" if sow_state.current_section != "complete" else "sow_ready_to_generate",
    )


async def _handle_gemini_sow_finalize(session: SessionState, tool_call: ToolCall) -> ChatResponse:
    """Handle SOW finalization from Gemini."""
    if session.session_id not in SOW_SESSIONS:
        return ChatResponse(
            session_id=session.session_id,
            response="No active SOW session to finalize.",
          action_type="ssession_needed
)
    
  e = SOW_SESSIOssion.session_id

as  try:
      yn# Generatc dhe SOW documentef _handle_confirmation_yes(session: SessionState, intent_result) -> ChatResponse:
        result   """Ha sow_adaptendlenerate_e yes coion.sessionnfirmaow_state)
ti      
     ons.""sion.add_message("assistant","ent generatecessfully!")
   
    p   return ChatResennse(
    ding    session_id=session.session_id,
           _actionse=f"✅ SOW doon = t generated ssession.mly!\n\n📄 **Docetadata.geresult.get('filename', t("pendix')}\n\n🔗 You ng_action")d it from thprovided.",
            action_type="sow_erated",
            action_data=result
       
        
    except Exception as e:
           ger.errorif Error genepending_OW: {eac)
        returtiohatRespon:(
            seid=session.s
            reonse=f"Sorry, I couenerate the SOW docError: {str(e)
            act"sow_geor",
        )


def _he_gemini_guidssion: SessionState, tool_call-> ChatResp
    ""dle guidance resses from Gemin"
    args =rguments
ance_type =rgs.get(ance_type")
    eation = axplanation
    main_respons       actio("main_responn_type = pending_action.get("type")
    suggest        s = "sugns", [])
    
    t the response
    response_      = []
    
  if actxplanation:
 ion    response_p_type ppend(f== "ask_nation}*\n")
   reason":
     esponse_parts.       main_response)
    
    if sugsessio_actin.s:
        rmetadse_parts.append("\n\n**You cata["waiti)
        for action in suggested_actions:
 ng_for_reasoesponse_parts.append(n"] = Ttion}")rue
            return ChatResponse(
    full_r      e = "\n".join(re       sesss)
    
   ion_id=sessi_message("assion.nt", full_respsess)
    
    # Addion_id, buttons baseguidance type
firmation_button= []
    if guidance_type in ["capalities, "help", ]:
        conrmation_buttons
            ConfirmationButton(
                 d="absence_h   r,
         espo   label="nse="Pe Management",
     lease provivalue="Whode thesent toda reason:",
                style="prim  y"
                 action_type="awaiting_reason",
            Confirm    nButton(
                id="     )
                label="SOW Gtion",
                valreate a SOW
         ="primary"
        )
  ]
    
    retResponse(
        sion_id=session.sessi,
       onse=full_response,
        a       ype=f"guidance_ance_type}",
        cbuttons=confirmat
    )
        # Execute other pending actions
        result = await _execute_pending_action(session, pending_action)
        session.metadata.pop("pending_action", None)
        return result
    
    return ChatResponse(
        session_id=session.session_id,
        response="I don't have any pending actions to confirm. How can I help you?",
        action_type="no_pending_action"
    )


async def _handle_confirmation_no(session: SessionState, intent_result) -> ChatResponse:
    """Handle no confirmations."""
    pending_action = session.metadata.get("pending_action")
    if pending_action and pending_action.get("type") == "ask_reason":
        # Execute without reason
        pending_action["data"]["reason"] = ""
        pending_action["type"] = "mark_absence"
        result = await _execute_pending_action(session, pending_action)
        session.metadata.pop("pending_action", None)
        return result
    
    # Cancel other pending actions
    session.metadata.pop("pending_action", None)
    return ChatResponse(
        session_id=session.session_id,
        response="Okay, cancelled. How else can I help you?",
        action_type="action_cancelled"
    )


async def _handle_reason_provided(session: SessionState, intent_result) -> ChatResponse:
    """Handle when user provides a reason."""
    pending_action = session.metadata.get("pending_action")
    if pending_action:
        reason = intent_result.extracted_data.get('reason', '')
        pending_action["data"]["reason"] = reason
        pending_action["type"] = "mark_absence"
        result = await _execute_pending_action(session, pending_action)
        session.metadata.pop("pending_action", None)
        session.metadata.pop("waiting_for_reason", None)
        return result
    
    return ChatResponse(
        session_id=session.session_id,
        response="Thank you for the information. How can I help you?",
        action_type="reason_acknowledged"
    )


def _handle_mixed_intent(session: SessionState, intent_result) -> ChatResponse:
    """Handle mixed absence/SOW intents."""
    return ChatResponse(
        session_id=session.session_id,
        response=intent_result.suggested_response,
        action_type="disambiguation_needed",
        confirmation_buttons=[
            ConfirmationButton(
                id="absence_choice",
                label="Absence Management",
                value="Who is absent today?",
                style="primary"
            ),
            ConfirmationButton(
                id="sow_choice",
                label="SOW Generation",
                value="Create a SOW",
                style="primary"
            )
        ]
    )


def _handle_confused_request(session: SessionState, intent_result) -> ChatResponse:
    """Handle confused/unclear requests."""
    return ChatResponse(
        session_id=session.session_id,
        response=intent_result.suggested_response,
        action_type="clarification_needed",
        confirmation_buttons=[
            ConfirmationButton(
                id="absence_help",
                label="Absence Management",
                value="Who is absent today?",
                style="primary"
            ),
            ConfirmationButton(
                id="sow_help",
                label="SOW Generation",
                value="Create a SOW",
                style="primary"
            )
        ]
    )


def _handle_sow_intent(session: SessionState, intent_result) -> ChatResponse:
    """Handle SOW-related intents - FLEXIBLE AND CONTEXT-AWARE."""
    if intent_result.requires_confirmation:
        return ChatResponse(
            session_id=session.session_id,
            response=intent_result.confirmation_message or intent_result.suggested_response,
            action_type="sow_confirmation_needed",
            confirmation_buttons=[
                ConfirmationButton(
                    id="sow_start",
                    label="Yes, create SOW",
                    value="Create a SOW",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_cancel",
                    label="No, not now",
                    value="no",
                    style="secondary"
                )
            ]
        )
    
    # Direct SOW start - but don't lock into rigid mode
    return ChatResponse(
        session_id=session.session_id,
        response="I'll help you create a professional Statement of Work document. Let's start!",
        action_type="sow_start_flexible",
        confirmation_buttons=[
            ConfirmationButton(
                id="sow_begin",
                label="Begin SOW Creation",
                value="start sow",
                style="primary"
            )
        ]
    )


async def _handle_absence_intent(session: SessionState, intent_result) -> ChatResponse:
    """Handle absence-related intents - CONTEXT AGNOSTIC."""
    # Don't force domain switching - let it flow naturally
    # session.active_domain = "absence"  # Removed rigid mode setting
    
    extracted_data = intent_result.extracted_data
    
    if intent_result.intent_type == IntentType.MARK_ABSENCE:
        employee_name_raw = (extracted_data.get('employee_name') or "").strip()
        status = extracted_data.get('status', 'A')
        date_str = extracted_data.get('date', 'today')
        normalized_date = _normalize_date_str(date_str)

        # Fetch employees once so we can provide smart guidance
        employees = await absence_adapter.get_employees()
        available_names = [emp.get("name", "") for emp in employees if emp.get("name")]

        # Ask for the employee name if we received a generic placeholder
        if not employee_name_raw or employee_name_raw.lower() in GENERIC_EMPLOYEE_TOKENS:
            session.metadata["pending_action"] = {
                "type": "ask_employee_name",
                "data": {
                    "status": status,
                    "dates": [normalized_date],
                    "reason": "",
                    "available_employees": available_names,
                }
            }

            status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
            preview = ", ".join(available_names[:5])
            more = f" (and {len(available_names) - 5} more)" if len(available_names) > 5 else ""

            return ChatResponse(
                session_id=session.session_id,
                response=f"Which employee would you like to mark as {status_text}? "
                         f"Please provide a name.\n\n**Available employees:** {preview}{more}",
                action_type="employee_name_needed",
            )

        # Try to match against known employees
        matches = _find_employee_matches(employee_name_raw, employees)

        if not matches:
            suggestions = []
            for emp in employees:
                name = emp.get("name", "")
                if name and _calculate_name_similarity(employee_name_raw.lower(), name.lower()) >= 0.6:
                    suggestions.append(name)

            suggestion_text = (
                f"I couldn't find an employee named '{employee_name_raw}'."
            )
            if suggestions:
                suggestion_text += f"\n\n**Did you mean:** {', '.join(suggestions[:3])}?"
            elif available_names:
                suggestion_text += f"\n\n**Available employees:** {', '.join(available_names[:5])}"
                if len(available_names) > 5:
                    suggestion_text += f" (and {len(available_names) - 5} more)"

            # Keep asking for a name until we have a valid one
            session.metadata["pending_action"] = {
                "type": "ask_employee_name",
                "data": {
                    "status": status,
                    "dates": [normalized_date],
                    "reason": "",
                    "available_employees": available_names,
                }
            }

            return ChatResponse(
                session_id=session.session_id,
                response=suggestion_text,
                action_type="employee_name_clarification",
            )

        if len(matches) > 1:
            session.metadata["pending_action"] = {
                "type": "ask_employee_name",
                "data": {
                    "status": status,
                    "dates": [normalized_date],
                    "reason": "",
                    "available_employees": available_names,
                }
            }

            options = [
                DisambiguationOption(
                    id=f"emp_{emp['id']}",
                    label=f"{emp['name']} ({emp.get('department', 'N/A')})",
                    value=emp['name'],
                    metadata={
                        "employee_id": emp['id'],
                        "action": "mark_absence",
                        "status": status,
                        "date": normalized_date,
                    },
                )
                for emp in matches
            ]

            return ChatResponse(
                session_id=session.session_id,
                response=f"I found {len(matches)} employees matching '{employee_name_raw}'. Please select one:",
                action_type="disambiguation_required",
                disambiguation_options=options,
            )

        matched_employee = matches[0]

        if matched_employee["name"].strip().lower() != employee_name_raw.lower():
            session.metadata["pending_action"] = {
                "type": "ask_employee_name",
                "data": {
                    "status": status,
                    "dates": [normalized_date],
                    "reason": "",
                    "available_employees": available_names,
                },
            }

            option = DisambiguationOption(
                id=f"emp_{matched_employee['id']}",
                label=f"{matched_employee['name']} ({matched_employee.get('department', 'N/A')})",
                value=matched_employee['name'],
                metadata={
                    "employee_id": matched_employee['id'],
                    "action": "mark_absence",
                    "status": status,
                    "date": normalized_date,
                },
            )

            return ChatResponse(
                session_id=session.session_id,
                response=(
                    f"I couldn't find an exact match for '{employee_name_raw}'. "
                    f"Did you mean **{matched_employee['name']}**?"
                ),
                action_type="employee_name_clarification",
                disambiguation_options=[option],
            )

        # We have a clear match – ask for reason next
        employee_name = matched_employee["name"]
        session.metadata["pending_action"] = {
            "type": "ask_reason",
            "data": {
                "employee_name": employee_name,
                "status": status,
                "dates": [normalized_date],
                "reason": "",
            },
        }

        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        return ChatResponse(
            session_id=session.session_id,
            response=f"Would you like to add a reason for marking {employee_name} as {status_text}?",
            action_type="reason_confirmation",
            confirmation_buttons=[
                ConfirmationButton(
                    id="reason_yes",
                    label="Yes, add reason",
                    value="yes",
                    style="primary",
                ),
                ConfirmationButton(
                    id="reason_no",
                    label="No, skip",
                    value="no",
                    style="secondary",
                ),
            ],
        )
    
    elif intent_result.intent_type == IntentType.QUERY_ABSENCE_TODAY:
        result = await absence_adapter.query_absence(
            query_type="byDate",
            dates=[_today()],
        )
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Could not retrieve today's absence information."),
            action_type="absence_query_result",
            action_data=result.get("details")
        )
    
    elif intent_result.intent_type == IntentType.QUERY_ABSENCE_MONTH:
        current_month = datetime.now().strftime("%Y-%m")
        result = await absence_adapter.query_absence(
            query_type="byMonth",
            month=current_month,
        )
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", "Could not retrieve this month's absence information."),
            action_type="absence_query_result",
            action_data=result.get("details")
        )
    
    elif intent_result.intent_type == IntentType.QUERY_ABSENCE_SPECIFIC_MONTH:
        extracted_data = intent_result.extracted_data
        month_name = extracted_data.get('month', 'september')
        year = extracted_data.get('year', 2025)
        
        # Convert month name to number
        month_mapping = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        month_num = month_mapping.get(month_name.lower(), 9)  # Default to September
        month_str = f"{year}-{month_num:02d}"
        
        result = await absence_adapter.query_absence(
            query_type="byMonth",
            month=month_str,
        )
        return ChatResponse(
            session_id=session.session_id,
            response=result.get("message", f"Could not retrieve absence information for {month_name.title()} {year}."),
            action_type="absence_query_result",
            action_data=result.get("details")
        )
    
    # Add more specific absence intent handlers as needed
    
    return ChatResponse(
        session_id=session.session_id,
        response=intent_result.suggested_response,
        action_type=intent_result.action_type
    )


def _handle_general_intent(session: SessionState, intent_result) -> ChatResponse:
    """Handle general intents like greetings and help."""
    if intent_result.intent_type == IntentType.GREETING:
        return ChatResponse(
            session_id=session.session_id,
            response="""Hello! 👋 I'm here to help you with your daily operations.

**I specialize in two main areas:**

🏢 **Absence Management**
- Check who's absent today
- Mark employees as absent, present, or on vacation
- View absence reports and history

📄 **SOW Generation** 
- Create professional Statement of Work documents
- Guided conversation to collect requirements

**What would you like to work on?**""",
            action_type="greeting_response",
            confirmation_buttons=[
                ConfirmationButton(
                    id="absence_start",
                    label="Absence Management",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_start",
                    label="Create SOW",
                    value="Create a SOW",
                    style="primary"
                )
            ]
        )
    
    elif intent_result.intent_type == IntentType.HELP:
        return ChatResponse(
            session_id=session.session_id,
            response="""**Here's what I can help you with:**

🏢 **Absence Management:**
- "Who is absent today?"
- "Mark John absent today"
- "Get absences for this month"
- "Who is on vacation?"
- "Is Sarah absent tomorrow?"

📄 **SOW Generation:**
- "Create a SOW"
- "Generate statement of work"
- "Start SOW process"

**Examples you can try:**
• Mark multiple employees absent
• Check absences between specific dates
• Get absence report for September
• Who is absent this week?

**What would you like to do?**""",
            action_type="help_response",
            confirmation_buttons=[
                ConfirmationButton(
                    id="absence_example",
                    label="Try Absence Query",
                    value="Who is absent today?",
                    style="primary"
                ),
                ConfirmationButton(
                    id="sow_example",
                    label="Try SOW Creation",
                    value="Create a SOW",
                    style="primary"
                )
            ]
        )
    
    return ChatResponse(
        session_id=session.session_id,
        response=intent_result.suggested_response,
        action_type=intent_result.action_type
    )


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
    background_tasks: BackgroundTasks = None,
    session: SessionState = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    logger.info("Processing chat message for session %s", session.session_id)
    
    user_message = request.message.strip()
    
    # Add user message to session history
    session.add_message("user", user_message)
    
    # **CORE CHANGE: ALWAYS GO TO GEMINI FIRST**
    # Let Gemini understand the full conversation context and decide what to do
    
    # Prepare rich context for Gemini
    context_parts = []
    
    # Add employee list context for better name matching
    try:
        employees = await absence_adapter.get_employees()
        employee_names = [emp.get("name", "") for emp in employees if emp.get("name")]
        if employee_names:
            context_parts.append(f"AVAILABLE EMPLOYEES: {', '.join(employee_names)}")
    except Exception as e:
        logger.warning(f"Could not fetch employees: {e}")
    
    # Add pending action context if any
    pending_action = session.metadata.get("pending_action")
    if pending_action:
        action_type = pending_action.get("type", "")
        if action_type == "ask_reason":
            context_parts.append("CONTEXT: User was asked if they want to add a reason for marking absence")
        elif action_type == "ask_employee_name":
            context_parts.append("CONTEXT: User was asked to provide an employee name")
        elif "waiting_for_reason" in session.metadata:
            context_parts.append("CONTEXT: User was asked to provide a reason for absence")
    
    # Add conversation flow context
    recent_messages = session.recent_history(3)
    if recent_messages:
        context_parts.append("RECENT CONVERSATION CONTEXT: User and assistant have been discussing absence/SOW topics")
    
    # Combine context
    full_context = " | ".join(context_parts) if context_parts else None
    
    # **ALWAYS SEND TO GEMINI - LET GEMINI DECIDE EVERYTHING**
    try:
        gemini_response = gemini_client.generate(session, user_message, full_context)
        parsed_response = gemini_client.parse_response(gemini_response)
        
        # Handle Gemini's tool calls
        if parsed_response["tool_calls"]:
            tool_call = parsed_response["tool_calls"][0]  # Handle first tool call
            
            if tool_call.name == "absence_chat":
                return await _handle_gemini_absence_call(session, tool_call, user_message)
            
            elif tool_call.name == "start_sow_session":
                return await _handle_gemini_sow_call(session, tool_call)
            
            elif tool_call.name == "update_sow_section":
                return await _handle_gemini_sow_update(session, tool_call)
            
            elif tool_call.name == "finalize_sow":
                return await _handle_gemini_sow_finalize(session, tool_call)
            
            elif tool_call.name == "provide_guidance":
                return _handle_gemini_guidance(session, tool_call)
        
        # If Gemini provided text response without tool calls, use provide_guidance
        if parsed_response["text"]:
            session.add_message("assistant", parsed_respon."employee_not
            if sresponse += f" Dse["teions: {', ion_id, '.join(responssugesponse, action_typgest
            return Cha      xte(session_id=se"])
            return ChatResponse(find '{employee_n
                session_id=session.session_id,
                nse = fr"I couldn'esponse=parsed_response["te
         xt"],",
                aype="empleeded"er()) >= 0.6
            )ee_name, emme_similty(employee_namr(), emp["name"].
       "] for emp in if _calculate_na
            sugg      s = [emp["name if  # Suggestnoimilar names
 t mmatchs:
        es = _find_empl   e_matches(em# Try to match     bsence_adapter.ge  eeployees()
  name
       action_ees type="gemini_text_re_names[:5])}sponse"{'...available_names) > 5 el
            )ed"\n**Ava** {', '.join(availa
        back ission_i"I unlarification_want help,you to be more I can help  managemenOW generation.
            }== 'A' else 'present'atus == 'P' else 'ocation'}
          n_id=  ponse(session.ses
               esponse=h employee ike to mark as {'absent' if
          
            ret   error: {e}Response(malize_date_str(da)], "reason": reas
        status = args.get("status   "A") {s"
                "data": {"  "typesk_eatus, "datemployee_name",
  
   return eiostr r =rgs.name getnding_actio("reason_name.lower( a ""GENERIC_Eoyees if emp.gMPLOYEE_TOKE)m:
                      employees = await absence_aisster.get_employees(ing, pecific nam
            session.m       av   if not ems = [emp.get("ployee_"") for     name is 
 rgn_   # If employid=sesate", "today")
        reasosii .sessiony"""
    action = ar    args ction")
    l_call.()
      
        employee_name  if ac.get("employee_name", tion == "m   _absence":
   )age: str) -> ChatRe natural lge understandi
    """HandlsionStni's absate, tool_tool callcall: ToolCall, user_me
call(session: Ses
async def _handle_gemini_absen   action_type=m havingecoverle ,ocessing your request. Could you pleas
            response="I understand you want help, but I need you to be more specific. I can help with absence management or SOW generation.",
            action_type="clarification_needed"
        )
        
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        return ChatResponse(
            session_id=session.session_id,
            response="I'm having trouble processing your request. Could you please rephrase it?",
            action_type="error_recovery"
        )
                disambiguation_options=options,
            )
            
        else:
            # No matches - suggest similar names
            all_names = [emp.get("name", "") for emp in employees if emp.get("name")]
            suggestion_text = f"I couldn't find an employee named '{user_message}'."
            
            # Try to find close matches for suggestions
            close_matches = []
            for emp in employees:
                emp_name = emp.get("name", "")
                if emp_name and _calculate_name_similarity(user_message.lower(), emp_name.lower()) > 0.4:
                    close_matches.append(emp_name)
            
            if close_matches:
                suggestion_text += f"\n\n**Did you mean:** {', '.join(close_matches[:3])}?"
            else:
                suggestion_text += f"\n\n**Available employees:** {', '.join(all_names[:5])}"
                if len(all_names) > 5:
                    suggestion_text += f" (and {len(all_names) - 5} more)"
            
            return ChatResponse(
                session_id=session.session_id,
                response=suggestion_text,
                action_type="employee_name_clarification",
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
            if background_tasks:
                background_tasks.add_task(session_manager.cleanup_expired)
            return result
    
    # Handle SOW exit requests FIRST (regardless of mode)
    if user_message.lower() in {"exit", "quit", "cancel", "abort", "/exit", "exit_sow"}:
        if session.session_id in SOW_SESSIONS:
            del SOW_SESSIONS[session.session_id]
        session.active_domain = None
        return ChatResponse(
            session_id=session.session_id,
            response="✅ **Exited SOW mode successfully!**\n\nI'm back to helping you with both absence management and SOW generation. What would you like to do next?",
            action_type="sow_exit"
        )
    
    # Check if user is actively in SOW conversation flow
    is_in_sow_flow = (session.session_id in SOW_SESSIONS and 
                      SOW_SESSIONS[session.session_id].generator.conversation_state != "COMPLETE")
    
    # Handle SOW flow continuation (only if actively in flow AND not an absence request)
    if is_in_sow_flow:
        # Check if this is clearly an absence request that should break SOW flow
        absence_indicators = ['absent', 'absence', 'vacation', 'leave', 'who is', 'get absence', 'mark']
        is_absence_request = any(indicator in user_message.lower() for indicator in absence_indicators)
        
        if is_absence_request:
            # User wants to switch to absence - pause SOW and handle absence
            session.metadata["paused_sow"] = True
            # Continue to normal processing below
        else:
            # Continue SOW flow
            state = SOW_SESSIONS[session.session_id]
            
            # Generate
            if user_message == "generate_sow":
                result = sow_adapter.finalize(state, session_id=session.session_id)
                return ChatResponse(
                    session_id=session.session_id,
                    response=result["message"],
                    action_type="sow_generated",
                    download_url=result["download_url"]
                )
            
            # Process SOW input
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
    
    # Handle SOW initiation requests
    if user_message.lower() in {"create a sow", "start sow", "/start", "generate sow"}:
        session.active_domain = "sow"
        SOW_SESSIONS[session.session_id] = SowState()
        q, hint = sow_adapter.start()
        return ChatResponse(
            session_id=session.session_id,
            response=q,
            action_type="sow_started",
            action_data=hint
        )

    # ALWAYS try advanced intent classification first (context-agnostic)
    advanced_response = await _handle_advanced_intent_classification(session, user_message)
    if advanced_response:
        # Clear any restrictive domain settings for natural flow
        if advanced_response.action_type in ["absence_query_result", "absence_mark", "query_absence_today"]:
            session.active_domain = None  # Allow natural flow
        session.add_message("user", user_message)
        if background_tasks:
            background_tasks.add_task(session_manager.cleanup_expired)
        return advanced_response

    session.add_message("user", user_message)

    # Early intent detection for better user experience (fallback)
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

    if background_tasks:
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
            normalized_request_date = _normalize_date_str(args.get("date", _today()))

            # FIRST: Check if employee name is missing or generic
            if not employee_name or employee_name.strip().lower() in GENERIC_EMPLOYEE_TOKENS:
                # Get employee list for suggestions
                employees = await absence_adapter.get_employees()
                employee_names = [emp.get("name", "") for emp in employees if emp.get("name")]
                
                # Store pending action with missing employee name
                session.metadata["pending_action"] = {
                    "type": "ask_employee_name",
                    "data": {
                        "status": args.get("status", "A"),
                        "dates": [normalized_request_date],
                        "reason": args.get("reason", ""),
                        "available_employees": employee_names,
                    }
                }
                
                status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(args.get("status", "A"), "absent")
                employee_list = ", ".join(employee_names[:5])  # Show first 5
                more_text = f" (and {len(employee_names) - 5} more)" if len(employee_names) > 5 else ""
                
                return {
                    "message": f"Which employee would you like to mark as {status_text}?\n\n**Available employees:** {employee_list}{more_text}\n\nPlease tell me the employee's name.",
                    "action_type": "employee_name_needed",
                }
            
            # SECOND: Check for multiple employee matches
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
                        "date": normalized_request_date,
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
                    # No match - provide smart suggestions
                    all_names = [emp.get("name", "") for emp in employees if emp.get("name")]
                    suggestion_text = f"I couldn't find an employee named '{employee_name}'."
                    
                    # Try to find close matches for suggestions
                    close_matches = []
                    for emp in employees:
                        emp_name = emp.get("name", "")
                        if emp_name and _calculate_name_similarity(employee_name.lower(), emp_name.lower()) > 0.4:
                            close_matches.append(emp_name)
                    
                    if close_matches:
                        suggestion_text += f"\n\n**Did you mean:** {', '.join(close_matches[:3])}?"
                    else:
                        suggestion_text += f"\n\n**Available employees:** {', '.join(all_names[:5])}"
                        if len(all_names) > 5:
                            suggestion_text += f" (and {len(all_names) - 5} more)"
                    
                    return {
                        "message": suggestion_text,
                        "action_type": "employee_name_clarification",
                    }
                else:
                    matched_employee = matches[0]
                    if matched_employee['name'].strip().lower() != employee_name.strip().lower():
                        option = DisambiguationOption(
                            id=f"emp_{matched_employee['id']}",
                            label=f"{matched_employee['name']} ({matched_employee.get('department', 'N/A')})",
                            value=matched_employee['name'],
                            metadata={
                                "employee_id": matched_employee['id'],
                                "action": action,
                                "status": args.get("status"),
                                "date": normalized_request_date,
                                "date_range": args.get("date_range"),
                                "reason": args.get("reason"),
                            }
                        )

                        session.metadata["pending_action"] = {
                            "type": "ask_employee_name",
                            "data": {
                                "status": args.get("status", "A"),
                                "dates": [normalized_request_date],
                                "reason": args.get("reason", ""),
                                "available_employees": [emp.get("name", "") for emp in employees if emp.get("name")],
                            }
                        }

                        return {
                            "message": (
                                f"I couldn't find an exact match for '{employee_name}'. "
                                f"Did you mean **{matched_employee['name']}**?"
                            ),
                            "action_type": "employee_name_clarification",
                            "disambiguation_options": [option],
                        }

                    # Exact match - use it
                    employee_name = matched_employee['name']
            
            if action == "mark_absence":
                status = args.get("status", "A")
                date_str = _normalize_date_str(args.get("date", _today()))
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
            
            elif action == "mark_multiple_absence":
                employee_names = args.get("employee_names", [])
                status = args.get("status", "A")
                date_str = _normalize_date_str(args.get("date", _today()))
                
                if not employee_names:
                    return {
                        "message": "Please provide the list of employee names to mark as absent. You can say something like: 'Mark John, Sarah, and Mike absent today'",
                        "action_type": "employee_names_needed",
                    }
                
                # Process multiple employees
                results = []
                for emp_name in employee_names:
                    try:
                        result = await absence_adapter.mark_absence(
                            emp_name, [date_str], status, args.get("reason", "")
                        )
                        if result.get("success"):
                            results.append(f"✅ {emp_name}")
                        else:
                            results.append(f"❌ {emp_name} - {result.get('message', 'Failed')}")
                    except Exception as e:
                        results.append(f"❌ {emp_name} - Error: {str(e)}")
                
                status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
                return {
                    "message": f"**Multiple Employee Update Results ({status_text}):**\n\n" + "\n".join(results),
                    "action_type": "multiple_absence_mark",
                }
            
            elif action == "query_vacation":
                # Query who is on vacation
                result = await absence_adapter.query_absence(
                    query_type="byStatus",
                    status="V",
                    dates=[normalized_request_date],
                )
                return {
                    "message": result.get("message", "Could not retrieve vacation information."),
                    "action_type": "vacation_query" if result.get("success") else "absence_error",
                    "action_data": result.get("details"),
                }
            
            elif action == "check_employee_status":
                # Check specific employee on specific day
                employee_name = args.get("employee_name")
                date_str = _normalize_date_str(args.get("date", _today()))
                
                if not employee_name:
                    return {
                        "message": "Please specify which employee you'd like to check.",
                        "action_type": "employee_name_needed",
                    }
                
                result = await absence_adapter.query_absence(
                    query_type="byEmployee",
                    employee_name=employee_name,
                    dates=[date_str],
                )
                return {
                    "message": result.get("message", f"Could not check status for {employee_name}."),
                    "action_type": "employee_status_check" if result.get("success") else "absence_error",
                    "action_data": result.get("details"),
                }
                    
            elif action == "query_absence":
                date_str = args.get("date")
                date_range = args.get("date_range")
                time_period = args.get("time_period")
                month = args.get("month")
                year = args.get("year", datetime.now().year)
                query_type = args.get("query_type", "all_absent")
                
                # Handle different query scenarios
                if date_range:
                    # Query between two specific dates
                    start = date_range.get("start")
                    end = date_range.get("end")
                    result = await absence_adapter.query_absence(
                        query_type="byDateRange",
                        dates=[start, end],
                        employee_name=employee_name,
                    )
                elif time_period:
                    # Handle time period queries
                    if time_period == "this_week":
                        # Calculate this week's date range
                        today = date.today()
                        start_week = today - timedelta(days=today.weekday())
                        end_week = start_week + timedelta(days=6)
                        result = await absence_adapter.query_absence(
                            query_type="byDateRange",
                            dates=[start_week.isoformat(), end_week.isoformat()],
                            employee_name=employee_name,
                        )
                    elif time_period == "next_week":
                        today = date.today()
                        start_week = today + timedelta(days=(7 - today.weekday()))
                        end_week = start_week + timedelta(days=6)
                        result = await absence_adapter.query_absence(
                            query_type="byDateRange",
                            dates=[start_week.isoformat(), end_week.isoformat()],
                            employee_name=employee_name,
                        )
                    elif time_period == "last_week":
                        today = date.today()
                        start_week = today - timedelta(days=today.weekday() + 7)
                        end_week = start_week + timedelta(days=6)
                        result = await absence_adapter.query_absence(
                            query_type="byDateRange",
                            dates=[start_week.isoformat(), end_week.isoformat()],
                            employee_name=employee_name,
                        )
                    elif time_period == "this_month":
                        # Current month
                        today = date.today()
                        start_month = today.replace(day=1)
                        if today.month == 12:
                            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                        else:
                            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                        result = await absence_adapter.query_absence(
                            query_type="byDateRange",
                            dates=[start_month.isoformat(), end_month.isoformat()],
                            employee_name=employee_name,
                        )
                    else:
                        # Default to today for other time periods
                        result = await absence_adapter.query_absence(
                            query_type="byDate",
                            dates=[_today()],
                            employee_name=employee_name,
                        )
                elif month:
                    # Specific month query
                    month_num = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }.get(month.lower(), datetime.now().month)
                    
                    start_month = date(year, month_num, 1)
                    if month_num == 12:
                        end_month = date(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_month = date(year, month_num + 1, 1) - timedelta(days=1)
                    
                    result = await absence_adapter.query_absence(
                        query_type="byDateRange",
                        dates=[start_month.isoformat(), end_month.isoformat()],
                        employee_name=employee_name,
                    )
                elif date_str:
                    # Specific date query
                    normalized_date = _normalize_date_str(date_str)
                    result = await absence_adapter.query_absence(
                        query_type="byDate",
                        dates=[normalized_date],
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
    """Enhanced direct routing for comprehensive scenarios without needing LLM processing."""
    if not message:
        return None

    lower = message.lower().strip()

    # Direct SOW patterns - high confidence
    sow_direct_patterns = [
        "create sow", "generate sow", "start sow", "make sow", 
        "sow generation", "new sow", "create statement of work",
        "generate statement of work", "make statement of work"
    ]
    if any(pattern in lower for pattern in sow_direct_patterns):
        return ToolCall(
            name="start_sow_session",
            arguments={"projectOverview": "User requested SOW generation"}
        )

    # Direct absence query patterns - high confidence
    absence_query_patterns = [
        ("who is absent today", {"action": "query_absence", "date": "today", "query_type": "all_absent"}),
        ("absent today", {"action": "query_absence", "date": "today", "query_type": "all_absent"}),
        ("who is absent", {"action": "query_absence", "date": "today", "query_type": "all_absent"}),
        ("absences today", {"action": "query_absence", "date": "today", "query_type": "all_absent"}),
        ("who is on vacation", {"action": "query_vacation", "query_type": "vacation_only"}),
        ("vacation today", {"action": "query_vacation", "date": "today", "query_type": "vacation_only"}),
        ("who is absent this month", {"action": "query_absence", "time_period": "this_month", "query_type": "monthly_report"}),
        ("absences this month", {"action": "query_absence", "time_period": "this_month", "query_type": "monthly_report"}),
    ]
    
    for pattern, args in absence_query_patterns:
        if pattern in lower:
            return ToolCall(name="absence_chat", arguments=args)

    # Direct mark absence patterns (simple cases)
    mark_patterns = [
        (r"mark (\w+) absent(?:\s+today)?", "A"),
        (r"(\w+) is absent(?:\s+today)?", "A"),
        (r"set (\w+) absent(?:\s+today)?", "A"),
        (r"mark (\w+) present(?:\s+today)?", "P"),
        (r"(\w+) is present(?:\s+today)?", "P"),
        (r"mark (\w+) on vacation", "V"),
        (r"(\w+) is on vacation", "V"),
    ]
    
    for pattern, status in mark_patterns:
        match = re.search(pattern, lower)
        if match:
            employee_name = match.group(1)
            return ToolCall(
                name="absence_chat",
                arguments={
                    "action": "mark_absence",
                    "employee_name": employee_name,
                    "status": status,
                    "date": "today"
                }
            )

    # Month queries - specific months
    months = ['january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december']
    
    for month in months:
        month_patterns = [
            f"absences for {month}",
            f"absent in {month}",
            f"absences in {month}",
            f"who was absent in {month}",
            f"get absences for {month}",
            f"{month} absences"
        ]
        
        for pattern in month_patterns:
            if pattern in lower:
                return ToolCall(
                    name="absence_chat",
                    arguments={
                        "action": "query_absence",
                        "month": month,
                        "year": 2025,
                        "query_type": "monthly_report"
                    }
                )

    # Week queries
    week_patterns = [
        ("absent this week", {"action": "query_absence", "time_period": "this_week"}),
        ("absences this week", {"action": "query_absence", "time_period": "this_week"}),
        ("who is absent this week", {"action": "query_absence", "time_period": "this_week"}),
        ("absent next week", {"action": "query_absence", "time_period": "next_week"}),
        ("absences next week", {"action": "query_absence", "time_period": "next_week"}),
        ("absent last week", {"action": "query_absence", "time_period": "last_week"}),
        ("absent previous week", {"action": "query_absence", "time_period": "last_week"}),
    ]
    
    for pattern, args in week_patterns:
        if pattern in lower:
            return ToolCall(name="absence_chat", arguments=args)

    # Employee-specific checks
    employee_check_patterns = [
        (r"is (\w+) absent today", "today"),
        (r"is (\w+) absent tomorrow", "tomorrow"),
        (r"is (\w+) absent yesterday", "yesterday"),
        (r"is (\w+) on leave", "today"),
    ]
    
    for pattern, day in employee_check_patterns:
        match = re.search(pattern, lower)
        if match:
            employee_name = match.group(1)
            return ToolCall(
                name="absence_chat",
                arguments={
                    "action": "check_employee_status",
                    "employee_name": employee_name,
                    "date": day,
                    "query_type": "specific_employee"
                }
            )

    # Check for mixed intents first - don't route these directly
    mixed_patterns = [
        "absence and sow", "sow and absence", "both absence", "both sow",
        "make absence sow", "absence sow report", "leave sow"
    ]
    if any(pattern in lower for pattern in mixed_patterns):
        return None  # Let advanced intent classification handle this
    
    # Fallback to general absence handling if contains absence keywords
    absence_keywords = [
        "absent", "absence", "vacation", "leave", "present", "attendance",
        "sick", "time off", "who is off", "on leave", "pto"
    ]
    if any(keyword in lower for keyword in absence_keywords):
        return ToolCall(name="absence_chat", arguments={"action": "query_absence", "date": "today"})

    # General SOW handling
    if (
        "statement of work" in lower
        or "create a sow" in lower
        or lower.startswith("sow")
        or " need a sow" in lower
        or "sow document" in lower
        or "sow report" in lower
    ):
        return ToolCall(name="start_sow_session", arguments={"projectOverview": message})

    # SOW state handling (existing logic)
    sow_state = getattr(session, 'sow_state', None)
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


def _normalize_date_str(value: str) -> str:
    """Convert natural language date tokens into ISO 8601 strings."""
    if not value:
        return _today()

    token = value.strip().lower()
    if token == "today":
        return _today()
    if token == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    if token == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()

    # Try a few common date formats
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue

    # Fallback to today if parsing fails
    logger.warning("Unable to parse date value '%s', defaulting to today()", value)
    return _today()


def _find_employee_matches(employee_name: str, employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find employee matches with advanced fuzzy matching and smart suggestions."""
    if not employee_name or not employees:
        return []
    
    employee_name_lower = employee_name.strip().lower()
    exact_matches = []
    partial_matches = []
    fuzzy_matches: List[tuple[Dict[str, Any], float]] = []
    
    for emp in employees:
        emp_name_raw = str(emp.get("name", "")).strip()
        if not emp_name_raw:
            continue
        emp_name = emp_name_raw.lower()

        # Exact match
        if emp_name == employee_name_lower:
            exact_matches.append(emp)
            continue

        # Partial match (contains)
        if employee_name_lower in emp_name or emp_name.startswith(employee_name_lower):
            partial_matches.append(emp)
            continue

        # Fuzzy match (similar spelling)
        similarity_score = _calculate_name_similarity(employee_name_lower, emp_name)
        if similarity_score >= 0.7:
            fuzzy_matches.append((emp, similarity_score))
    
    # Sort fuzzy matches by similarity score
    fuzzy_matches.sort(key=lambda item: item[1], reverse=True)
    fuzzy_results = [match[0] for match in fuzzy_matches[:3]]  # Top 3 fuzzy matches
    
    # Return in order of preference: exact, partial, fuzzy
    return exact_matches or partial_matches or fuzzy_results


def _calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names."""
    if not name1 or not name2:
        return 0.0
    ratio = SequenceMatcher(None, name1, name2).ratio()

    if name1 in name2 or name2 in name1:
        ratio = max(ratio, 0.8)

    return ratio


async def _execute_pending_action(session: SessionState, pending_action: Dict[str, Any]) -> ChatResponse:
    """Execute a pending action that was confirmed by the user."""
    action_type = pending_action.get("type")
    data = pending_action.get("data", {})
    
    if action_type == "mark_absence":
        employee_name = data.get("employee_name")
        status = data.get("status", "A")
        dates = data.get("dates", [_today()])
        reason = data.get("reason", "")

        date_list = dates if isinstance(dates, list) else [dates]
        normalized_dates = [_normalize_date_str(value) for value in date_list]

        result = await absence_adapter.mark_absence(employee_name, normalized_dates, status, reason)
        status_text = {"A": "absent", "P": "present", "V": "on vacation"}.get(status, status)
        
        if result.get("success"):
            return ChatResponse(
                session_id=session.session_id,
                response=f"✅ Marked {employee_name} as {status_text} for {', '.join(normalized_dates)}.",
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
