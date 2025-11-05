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
            "start_date": sow_context.timeline.start_date.strftime("%B %d, %Y") if sow_context.timeline else "",
            "end_date": sow_context.timeline.end_date.strftime("%B %d, %Y") if sow_context.timeline else "",
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
        """Generate SOW document from template and context"""
        try:
            # Load template
            doc = DocxTemplate(template_path)
            
            # Prepare context
            context = self.prepare_context(sow_context)
            
            # Render template with context
            doc.render(context)
            
            # Generate output filename if not provided
            if not output_filename:
                doc_id = generate_document_id()
                project_name = sow_context.project_info.project_name.replace(" ", "_") if sow_context.project_info else "SOW"
                output_filename = f"SOW_{project_name}_{doc_id}.docx"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save generated document
            doc.save(output_path)
            
            logger.info(f"Document generated successfully: {output_filename}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating document: {e}")
            raise

    def validate_template(self, template_path: str) -> bool:
        """Validate that file is a valid DOCX template"""
        try:
            doc = DocxTemplate(template_path)
            return True
        except Exception as e:
            logger.error(f"Invalid template file: {e}")
            return False
