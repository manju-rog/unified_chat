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
        import time
        import json
        
        # **INTERCEPT YES/NO RESPONSES - DON'T EVEN CALL GEMINI**
        message_lower = user_message.lower().strip()
        simple_confirmations = ["yes", "no", "y", "n", "yeah", "yep", "nope", "ok", "okay"]
        
        if message_lower in simple_confirmations and context and "reason" in context:
            print(f"🚫 INTERCEPTING CONFIRMATION: '{user_message}' - returning empty response for system handler")
            # Return empty response so fallback classifier can handle it
            class EmptyResponse:
                def __init__(self):
                    self.candidates = [EmptyCandidate()]
            
            class EmptyCandidate:
                def __init__(self):
                    self.content = EmptyContent()
                    self.finish_reason = None
            
            class EmptyContent:
                def __init__(self):
                    self.parts = [EmptyPart()]
            
            class EmptyPart:
                def __init__(self):
                    self.function_call = None
                    self.text = ""  # Empty text to trigger fallback
            
            return EmptyResponse()
        
        try:
            history = session.recent_history(self._settings.session_history_limit)
            messages: List[Dict[str, Any]] = []
            if history:
                messages.extend(history)
            
            # Add context if provided
            context_parts = []
            
            # ALWAYS include current date in context
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            day_name = datetime.now().strftime("%A")
            context_parts.append(f"TODAY'S DATE: {today} ({day_name})")
            
            if context:
                context_parts.append(context)
            
            if context_parts:
                full_message = f"{' | '.join(context_parts)}\n\nUser request: {user_message}"
            else:
                full_message = user_message
                
            messages.append({"role": "user", "parts": [full_message]})

            # **DETAILED LOGGING FOR DEBUGGING**
            print(f"\n🔍 GEMINI REQUEST DEBUG:")
            print(f"📝 User Message: '{user_message}'")
            print(f"🎯 Context: {context}")
            print(f"📚 History Length: {len(history)}")
            print(f"💬 Full Message to Gemini: '{full_message}'")
            print(f"🛠️ Available Tools: {len(self._tool_definitions()[0]['function_declarations'])}")
            
            # Add timeout and retry logic
            start_time = time.time()
            response = self._model.generate_content(
                messages,
                tool_config={"function_calling_config": {"mode": "AUTO"}},
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️ Gemini Response Time: {elapsed:.2f}s")
            
            return response
            
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            # Return a fallback response that will trigger absence_chat
            class FallbackResponse:
                def __init__(self):
                    self.candidates = [FallbackCandidate()]
            
            class FallbackCandidate:
                def __init__(self):
                    self.content = FallbackContent()
            
            class FallbackContent:
                def __init__(self):
                    self.parts = [FallbackPart()]
            
            class FallbackPart:
                def __init__(self):
                    self.function_call = FallbackFunctionCall()
                    self.text = None
            
            class FallbackFunctionCall:
                def __init__(self):
                    self.name = "absence_chat"
                    self.args = {
                        "action": "check_employee_status" if "is" in user_message.lower() else "mark_absence",
                        "employee_name": self._extract_name_from_message(user_message),
                        "query_type": "specific_employee"
                    }
            
            return FallbackResponse()
    
    def _extract_name_from_message(self, message: str) -> str:
        """Extract employee name from message as fallback."""
        words = message.lower().split()
        # Common employee names in the system
        known_names = ["manju", "ganesh", "shreyas", "suhas", "anushri"]
        for word in words:
            for name in known_names:
                if word in name or name in word:
                    return name
        return "someone"  # Fallback

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """Normalize Gemini responses into text/tool actions."""
        import json

        print(f"\n🔍 GEMINI RESPONSE DEBUG:")
        
        if not response.candidates:
            print("❌ No candidates in response")
            raise RuntimeError("Gemini returned no candidates")

        candidate = response.candidates[0]
        print(f"📊 Candidate finish reason: {getattr(candidate, 'finish_reason', 'unknown')}")
        
        if not candidate.content or not candidate.content.parts:
            print("❌ No content parts in candidate")
            raise RuntimeError("Gemini candidate missing content parts")

        parts = candidate.content.parts
        tool_calls: List[ToolCall] = []
        text_fragments: List[str] = []
        thinking_parts: List[str] = []

        print(f"🧩 Response parts count: {len(parts)}")
        
        for i, part in enumerate(parts):
            print(f"  Part {i+1}:")
            
            if getattr(part, "function_call", None):
                func_call = part.function_call
                name = func_call.name
                raw_args = func_call.args or {}
                
                print(f"    🛠️ FUNCTION CALL: {name}")
                print(f"    📋 Raw Args Type: {type(raw_args)}")
                print(f"    📋 Raw Args: {raw_args}")
                
                # Build thinking description
                thinking_parts.append(f"Calling {name}")
                if name == "absence_chat":
                    action = raw_args.get("action", "unknown")
                    thinking_parts.append(f"Action: {action}")
                elif name == "start_sow_session":
                    thinking_parts.append("Initiating SOW generation flow")
                
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {"value": raw_args}
                else:
                    # Use dict() for tool execution, safe serialization only for debug
                    args = dict(raw_args)
                
                print(f"    ✅ Parsed Args: {args}")
                tool_calls.append(ToolCall(name=name, arguments=args))
                
            elif getattr(part, "text", None):
                print(f"    💬 TEXT: '{part.text}'")
                text_fragments.append(part.text)
            else:
                print(f"    ❓ UNKNOWN PART TYPE: {type(part)}")

        # Generate thinking summary
        thinking = None
        if tool_calls:
            thinking = " → ".join(thinking_parts) if thinking_parts else f"Processing {tool_calls[0].name}"
        elif text_fragments:
            thinking = "Generating response"

        result = {
            "tool_calls": tool_calls,
            "text": "\n".join(fragment for fragment in text_fragments if fragment),
            "thinking": thinking,
        }
        
        print(f"🎯 FINAL PARSED RESULT:")
        print(f"  Tool calls: {len(tool_calls)}")
        for tc in tool_calls:
            print(f"    - {tc.name}: {tc.arguments}")
        print(f"  Text: '{result['text']}'")
        print(f"  Thinking: '{result.get('thinking')}'")
        print(f"{'='*50}")
        
        return result



    @staticmethod
    def _system_prompt() -> str:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        day_name = datetime.now().strftime("%A")
        
        current_year = datetime.now().year
        current_month = datetime.now().strftime("%B")
        
        lines = [
            f"You are the Unified Operations AI Assistant. Today's date is {today} ({day_name}). Current year is {current_year}. Current month is {current_month}. Always respond by calling one of the registered tools.",
            "",
            "**Absence Management — use `absence_chat`:**",
            "- action='mark_absence' with `employee_name`, `status` (A/P/V), optional `reason`, and `date`.",
            "- action='mark_multiple_absence' with `employee_names` for bulk updates.",
            "- action='query_absence' with `time_period`, `date`, `date_range`, or (`month`, `year`).",
            "- action='query_vacation' (optional `date`) to list who is on vacation.",
            "- action='check_employee_status' with `employee_name`, optional `date`, and optional `query_type='leave_status'`.",
            "",
            "**EMPLOYEE NAME HANDLING:**",
            "- You will receive EMPLOYEE_DIRECTORY in context with format: Name|ID|Department",
            "- When user says 'someone', 'somebody', 'anyone', or doesn't specify a name, pick the FIRST employee from the directory",
            "- NEVER use 'Unknown', 'someone', 'somebody' as employee_name - always use an actual name from the directory",
            "- The backend will handle fuzzy matching and disambiguation if needed",
            "- If the directory is empty or not provided, then use `provide_guidance` to ask for the name",
            "",
            f"**CRITICAL DATE RULES:**",
            f"- TODAY is {today} ({day_name})",
            f"- CURRENT YEAR is {current_year} - ALWAYS use this year unless user explicitly mentions a different year",
            f"- CURRENT MONTH is {current_month}",
            f"- When user says 'September absences' or any month name WITHOUT a year, use year={current_year}",
            f"- When user says 'this week', calculate from today ({today})",
            f"- When user says 'this month', use current month ({current_month} {current_year})",
            f"- NEVER assume year 2024 or any past year - ALWAYS use {current_year} unless explicitly stated otherwise",
            "",
            "**Dates & Periods:** support tokens like today/yesterday/tomorrow; use time_period='this_week'/'next_week'/'last_week' and 'this_month'/'next_month'/'last_month'; provide explicit `date_range` {start, end} for 'between' queries; supply `month` (month name like 'september') and `year` (use current year if not specified) for named months.",
            "",
            "**Reasons:** when marking an absence without a reason, return confirmation buttons asking whether to add one. If the user supplies a reason, call `absence_chat` again with that reason included.",
            "",
            "**SOW Generation:** ALWAYS use `start_sow_session` for ANY SOW-related request including 'create sow', 'generate sow', 'statement of work', 'sow generation'. Use `update_sow_section` to collect sections, and call `finalize_sow` only when all sections are complete.",
            "",
            "**EXIT COMMANDS:** If user says 'exit sow', 'exit', 'quit', 'cancel', 'stop sow', or 'exit_sow', they want to exit SOW mode. Use `provide_guidance` with guidance_type='help' and main_response='Exiting SOW mode. You're back to the main assistant.' This is a VALID operation, not out_of_context.",
            "",
            "**Guidance & Confusion Handling:** use `provide_guidance` for:",
            "- Greetings, capability questions, or help requests",
            "- Ambiguous, incomplete, or confusing queries where you need more information",
            "- Out-of-context messages that don't relate to absence or SOW",
            "- Vague requests like 'do something', 'help me', 'what can you do'",
            "- EXIT commands like 'exit sow', 'quit', 'cancel' (use guidance_type='help')",
            "When confused, be friendly and conversational. Use light humor when appropriate. Ask clarifying questions in a natural way.",
            "For guidance_type, use: 'greeting', 'capabilities', 'confused', 'incomplete', 'out_of_context', 'ambiguous', or 'help'.",
            "",
            "Be decisive: interpret any phrasing about absences, vacations, or leave, choose the correct action, and call the tool with complete parameters. Never ask the user to rephrase—you can resolve typos using the employee directory.",
            "",
            "**CRITICAL SOW DETECTION:** When user mentions 'sow', 'statement of work', 'create sow', 'generate sow', or similar, ALWAYS call `start_sow_session` immediately. Do not use `provide_guidance` for SOW requests.",
            "",
            "**ABSOLUTE RULE - NEVER BREAK:** If the user message is ONLY 'yes', 'no', 'y', 'n', or similar single-word confirmations, you MUST NOT call ANY tool. Do not use provide_guidance, do not use absence_chat. Return completely empty response. The system has special handlers for these. This rule overrides everything else.",
        ]
        return "\n".join(lines)


    @staticmethod
    def _tool_definitions() -> List[Dict[str, Any]]:
        return [
            {
                "function_declarations": [
                    {
                        "name": "absence_chat",
                        "description": (
                            "Perform any absence or leave related operation: mark employees, query reports, "
                            "or check individual status."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": [
                                        "mark_absence",
                                        "mark_multiple_absence",
                                        "query_absence",
                                        "query_vacation",
                                        "check_employee_status"
                                    ],
                                },
                                "employee_name": {"type": "string"},
                                "employee_names": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "status": {"type": "string", "enum": ["A", "P", "V"]},
                                "date": {"type": "string"},
                                "date_range": {
                                    "type": "object",
                                    "properties": {
                                        "start": {"type": "string"},
                                        "end": {"type": "string"}
                                    }
                                },
                                "time_period": {
                                    "type": "string",
                                    "enum": [
                                        "today", "yesterday", "tomorrow",
                                        "this_week", "next_week", "last_week",
                                        "this_month", "next_month", "last_month"
                                    ]
                                },
                                "month": {"type": "string"},
                                "year": {"type": "integer"},
                                "reason": {"type": "string"},
                                "query_type": {"type": "string"}
                            },
                            "required": ["action"],
                        },
                    },
                    {
                        "name": "start_sow_session",
                        "description": "Begin the Statement of Work guided conversation.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "projectOverview": {"type": "string"}
                            },
                            "required": ["projectOverview"],
                        },
                    },
                    {
                        "name": "update_sow_section",
                        "description": "Provide details for the current SOW section.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "section": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["section", "content"],
                        },
                    },
                    {
                        "name": "finalize_sow",
                        "description": "Generate the final SOW output once all sections are complete.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "provide_guidance",
                        "description": (
                            "Offer help, clarification, or friendly responses when no direct action should be executed. "
                            "Use this for greetings, capability questions, confused/incomplete/ambiguous queries, or out-of-context messages. "
                            "Be conversational, friendly, and use light humor when appropriate."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "guidance_type": {
                                    "type": "string",
                                    "enum": [
                                        "greeting",
                                        "capabilities", 
                                        "confused",
                                        "incomplete",
                                        "out_of_context",
                                        "ambiguous",
                                        "help"
                                    ],
                                    "description": "Type of guidance being provided"
                                },
                                "explanation": {
                                    "type": "string",
                                    "description": "Brief italic explanation of why you're asking for clarification (optional)"
                                },
                                "main_response": {
                                    "type": "string",
                                    "description": "Main friendly response with personality. Can include light humor for confused/incomplete queries."
                                },
                                "suggested_actions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific examples the user can try"
                                }
                            },
                            "required": ["guidance_type", "main_response"],
                        },
                    },
                ]
            }
        ]


gemini_client = GeminiClient()
