from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Tuple
import json

from ..sow_components.models import SowState, STAGES
from ..sow_components.document_service import DocumentService
from ..sow_components.gemini_client import GeminiClient

BASE_DIR = Path(__file__).resolve().parents[1]
CONTACTS_PATH = BASE_DIR / "sow_components" / "contacts_data.json"
TEMPLATE_PATH = BASE_DIR / "sow_components" / "templates" / "sow_template.docx"

class SowAdapter:
    """Blind intake across 7 stages.
    AI (Gemini) is called once in finalize()."""
    
    def __init__(self, out_root: Path):
        self.out_root = Path(out_root)
        self.doc_service = DocumentService(out_dir=self.out_root)
        self.gemini = GeminiClient()
    
    # ---- lifecycle ---------------------------------------------------------
    
    def start(self) -> Tuple[str, Dict[str, Any]]:
        return self._question_for("project_info"), {
            "tips": "We'll collect details first (no AI yet). Type 'exit' anytime to cancel."
        }
    
    def process(self, state: SowState, user_message: str) -> Tuple[SowState, Dict[str, Any]]:
        txt = (user_message or "").strip()
        resp: Dict[str, Any] = {}
        
        if state.stage == "project_info":
            state.data["project_info"] = txt
            state.stage = "services"
            resp["message"] = "✅ **Project Info captured!**\n\n**Step 2: Services**\nChoose the type of services for this SOW:"
            resp["confirmation_buttons"] = [
                {"id":"sow_service_standard","label":"📦 Standard Package","value":"standard","style":"primary"},
                {"id":"sow_service_custom","label":"🛠️ Custom Services","value":"custom","style":"secondary"},
            ]
            return state, resp
        
        if state.stage == "services":
            val = txt.lower()
            if val not in {"standard", "custom"}:
                resp["message"] = "Please select one of the service options:"
                resp["confirmation_buttons"] = [
                    {"id":"sow_service_standard","label":"📦 Standard Package","value":"standard","style":"primary"},
                    {"id":"sow_service_custom","label":"🛠️ Custom Services","value":"custom","style":"secondary"},
                ]
                return state, resp
            
            if val == "standard":
                # Standard service - continue directly
                state.data["services"] = "Standard Package - Comprehensive service package including design, development, testing, deployment, and support"
                state.stage = "deliverables"
                resp["message"] = "✅ **Standard Package selected!**\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
                return state, resp
            else:
                # Custom service - ask for details
                state.data["services"] = "custom"
                state.stage = "services_custom"
                resp["message"] = "✅ **Custom Services selected!**\n\nPlease describe your custom services in detail:\n• What specific services do you need?\n• What work will be performed?\n• Any special requirements or methodologies?"
                return state, resp
        
        if state.stage == "services_custom":
            # Store custom service details
            state.data["services"] = f"Custom Services: {txt}"
            state.stage = "deliverables"
            resp["message"] = "✅ **Custom services captured!**\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
            return state, resp
        
        if state.stage == "deliverables":
            state.data["deliverables"] = txt
            state.stage = "timeline"
            resp["message"] = "✅ **Deliverables captured!**\n\n**Step 4: Timeline**\nProvide the project timeline (milestones, dates, duration):"
            return state, resp
        
        if state.stage == "timeline":
            state.data["timeline"] = txt
            state.stage = "resources"
            resp["message"] = "✅ **Timeline captured!**\n\n**Step 5: Resources**\nSelect the team members needed for this project:"
            resp["show_resource_builder"] = True
            resp["resource_roles"] = ["Developer", "DevOps", "Tester", "Quality Analyst", "BA", "Project Manager"]
            resp["current_resources"] = state.data.get("resources", [])
            return state, resp
        
        if state.stage == "resources":
            # Controls: "+:Developer" / "-:Tester" / "next"
            data = state.data.setdefault("resources", [])
            
            def set_count(role: str, delta: int):
                for r in data:
                    if r["role"].lower() == role.lower():
                        r["count"] = max(0, r["count"] + delta)
                        if r["count"] == 0:
                            data.remove(r)
                        return
                if delta > 0:
                    data.append({"role": role, "count": delta})
            
            if txt.startswith("+:") or txt.startswith("add:"):
                role = txt.split(":",1)[1].strip()
                set_count(role, 1)
                # Don't return a new message, just update the data silently
                resp["silent_update"] = True
                resp["show_resource_builder"] = True
                resp["resource_roles"] = ["Developer", "DevOps", "Tester", "Quality Analyst", "BA", "Project Manager"]
                resp["current_resources"] = data
                return state, resp
            elif txt.startswith("-:"):
                role = txt.split(":",1)[1].strip()
                set_count(role, -1)
                # Don't return a new message, just update the data silently
                resp["silent_update"] = True
                resp["show_resource_builder"] = True
                resp["resource_roles"] = ["Developer", "DevOps", "Tester", "Quality Analyst", "BA", "Project Manager"]
                resp["current_resources"] = data
                return state, resp
            elif txt.lower() == "next":
                state.stage = "contacts"
                state.data.pop("_awaiting_contact_details", None)
                contact_hint = self._contact_selection_hint(
                    "✅ **Resources selected!**\n\n"
                    "**Step 6: Contacts**\n"
                    "Select the contact for this project. Choose an existing contact from the dropdown "
                    "or add a brand new contact."
                )
                resp.update(contact_hint)
                return state, resp
            
            resp["message"] = "Please select resources using the buttons or click Next to continue:"
            resp["show_resource_builder"] = True
            resp["resource_roles"] = ["Developer", "DevOps", "Tester", "Quality Analyst", "BA", "Project Manager"]
            resp["current_resources"] = data
            return state, resp
        
        if state.stage == "contacts":
            awaiting_new = bool(state.data.get("_awaiting_contact_details"))
            normalized = txt.strip().lower()

            if awaiting_new and normalized in {"cancel", "back"}:
                state.data.pop("_awaiting_contact_details", None)
                contact_hint = self._contact_selection_hint(
                    "Okay, no problem. Please choose an existing contact from the dropdown "
                    "or add a new contact."
                )
                resp.update(contact_hint)
                return state, resp

            if awaiting_new:
                contact_info = self._parse_contact_details(txt)
                required_labels = {
                    "name": "Organization",
                    "contact_person": "Contact Person",
                    "email": "Email"
                }
                missing = [label for key, label in required_labels.items() if not contact_info.get(key)]

                if missing:
                    resp["message"] = (
                        "I still need the following details for the new contact: "
                        f"{', '.join(missing)}.\n"
                        "Please provide them using the format `Field: value`."
                    )
                    return state, resp

                state.data["contacts"] = contact_info
                state.data.pop("_awaiting_contact_details", None)
                state.stage = "budget"
                resp["message"] = self._contact_confirmation_message(contact_info)
                return state, resp

            if normalized.startswith("contact:new") or normalized in {
                "new",
                "new contact",
                "add contact",
                "add new contact",
            }:
                state.data["_awaiting_contact_details"] = True
                resp["message"] = (
                    "Great, let's capture the new contact details.\n\n"
                    "Please provide the information using lines like these:\n"
                    "Organization: Example Corp\n"
                    "Contact Person: Jane Doe\n"
                    "Designation: Director of Operations\n"
                    "Department: Operations\n"
                    "Email: jane.doe@example.com\n"
                    "Phone: +1-555-123-4567\n"
                    "Address: 123 Main Street, City, Country\n\n"
                    "You can also separate the fields with commas. Type `cancel` to go back to the contact list."
                )
                return state, resp

            if txt.startswith("contact:"):
                contact_id = txt.split(":", 1)[1].strip()
                db = self._read_contacts()
                selected_contact = next((c for c in db.get("contacts", []) if c["id"] == contact_id), None)

                if selected_contact:
                    state.data["contacts"] = {
                        "name": selected_contact.get("name", ""),
                        "email": selected_contact.get("email", ""),
                        "phone": selected_contact.get("phone", ""),
                        "address": selected_contact.get("address", ""),
                        "contact_person": selected_contact.get("contact_person", ""),
                        "designation": selected_contact.get("designation", ""),
                        "department": selected_contact.get("department", ""),
                    }
                    state.stage = "budget"
                    resp["message"] = self._contact_confirmation_message(state.data["contacts"])
                    return state, resp

            contact_hint = self._contact_selection_hint(
                "Please select a contact from the dropdown or choose **Add New Contact** to enter details manually."
            )
            resp.update(contact_hint)
            return state, resp
        
        if state.stage == "budget":
            state.data["budget"] = txt
            resp["message"] = "✅ **Budget captured!**\n\n🎉 **All information collected successfully!**\n\nReady to generate your professional SOW document?"
            resp["generate_buttons"] = [
                {"id":"sow_generate","label":"📄 Generate SOW Document","value":"generate_sow","style":"primary"}
            ]
            return state, resp
        
        resp["message"] = "Please continue with the current step."
        return state, resp
    
    def finalize(self, state: SowState, session_id: str) -> Dict[str, Any]:
        prompt = self._prompt_from_state(state.data)
        _ = self.gemini.generate_sow_text(prompt)  # optional polish step
        
        context = {
            "project_info": state.data["project_info"],
            "services": state.data["services"],
            "deliverables": state.data["deliverables"],
            "timeline": state.data["timeline"],
            "resources": state.data["resources"],
            "contacts": state.data["contacts"],
            "budget": state.data["budget"],
        }
        
        template = TEMPLATE_PATH if TEMPLATE_PATH.exists() else None
        out_path = self.doc_service.generate(
            context=context, 
            session_id=session_id, 
            template_path=template
        )
        
        return {
            "message": "SOW generated successfully.",
            "download_url": f"/api/sow/documents/{session_id}/{out_path.name}"
        }
    
    # ---- helpers -----------------------------------------------------------
    
    def _question_for(self, stage: str) -> str:
        return {
            "project_info": "Project Info: briefly describe project, goal, and scope.",
            "services": "Choose service type: Standard or Custom.",
            "deliverables": "List key deliverables (bullet text or comma separated).",
            "timeline": "Provide timeline (milestones, dates).",
            "resources": "Add resources with +:/-:Role (or buttons), then say 'next'.",
            "contacts": "Pick client & contractor from the options.",
            "budget": "Provide budget (amount + currency)."
        }[stage]
    
    def _get_contact_options(self):
        db = self._read_contacts()
        options = []
        for contact in db.get("contacts", []):
            options.append({
                "id": contact["id"],
                "label": f"{contact['name']} ({contact['type'].title()})",
                "value": f"contact:{contact['id']}",
                "details": {
                    "name": contact["name"],
                    "type": contact["type"],
                    "contact_person": contact["contact_person"],
                    "designation": contact["designation"],
                    "email": contact["email"],
                    "phone": contact["phone"]
                }
            })
        return options

    def _contact_selection_hint(self, message: str) -> Dict[str, Any]:
        return {
            "message": message,
            "contact_dropdown": self._get_contact_options(),
            "contact_prompt": "Select an existing contact or choose Add New Contact to provide fresh details.",
            "contact_allow_new": True,
            "contact_new_button": {
                "id": "sow_contact_new",
                "label": "Add New Contact",
                "value": "contact:new",
                "style": "secondary",
            },
        }

    def _contact_confirmation_message(self, contact: Dict[str, Any]) -> str:
        def field(key: str) -> str:
            value = contact.get(key)
            return value if value else "—"

        return (
            f"✅ **Contact selected: {field('name')}**\n\n"
            "**Contact Details:**\n"
            f"• **Organization**: {field('name')}\n"
            f"• **Contact Person**: {field('contact_person')}\n"
            f"• **Designation**: {field('designation')}\n"
            f"• **Department**: {field('department')}\n"
            f"• **Email**: {field('email')}\n"
            f"• **Phone**: {field('phone')}\n"
            f"• **Address**: {field('address')}\n\n"
            "**Step 7: Budget**\nFinally, provide the budget details for this project:"
        )

    @staticmethod
    def _normalize_key(raw_key: str) -> str:
        return "".join(ch for ch in raw_key.lower() if ch.isalnum())

    def _parse_contact_details(self, text: str) -> Dict[str, str]:
        details = {
            "name": "",
            "contact_person": "",
            "designation": "",
            "department": "",
            "email": "",
            "phone": "",
            "address": "",
            "type": "custom",
        }

        if not text:
            return details

        segments = [line.strip() for line in text.splitlines() if line.strip()]
        if not segments:
            segments = [part.strip() for part in text.split(",") if part.strip()]

        key_map = {
            "organization": "name",
            "company": "name",
            "client": "name",
            "business": "name",
            "contactperson": "contact_person",
            "contactname": "contact_person",
            "person": "contact_person",
            "designation": "designation",
            "title": "designation",
            "role": "designation",
            "department": "department",
            "team": "department",
            "email": "email",
            "emailaddress": "email",
            "phone": "phone",
            "phonenumber": "phone",
            "mobile": "phone",
            "telephone": "phone",
            "address": "address",
            "location": "address",
        }

        for segment in segments:
            if ":" not in segment:
                continue
            raw_key, raw_value = segment.split(":", 1)
            normalized_key = self._normalize_key(raw_key)
            value = raw_value.strip()
            if not value:
                continue

            if normalized_key == "name":
                target = "name" if not details["name"] else "contact_person"
                details[target] = value
                continue

            target_key = key_map.get(normalized_key)
            if target_key:
                details[target_key] = value

        return details
    
    def _read_contacts(self):
        if not CONTACTS_PATH.exists():
            return {"contacts": []}
        return json.loads(CONTACTS_PATH.read_text())
    
    @staticmethod
    def _parse_pairs(s: str) -> Dict[str, str]:
        out = {}
        for part in s.split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                out[k.strip().lower()] = v.strip()
        return out
    
    def _prompt_from_state(self, data: Dict[str, Any]) -> str:
        """Generate prompt for Gemini from collected data"""
        return f"""
        Generate a professional Statement of Work based on:
        
        Project: {data.get('project_info', '')}
        Services: {data.get('services', '')}
        Deliverables: {data.get('deliverables', '')}
        Timeline: {data.get('timeline', '')}
        Resources: {data.get('resources', [])}
        Budget: {data.get('budget', '')}
        """
