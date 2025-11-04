"""
SOW Session Management Service
Handles SOW data collection, session state, and integration with use_sow generation system.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
import json
import os
from pathlib import Path

class SOWStage(str, Enum):
    """SOW Collection Stages"""
    CONFIRMATION = "confirmation"  # Ask if user wants to start SOW
    PROJECT_INFO = "project_info"  # Step 1: Project details
    SERVICES = "services"          # Step 2: Services (Standard/Custom)
    DELIVERABLES = "deliverables"  # Step 3: Deliverables
    TIMELINE = "timeline"          # Step 4: Timeline
    RESOURCES = "resources"        # Step 5: Resources (+ buttons)
    CONTACTS = "contacts"          # Step 6: Contacts (dropdown)
    BUDGET = "budget"             # Step 7: Budget
    GENERATE = "generate"         # Step 8: Generate document
    COMPLETED = "completed"       # Done

class SOWSessionManager:
    """Manages SOW collection sessions with proper state management"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.contacts_data = self._load_contacts_data()
    
    def _load_contacts_data(self) -> Dict[str, Any]:
        """Load contacts data from JSON file"""
        try:
            contacts_path = Path("use_sow/contacts_data.json")
            if contacts_path.exists():
                with open(contacts_path, 'r') as f:
                    return json.load(f)
            return {"contractors": [], "clients": []}
        except Exception:
            return {"contractors": [], "clients": []}
    
    def is_sow_session_active(self, session_id: str) -> bool:
        """Check if SOW session is active for this session"""
        return session_id in self.sessions
    
    def start_sow_session(self, session_id: str) -> Dict[str, Any]:
        """Start a new SOW collection session"""
        self.sessions[session_id] = {
            "stage": SOWStage.PROJECT_INFO,
            "data": {
                "project_info": {},
                "services": [],
                "deliverables": [],
                "timeline": {},
                "resources": [],
                "contacts": {"contractor": {}, "client": {}},
                "budget": {"milestones": [], "total_fee": 0, "expenses": 0}
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "stage": SOWStage.PROJECT_INFO,
            "message": "🔴 **SOW Generation Mode Activated**\n\nLet's create your Statement of Work step by step.\n\n**Step 1: Project Information**\n\nPlease provide:\n• Document number (optional)\n• Project name\n• Project objectives",
            "theme": "sow",
            "show_exit": True,
            "progress": 1,
            "total_steps": 8
        }
    
    def exit_sow_session(self, session_id: str) -> Dict[str, Any]:
        """Exit SOW session and return to normal mode"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        return {
            "message": "✅ Exited SOW generation mode. Back to normal chat.",
            "theme": "normal",
            "show_exit": False
        }
    
    def process_sow_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for current SOW stage"""
        if session_id not in self.sessions:
            return {"error": "No active SOW session"}
        
        session = self.sessions[session_id]
        current_stage = session["stage"]
        
        # Update timestamp
        session["updated_at"] = datetime.now().isoformat()
        
        if current_stage == SOWStage.PROJECT_INFO:
            return self._handle_project_info(session_id, user_input)
        elif current_stage == SOWStage.SERVICES:
            return self._handle_services(session_id, user_input)
        elif current_stage == SOWStage.DELIVERABLES:
            return self._handle_deliverables(session_id, user_input)
        elif current_stage == SOWStage.TIMELINE:
            return self._handle_timeline(session_id, user_input)
        elif current_stage == SOWStage.RESOURCES:
            return self._handle_resources(session_id, user_input)
        elif current_stage == SOWStage.CONTACTS:
            return self._handle_contacts(session_id, user_input)
        elif current_stage == SOWStage.BUDGET:
            return self._handle_budget(session_id, user_input)
        elif current_stage == SOWStage.GENERATE:
            return self._handle_generate(session_id, user_input)
        
        return {"error": "Unknown stage"}
    
    def _handle_project_info(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle project information collection"""
        session = self.sessions[session_id]
        
        # Parse project info from user input
        lines = user_input.strip().split('\n')
        project_info = {}
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith(('doc', 'document')):
                project_info['document_number'] = line.split(':', 1)[-1].strip()
            elif line.lower().startswith(('project', 'name')):
                project_info['project_name'] = line.split(':', 1)[-1].strip()
            elif line.lower().startswith(('objective', 'goal')):
                project_info['objectives'] = [line.split(':', 1)[-1].strip()]
        
        # If no structured input, treat as project name
        if not project_info and user_input.strip():
            project_info['project_name'] = user_input.strip()
            project_info['objectives'] = ['To be defined']
        
        session["data"]["project_info"] = project_info
        session["stage"] = SOWStage.SERVICES
        
        return {
            "stage": SOWStage.SERVICES,
            "message": "✅ Project information saved!\n\n**Step 2: Services**\n\nWhat services will be provided? Choose from:\n\n🔹 **Standard Services** (click to add):\n• Web Development\n• Mobile App Development\n• API Development\n• Database Design\n• UI/UX Design\n\n🔹 **Custom Service**: Describe your custom service",
            "theme": "sow",
            "show_exit": True,
            "progress": 2,
            "total_steps": 8,
            "buttons": [
                {"id": "web_dev", "label": "Web Development", "value": "Web Development"},
                {"id": "mobile_dev", "label": "Mobile App Development", "value": "Mobile App Development"},
                {"id": "api_dev", "label": "API Development", "value": "API Development"},
                {"id": "db_design", "label": "Database Design", "value": "Database Design"},
                {"id": "ui_ux", "label": "UI/UX Design", "value": "UI/UX Design"}
            ]
        }
    
    def _handle_services(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle services collection"""
        session = self.sessions[session_id]
        
        # Add service to list
        service = {
            "name": user_input.strip(),
            "description": "To be defined",
            "duration": "TBD"
        }
        
        session["data"]["services"].append(service)
        
        # Check if user wants to add more services
        services_list = "\n".join([f"• {s['name']}" for s in session["data"]["services"]])
        
        return {
            "stage": SOWStage.SERVICES,
            "message": f"✅ Added service: **{user_input.strip()}**\n\n**Current Services:**\n{services_list}\n\n➕ Add another service or type **'next'** to continue to deliverables.",
            "theme": "sow",
            "show_exit": True,
            "progress": 2,
            "total_steps": 8,
            "buttons": [
                {"id": "next_deliverables", "label": "Continue to Deliverables", "value": "next"}
            ]
        }
    
    def _handle_deliverables(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle deliverables collection"""
        session = self.sessions[session_id]
        
        if user_input.lower().strip() == 'next':
            session["stage"] = SOWStage.TIMELINE
            return {
                "stage": SOWStage.TIMELINE,
                "message": "**Step 4: Timeline**\n\nPlease provide:\n• Project start date (YYYY-MM-DD)\n• Project end date (YYYY-MM-DD)\n• Total number of sprints\n• Sprint duration (e.g., '2 weeks')",
                "theme": "sow",
                "show_exit": True,
                "progress": 4,
                "total_steps": 8
            }
        
        # Add deliverable
        deliverable = {
            "id": len(session["data"]["deliverables"]) + 1,
            "name": user_input.strip(),
            "description": user_input.strip(),
            "sprint_start": None,
            "sprint_end": None
        }
        
        session["data"]["deliverables"].append(deliverable)
        session["stage"] = SOWStage.DELIVERABLES
        
        deliverables_list = "\n".join([f"{d['id']}. {d['name']}" for d in session["data"]["deliverables"]])
        
        return {
            "stage": SOWStage.DELIVERABLES,
            "message": f"✅ Added deliverable: **{user_input.strip()}**\n\n**Current Deliverables:**\n{deliverables_list}\n\n➕ Add another deliverable or type **'next'** to continue to timeline.",
            "theme": "sow",
            "show_exit": True,
            "progress": 3,
            "total_steps": 8,
            "buttons": [
                {"id": "next_timeline", "label": "Continue to Timeline", "value": "next"}
            ]
        }
    
    def _handle_timeline(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle timeline collection"""
        session = self.sessions[session_id]
        
        # Parse timeline info
        lines = user_input.strip().split('\n')
        timeline = {}
        
        for line in lines:
            line = line.strip()
            if 'start' in line.lower():
                try:
                    date_str = line.split(':', 1)[-1].strip()
                    timeline['start_date'] = date_str
                except:
                    pass
            elif 'end' in line.lower():
                try:
                    date_str = line.split(':', 1)[-1].strip()
                    timeline['end_date'] = date_str
                except:
                    pass
            elif 'sprint' in line.lower() and ('total' in line.lower() or 'number' in line.lower()):
                try:
                    timeline['total_sprints'] = int(''.join(filter(str.isdigit, line)))
                except:
                    pass
            elif 'duration' in line.lower():
                timeline['sprint_duration'] = line.split(':', 1)[-1].strip()
        
        session["data"]["timeline"] = timeline
        session["stage"] = SOWStage.RESOURCES
        
        return {
            "stage": SOWStage.RESOURCES,
            "message": "✅ Timeline saved!\n\n**Step 5: Resources**\n\nAdd team members and their roles:\n\n🔹 **Quick Add** (click to add):\n• Project Manager\n• Senior Developer\n• Junior Developer\n• UI/UX Designer\n• QA Engineer\n\n🔹 **Custom Role**: Describe custom role and allocation",
            "theme": "sow",
            "show_exit": True,
            "progress": 5,
            "total_steps": 8,
            "buttons": [
                {"id": "pm", "label": "+ Project Manager", "value": "Project Manager"},
                {"id": "sr_dev", "label": "+ Senior Developer", "value": "Senior Developer"},
                {"id": "jr_dev", "label": "+ Junior Developer", "value": "Junior Developer"},
                {"id": "designer", "label": "+ UI/UX Designer", "value": "UI/UX Designer"},
                {"id": "qa", "label": "+ QA Engineer", "value": "QA Engineer"}
            ]
        }
    
    def _handle_resources(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle resources collection"""
        session = self.sessions[session_id]
        
        if user_input.lower().strip() == 'next':
            session["stage"] = SOWStage.CONTACTS
            
            # Prepare contacts dropdown
            contractors = self.contacts_data.get("contractors", [])
            clients = self.contacts_data.get("clients", [])
            
            return {
                "stage": SOWStage.CONTACTS,
                "message": "**Step 6: Contacts**\n\nSelect contractor and client contacts:",
                "theme": "sow",
                "show_exit": True,
                "progress": 6,
                "total_steps": 8,
                "dropdowns": {
                    "contractor": contractors,
                    "client": clients
                }
            }
        
        # Add resource
        resource = {
            "role": user_input.strip(),
            "team": "Development",
            "count": 1,
            "allocation": "TBD"
        }
        
        session["data"]["resources"].append(resource)
        
        resources_list = "\n".join([f"• {r['role']}" for r in session["data"]["resources"]])
        
        return {
            "stage": SOWStage.RESOURCES,
            "message": f"✅ Added resource: **{user_input.strip()}**\n\n**Current Resources:**\n{resources_list}\n\n➕ Add another resource or type **'next'** to continue to contacts.",
            "theme": "sow",
            "show_exit": True,
            "progress": 5,
            "total_steps": 8,
            "buttons": [
                {"id": "next_contacts", "label": "Continue to Contacts", "value": "next"}
            ]
        }
    
    def _handle_contacts(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle contacts selection"""
        session = self.sessions[session_id]
        
        # Parse contact selection (simplified)
        session["data"]["contacts"] = {
            "contractor": {"name": "Default Contractor", "company": "Tech Solutions Inc."},
            "client": {"name": "Default Client", "company": "Client Corp"}
        }
        
        session["stage"] = SOWStage.BUDGET
        
        return {
            "stage": SOWStage.BUDGET,
            "message": "✅ Contacts saved!\n\n**Step 7: Budget**\n\nDefine project milestones and fees:\n\nExample format:\n• Milestone 1: Planning & Design - $5000\n• Milestone 2: Development Phase 1 - $10000\n• Milestone 3: Testing & Deployment - $3000\n\nOr provide total project fee.",
            "theme": "sow",
            "show_exit": True,
            "progress": 7,
            "total_steps": 8
        }
    
    def _handle_budget(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle budget collection"""
        session = self.sessions[session_id]
        
        # Parse budget info (simplified)
        milestones = []
        total_fee = 0
        
        lines = user_input.strip().split('\n')
        for i, line in enumerate(lines, 1):
            if '$' in line:
                try:
                    # Extract fee amount
                    fee_str = line.split('$')[-1].replace(',', '').strip()
                    fee = float(''.join(filter(lambda x: x.isdigit() or x == '.', fee_str)))
                    
                    milestone = {
                        "id": i,
                        "name": line.split('$')[0].strip().replace('•', '').replace('-', '').strip(),
                        "fee": fee,
                        "description": ""
                    }
                    milestones.append(milestone)
                    total_fee += fee
                except:
                    pass
        
        # If no milestones parsed, create default
        if not milestones:
            try:
                total_fee = float(''.join(filter(lambda x: x.isdigit() or x == '.', user_input.replace(',', ''))))
                milestones = [{
                    "id": 1,
                    "name": "Project Completion",
                    "fee": total_fee,
                    "description": "Full project delivery"
                }]
            except:
                total_fee = 10000
                milestones = [{
                    "id": 1,
                    "name": "Project Completion",
                    "fee": 10000,
                    "description": "Full project delivery"
                }]
        
        session["data"]["budget"] = {
            "milestones": milestones,
            "total_fee": total_fee,
            "expenses": 0
        }
        
        session["stage"] = SOWStage.GENERATE
        
        return {
            "stage": SOWStage.GENERATE,
            "message": f"✅ Budget saved! Total: **${total_fee:,.2f}**\n\n**Step 8: Generate Document**\n\n🎉 All information collected! Ready to generate your SOW document.\n\n📋 **Summary:**\n• Project: {session['data']['project_info'].get('project_name', 'Unnamed Project')}\n• Services: {len(session['data']['services'])} services\n• Deliverables: {len(session['data']['deliverables'])} items\n• Resources: {len(session['data']['resources'])} roles\n• Total Fee: ${total_fee:,.2f}",
            "theme": "sow",
            "show_exit": True,
            "progress": 8,
            "total_steps": 8,
            "buttons": [
                {"id": "generate_sow", "label": "🚀 Generate SOW Document", "value": "generate", "style": "primary"}
            ]
        }
    
    def _handle_generate(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Handle document generation"""
        if user_input.lower().strip() == 'generate':
            # This will trigger the actual document generation
            return {
                "stage": SOWStage.GENERATE,
                "action": "generate_document",
                "session_data": self.sessions[session_id]["data"]
            }
        
        return {
            "message": "Click 'Generate SOW Document' to create your document.",
            "theme": "sow"
        }
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for document generation"""
        return self.sessions.get(session_id)

# Global instance
sow_session_manager = SOWSessionManager()