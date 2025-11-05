from app.services.document_service import DocumentService
from app.models.sow_models import (
    SOWContext, ProjectInfo, Service, Deliverable,
    Resource, Contact, Milestone, ProjectTimeline
)
from datetime import date

# Create document service
doc_service = DocumentService()

# Create complete SOW context with real data
sow_context = SOWContext()

# Project Info
sow_context.project_info = ProjectInfo(
    document_number="SOW-2025-001",
    project_name="Cloud Migration Project",
    objectives=[
        "Reduce infrastructure costs",
        "Improve scalability",
        "Enhance security"
    ]
)

# Services
sow_context.services = [
    Service(name="Migration planning", description="Planning and assessment", duration="2 weeks"),
    Service(name="Data migration", description="Migrate data to cloud", duration="4 weeks"),
    Service(name="Testing and validation", description="Verify migration success", duration="2 weeks")
]

# Deliverables
sow_context.deliverables = [
    Deliverable(id=1, name="Migration plan", description="Detailed migration roadmap"),
    Deliverable(id=2, name="Migrated data", description="Data migrated with validation reports"),
    Deliverable(id=3, name="Test results", description="Performance benchmarks")
]

# Timeline
sow_context.timeline = ProjectTimeline(
    start_date=date(2025, 11, 1),
    end_date=date(2026, 1, 31),
    total_sprints=6,
    sprint_duration="2 weeks"
)

# Resources
sow_context.resources = [
    Resource(role="Senior Cloud Engineer", team="Development", count=2, allocation="Full-time"),
    Resource(role="Data Migration Specialist", team="Migration", count=1, allocation="Full-time"),
    Resource(role="QA Engineer", team="Testing", count=1, allocation="Part-time")
]

# Contacts
sow_context.contractor_contact = Contact(
    name="John Smith",
    company="TechCorp Solutions",
    address="123 Tech Street, New York, NY",
    phone="+1-555-0100",
    email="john@techcorp.com",
    role="Project Manager"
)

sow_context.client_contact = Contact(
    name="Jane Doe",
    company="ClientCo Inc",
    address="456 Business Ave, Boston, MA",
    phone="+1-555-0200",
    email="jane@clientco.com",
    role="IT Director"
)

# Milestones
sow_context.milestones = [
    Milestone(id=1, name="Planning", fee=15000.0),
    Milestone(id=2, name="Data migration", fee=40000.0),
    Milestone(id=3, name="Testing", fee=10000.0)
]

sow_context.estimated_expenses = 5000.0
sow_context.calculate_total_fee()

# Generate document
print("Generating SOW document...")
output_path = doc_service.generate_document(
    template_path="templates/doc_20251008142656_9c82ed_template.docx",  # Use your latest template
    sow_context=sow_context,
    output_filename="SOW_Cloud_Migration_DIRECT_TEST.docx"
)

print(f"✅ Document generated successfully!")
print(f"📄 Location: {output_path}")
print(f"\nOpen the document to verify it works!")
