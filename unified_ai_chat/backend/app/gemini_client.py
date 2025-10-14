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
        """Generate a response from Gemini with intelligent intent detection and reasoning."""

        history = session.recent_history(self._settings.session_history_limit)
        messages: List[Dict[str, Any]] = []
        if history:
            messages.extend(history)
        
        # Enhanced context with intelligent mode detection
        context_parts = []
        if context:
            context_parts.append(context)
        
        # Smart mode context with reasoning
        current_mode = "Unified Mode"
        mode_context = ""
        if hasattr(session, 'active_domain') and session.active_domain:
            if session.active_domain == "sow":
                current_mode = "SOW Generation Mode"
                mode_context = """
CURRENT MODE: SOW Generation (Red Theme)
- You are currently helping with Statement of Work creation
- Focus on SOW-related queries unless user explicitly switches
- If user asks about absence/attendance, acknowledge but suggest switching modes
"""
            elif session.active_domain == "absence":
                current_mode = "Absence Management Mode"
                mode_context = """
CURRENT MODE: Absence Management (Blue Theme)  
- You are currently helping with absence/attendance management
- Focus on absence-related queries unless user explicitly switches
- If user asks about SOW, acknowledge but suggest switching modes
"""
        else:
            mode_context = """
CURRENT MODE: Unified Mode (Neutral)
- Ready to help with both Absence Management and SOW Generation
- Intelligently detect user intent and switch to appropriate mode
- Blue theme for Absence, Red theme for SOW
"""
        
        context_parts.append(mode_context)
        
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
            "You are an INTELLIGENT Unified Operations AI Assistant. Today's date is 2025-10-14. You have advanced reasoning capabilities.\n\n"
            
            "🎯 **CORE CAPABILITIES:**\n"
            "1. **Absence Management** (Blue Theme 🔵): Employee attendance, vacation tracking, absence reports\n"
            "2. **SOW Generation** (Red Theme 🔴): Statement of Work document creation\n\n"
            
            "🧠 **INTELLIGENT REASONING:**\n"
            "- **Think First**: Always analyze user intent before responding\n"
            "- **Show Reasoning**: Include brief reasoning in your responses\n"
            "- **Context Aware**: Consider conversation history and current mode\n"
            "- **Smart Dates**: Handle relative dates intelligently (this month = October 2025)\n"
            "- **Edge Cases**: Handle ambiguous or complex requests gracefully\n\n"
            
            "📅 **SMART DATE HANDLING:**\n"
            "- 'today' = 2025-10-14\n"
            "- 'this month' = October 2025 (2025-10)\n"
            "- 'last month' = September 2025 (2025-09)\n"
            "- 'current month absences' = October 2025 absences\n"
            "- Handle all date variations intelligently\n\n"
            
            "🎨 **RESPONSE FORMAT WITH REASONING:**\n"
            "Always structure responses as:\n"
            "1. *[Brief reasoning in light text]*\n"
            "2. **Main response in normal text**\n"
            "3. Include appropriate mode indicators\n\n"
            
            "🔄 **INTELLIGENT MODE SWITCHING:**\n"
            "- **Unified Mode**: Ready for both domains\n"
            "- **Absence Mode** (🔵): Focus on attendance, but can switch\n"
            "- **SOW Mode** (🔴): SOW creation (handled separately)\n"
            "- Detect intent changes mid-conversation\n"
            "- Switch modes seamlessly when user intent changes\n\n"
            
            "⚡ **CRITICAL TOOL USAGE:**\n"
            "- **absence_chat**: For ALL absence/attendance queries (with proper action, query_type, dates)\n"
            "- **start_sow_session**: For SOW creation requests\n"
            "- **provide_guidance**: For ambiguous requests or mode switching\n"
            "- NEVER return raw text - ALWAYS use appropriate tools\n\n"
            
            "🎯 **ABSENCE MANAGEMENT INTELLIGENCE:**\n"
            "- 'Who is absent today?' → absence_chat(action='query_absence', query_type='byDate', date='2025-10-14')\n"
            "- 'Show this month absences' → absence_chat(action='query_absence', query_type='byMonth', month='2025-10')\n"
            "- 'Mark John absent' → absence_chat(action='mark_absence', employee_name='John', status='A')\n"
            "- Handle employee name variations and date parsing intelligently\n\n"
            
            "🚀 **EXAMPLES OF INTELLIGENT BEHAVIOR:**\n"
            "User: 'Show this month's absences' → *Interpreting as October 2025 absences* → Call absence_chat with byMonth\n"
            "User: 'Create SOW' → *Switching to SOW generation mode* → Call start_sow_session\n"
            "User: 'Help' → *User needs guidance on capabilities* → Call provide_guidance with options\n"
            "User in SOW asks about absence → *User wants to switch modes* → Provide guidance to exit SOW first\n\n"
            
            "🎨 **VISUAL INDICATORS:**\n"
            "- Use 🔵 for Absence-related responses\n"
            "- Use 🔴 for SOW-related responses\n"
            "- Use ⚡ for mode switching\n"
            "- Show reasoning in *italics* before main response\n\n"
            
            "Be intelligent, adaptive, and always provide maximum value to the user."
        )

    @staticmethod
    def _tool_definitions() -> List[Dict[str, Any]]:
        return [
            {
                "function_declarations": [
                    {
                        "name": "absence_chat",
                        "description": (
                            "🔵 INTELLIGENT Absence Management Tool. Use for ALL attendance, absence, vacation queries and commands. "
                            "SMART DATE PARSING: Handle 'today', 'this month', 'current month', 'last month', relative dates intelligently. "
                            "Today is 2025-10-14, current month is October 2025 (2025-10)."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["mark_absence", "query_absence"],
                                    "description": "mark_absence: Mark employee status | query_absence: Get absence reports/data",
                                },
                                "query_type": {
                                    "type": "string",
                                    "enum": ["byDate", "byDateRange", "byMonth"],
                                    "description": "For query_absence: byDate=single day, byDateRange=date range, byMonth=full month",
                                },
                                "employee_name": {
                                    "type": "string",
                                    "description": "Employee name (required for mark_absence, optional for query_absence)",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["A", "P", "V"],
                                    "description": "For mark_absence: A=Absent, P=Present, V=Vacation",
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Single date YYYY-MM-DD (for byDate queries or mark_absence). Use 2025-10-14 for 'today'",
                                },
                                "dates": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of dates YYYY-MM-DD for mark_absence or byDateRange [start, end]",
                                },
                                "month": {
                                    "type": "string",
                                    "description": "Month in YYYY-MM format for byMonth queries. Use 2025-10 for 'this month/current month'",
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
