from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from docx import Document

try:
    from docxtpl import DocxTemplate
    HAS_DOXCTPL = True
except Exception:
    HAS_DOXCTPL = False

class DocumentService:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
    
    def _default_filename(self) -> str:
        return f"SOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    
    def generate(self,
                context: Dict[str, Any],
                session_id: str,
                template_path: Optional[Path] = None) -> Path:
        
        # Prefer a docxtpl template (mirrors your standalone behavior)
        if template_path and template_path.exists() and HAS_DOXCTPL:
            doc = DocxTemplate(str(template_path))
            doc.render(context)
            out = self.out_dir / session_id / self._default_filename()
            out.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(out))
            return out
        
        # Fallback: simple python-docx build
        doc = Document()
        doc.add_heading('Statement of Work', 0)
        
        doc.add_heading('1. Project Info', 1)
        doc.add_paragraph(context.get("project_info",""))
        
        doc.add_heading('2. Services', 1)
        doc.add_paragraph(context.get("services",""))
        
        doc.add_heading('3. Deliverables', 1)
        doc.add_paragraph(context.get("deliverables",""))
        
        doc.add_heading('4. Timeline', 1)
        doc.add_paragraph(context.get("timeline",""))
        
        doc.add_heading('5. Resources', 1)
        for r in context.get("resources", []):
            doc.add_paragraph(f"{r['role']}: {r['count']}")
        
        doc.add_heading('6. Contacts', 1)
        for k, v in (context.get("contacts") or {}).items():
            doc.add_paragraph(f"{k}: {v}")
        
        doc.add_heading('7. Budget', 1)
        doc.add_paragraph(context.get("budget",""))
        
        out = self.out_dir / session_id / self._default_filename()
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out))
        return out