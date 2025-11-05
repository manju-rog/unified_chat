import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from app.models.sow_models import (
    SessionData, ConversationStage, ProjectInfo, Service,
    Deliverable, Resource, Contact, Milestone, ProjectTimeline
)
from app.utils.prompts import PromptTemplates
from datetime import datetime
from app.config import settings
from app.services.contacts_service import ContactsService
from app.services.standard_services import STANDARD_SERVICES


logger = logging.getLogger(__name__)


class DataCollectorAgentV2:
    """Improved agent using single-pass extraction with function calling"""
    
    def __init__(self):
        self.prompts = PromptTemplates()
        self.contacts_service = ContactsService()
        
        # Configure Gemini with function calling
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Define SOW extraction function schema
        self.sow_function = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="extract_sow_data",
                    description="Extract complete Statement of Work data from conversation",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "document_number": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="SOW document number (e.g., SOW-2025-001)"
                            ),
                            "project_name": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="Name of the project"
                            ),
                            "objectives": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                items=genai.protos.Schema(type=genai.protos.Type.STRING),
                                description="List of project objectives"
                            ),
                            "services": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                items=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                        "description": genai.protos.Schema(type=genai.protos.Type.STRING),
                                        "duration": genai.protos.Schema(type=genai.protos.Type.STRING)
                                    }
                                ),
                                description="List of services to be provided"
                            ),
                            "deliverables": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                items=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        "name": genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description="Deliverable name"
                                        ),
                                        "description": genai.protos.Schema(
                                            type=genai.protos.Type.STRING,
                                            description="Detailed description of what will be delivered"
                                        ),
                                        "sprint_start": genai.protos.Schema(
                                            type=genai.protos.Type.INTEGER,
                                            description="Starting sprint number for this deliverable (e.g., 1)"
                                        ),
                                        "sprint_end": genai.protos.Schema(
                                            type=genai.protos.Type.INTEGER,
                                            description="Ending sprint number for this deliverable (e.g., 3)"
                                        ),
                                        "sprint_duration": genai.protos.Schema(
                                            type=genai.protos.Type.INTEGER,
                                            description="Total number of sprints needed (sprint_end - sprint_start + 1)"
                                        )
                                    },
                                    required=["name", "description"]
                                ),
                                description="List of project deliverables with sprint allocation"
                            ),
                            "start_date": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="Project start date in YYYY-MM-DD format"
                            ),
                            "end_date": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="Project end date in YYYY-MM-DD format"
                            ),
                            "total_sprints": genai.protos.Schema(
                                type=genai.protos.Type.INTEGER,
                                description="Total number of sprints"
                            ),
                            "sprint_duration": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="Duration of each sprint (e.g., '2 weeks')"
                            ),
                            "resources": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                items=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        "role": genai.protos.Schema(type=genai.protos.Type.STRING),
                                        "team": genai.protos.Schema(type=genai.protos.Type.STRING),
                                        "count": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                        "allocation": genai.protos.Schema(type=genai.protos.Type.STRING)
                                    }
                                ),
                                description="List of resource allocations"
                            ),
                            "contractor_contact": genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "company": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "address": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "phone": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "email": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "role": genai.protos.Schema(type=genai.protos.Type.STRING)
                                },
                                description="Contractor contact information"
                            ),
                            "client_contact": genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "company": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "address": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "phone": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "email": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "role": genai.protos.Schema(type=genai.protos.Type.STRING)
                                },
                                description="Client contact information"
                            ),
                            "milestones": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                items=genai.protos.Schema(
                                    type=genai.protos.Type.OBJECT,
                                    properties={
                                        "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                        "fee": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                                        "description": genai.protos.Schema(type=genai.protos.Type.STRING)
                                    }
                                ),
                                description="List of project milestones with fees"
                            ),
                            "estimated_expenses": genai.protos.Schema(
                                type=genai.protos.Type.NUMBER,
                                description="Estimated expenses amount"
                            )
                        },
                        required=["document_number", "project_name"]
                    )
                )
            ]
        )
        
        # Create model with function calling
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            tools=[self.sow_function]
        )
    
    async def process_user_input(
        self,
        session_data: SessionData,
        user_message: str
    ) -> tuple[str, SessionData]:
        """Process user input - store response and advance stage"""
        current_stage = session_data.current_stage
        
        # ========================================
        # SPECIAL HANDLING FOR SERVICES STAGE
        # ========================================
        if current_stage == ConversationStage.SERVICES:
            user_message_lower = user_message.strip().lower()
            
            # Check if user selected "standard" services
            if user_message_lower == "standard":
                logger.info("📦 User selected STANDARD services - auto-populating")
                
                # Auto-fill with standard services
                for standard_service in STANDARD_SERVICES:
                    service = Service(
                        name=standard_service["name"],
                        description=standard_service["description"],
                        duration=standard_service.get("duration", "See project timeline")
                    )
                    session_data.sow_context.services.append(service)
                
                logger.info(f"✅ Added {len(STANDARD_SERVICES)} standard services")
                
                # Store the response
                session_data.raw_responses[current_stage.value] = "Standard services package selected"
                
                # Move to next stage
                next_stage, response_message = self._determine_next_stage(current_stage)
                session_data.current_stage = next_stage
                
                # Custom response message
                response_message = f"""✅ **Standard services package has been applied!**

The following comprehensive service package has been added to your SOW:

📋 **Design and Development / Test / Post-Go-live support for Data Extraction, Compression, and Transfer Implementation**

This includes all design, development, testing, and go-live activities with 15 detailed scope items.

{response_message}"""
                
                logger.info(f"🔄 Advanced from SERVICES to {next_stage.value}")
                return response_message, session_data
            
            # Check if user wants custom services
            elif user_message_lower == "custom":
                logger.info("✏️ User selected CUSTOM services - waiting for input")
                
                # Store the choice but don't advance yet
                session_data.raw_responses[current_stage.value] = "Waiting for custom services input"
                
                # Ask for custom services details
                return """Great! Please provide your custom services.

For each service, specify:
- Service name
- Description of what will be done
- Duration or timeline (e.g., "3 weeks", "2 months")

You can list multiple services at once.""", session_data
            
            # If not "standard" or "custom", treat as custom service input
            else:
                logger.info("📝 Processing as custom service input")
                # Continue with normal flow (store and advance)
        
        # ========================================
        # NORMAL FLOW FOR ALL OTHER STAGES
        # ========================================
        
        # Store in session data
        session_data.raw_responses[current_stage.value] = user_message
        logger.info(f"📝 Stored response for stage: {current_stage.value}")
        
        # Advance to next stage
        next_stage, response_message = self._determine_next_stage(current_stage)
        session_data.current_stage = next_stage
        
        logger.info(f"🔄 Advanced from {current_stage.value} to {next_stage.value}")
        
        # If reached completed stage, extract all data
        if next_stage == ConversationStage.COMPLETED:
            logger.info("=" * 70)
            logger.info("🎯 REACHED COMPLETED STAGE - EXTRACTING ALL DATA")
            logger.info("=" * 70)
            logger.info(f"Total responses collected: {len(session_data.raw_responses)}")
            
            success = await self._extract_all_data_with_function_calling(session_data)
            
            if success:
                session_data.is_completed = True
                response_message = """Perfect! I've collected all the necessary information for your Statement of Work.

**Summary of Information Collected:**
✓ Project Information
✓ Services  
✓ Deliverables
✓ Timeline
✓ Resources
✓ Contact Information
✓ Budget & Milestones

Your SOW document is ready to be generated!"""
                logger.info("✅ Data extraction successful - session marked as completed")
                logger.info("=" * 70)
            else:
                session_data.is_completed = False
                response_message = "Data collected, but there were some extraction issues. Please check server logs."
                logger.error("❌ Data extraction failed - session NOT marked as completed")
                logger.info("=" * 70)
        
        return response_message, session_data
    
    async def _extract_all_data_with_function_calling(self, session_data: SessionData) -> bool:
        """Extract all data at once using Gemini function calling"""
        try:
            # ========================================
            # CHECK IF SERVICES WERE ALREADY POPULATED
            # ========================================
            services_already_populated = len(session_data.sow_context.services) > 0
            
            if services_already_populated:
                logger.info(f"ℹ️ Services already populated ({len(session_data.sow_context.services)} services), skipping extraction for services")
            
            conversation = self._build_complete_conversation(session_data.raw_responses)
            
            logger.info(f"Building conversation from {len(session_data.raw_responses)} responses")
            logger.info("Calling Gemini with function calling...")
            
            enhanced_prompt = f"""Extract complete SOW data from this conversation:

{conversation}

========================================
CRITICAL: DELIVERABLES SPRINT ALLOCATION WITH PARALLEL WORK
========================================

**PROJECT CONSTRAINT:**
- Total sprints from timeline: Extract this value first (e.g., 10, 16, 20 sprints)
- ALL deliverable sprint ranges MUST fit within 1 to [total_sprints]
- Maximum sprint_end value = total_sprints

**PARALLEL WORK CONCEPT:**
Multiple deliverables can be developed SIMULTANEOUSLY (overlapping sprints).
- Frontend and Backend can be built in parallel
- Multiple features can be developed at the same time
- Testing can overlap with late-stage development

**SPRINT ALLOCATION STRATEGY:**

Phase 1: PLANNING & REQUIREMENTS (Sprints 1-2)
- Documentation, requirements, compliance
- Example: "Requirements Doc" → sprints 1-2

Phase 2: DESIGN & ARCHITECTURE (Sprints 2-4)
- System design, database schema, API definitions
- Can OVERLAP with late requirements
- Example: "System Design" → sprints 2-3 (overlaps with requirements sprint 2)

Phase 3: DEVELOPMENT (Sprints 3-12)
- MULTIPLE deliverables developed IN PARALLEL
- Frontend, Backend, Mobile, Integrations happen simultaneously
- Example with OVERLAPPING:
  * "Web Application" → sprints 3-8 (6 sprints)
  * "Mobile App" → sprints 4-10 (7 sprints) ← OVERLAPS with Web (sprints 4-8)
  * "API Backend" → sprints 5-11 (7 sprints) ← OVERLAPS with both

Phase 4: TESTING & QA (Sprints 11-15)
- Can OVERLAP with late development
- Example: "Testing Documentation" → sprints 12-15 (while final dev happens)

Phase 5: DEPLOYMENT (Sprints 15-16)
- Final sprints, can overlap with testing
- Example: "Deployment Package" → sprints 15-16

========================================
CONCRETE EXAMPLE: 16 SPRINTS, 8 DELIVERABLES
========================================

Deliverable 1: HIPAA Compliance Documentation
→ sprint_start: 1, sprint_end: 2, sprint_duration: 2
(Early planning phase, no overlap)

Deliverable 2: Patient Portal Web Application  
→ sprint_start: 3, sprint_end: 8, sprint_duration: 6
(Main development)

Deliverable 3: Mobile Apps (iOS & Android)
→ sprint_start: 4, sprint_end: 10, sprint_duration: 7
**OVERLAPS with Portal (sprints 4-8) - parallel development**

Deliverable 4: EHR Integration Module
→ sprint_start: 7, sprint_end: 11, sprint_duration: 5
**OVERLAPS with Mobile (sprints 7-10) - parallel backend work**

Deliverable 5: Prescription Management System
→ sprint_start: 9, sprint_end: 13, sprint_duration: 5
**OVERLAPS with EHR (sprints 9-11) - parallel feature development**

Deliverable 6: Appointment Scheduling Engine
→ sprint_start: 11, sprint_end: 14, sprint_duration: 4
**OVERLAPS with Prescription (sprints 11-13) - another parallel feature**

Deliverable 7: Security Audit Report
→ sprint_start: 13, sprint_end: 15, sprint_duration: 3
**OVERLAPS with Scheduling (sprint 13-14) - testing while finishing dev**

Deliverable 8: Deployment and Training Package
→ sprint_start: 15, sprint_end: 16, sprint_duration: 2
**OVERLAPS with Security (sprint 15) - final activities**

**NOTICE:**
- Sum of durations: 2+6+7+5+5+4+3+2 = 34 sprints
- But project is only 16 sprints total
- This works because of PARALLELIZATION
- All sprint_end values ≤ 16 ✓

========================================
VALIDATION CHECKLIST
========================================
Before returning data, verify:
✓ Extracted total_sprints from timeline
✓ All sprint_start values ≥ 1
✓ All sprint_end values ≤ total_sprints
✓ sprint_duration = sprint_end - sprint_start + 1 (for each deliverable)
✓ Deliverables show logical progression (don't test before development)
✓ Multiple deliverables overlap in development phase
✓ Dependencies respected (design before development, testing after development starts)

========================================
COMMON MISTAKES TO AVOID
========================================
❌ Making deliverables sequential when they could be parallel
❌ Having sprint_end exceed total_sprints
❌ Not overlapping development deliverables
❌ Starting testing before any development begins
❌ Allocating as if only one deliverable can be worked on at a time

Use the extract_sow_data function to return all information in structured format."""

            
            response = self.model.generate_content(
                enhanced_prompt,
                tool_config={'function_calling_config': 'AUTO'}
            )
            
            if not response.candidates:
                logger.error("No candidates in Gemini response")
                return False
            
            function_call = response.candidates[0].content.parts[0].function_call
            
            if function_call.name != "extract_sow_data":
                logger.error(f"Unexpected function called: {function_call.name}")
                return False
            
            extracted_data = dict(function_call.args)
            
            logger.info(f"✅ Successfully extracted data via function calling")
            logger.info(f"Extracted keys: {list(extracted_data.keys())}")
            
            # ========================================
            # SKIP SERVICES IF ALREADY POPULATED
            # ========================================
            if services_already_populated:
                logger.info("⚠️ Removing 'services' from extracted data (already populated with standard services)")
                extracted_data.pop("services", None)
            
            # Populate session context
            self._populate_context_from_dict(session_data, extracted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in function calling extraction: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_complete_conversation(self, raw_responses: Dict[str, str]) -> str:
        """Build complete conversation from all raw responses"""
        conversation_parts = []
        
        for stage_name, response in raw_responses.items():
            question = self.prompts.STAGE_QUESTIONS.get(stage_name, "")
            conversation_parts.append(f"""
**Stage: {stage_name.upper()}**
Question: {question}
User Response: {response}
""")
        
        return "\n".join(conversation_parts)
    
    def _populate_context_from_dict(self, session_data: SessionData, data: Dict[str, Any]):
        """Populate SOW context from extracted dictionary"""
        try:
            # Project Info
            if "document_number" in data and "project_name" in data:
                session_data.sow_context.project_info = ProjectInfo(
                    document_number=data.get("document_number", ""),
                    project_name=data.get("project_name", ""),
                    objectives=list(data.get("objectives", []))
                )
                logger.info(f"✓ Project info: {data.get('project_name')}")

            # Services (only if not already populated from standard package)
            if "services" in data and len(session_data.sow_context.services) == 0:
                # Only populate if services list is empty
                services_data = data.get("services", [])
                for svc in services_data:
                    service = Service(
                        name=svc.get("name", ""),
                        description=svc.get("description", ""),
                        duration=svc.get("duration", "")
                    )
                    session_data.sow_context.services.append(service)
                logger.info(f"✓ {len(services_data)} services added from extraction")
            elif len(session_data.sow_context.services) > 0:
                logger.info(f"⚠️ Skipping services extraction - already have {len(session_data.sow_context.services)} standard services")

            
            # Deliverables
            deliverables_data = data.get("deliverables", [])
            
            for idx, deliv in enumerate(deliverables_data, 1):
                deliverable = Deliverable(
                    id=idx,
                    name=deliv.get("name", ""),
                    description=deliv.get("description", ""),
                    sprint_start=deliv.get("sprint_start"),
                    sprint_end=deliv.get("sprint_end"),
                    sprint_duration=deliv.get("sprint_duration")
                )
                session_data.sow_context.deliverables.append(deliverable)
            
            logger.info(f"✓ {len(deliverables_data)} deliverables added")
            
            # Timeline
            if "start_date" in data or "end_date" in data:
                start_date = None
                end_date = None
                
                if data.get("start_date"):
                    try:
                        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
                    except:
                        logger.warning(f"Could not parse start date: {data['start_date']}")
                
                if data.get("end_date"):
                    try:
                        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
                    except:
                        logger.warning(f"Could not parse end date: {data['end_date']}")
                
                session_data.sow_context.timeline = ProjectTimeline(
                    start_date=start_date,
                    end_date=end_date,
                    total_sprints=int(data.get("total_sprints", 0)),
                    sprint_duration=data.get("sprint_duration", "2 weeks")
                )
                logger.info(f"✓ Timeline: {start_date} to {end_date}")
            
            # Resources
            resources_data = data.get("resources", [])
            for res in resources_data:
                resource = Resource(
                    role=res.get("role", ""),
                    team=res.get("team", "General"),
                    count=int(res.get("count", 1)),
                    allocation=res.get("allocation", "Full-time")
                )
                session_data.sow_context.resources.append(resource)
            logger.info(f"✓ {len(resources_data)} resources added")
            
            # Contact Lookup Logic
            client_company = None
            contractor_company = None
            
            if "client_contact" in data:
                client_company = data["client_contact"].get("company", "")
            
            if "contractor_contact" in data:
                contractor_company = data["contractor_contact"].get("company", "")
            
            if not client_company:
                client_company = data.get("client_company", "")
            
            if not contractor_company:
                contractor_company = data.get("contractor_company", "")
            
            logger.info(f"🔍 Looking up contacts - Client: '{client_company}', Contractor: '{contractor_company}'")
            
            client_contact_data = self.contacts_service.get_client_contact(client_company) if client_company else None
            contractor_contact_data = self.contacts_service.get_contractor_contact(contractor_company) if contractor_company else None
            
            if contractor_contact_data:
                logger.info(f"✅ Found contractor in database: {contractor_contact_data['company']}")
                session_data.sow_context.contractor_contact = Contact(**contractor_contact_data)
            else:
                logger.info(f"⚠️ Contractor not in database, using extracted data")
                if "contractor_contact" in data:
                    cc = data["contractor_contact"]
                    session_data.sow_context.contractor_contact = Contact(
                        name=cc.get("name", ""),
                        company=cc.get("company", ""),
                        address=cc.get("address", ""),
                        phone=cc.get("phone", ""),
                        email=cc.get("email", ""),
                        role=cc.get("role", "")
                    )
                else:
                    session_data.sow_context.contractor_contact = Contact(
                        name=data.get("contractor_name", ""),
                        company=contractor_company or "",
                        address=data.get("contractor_address", ""),
                        phone=data.get("contractor_phone", ""),
                        email=data.get("contractor_email", ""),
                        role=data.get("contractor_role", "")
                    )
            
            logger.info(f"✓ Contractor: {session_data.sow_context.contractor_contact.name} ({session_data.sow_context.contractor_contact.company})")
            
            if client_contact_data:
                logger.info(f"✅ Found client in database: {client_contact_data['company']}")
                session_data.sow_context.client_contact = Contact(**client_contact_data)
            else:
                logger.info(f"⚠️ Client not in database, using extracted data")
                if "client_contact" in data:
                    cc = data["client_contact"]
                    session_data.sow_context.client_contact = Contact(
                        name=cc.get("name", ""),
                        company=cc.get("company", ""),
                        address=cc.get("address", ""),
                        phone=cc.get("phone", ""),
                        email=cc.get("email", ""),
                        role=cc.get("role", "")
                    )
                else:
                    session_data.sow_context.client_contact = Contact(
                        name=data.get("client_name", ""),
                        company=client_company or "",
                        address=data.get("client_address", ""),
                        phone=data.get("client_phone", ""),
                        email=data.get("client_email", ""),
                        role=data.get("client_role", "")
                    )
            
            logger.info(f"✓ Client: {session_data.sow_context.client_contact.name} ({session_data.sow_context.client_contact.company})")
            
            # Milestones
            milestones_data = data.get("milestones", [])
            for idx, mile in enumerate(milestones_data, 1):
                milestone = Milestone(
                    id=idx,
                    name=mile.get("name", ""),
                    fee=float(mile.get("fee", 0)),
                    description=mile.get("description", "")
                )
                session_data.sow_context.milestones.append(milestone)
            logger.info(f"✓ {len(milestones_data)} milestones added")
            
            # Expenses
            session_data.sow_context.estimated_expenses = float(data.get("estimated_expenses", 0))
            session_data.sow_context.calculate_total_fee()
            logger.info(f"✓ Total fee calculated: ${session_data.sow_context.total_fee}")
            
            logger.info("✅ ALL DATA POPULATED SUCCESSFULLY!")
            
        except Exception as e:
            logger.error(f"❌ Error populating context: {e}")
            import traceback
            traceback.print_exc()
    
    def _determine_next_stage(self, current_stage: ConversationStage) -> tuple[ConversationStage, str]:
        """Determine next conversation stage"""
        stage_flow = [
            ConversationStage.PROJECT_INFO,
            ConversationStage.SERVICES,
            ConversationStage.DELIVERABLES,
            ConversationStage.TIMELINE,
            ConversationStage.RESOURCES,
            ConversationStage.CONTACTS,
            ConversationStage.BUDGET,
            ConversationStage.COMPLETED
        ]
        
        try:
            current_index = stage_flow.index(current_stage)
            
            if current_stage == ConversationStage.BUDGET:
                logger.info("Budget stage complete - moving to COMPLETED")
                return ConversationStage.COMPLETED, ""
            
            if current_index + 1 < len(stage_flow):
                next_stage = stage_flow[current_index + 1]
                response = self.prompts.STAGE_QUESTIONS.get(next_stage.value, "")
                return next_stage, response
            else:
                return ConversationStage.COMPLETED, ""
                
        except (ValueError, IndexError):
            return ConversationStage.COMPLETED, ""
    
    def get_initial_message(self) -> str:
        """Get initial greeting message"""
        return self.prompts.STAGE_QUESTIONS["initial"]
    
    def get_stage_question(self, stage: ConversationStage) -> str:
        """Get question for specific stage"""
        return self.prompts.STAGE_QUESTIONS.get(stage.value, "")
