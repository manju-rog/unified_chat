from docxtpl import DocxTemplate
from docx import Document
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.config import settings
from app.models.sow_models import SOWContext
from app.utils.helpers import sanitize_filename, generate_document_id

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for handling DOCX template operations"""
    
    def __init__(self):
        self.template_dir = settings.TEMPLATE_DIR
        self.output_dir = settings.OUTPUT_DIR
    
    def save_template(self, file_content: bytes, filename: str) -> tuple[str, str]:
        """Save uploaded template file"""
        try:
            # Sanitize filename
            safe_filename = sanitize_filename(filename)
            template_id = generate_document_id()
            template_filename = f"{template_id}_{safe_filename}"
            template_path = os.path.join(self.template_dir, template_filename)
            
            # Save file
            with open(template_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Template saved: {template_filename}")
            return template_id, template_path
            
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            raise
    
    def analyze_template(self, template_path: str) -> List[str]:
        """Analyze template and extract placeholders"""
        try:
            doc = DocxTemplate(template_path)
            
            # Get template variables (placeholders)
            # This is a simplified version - docxtpl uses Jinja2
            # In practice, you'd parse the actual Jinja2 syntax
            placeholders = []
            
            # Read document XML to find placeholders
            from docx import Document as DocxDocument
            docx_doc = DocxDocument(template_path)
            
            for paragraph in docx_doc.paragraphs:
                text = paragraph.text
                if '{{' in text and '}}' in text:
                    # Extract placeholders
                    import re
                    found = re.findall(r'\{\{(.*?)\}\}', text)
                    placeholders.extend([p.strip() for p in found])
            
            for table in docx_doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text = cell.text
                        if '{{' in text and '}}' in text:
                            import re
                            found = re.findall(r'\{\{(.*?)\}\}', text)
                            placeholders.extend([p.strip() for p in found])
            
            # Remove duplicates and Jinja2 control structures
            placeholders = list(set([
                p.split('|')[0].split('.')[0].strip() 
                for p in placeholders 
                if not p.startswith(('for', 'if', 'endif', 'endfor'))
            ]))
            
            logger.info(f"Found {len(placeholders)} placeholders in template")
            return placeholders
            
        except Exception as e:
            logger.error(f"Error analyzing template: {e}")
            return []
    
    def prepare_context(self, sow_context: SOWContext) -> Dict[str, Any]:
        """Prepare context dictionary for template rendering"""
        # Add auto-incrementing IDs to deliverables if not present
        deliverables_for_template = []
        for deliv in sow_context.deliverables:
            deliverable_dict = {
                'id': deliv.id,
                'name': deliv.name,
                'description': deliv.get_full_description(),  # ← Use enhanced description
                'sprint_start': deliv.sprint_start,
                'sprint_end': deliv.sprint_end,
                'sprint_duration': deliv.sprint_duration
            }
            deliverables_for_template.append(deliverable_dict)
        
        # Add auto-incrementing IDs to milestones if not present
        for idx, milestone in enumerate(sow_context.milestones, 1):
            if not milestone.id:
                milestone.id = idx
        
        # Calculate total fee
        sow_context.calculate_total_fee()
        
        # Prepare context dictionary
        context = {
            # Project Info
            "document_number": sow_context.project_info.document_number if sow_context.project_info else "",
            "project_name": sow_context.project_info.project_name if sow_context.project_info else "",
            "objectives": sow_context.project_info.objectives if sow_context.project_info else [],
            
            # Services - as list of dicts for Jinja2 iteration
            "services": [
                            {
                                'name': service.name,
                                'description': service.description,  # ← Preserve raw string
                                'duration': service.duration
                            } 
                            for service in sow_context.services
                        ],
            
            # Deliverables - as list of dicts
            'deliverables': deliverables_for_template,
            
            # Timeline
            "start_date": sow_context.timeline.start_date.strftime("%B %d, %Y") if sow_context.timeline and sow_context.timeline.start_date else "TBD",
            "end_date": sow_context.timeline.end_date.strftime("%B %d, %Y") if sow_context.timeline and sow_context.timeline.end_date else "TBD",
            "total_sprints": sow_context.timeline.total_sprints if sow_context.timeline else 0,
            "sprint_duration": sow_context.timeline.sprint_duration if sow_context.timeline else "2 weeks",
            
            # Resources
            "resources": [r.model_dump() for r in sow_context.resources],
            
            # Contractor Contact
            "contractor_name": sow_context.contractor_contact.name if sow_context.contractor_contact else "",
            "contractor_company": sow_context.contractor_contact.company if sow_context.contractor_contact else "",
            "contractor_address": sow_context.contractor_contact.address if sow_context.contractor_contact else "",
            "contractor_phone": sow_context.contractor_contact.phone if sow_context.contractor_contact else "",
            "contractor_email": sow_context.contractor_contact.email if sow_context.contractor_contact else "",
            "contractor_role": sow_context.contractor_contact.role if sow_context.contractor_contact else "",
            
            # Client Contact
            "client_name": sow_context.client_contact.name if sow_context.client_contact else "",
            "client_company": sow_context.client_contact.company if sow_context.client_contact else "",
            "client_address": sow_context.client_contact.address if sow_context.client_contact else "",
            "client_phone": sow_context.client_contact.phone if sow_context.client_contact else "",
            "client_email": sow_context.client_contact.email if sow_context.client_contact else "",
            "client_role": sow_context.client_contact.role if sow_context.client_contact else "",
            
            # Milestones and Budget
            "milestones": [m.model_dump() for m in sow_context.milestones],
            "total_fee": f"${sow_context.total_fee:,.2f}",
            "estimated_expenses": f"${sow_context.estimated_expenses:,.2f}",
            
            # Additional
            "assumptions": sow_context.assumptions,
            "terms": sow_context.terms,
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
        
        return context
    
    def generate_document(
        self,
        template_path: str,
        sow_context: SOWContext,
        output_filename: Optional[str] = None
    ) -> str:
        """Generate SOW document from template and context with AI enhancement"""
        try:
            # Enforce Gemini API key requirement
            from app.config import settings
            if not settings.GEMINI_API_KEY:
                raise RuntimeError("Gemini API key missing; cannot generate enhanced SOW content")
            
            logger.info("🤖 Starting AI-enhanced SOW document generation")
            
            # Enhance SOW content with Gemini AI
            enhanced_context = self._enhance_with_gemini(sow_context)
            
            # Load template
            doc = DocxTemplate(template_path)
            
            # Render template with enhanced context
            doc.render(enhanced_context)
            
            # Generate output filename if not provided
            if not output_filename:
                doc_id = generate_document_id()
                project_name = sow_context.project_info.project_name.replace(" ", "_") if sow_context.project_info else "SOW"
                output_filename = f"SOW_{project_name}_{doc_id}.docx"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save generated document
            doc.save(output_path)
            
            logger.info(f"✅ AI-enhanced document generated successfully: {output_filename}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error generating document: {e}")
            raise
    
    def _enhance_with_gemini(self, sow_context: SOWContext) -> Dict[str, Any]:
        """Enhance SOW content using Gemini AI"""
        try:
            from app.services.gemini_service import GeminiService
            import asyncio
            
            logger.info("🧠 Enhancing SOW content with Gemini AI...")
            
            # Create Gemini service
            gemini = GeminiService()
            
            # Prepare base context
            base_context = self.prepare_context(sow_context)
            
            # Create enhancement prompt
            enhancement_prompt = self._create_enhancement_prompt(sow_context)
            
            # Get AI enhancement (run in sync context)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                chat = loop.run_until_complete(gemini.create_chat_session())
                enhanced_content = loop.run_until_complete(
                    gemini.send_message(chat, enhancement_prompt)
                )
            finally:
                loop.close()
            
            # Parse and integrate enhanced content
            enhanced_context = self._integrate_enhanced_content(base_context, enhanced_content)
            
            logger.info("✅ SOW content enhanced with AI")
            return enhanced_context
            
        except Exception as e:
            logger.warning(f"⚠️ AI enhancement failed, using basic content: {e}")
            # Fallback to basic context if AI enhancement fails
            return self.prepare_context(sow_context)
    
    def _create_enhancement_prompt(self, sow_context: SOWContext) -> str:
        """Create prompt for Gemini to enhance SOW content"""
        project_name = sow_context.project_info.project_name if sow_context.project_info else "Project"
        services = [s.name for s in sow_context.services]
        deliverables = [d.name for d in sow_context.deliverables]
        
        return f"""
