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
        
        # Add context if provided (e.g., employee list)
        if context:
            full_message = f"{context}\n\nUser request: {user_message}"
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
            "You are the Unified Operations AI for HR. Today's date is 2025-10-04. You ONLY assist with two domains and must stay strictly within them.\n"
            "1. Employee absence management (marking attendance, updating records, retrieving absence or vacation reports).\n"
            "2. Statement of Work (SOW) document preparation (gathering required project details and generating the final document).\n\n"
            "Instructions:\n"
            "- ALWAYS call the appropriate tool instead of crafting your own answer for supported actions.\n"
            "- For ANY absence related questions:\n"
            "  * Call `absence_chat` with structured parameters\n"
            "  * Parse employee names from the provided employee list (handle typos and partial names)\n"
            "  * If a name is misspelled, ask for clarification: 'Did you mean [correct name]?'\n"
            "  * For dates: 'today' = 2025-10-04, 'yesterday' = 2025-10-03, 'tomorrow' = 2025-10-05\n"
            "  * For months without year: assume current year 2025 (e.g., 'september' = September 2025 = 2025-09-01 to 2025-09-30)\n"
            "  * For 'this week': calculate from today (2025-10-04)\n"
            "  * For 'this month': October 2025 (2025-10-01 to 2025-10-31)\n"
            "- For SOW creation, first call `start_sow_session` (provide the user's project overview), then request sections in this exact order using `update_sow_section`: services, deliverables, timeline, resources, contacts, budget. Finish with `finalize_sow` when all sections are complete.\n"
            "- If the user asks for anything outside absence management or SOW generation, respond with: \"I'm sorry, I can help only with absence management and SOW generation right now.\"\n"
            "- Keep answers concise and actionable. Confirm completed actions clearly."
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
                ]
            }
        ]


gemini_client = GeminiClient()
