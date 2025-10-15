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
            
            state.data["services"] = val
            state.stage = "deliverables"
            service_type = "Standard Package" if val == "standard" else "Custom Services"
            resp["message"] = f"✅ **{service_type} selected!**\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
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
                contacts = self._get_contact_options()
                resp["message"] = "✅ **Resources selected!**\n\n**Step 6: Contacts**\nSelect the contact for this project:"
                resp["contact_dropdown"] = contacts
                return state, resp
            
            resp["message"] = "Please select resources using the buttons or click Next to continue:"
            resp["show_resource_builder"] = True
            resp["resource_roles"] = ["Developer", "DevOps", "Tester", "Quality Analyst", "BA", "Project Manager"]
            resp["current_resources"] = data
            return state, resp
        
        if state.stage == "contacts":
            # Handle contact selection by ID
            if txt.startswith("contact:"):
                contact_id = txt.split(":",1)[1].strip()
                db = self._read_contacts()
                selected_contact = next((c for c in db["contacts"] if c["id"] == contact_id), None)
                
                if selected_contact:
                    state.data["contacts"] = {
                        "name": selected_contact["name"],
                        "email": selected_contact["email"],
                        "phone": selected_contact["phone"],
                        "address": selected_contact["address"],
                        "contact_person": selected_contact["contact_person"],
                        "designation": selected_contact["designation"],
                        "department": selected_contact["department"]
                    }
                    
                    contact_details = f"""✅ **Contact selected: {selected_contact['name']}**

**Contact Details:**
• **Organization**: {selected_contact['name']}
• **Contact Person**: {selected_contact['contact_person']}
• **Designation**: {selected_contact['designation']}
• **Department**: {selected_contact['department']}
• **Email**: {selected_contact['email']}
• **Phone**: {selected_contact['phone']}
• **Address**: {selected_contact['address']}

**Step 7: Budget**
Finally, provide the budget details for this project:"""
                    
                    state.stage = "budget"
                    resp["message"] = contact_details
                    return state, resp
            
            # If no valid contact selected, show dropdown again
            contacts = self._get_contact_options()
            resp["message"] = "Please select a contact from the dropdown:"
            resp["contact_dropdown"] = contacts
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