You are an expert business analyst creating professional Statement of Work content. 
Please enhance the following project information with professional, detailed descriptions:

PROJECT: {project_name}
SERVICES: {', '.join(services)}
DELIVERABLES: {', '.join(deliverables)}

Please provide enhanced content in this JSON format:
{{
    "executive_summary": "2-3 sentence professional summary",
    "project_scope": "Detailed project scope paragraph",
    "enhanced_services": [
        {{"name": "Service Name", "description": "Professional description", "value_proposition": "Why this service matters"}}
    ],
    "enhanced_deliverables": [
        {{"name": "Deliverable Name", "description": "Detailed description with acceptance criteria"}}
    ],
    "risk_mitigation": "Key risks and mitigation strategies",
    "success_metrics": "How success will be measured"
}}

Make all content professional, client-ready, and specific to this project type.
"""
    
    def _integrate_enhanced_content(self, base_context: Dict[str, Any], enhanced_content: str) -> Dict[str, Any]:
        """Integrate AI-enhanced content into the base context"""
        try:
            import json
            
            # Try to parse JSON response
            enhanced_data = json.loads(enhanced_content.strip())
            
            # Integrate enhanced content
            base_context.update({
                "executive_summary": enhanced_data.get("executive_summary", "Professional services engagement"),
                "project_scope": enhanced_data.get("project_scope", base_context.get("project_name", "")),
                "risk_mitigation": enhanced_data.get("risk_mitigation", "Standard project risk management practices apply"),
                "success_metrics": enhanced_data.get("success_metrics", "Project completion within timeline and budget"),
                "ai_enhanced": True
            })
            
            # Enhance services if provided
            if "enhanced_services" in enhanced_data:
                for i, service in enumerate(base_context.get("services", [])):
                    if i < len(enhanced_data["enhanced_services"]):
                        enhanced_service = enhanced_data["enhanced_services"][i]
                        service["description"] = enhanced_service.get("description", service["description"])
                        service["value_proposition"] = enhanced_service.get("value_proposition", "")
            
            # Enhance deliverables if provided
            if "enhanced_deliverables" in enhanced_data:
                for i, deliverable in enumerate(base_context.get("deliverables", [])):
                    if i < len(enhanced_data["enhanced_deliverables"]):
                        enhanced_deliv = enhanced_data["enhanced_deliverables"][i]
                        deliverable["description"] = enhanced_deliv.get("description", deliverable["description"])
            
            return base_context
            
        except Exception as e:
            logger.warning(f"Failed to parse enhanced content, using base: {e}")
            return base_context

    def validate_template(self, template_path: str) -> bool:
        """Validate that file is a valid DOCX template"""
        try:
            doc = DocxTemplate(template_path)
            return True
        except Exception as e:
            logger.error(f"Invalid template file: {e}")
            return False
