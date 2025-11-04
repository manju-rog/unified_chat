# 📘 SOW GENERATION COMPLETE GUIDE - PART 2

## Continuation from Part 1...

---

## 🔗 INTEGRATION WITH NEW_SOW APPLICATION {#integration}

### new_sow Application Processing

When new_sow receives the request, here's what happens:

#### Step 1: API Endpoint Receives Request

**File: new_sow/app/api/direct_generation.py**

```python
@router.post("/generate-direct")
async def generate_direct(request: DirectGenerationRequest):
    """
    Direct generation endpoint - receives raw responses and generates SOW
    """
    logger.info("📥 Received direct generation request")
    logger.info(f"   Session: {request.session_id}")
    logger.info(f"   Template: {request.template_path}")
    
    # Extract project data
    project_data = request.project_data
    
    # Log received data
    logger.info(f"   Project: {project_data.get('project_info', 'N/A')[:50]}...")
    logger.info(f"   Services: {project_data.get('services', 'N/A')[:50]}...")
    
    # Call orchestrator to process with Gemini
    result = await orchestrator.process_and_generate(
        raw_responses=project_data,
        template_path=request.template_path,
        session_id=request.session_id
    )
    
    return result
```

**Explanation:**
- Receives POST request with project data
- Logs the request details
- Calls orchestrator to process with AI

---

#### Step 2: Orchestrator Processes with Gemini AI

**File: new_sow/app/agents/orchestrator.py**

```python
async def process_and_generate(self, raw_responses: Dict, template_path: str, session_id: str):
    """
    Process raw responses with Gemini AI and generate document
    """
    logger.info("🤖 Starting AI processing with Gemini...")
    
    # Step 1: Create comprehensive prompt for Gemini
    prompt = self._create_enhancement_prompt(raw_responses)
    
    # Step 2: Call Gemini API
    enhanced_content = await self.gemini_client.enhance_content(prompt)
    
    # Step 3: Parse Gemini response into structured data
    structured_data = self._parse_gemini_response(enhanced_content, raw_responses)
    
    # Step 4: Generate document
    filename = await self.document_generator.generate(
        template_path=template_path,
        data=structured_data,
        session_id=session_id
    )
    
    return {
        "success": True,
        "filename": filename,
        "message": "SOW generated successfully"
    }
```

**Explanation:**
1. Creates a detailed prompt for Gemini AI
2. Sends prompt to Gemini and gets enhanced content
3. Parses Gemini's response into structured format
4. Generates Word document using template

---

#### Step 3: Creating Gemini Prompt

```python
def _create_enhancement_prompt(self, raw_responses: Dict) -> str:
    """
    Create comprehensive prompt for Gemini to enhance SOW content
    """
    
    prompt = f"""
You are an expert business analyst creating a professional Statement of Work (SOW) document.

I will provide you with raw project information. Please analyze it and create comprehensive, 
professional content for each section of the SOW.

**RAW PROJECT INFORMATION:**

1. PROJECT INFORMATION:
{raw_responses.get('project_info', 'Not specified')}

2. SERVICES:
{raw_responses.get('services', 'Not specified')}

3. DELIVERABLES:
{raw_responses.get('deliverables', 'Not specified')}

4. TIMELINE:
{raw_responses.get('timeline', 'Not specified')}

5. TEAM RESOURCES:
{raw_responses.get('resources', 'Not specified')}

6. CLIENT CONTACT:
{raw_responses.get('contacts', 'Not specified')}

7. BUDGET:
{raw_responses.get('budget', 'Not specified')}

**INSTRUCTIONS:**

Please provide enhanced, professional content for the following sections:

1. **Executive Summary** (2-3 paragraphs)
   - Brief overview of the project
   - Key objectives
   - Expected outcomes

2. **Project Scope** (detailed description)
   - What is included in the project
   - What is NOT included (out of scope)
   - Success criteria

3. **Services Description** (professional explanation)
   - Detailed description of each service phase
   - Methodology and approach
   - Quality standards

4. **Deliverables** (with acceptance criteria)
   - Each deliverable with detailed description
   - Acceptance criteria for each
   - Format and delivery method

5. **Timeline and Milestones** (structured breakdown)
   - Project phases with dates
   - Key milestones
   - Dependencies

6. **Resource Allocation** (team description)
   - Role descriptions
   - Responsibilities
   - Reporting structure

7. **Budget Breakdown** (value proposition)
   - Cost breakdown by phase
   - Payment schedule
   - Value justification

8. **Assumptions and Constraints**
   - Project assumptions
   - Known constraints
   - Risk factors

9. **Terms and Conditions**
   - Change management process
   - Intellectual property rights
   - Confidentiality

Please format your response in a structured way with clear section headers.
Use professional business language suitable for a client-facing document.
"""
    
    return prompt
```

