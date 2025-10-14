"""Wrapper around the Gemini API with tool definitions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from .config import get_settings
from .models import SessionState


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


class GeminiClient:
    """Handles Gemini interactions with function calling."""

    def __init__(self) -> None:
        self._settings = get_settings()
        genai.configure(api_key=self._settings.gemini_api_key)
        self._model = genai.GenerativeModel(
            model_name=self._settings.gemini_model,
            tools=self._tool_definitions(),
            system_instruction=self._system_prompt(),
        )


    def generate(self, session: SessionState, user_message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response from Gemini including potential tool calls."""

        history = session.recent_history(self._settings.session_history_limit)
        messages: List[Dict[str, Any]] = []
        if history:
            messages.extend(history)
        
        # Add context if provided (e.g., employee list, current mode)
        context_parts = []
        if context:
            context_parts.append(context)
        
        # Add current mode context
        current_mode = "Unified Mode"
        if hasattr(session, 'active_domain') and session.active_domain:
            if session.active_domain == "sow":
                current_mode = "SOW Generation Mode - Focus exclusively on SOW-related queries"
            elif session.active_domain == "absence":
                current_mode = "Absence Management Mode - Focus on absence-related queries"
        else:
            current_mode = "Unified Mode - Can help with both absence and SOW"
        
        context_parts.append(f"CURRENT MODE: {current_mode}")
        
        if context_parts:
            full_message = f"{' | '.join(context_parts)}\n\nUser request: {user_message}"
        else:
            full_message = user_message
            
        messages.append({"role": "user", "parts": [full_message]})

        response = self._model.generate_content(
            messages,
            tool_config={"function_calling_config": {"mode": "AUTO"}},
        )
        
        return response

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """Normalize Gemini responses into text/tool actions."""

        if not response.candidates:
            raise RuntimeError("Gemini returned no candidates")

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            raise RuntimeError("Gemini candidate missing content parts")

        parts = candidate.content.parts
        tool_calls: List[ToolCall] = []
        text_fragments: List[str] = []

        for part in parts:
            if getattr(part, "function_call", None):
                func_call = part.function_call
                name = func_call.name
                raw_args = func_call.args or {}
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {"value": raw_args}
                else:
                    # Use dict() for tool execution, safe serialization only for debug
                    args = dict(raw_args)
                tool_calls.append(ToolCall(name=name, arguments=args))
            elif getattr(part, "text", None):
                text_fragments.append(part.text)

        return {
            "tool_calls": tool_calls,
            "text": "\n".join(fragment for fragment in text_fragments if fragment),
        }



    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are the Unified Operations AI Assistant. Today's date is 2025-10-04. You specialize in two main areas:\n"
            "1. **Absence Management** - Employee attendance, vacation tracking, absence reports\n"
            "2. **SOW Generation** - Statement of Work document creation and management\n\n"
            "**CRITICAL: ALWAYS USE TOOLS - NEVER RETURN RAW JSON OR TEXT RESPONSES**\n"
            "You MUST call the appropriate tool for every response. Never return raw JSON or plain text.\n\n"
            "**MODE-BASED BEHAVIOR:**\n"
            "- **UNIFIED MODE**: Help with both domains, provide guidance and disambiguation\n"
            "- **SOW MODE**: Focus EXCLUSIVELY on SOW generation, ignore absence requests\n"
            "- **ABSENCE MODE**: Focus on absence management, can switch to other modes\n\n"
            "**INTENT CLASSIFICATION RULES:**\n"
            "- For CLEAR requests: Use appropriate tools immediately (absence_chat, start_sow_session, etc.)\n"
            "- For AMBIGUOUS requests: Use provide_guidance tool with disambiguation\n"
            "- For GENERAL greetings/questions: Use provide_guidance tool with capabilities\n"
            "- For MIXED intents (e.g., 'absence and sow'): Use provide_guidance tool with clarification\n"
            "- **IN SOW MODE**: Only process SOW-related requests, use provide_guidance to redirect others\n\n"
            "**RESPONSE FORMAT:**\n"
            "When using provide_guidance tool, format responses like:\n"
            "*[Light explanation in italics]*\n\n"
            "**Main response in bold/normal text**\n\n"
            "**SOW MODE RULES:**\n"
            "- IN SOW MODE: You should NEVER be called - SOW inputs are handled directly by the SOW system\n"
            "- If somehow called in SOW mode: Use provide_guidance to redirect to SOW system\n"
            "- For absence questions in SOW mode: Use provide_guidance to redirect to exit SOW first\n"
            "- SOW conversation flow is handled separately - do not interfere\n\n"
            "**ABSENCE MANAGEMENT:**\n"
            "- Call `absence_chat` for attendance queries, marking absent/present/vacation\n"
            "- Handle employee name variations and typos gracefully\n"
            "- Date parsing: 'today'=2025-10-04, 'yesterday'=2025-10-03, 'tomorrow'=2025-10-05\n"
            "- Month queries: assume 2025 (e.g., 'september' = September 2025)\n\n"
            "**HELPFUL RESPONSES:**\n"
            "- For 'What can you do?' or similar: List capabilities clearly\n"
            "- For unclear requests: Ask specific clarifying questions\n"
            "- For mixed intents: 'I can help with both! Which would you like to start with?'\n"
            "- Always be conversational and helpful, not restrictive\n\n"
            "**EXAMPLES:**\n"
            "User: 'What would you like to do today?' → Explain your capabilities and ask what they need\n"
            "User: 'absence and sow' → Ask which they'd like to focus on first\n"
            "User: 'help' → Provide clear options for both domains\n"
            "User in SOW mode asks about absence → Redirect to exit SOW mode first"
        )

    @staticmethod
    def _tool_definitions() -> List[Dict[str, Any]]:
        return [
            {
                "function_declarations": [
                    {
                        "name": "absence_chat",
                        "description": (
                            "Handle absence management queries. Use for ANY question or command about attendance, absences, vacations, employee availability, or absence reports. "
                            "You must parse the user's request and extract: employee name (if mentioned), date/date range, and action type (mark absent/present/vacation OR query absences)."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["mark_absence", "query_absence"],
                                    "description": "Whether to mark someone absent/present/vacation OR query absence records",
                                },
                                "employee_name": {
                                    "type": "string",
                                    "description": "Employee name (required for mark_absence, optional for query_absence to filter by person)",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["A", "P", "V"],
                                    "description": "For mark_absence: A=Absent, P=Present, V=Vacation",
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Single date in YYYY-MM-DD format, or 'today', 'yesterday', 'tomorrow'",
                                },
                                "date_range": {
                                    "type": "object",
                                    "properties": {
                                        "start": {"type": "string", "description": "Start date YYYY-MM-DD"},
                                        "end": {"type": "string", "description": "End date YYYY-MM-DD"}
                                    },
                                    "description": "Date range for queries (e.g., 'this week', 'september', 'last month')",
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Optional reason for marking absence",
                                },
                            },
                            "required": ["action"],
                        },
                    },
                    {
                        "name": "start_sow_session",
                        "description": (
                            "Begin a new Statement of Work collection flow. Provide the project overview so the system "
                            "can progress to the next step."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "projectOverview": {
                                    "type": "string",
                                    "description": "Natural language description of the project goals and context.",
                                }
                            },
                            "required": ["projectOverview"],
                        },
                    },
                    {
                        "name": "update_sow_section",
                        "description": (
                            "Supply content for the next SOW section (services, deliverables, timeline, resources, "
                            "contacts, budget)."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "section": {
                                    "type": "string",
                                    "enum": [
                                        "services",
                                        "deliverables",
                                        "timeline",
                                        "resources",
                                        "contacts",
                                        "budget",
                                    ],
                                    "description": "Which section is being provided.",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "User-provided content for this section.",
                                },
                            },
                            "required": ["section", "content"],
                        },
                    },
                    {
                        "name": "finalize_sow",
                        "description": (
                            "Generate the finished SOW document once all sections are complete."
                        ),
                        "parameters": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "provide_guidance",
                        "description": (
                            "REQUIRED for general questions, ambiguous requests, or when user needs help. "
                            "Use this tool for: greetings, 'what can you do', unclear requests, mixed intents, "
                            "or when user asks about capabilities. NEVER return raw text - always use this tool."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "guidance_type": {
                                    "type": "string",
                                    "enum": ["capabilities", "disambiguation", "clarification", "help", "greeting"],
                                    "description": "Type of guidance: capabilities=list what you can do, disambiguation=clarify mixed intents, clarification=ask for more info, help=general help, greeting=respond to hello/hi"
                                },
                                "explanation": {
                                    "type": "string",
                                    "description": "Light explanation in italics (optional) - why you're providing guidance"
                                },
                                "main_response": {
                                    "type": "string", 
                                    "description": "Main response in normal text - the helpful guidance or information"
                                },
                                "suggested_actions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of example actions user can try (optional)"
                                }
                            },
                            "required": ["guidance_type", "main_response"]
                        }
                    },
                ]
            }
        ]


gemini_client = GeminiClient()
