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
        # Use generated_docs_sow folder at project root
        project_root = Path(__file__).resolve().parents[3]  # Go up to project root
        self.out_root = project_root / "generated_docs_sow"
        self.out_root.mkdir(parents=True, exist_ok=True)
        print(f"📁 SOW output directory: {self.out_root}")
        
        self.doc_service = DocumentService(out_dir=self.out_root)
        # Initialize Gemini client with API key from environment
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"🔑 Gemini API Key loaded: {'Yes' if api_key else 'No'} (length: {len(api_key) if api_key else 0})")
        self.gemini = GeminiClient(api_key=api_key)
    
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
            
            # Load standard services from new_sow for button
            try:
                import importlib.util
                from pathlib import Path
                
                # Direct path to standard_services.py
                # parents[4] goes: sow_direct.py -> services -> app -> backend -> unified_ai_chat -> project root
                standard_services_path = Path(__file__).resolve().parents[4] / "new_sow" / "app" / "services" / "standard_services.py"
                
                # Load module from file
                spec = importlib.util.spec_from_file_location("standard_services", standard_services_path)
                standard_services_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(standard_services_module)
                
                STANDARD_SERVICES = standard_services_module.STANDARD_SERVICES
                standard_service = STANDARD_SERVICES[0]
                standard_text = f"SERVICES: {standard_service['name']}\n\n{standard_service['description']}"
                print(f"✅ Loaded standard services from new_sow for button")
            except Exception as e:
                print(f"⚠️ Could not load standard services for button: {e}")
                import traceback
                traceback.print_exc()
                standard_text = "SERVICES: Discovery & Planning (3 weeks), Data Migration (4 weeks), Application Development (8 weeks), Testing & QA (2 weeks), Deployment & Go-Live (1 week)"
            
            resp["confirmation_buttons"] = [
                {"id":"sow_service_standard","label":"📦 Standard Package","populate_input":standard_text,"style":"primary"},
                {"id":"sow_service_custom","label":"🛠️ Custom Services","populate_input":"Custom Services (to be defined based on project requirements)","style":"secondary"},
            ]
            return state, resp
        
        if state.stage == "services":
            # Handle button clicks, keywords, OR manual typing
            # CRITICAL: Store just "standard" or "custom" keyword for new_sow to process
            if txt.startswith("SERVICES:"):
                # Full standard package text (from button) - extract keyword
                state.data["services"] = "standard"  # ← Pass keyword to new_sow
                service_type = "Standard Package"
                
                # Load preview text for display only
                try:
                    import importlib.util
                    from pathlib import Path
                    standard_services_path = Path(__file__).resolve().parents[4] / "new_sow" / "app" / "services" / "standard_services.py"
                    spec = importlib.util.spec_from_file_location("standard_services", standard_services_path)
                    standard_services_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(standard_services_module)
                    STANDARD_SERVICES = standard_services_module.STANDARD_SERVICES
                    standard_service = STANDARD_SERVICES[0]
                    preview_text = f"{standard_service['name']}\n\n{standard_service['description'][:200]}..."
                except:
                    preview_text = "Standard services package (15 detailed scope items)"
            elif txt.startswith("Custom Services"):
                # Full custom services text (from button) - extract keyword
                state.data["services"] = "custom"  # ← Pass keyword to new_sow
                service_type = "Custom Services"
                preview_text = "Custom services (to be defined based on project requirements)"
            elif txt.lower() == "standard":
                # Short keyword - pass directly to new_sow
                state.data["services"] = "standard"  # ← Pass keyword to new_sow
                service_type = "Standard Package"
                
                # Load preview text for display only
                try:
                    import importlib.util
                    from pathlib import Path
                    standard_services_path = Path(__file__).resolve().parents[4] / "new_sow" / "app" / "services" / "standard_services.py"
                    spec = importlib.util.spec_from_file_location("standard_services", standard_services_path)
                    standard_services_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(standard_services_module)
                    STANDARD_SERVICES = standard_services_module.STANDARD_SERVICES
                    standard_service = STANDARD_SERVICES[0]
                    preview_text = f"{standard_service['name']}\n\n{standard_service['description'][:200]}..."
                    print(f"✅ Loaded standard services preview from new_sow")
                except Exception as e:
                    print(f"⚠️ Could not load standard services preview: {e}")
                    preview_text = "Standard services package (15 detailed scope items)"
            elif txt.lower() == "custom":
                # Short keyword - pass directly to new_sow
                state.data["services"] = "custom"  # ← Pass keyword to new_sow
                service_type = "Custom Services"
                preview_text = "Custom services (to be defined based on project requirements)"
            else:
                # Accept ANY manual text - user typed their own services
                state.data["services"] = txt  # ← Pass custom text to new_sow
                service_type = "Custom Services"
                preview_text = txt
            
            state.stage = "deliverables"
            resp["message"] = f"✅ **{service_type} selected!**\n\n**Services Preview:**\n{preview_text}\n\n**Step 3: Deliverables**\nNow tell me about the specific deliverables for this project:"
            return state, resp
        
        if state.stage == "deliverables":
            state.data["deliverables"] = txt
            state.stage = "timeline"
            resp["message"] = "✅ **Deliverables captured!**\n\n**Step 4: Timeline**\nProvide the project timeline (milestones, dates, duration):"
            return state, resp
        
        if state.stage == "timeline":
            state.data["timeline"] = txt
            state.stage = "resources"
            resp["message"] = "✅ **Timeline captured!**\n\n**Step 5: Resources**\nSelect team members using the + and - buttons below:"
            resp["show_resource_builder"] = True
            resp["resource_roles"] = ["Developer", "DevOps", "Tester", "QA Engineer", "Business Analyst", "Project Manager"]
            data = state.data.get("resources", [])
            resp["current_resources"] = data
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
                # Silent update - just update the data without new message
                resp["silent_update"] = True
                resp["show_resource_builder"] = True
                resp["resource_roles"] = ["Developer", "DevOps", "Tester", "QA Engineer", "Business Analyst", "Project Manager"]
                resp["current_resources"] = data
                return state, resp
            elif txt.startswith("-:"):
                role = txt.split(":",1)[1].strip()
                set_count(role, -1)
                # Silent update - just update the data without new message
                resp["silent_update"] = True
                resp["show_resource_builder"] = True
                resp["resource_roles"] = ["Developer", "DevOps", "Tester", "QA Engineer", "Business Analyst", "Project Manager"]
                resp["current_resources"] = data
                return state, resp
            elif txt.lower() == "next" or txt.startswith("Add these resources:"):
                # Handle resource summary commit
                if txt.startswith("Add these resources:"):
                    # Extract and format the resource summary
                    resource_summary = txt.replace("Add these resources: ", "")
                    resp["message"] = f"✅ **Resources captured:**\n{resource_summary}\n\n**Step 6: Contacts**\nSelect a contact (it will appear in the input field):"
                else:
                    resp["message"] = "✅ **Resources selected!**\n\n**Step 6: Contacts**\nSelect a contact (it will appear in the input field):"
                
                state.stage = "contacts"
                contacts = self._get_contact_options()
                resp["confirmation_buttons"] = [
                    {"id": contact["id"], "label": contact["label"], "populate_input": contact["value"], "style": "primary"}
                    for contact in contacts[:5]  # Show first 5 contacts as buttons
                ]
                return state, resp
            else:
                # Accept manual text input - parse as free-form resource description
                # User can type: "2 Developers, 1 Tester, 1 Project Manager"
                # Store as-is and move to next stage
                state.data["resources_text"] = txt
                state.stage = "contacts"
                
                resp["message"] = f"✅ **Resources captured:**\n{txt}\n\n**Step 6: Contacts**\nSelect a contact (it will appear in the input field):"
                contacts = self._get_contact_options()
                resp["confirmation_buttons"] = [
                    {"id": contact["id"], "label": contact["label"], "populate_input": contact["value"], "style": "primary"}
                    for contact in contacts[:5]
                ]
                return state, resp
        
        if state.stage == "contacts":
            # Handle contact selection - button click, database match, OR manual typing
            selected_contact = None
            db = self._read_contacts()
            
            if txt.startswith("CONTACT:"):
                # Full text format from button - extract organization name
                # Format: "CONTACT: MUFG Bank | Contact Person: ..."
                org_name = txt.split("|")[0].replace("CONTACT:", "").strip()
                selected_contact = next((c for c in db["contacts"] if c["name"].lower() == org_name.lower()), None)
            elif txt.startswith("contact:"):
                # ID format
                contact_id = txt.split(":",1)[1].strip()
                selected_contact = next((c for c in db["contacts"] if c["id"] == contact_id), None)
            else:
                # Try to match by name in database
                selected_contact = next((c for c in db["contacts"] if c["name"].lower() in txt.lower()), None)
            
            if selected_contact:
                # Found in database - use structured data
                contact_full_text = f"CONTACT: {selected_contact['name']} | Contact Person: {selected_contact['contact_person']} ({selected_contact['designation']}, {selected_contact['department']}) | Email: {selected_contact['email']} | Phone: {selected_contact['phone']} | Address: {selected_contact['address']}"
                
                state.data["contacts"] = {
                    "name": selected_contact["name"],
                    "email": selected_contact["email"],
                    "phone": selected_contact["phone"],
                    "address": selected_contact["address"],
                    "contact_person": selected_contact["contact_person"],
                    "designation": selected_contact["designation"],
                    "department": selected_contact["department"],
                    "full_text": contact_full_text
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
            else:
                # Not found in database - accept manual text input
                # User typed their own contact info
                state.data["contacts"] = {
                    "name": "Custom Contact",
                    "email": "N/A",
                    "phone": "N/A",
                    "address": "N/A",
                    "contact_person": "N/A",
                    "designation": "N/A",
                    "department": "N/A",
                    "full_text": txt
                }
                
                state.stage = "budget"
                resp["message"] = f"✅ **Contact information captured:**\n{txt}\n\n**Step 7: Budget**\nFinally, provide the budget details for this project:"
                return state, resp
        
        if state.stage == "budget":
            state.data["budget"] = txt
            resp["message"] = "✅ **Budget captured!**\n\n🎉 **All information collected successfully!**\n\nReady to generate your professional SOW document?"
            resp["confirmation_buttons"] = [
                {"id":"sow_generate","label":"📄 Generate SOW Document","populate_input":"generate_sow","style":"primary"}
            ]
            return state, resp
        
        resp["message"] = "Please continue with the current step."
        return state, resp
    
    def finalize(self, state: SowState, session_id: str) -> Dict[str, Any]:
        """Generate final SOW document using new_sow application"""
        print(f"🎯 GENERATING SOW VIA NEW_SOW APPLICATION...")
        
        try:
            # Import the new_sow adapter
            from .new_sow_adapter import new_sow_adapter
            
            # Call new_sow application via adapter
            import asyncio
            
            # Check if we're already in an async context
            try:
                # Try to get the current event loop
                current_loop = asyncio.get_running_loop()
                # If we get here, we're in an async context - use asyncio.create_task
                # But since this is a sync function, we need to handle this differently
                raise RuntimeError("Cannot call async function from sync context with running loop")
            except RuntimeError as e:
                if "no running event loop" in str(e).lower():
                    # No loop running, safe to create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            new_sow_adapter.generate_sow_document(state.data, session_id)
                        )
                    finally:
                        loop.close()
                else:
                    # There's a running loop, we can't create a new one
                    raise RuntimeError("Cannot run async adapter in sync context with existing event loop")
            
            if result["success"]:
                print(f"✅ new_sow generation completed: {result['filename']}")
                
                return {
                    "message": f"✅ **SOW Generated Successfully!**\n\nYour professional Statement of Work document has been created using the new_sow application.\n\n📄 **Document Details:**\n- Project: {state.data.get('project_info', 'N/A')}\n- Total Value: {state.data.get('budget', 'N/A')}\n- Timeline: {state.data.get('timeline', 'N/A')}\n\n**Document is ready for download!**",
                    "download_url": result['download_url'],
                    "filename": result['filename']
                }
            else:
                raise Exception(f"new_sow generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ new_sow generation failed: {e}")
            # Fallback to direct generation if new_sow fails
            print("🔄 Falling back to direct document generation...")
            return self._fallback_generation(state, session_id)
    
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
            # Create full contact text for populate_input
            full_contact_text = f"CONTACT: {contact['name']} | Contact Person: {contact['contact_person']} ({contact['designation']}, {contact['department']}) | Email: {contact['email']} | Phone: {contact['phone']} | Address: {contact['address']}"
            
            options.append({
                "id": contact["id"],
                "label": f"{contact['name']} ({contact['type'].title()})",
                "value": full_contact_text,  # Full details in populate_input
                "contact_id": contact["id"],  # Keep ID for backend processing
                "details": {
                    "name": contact["name"],
                    "type": contact["type"],
                    "contact_person": contact["contact_person"],
                    "designation": contact["designation"],
                    "email": contact["email"],
                    "phone": contact["phone"],
                    "address": contact["address"],
                    "department": contact["department"]
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
    
    def _create_comprehensive_prompt(self, data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for Gemini AI processing"""
        resources_text = ""
        if data.get('resources'):
            resources_text = "\n".join([f"- {r['role']}: {r['count']} person(s)" for r in data['resources']])
        
        contacts_text = ""
        if data.get('contacts'):
            contacts = data['contacts']
            contacts_text = f"""
Client Contact:
- Organization: {contacts.get('name', 'N/A')}
- Contact Person: {contacts.get('contact_person', 'N/A')}
- Email: {contacts.get('email', 'N/A')}
- Phone: {contacts.get('phone', 'N/A')}
- Address: {contacts.get('address', 'N/A')}
"""
        
        return f"""
You are an expert business analyst creating a professional Statement of Work (SOW) document. 
Please analyze the following project information and create comprehensive, professional content for each section:

**PROJECT INFORMATION:**
{data.get('project_info', 'Not specified')}

**SERVICES TYPE:**
{data.get('services', 'Not specified')} package

**DELIVERABLES:**
{data.get('deliverables', 'Not specified')}

**TIMELINE:**
{data.get('timeline', 'Not specified')}

**TEAM RESOURCES:**
{resources_text or 'Not specified'}

**CLIENT INFORMATION:**
{contacts_text or 'Not specified'}

**BUDGET:**
{data.get('budget', 'Not specified')}

Please provide enhanced, professional descriptions for:
1. Executive Summary (2-3 sentences)
2. Project Scope and Objectives (detailed paragraph)
3. Detailed Services Description (professional explanation)
4. Deliverables with Acceptance Criteria (enhanced descriptions)
5. Timeline and Milestones (structured breakdown)
6. Resource Allocation (professional team description)
7. Budget Justification (value proposition)

Format your response as structured sections that can be used in a professional SOW document.
Use professional business language and ensure all content is client-ready.
"""
    
    def _prepare_enhanced_context(self, data: Dict[str, Any], enhanced_content: str) -> Dict[str, Any]:
        """Prepare enhanced context dictionary for template rendering"""
        from datetime import datetime
        
        # Parse enhanced content (simplified - in production you'd use more sophisticated parsing)
        context = {
            # Basic project information
            "document_number": f"SOW-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "project_name": data.get('project_info', 'Professional Services Project'),
            "current_date": datetime.now().strftime("%B %d, %Y"),
            
            # Enhanced content from Gemini
            "executive_summary": enhanced_content[:500] + "..." if len(enhanced_content) > 500 else enhanced_content,
            "project_scope": data.get('project_info', ''),
            "services_description": f"{data.get('services', 'standard').title()} Package Services",
            "deliverables_description": data.get('deliverables', ''),
            "timeline_description": data.get('timeline', ''),
            "budget_description": data.get('budget', ''),
            
            # Resources
            "resources": data.get('resources', []),
            "team_description": self._format_team_description(data.get('resources', [])),
            
            # Contacts
            "client_name": data.get('contacts', {}).get('name', 'Client Organization'),
            "client_contact_person": data.get('contacts', {}).get('contact_person', 'Contact Person'),
            "client_email": data.get('contacts', {}).get('email', 'client@example.com'),
            "client_phone": data.get('contacts', {}).get('phone', 'Phone Number'),
            "client_address": data.get('contacts', {}).get('address', 'Client Address'),
            
            # Contractor (default values)
            "contractor_name": "Professional Services Team",
            "contractor_contact_person": "Project Manager",
            "contractor_email": "pm@company.com",
            "contractor_phone": "+1 (555) 123-4567",
            "contractor_address": "123 Business Ave, Suite 100, City, State 12345",
            
            # Financial
            "total_fee": data.get('budget', 'To be determined'),
            "payment_terms": "Net 30 days",
            
            # Additional professional content
            "assumptions": [
                "Client will provide timely feedback and approvals",
                "All necessary resources and access will be provided",
                "Project scope remains as defined in this SOW"
            ],
            "terms": [
                "Changes to scope require written approval",
                "Payment terms are Net 30 days",
                "Intellectual property rights as per master agreement"
            ]
        }
        
        return context
    
    def _format_team_description(self, resources: list) -> str:
        """Format team resources into professional description"""
        if not resources:
            return "Professional team to be assigned based on project requirements."
        
        descriptions = []
        for resource in resources:
            role = resource.get('role', 'Team Member')
            count = resource.get('count', 1)
            if count == 1:
                descriptions.append(f"1 {role}")
            else:
                descriptions.append(f"{count} {role}s")
        
        return f"The project team will consist of: {', '.join(descriptions)}."
    

    
    def _fallback_generation(self, state: SowState, session_id: str) -> Dict[str, Any]:
        """Fallback to original generation method if use_sow fails"""
        print(f"🔄 Using direct document generation...")
        
        # Use original method as fallback
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
        
        # Return download URL pointing to generated_docs_sow folder
        return {
            "message": f"✅ **SOW Generated Successfully!**\n\n📄 Your Statement of Work is ready for download.",
            "download_url": f"/api/sow/download/{out_path.name}",
            "filename": out_path.name
        }