**Explanation:**
- Creates a detailed prompt with all collected information
- Asks Gemini to enhance each section professionally
- Specifies the format and tone required

---

#### Step 4: Gemini API Call

```python
async def enhance_content(self, prompt: str) -> str:
    """
    Call Gemini API to enhance content
    """
    logger.info("📤 Sending prompt to Gemini API...")
    
    # Configure Gemini model
    model = genai.GenerativeModel('gemini-pro')
    
    # Generate content
    response = await model.generate_content_async(prompt)
    
    # Extract text
    enhanced_text = response.text
    
    logger.info(f"✅ Received {len(enhanced_text)} characters from Gemini")
    
    return enhanced_text
```

**Example Gemini Response:**
```
**EXECUTIVE SUMMARY**

This Statement of Work outlines the development of a comprehensive mobile e-commerce 
application for MUFG Bank. The project encompasses the creation of native iOS and Android 
applications, an administrative web dashboard, and a robust REST API backend. The solution 
will feature secure payment gateway integration, user authentication, product catalog 
management, and shopping cart functionality.

The primary objective is to deliver a scalable, secure, and user-friendly e-commerce 
platform that meets modern banking standards and regulatory requirements. The project 
will be executed over a 6-month period with a dedicated team of experienced professionals.

Expected outcomes include increased customer engagement, streamlined transaction processing, 
and enhanced digital service offerings for MUFG Bank's clientele.

**PROJECT SCOPE**

In Scope:
- Development of native iOS application (Swift/SwiftUI)
- Development of native Android application (Kotlin/Jetpack Compose)
- Creation of administrative web dashboard (React.js)
- Implementation of REST API backend (Node.js/Express)
- Integration with secure payment gateways (Stripe, PayPal)
- User authentication and authorization system
- Product catalog management system
- Shopping cart and checkout functionality
- Order management and tracking
- Push notifications for order updates
- Comprehensive user documentation
- Deployment guides and DevOps setup

Out of Scope:
- Marketing and promotional content creation
- Third-party vendor negotiations
- Hardware procurement
- Post-launch marketing campaigns
- Integration with legacy banking systems (unless specified)

Success Criteria:
- All applications pass security audit
- Performance benchmarks met (< 2s page load time)
- 99.9% uptime during testing phase
- User acceptance testing completed successfully
- All deliverables approved by client stakeholders

**SERVICES DESCRIPTION**

Phase 1: Discovery & Planning (3 weeks)
During this phase, our team will conduct comprehensive requirements gathering sessions 
with key stakeholders. We will create detailed technical specifications, architecture 
diagrams, and project plans. This includes security assessment, technology stack 
finalization, and risk analysis.

Phase 2: Data Migration (4 weeks)
Our data specialists will design and implement secure data migration strategies, ensuring 
data integrity and compliance with banking regulations. This includes data mapping, 
transformation scripts, and validation procedures.

Phase 3: Application Development (8 weeks)
The core development phase where our engineering team builds all application components 
following agile methodologies. This includes sprint planning, daily standups, and 
bi-weekly demos to ensure alignment with client expectations.

Phase 4: Testing & QA (2 weeks)
Comprehensive testing including unit tests, integration tests, security testing, 
performance testing, and user acceptance testing. Our QA team will ensure all 
functionality meets specifications and industry standards.

Phase 5: Deployment & Go-Live (1 week)
Final deployment to production environments, including monitoring setup, performance 
optimization, and knowledge transfer to client's technical team.

... (continues with more sections)
```

---

#### Step 5: Parsing Gemini Response

