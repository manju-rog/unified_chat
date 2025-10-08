"""Adapter for Statement of Work generation workflows."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any, Dict

from ..config import get_settings


# Ensure sow project is on sys.path before importing
_settings = get_settings()
if str(_settings.sow_project_root) not in sys.path:
    sys.path.insert(0, str(_settings.sow_project_root))

from interactive_sow_chat import ConversationalSOWGenerator  # type: ignore  # noqa: E402

from ..models import SessionState, SOWSessionState


SECTION_STATE_SEQUENCE = {
    "services": "PROJECT_BASICS",
    "deliverables": "SERVICES",
    "timeline": "DELIVERABLES",
    "resources": "TIMELINE",
    "contacts": "RESOURCES",
    "budget": "CONTACTS",
}


class SOWAdapter:
    """Manages conversational SOW flows per chat session."""

    def __init__(self) -> None:
        self._settings = _settings

    def start_session(self, session: SessionState, project_overview: str) -> Dict[str, Any]:
        state = self._ensure_state(session)
        generator = state.generator

        # If this is the first time, load the template
        if state.current_step == "INITIAL_LOAD":
            generator.process_user_input(
                None,
                uploaded_file=str(self._settings.sow_default_template),
                use_default=False,
            )
            state.current_step = generator.conversation_state

        result = generator.process_user_input(project_overview)
        state.current_step = generator.conversation_state
        session.active_domain = "sow"

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Let me know more about your project."),
            "next_step": state.current_step,
        }

    def update_section(self, session: SessionState, section: str, content: str) -> Dict[str, Any]:
        state = self._ensure_state(session)
        expected_state = SECTION_STATE_SEQUENCE.get(section)
        if expected_state is None:
            return {"success": False, "message": f"Unknown SOW section '{section}'."}

        if state.generator.conversation_state != expected_state:
            return {
                "success": False,
                "message": (
                    f"I was expecting information for {state.generator.conversation_state.lower()} before "
                    f"handling {section}. Let's continue in order."
                ),
            }

        result = state.generator.process_user_input(content)
        state.current_step = state.generator.conversation_state
        state.collected_sections[section] = content

        response: Dict[str, Any] = {
            "success": result.get("success", False),
            "message": result.get("message", "Thanks!"),
            "next_step": state.current_step,
        }

        if result.get("filename"):
            stored_path = self._store_generated_file(session.session_id, result["filename"])
            state.generated_files.append(stored_path.name)
            response["download_path"] = stored_path.name

        return response

    def finalize(self, session: SessionState) -> Dict[str, Any]:
        state = self._ensure_state(session)
        if state.generator.conversation_state not in {"BUDGET", "GENERATE"}:
            return {
                "success": False,
                "message": "I still need more project details before generating the SOW.",
                "next_step": state.generator.conversation_state,
            }

        if state.generator.conversation_state == "BUDGET" and not state.generated_files:
            result = state.generator.process_user_input("Generate document")
            if result.get("filename"):
                stored_path = self._store_generated_file(session.session_id, result["filename"])
                state.generated_files.append(stored_path.name)

        if not state.generated_files:
            return {"success": False, "message": "Document generation did not complete yet."}

        latest = state.generated_files[-1]
        return {
            "success": True,
            "message": "Your SOW document is ready to download.",
            "download_path": latest,
        }

    def _ensure_state(self, session: SessionState) -> SOWSessionState:
        if session.sow_state is None:
            generator = ConversationalSOWGenerator()
            key = (self._settings.gemini_api_key or "").strip()
            generator.ai_enabled = bool(key) and key.upper() != "OFFLINE"
            session.sow_state = SOWSessionState(
                generator=generator,
                current_step="INITIAL_LOAD",
            )
        return session.sow_state

    def _store_generated_file(self, session_id: str, filename: str) -> Path:
        source_path = Path(filename)
        if not source_path.exists():
            # Try relative to sow project root
            candidate = self._settings.sow_project_root / filename
            if candidate.exists():
                source_path = candidate
            else:
                raise FileNotFoundError(f"Generated file {filename} not found")

        target_dir = self._settings.sow_output_dir / session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / source_path.name
        shutil.move(str(source_path), target_path)
        return target_path


sow_adapter = SOWAdapter()