```python
def _parse_gemini_response(self, enhanced_content: str, raw_responses: Dict) -> Dict:
    """
    Parse Gemini's enhanced content into structured data for template
    """
    
    # Extract sections using regex or string parsing
    sections = {}
    
    # Extract Executive Summary
    exec_summary_match = re.search(
        r'\*\*EXECUTIVE SUMMARY\*\*(.*?)\*\*PROJECT SCOPE\*\*',
        enhanced_content,
        re.DOTALL
    )
    if exec_summary_match:
        sections['executive_summary'] = exec_summary_match.group(1).strip()
    
    # Extract Project Scope
    scope_match = re.search(
        r'\*\*PROJECT SCOPE\*\*(.*?)\*\*SERVICES DESCRIPTION\*\*',
        enhanced_content,
        re.DOTALL
    )
    if scope_match:
        sections['project_scope'] = scope_match.group(1).strip()
    
    # ... parse other sections
    
    # Combine with original data
    structured_data = {
        # Document metadata
        "document_number": f"SOW-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "current_date": datetime.now().strftime("%B %d, %Y"),
        "project_name": raw_responses.get('project_info', 'Professional Services Project')[:100],
        
        # Enhanced content from Gemini
        "executive_summary": sections.get('executive_summary', ''),
        "project_scope": sections.get('project_scope', ''),
        "services_description": sections.get('services_description', ''),
        "deliverables_description": sections.get('deliverables_description', ''),
        "timeline_description": sections.get('timeline_description', ''),
        "resource_description": sections.get('resource_description', ''),
        "budget_description": sections.get('budget_description', ''),
        "assumptions": sections.get('assumptions', []),
        "terms": sections.get('terms', []),
        
        # Original data
        "client_name": self._extract_client_name(raw_responses.get('contacts', '')),
        "client_email": self._extract_client_email(raw_responses.get('contacts', '')),
        "client_phone": self._extract_client_phone(raw_responses.get('contacts', '')),
        "client_address": self._extract_client_address(raw_responses.get('contacts', '')),
        
        "total_fee": raw_responses.get('budget', 'To be determined'),
        
        # Parse resources into list
        "resources": self._parse_resources(raw_responses.get('resources', '')),
        
        # Parse deliverables into list
        "deliverables": self._parse_deliverables(raw_responses.get('deliverables', '')),
    }
    
    return structured_data
```

**Explanation:**
- Uses regex to extract sections from Gemini's response
- Combines enhanced content with original data
- Structures everything for template rendering

---

#### Step 6: Document Generation with Template

```python
async def generate(self, template_path: str, data: Dict, session_id: str) -> str:
    """
    Generate Word document using template and data
    """
    logger.info(f"📄 Generating document from template: {template_path}")
    
    # Load template
    doc = DocxTemplate(template_path)
    
    # Render template with data
    doc.render(data)
    
    # Generate filename
    project_name = data.get('project_name', 'SOW')[:50]
    safe_name = project_name.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"SOW_{safe_name}_{timestamp}.docx"
    
    # Save to output folder
    output_path = Path("output") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    
    logger.info(f"✅ Document generated: {filename}")
    
    return filename
```

**Template Variables Used:**
```
{{ document_number }}
{{ current_date }}
{{ project_name }}
{{ executive_summary }}
{{ project_scope }}
{{ services_description }}
{{ deliverables_description }}
{{ timeline_description }}
{{ resource_description }}
{{ budget_description }}
{{ client_name }}
{{ client_email }}
{{ client_phone }}
{{ client_address }}
{{ total_fee }}

{% for resource in resources %}
  {{ resource.role }}: {{ resource.count }} person(s)
{% endfor %}

{% for deliverable in deliverables %}
  {{ deliverable.name }}
  {{ deliverable.description }}
{% endfor %}

{% for assumption in assumptions %}
  • {{ assumption }}
{% endfor %}

{% for term in terms %}
  • {{ term }}
{% endfor %}
```

---

#### Step 7: Response Back to unified_ai_chat

**new_sow returns:**
```json
{
  "success": true,
  "filename": "SOW_Mobile_e-commerce_app_20241030_103045.docx",
  "message": "SOW generated successfully"
}
```

**new_sow_adapter processes:**
```python
# Copy file to generated_docs_sow folder
self._copy_to_generated_docs_sow_sync(
    "SOW_Mobile_e-commerce_app_20241030_103045.docx",
    "session_abc123"
)

# Return success response
return {
    "success": True,
    "filename": "SOW_Mobile_e-commerce_app_20241030_103045.docx",
    "download_url": "/api/sow/download/SOW_Mobile_e-commerce_app_20241030_103045.docx",
    "message": "SOW document generated successfully using new_sow application"
}
```

**sow_direct.py finalize() returns:**
```python
return {
    "message": "✅ **SOW Generated Successfully!**\n\nYour professional Statement of Work document has been created using the new_sow application.\n\n📄 **Document Details:**\n- Project: Mobile e-commerce app with payment gateway integration...\n- Total Value: $150,000 USD - Fixed price contract...\n- Timeline: 6 months project starting January 15, 2025...\n\n**Document is ready for download!**",
    "download_url": "/api/sow/download/SOW_Mobile_e-commerce_app_20241030_103045.docx",
    "filename": "SOW_Mobile_e-commerce_app_20241030_103045.docx"
}
```

**Frontend displays:**
```
Bot: ✅ **SOW Generated Successfully!**

Your professional Statement of Work document has been created using the new_sow application.

📄 **Document Details:**
- Project: Mobile e-commerce app with payment gateway integration...
- Total Value: $150,000 USD - Fixed price contract...
- Timeline: 6 months project starting January 15, 2025...

**Document is ready for download!**

[📥 Download SOW Document]
```

---

## 📄 DOCUMENT GENERATION PROCESS {#document-generation}

### Template Structure

The SOW template (`sample_sow_template.docx`) has the following structure:

```
┌─────────────────────────────────────────────────────────┐
│                  STATEMENT OF WORK                      │
│                                                         │
│  Document Number: {{ document_number }}                │
│  Date: {{ current_date }}                              │
└─────────────────────────────────────────────────────────┘

1. EXECUTIVE SUMMARY
   {{ executive_summary }}

2. PROJECT INFORMATION
   Project Name: {{ project_name }}
   {{ project_scope }}

3. SERVICES DESCRIPTION
   {{ services_description }}

4. DELIVERABLES
   {{ deliverables_description }}
   
   {% for deliverable in deliverables %}
   {{ loop.index }}. {{ deliverable.name }}
      Description: {{ deliverable.description }}
      Acceptance Criteria: {{ deliverable.acceptance_criteria }}
   {% endfor %}

5. TIMELINE AND MILESTONES
   {{ timeline_description }}
   
   Start Date: {{ start_date }}
   End Date: {{ end_date }}
   Total Duration: {{ total_duration }}

6. RESOURCE ALLOCATION
   {{ resource_description }}
   
   Team Composition:
   {% for resource in resources %}
   • {{ resource.role }}: {{ resource.count }} person(s)
   {% endfor %}

7. CLIENT INFORMATION
   Organization: {{ client_name }}
   Contact Person: {{ client_contact_person }}
   Email: {{ client_email }}
   Phone: {{ client_phone }}
   Address: {{ client_address }}

8. CONTRACTOR INFORMATION
   Organization: {{ contractor_name }}
   Contact Person: {{ contractor_contact_person }}
   Email: {{ contractor_email }}
   Phone: {{ contractor_phone }}
   Address: {{ contractor_address }}

9. BUDGET AND PAYMENT TERMS
   {{ budget_description }}
   
   Total Project Fee: {{ total_fee }}
   Payment Terms: {{ payment_terms }}
   
   Payment Schedule:
   {% for milestone in milestones %}
   • {{ milestone.name }}: {{ milestone.payment_percentage }}%
   {% endfor %}

10. ASSUMPTIONS
    {% for assumption in assumptions %}
    • {{ assumption }}
    {% endfor %}

11. TERMS AND CONDITIONS
    {% for term in terms %}
    • {{ term }}
    {% endfor %}

12. SIGNATURES
    
    Client Representative:
    Name: _______________________
    Signature: __________________
    Date: ______________________
    
    Contractor Representative:
    Name: _______________________
    Signature: __________________
    Date: ______________________
```

### Data Flow to Template

```
Collected Data (7 stages)
         ↓
new_sow_adapter converts to strings
         ↓
new_sow receives raw strings
         ↓
Gemini AI enhances content
         ↓
Orchestrator parses into structured data
         ↓
Template engine (docxtpl) renders
         ↓
Word document (.docx) generated
```

### Example Data Mapping

**Input Data:**
```python
{
  "project_info": "Mobile e-commerce app",
  "services": "SERVICES: Discovery & Planning (3 weeks)...",
  "deliverables": "iOS app, Android app, Admin panel",
  "timeline": "6 months starting January 2025",
  "resources": [
    {"role": "Developer", "count": 2},
    {"role": "Tester", "count": 1}
  ],
  "contacts": {
    "name": "MUFG Bank",
    "email": "john@mufg.com",
    ...
  },
  "budget": "$150,000 USD"
}
```

**After Gemini Enhancement:**
```python
{
  "document_number": "SOW-20241030-1030",
  "current_date": "October 30, 2024",
  "project_name": "Mobile e-commerce app",
  
  "executive_summary": "This Statement of Work outlines the development of a comprehensive mobile e-commerce application for MUFG Bank. The project encompasses the creation of native iOS and Android applications...",
  
  "project_scope": "In Scope:\n- Development of native iOS application (Swift/SwiftUI)\n- Development of native Android application (Kotlin/Jetpack Compose)...",
  
  "services_description": "Phase 1: Discovery & Planning (3 weeks)\nDuring this phase, our team will conduct comprehensive requirements gathering sessions...",
  
  "deliverables": [
    {
      "id": 1,
      "name": "iOS Mobile Application",
      "description": "Native iOS application built with Swift/SwiftUI featuring secure payment integration, user authentication, and product catalog",
      "acceptance_criteria": "App passes Apple App Store review, security audit completed, performance benchmarks met"
    },
    {
      "id": 2,
      "name": "Android Mobile Application",
      "description": "Native Android application built with Kotlin/Jetpack Compose with feature parity to iOS version",
      "acceptance_criteria": "App passes Google Play Store review, security audit completed, performance benchmarks met"
    },
    ...
  ],
  
  "timeline_description": "The project will be executed over a 6-month period starting January 15, 2025...",
  
  "resources": [
    {"role": "Developer", "count": 2, "description": "Senior full-stack developers with mobile expertise"},
    {"role": "Tester", "count": 1, "description": "QA engineer specializing in mobile testing"}
  ],
  
  "client_name": "MUFG Bank",
  "client_email": "john@mufg.com",
  "client_phone": "+1-555-0123",
  "client_address": "1251 Avenue of the Americas, New York, NY 10020",
  
  "total_fee": "$150,000 USD",
  "budget_description": "The total project fee of $150,000 USD represents a fixed-price contract with milestone-based payments...",
  
  "assumptions": [
    "Client will provide timely feedback and approvals within 3 business days",
    "All necessary API access and credentials will be provided at project kickoff",
    "Project scope remains as defined in this SOW; changes require formal change request"
  ],
  
  "terms": [
    "Changes to scope require written approval and may impact timeline and budget",
    "Payment terms are Net 30 days from invoice date",
    "Intellectual property rights transfer to client upon final payment",
    "Confidentiality agreement remains in effect for 5 years post-project"
  ]
}
```

**Template Renders To:**
```
┌─────────────────────────────────────────────────────────┐
│                  STATEMENT OF WORK                      │
│                                                         │
│  Document Number: SOW-20241030-1030                    │
│  Date: October 30, 2024                                │
└─────────────────────────────────────────────────────────┘

1. EXECUTIVE SUMMARY

This Statement of Work outlines the development of a comprehensive 
mobile e-commerce application for MUFG Bank. The project encompasses 
the creation of native iOS and Android applications, an administrative 
web dashboard, and a robust REST API backend...

2. PROJECT INFORMATION

Project Name: Mobile e-commerce app

In Scope:
- Development of native iOS application (Swift/SwiftUI)
- Development of native Android application (Kotlin/Jetpack Compose)
- Creation of administrative web dashboard (React.js)
...

3. SERVICES DESCRIPTION

Phase 1: Discovery & Planning (3 weeks)
During this phase, our team will conduct comprehensive requirements 
gathering sessions with key stakeholders...

... (continues with all sections)
```

---

