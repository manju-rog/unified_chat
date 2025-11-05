from typing import Dict, Any

class PromptTemplates:
    """Centralized prompt templates for Gemini API"""
    
    SYSTEM_INSTRUCTION = """You are an expert business analyst assistant specializing in Statement of Work (SOW) document creation. 
Your role is to:
1. Ask clear, professional questions to gather SOW information
2. Extract structured data from conversational user responses
3. Maintain a professional, business-appropriate tone
4. Handle ambiguous responses by asking clarifying questions
5. Validate data completeness and correctness


Always be concise, specific, and guide the user through the SOW creation process systematically."""

    STAGE_QUESTIONS: Dict[str, str] = {
        "initial": """Hello! I'll help you create a comprehensive Statement of Work document. 
First, please upload your SOW template document (.docx format). If you've already uploaded it, let me know and we'll proceed.""",
        
        "project_info": """Great! Let's start with the project basics. Please provide:
1. Document Number (e.g., SOW-2025-001)
2. Project Name
3. Key project objectives (list as many as needed)


You can provide all at once or one at a time.""",
        
        "services":  """Excellent! Now, tell me about the services that will be provided under this SOW.

You have two options:
- Type **'standard'** to auto-fill with the standard service package (recommended for most data projects)
- Or type **'custom'** to provide your own detailed services (as before).

If you select standard, all design, development, testing, go-live and post-go-live activities for Data Extraction, Compression, and Transfer Implementation will be included automatically.

For custom, please specify for each service:
- Service name
- Description of what will be done
- Duration or timeline (e.g., "3 weeks", "2 months")
""",
        
        "deliverables": """Perfect! Now let's define the specific deliverables.
For each deliverable, provide:
- Deliverable name
- Detailed description of what will be delivered


I'll automatically assign IDs to each deliverable. Please list all deliverables.""",
        
        "timeline": """Great work! Now for the project timeline:
1. Project start date (format: YYYY-MM-DD or MM/DD/YYYY)
2. Project end date
3. Number of sprints planned
4. Sprint duration (if different from standard 2 weeks)""",
        
        "resources": """Now let's document the resources allocated to this project.
For each resource type, specify:
- Role (e.g., "Senior Developer", "QA Engineer")
- Team (e.g., "Development", "Testing", "DevOps")
- Number of people
- Allocation (e.g., "Full-time", "50%", "Part-time")


List all resource allocations.""",
        
        "contacts": """Excellent! Now I need contact information for both parties.


**Quick Option:** If you're working with a registered client or contractor, simply provide their company name (e.g., 'WareMax Distribution' or 'LogiTech Solutions'), and I'll automatically fill in all their contact details.


**Manual Option:** Otherwise, provide complete contact information:


**Contractor Representative:**
- Name
- Company name
- Complete address
- Phone number
- Email
- Role/Title


**Client Representative:**
- Name
- Company name
- Complete address
- Phone number
- Email
- Role/Title


You can use registered companies for faster input, or provide full details for new contacts.""",
        
        "budget": """Finally, let's document the financial details.
For each milestone/deliverable, provide:
- Milestone name (can match deliverable names)
- Fee amount (in USD or specify currency)
- Any additional details about payment terms


Also mention:
- Any estimated expenses
- Payment schedule if applicable"""
    }
    
    DATA_EXTRACTION_PROMPT = """Extract structured information from the user's response.


**Stage:** {stage}
**User Response:** "{user_message}"


**Instructions:**
- Extract ONLY what the user provided
- If a field is missing, use null
- For dates: Always use YYYY-MM-DD format
- For numbers: Extract as integers or floats (no $ symbols)
- For lists: Always return as arrays, never null
- Return ONLY valid JSON, no explanations


**Expected Format:**
{expected_structure}


**Extraction Rules:**
1. Be precise - extract exactly what was said
2. If user provides multiple items, create array entries
3. Maintain data types as specified
4. Never invent information


**JSON Output (no extra text):**"""


    VALIDATION_PROMPT = """Validate the extracted data for completeness and correctness.


**Data to validate:**
{data}


**Required fields:**
{required_fields}


**Validation checks:**
1. All required fields are present
2. Data types are correct (dates, numbers, strings)
3. Email addresses are valid
4. Phone numbers follow a reasonable format
5. Dates are logical (end date after start date)
6. Numbers are positive where applicable


Return JSON with:
{{
    "is_valid": true/false,
    "missing_fields": ["field1", "field2"],
    "errors": ["error description 1", "error description 2"],
    "suggestions": ["suggestion 1", "suggestion 2"]
}}"""


    CLARIFICATION_PROMPT = """The user's response is incomplete or unclear. Generate a helpful clarifying question.


**Original Question:** {original_question}
**User Response:** {user_response}
**Missing Information:** {missing_info}


Generate a polite, specific follow-up question to gather the missing information. Be conversational and helpful."""


    @staticmethod
    def get_extraction_structure(stage: str) -> str:
        """Return expected JSON structure for each stage"""
        structures = {
            "project_info": """{
  "document_number": "string or null",
  "project_name": "string or null",
  "objectives": ["objective1", "objective2"]
}""",
            "services": """{
  "services": [
    {
      "name": "Service name",
      "description": "What will be done",
      "duration": "Time period"
    }
  ]
}""",
            "deliverables": """{
  "deliverables": [
    {
      "name": "Deliverable name",
      "description": "What will be delivered"
    }
  ]
}""",
            "timeline": """{
  "start_date": "2025-11-01",
  "end_date": "2026-01-31",
  "total_sprints": 6,
  "sprint_duration": "2 weeks"
}""",
            "resources": """{
  "resources": [
    {
      "role": "Job title",
      "team": "Team name",
      "count": number,
      "allocation": "Full-time or Part-time"
    }
  ]
}""",
            "contacts": """{
  "contractor_contact": {
    "name": "Full name",
    "company": "Company name",
    "address": "Complete address",
    "phone": "Phone number",
    "email": "Email address",
    "role": "Job title"
  },
  "client_contact": {
    "name": "Full name",
    "company": "Company name",
    "address": "Complete address",
    "phone": "Phone number",
    "email": "Email address",
    "role": "Job title"
  }
}""",
            "budget": """{
  "milestones": [
    {
      "name": "Milestone name",
      "fee": 15000.00,
      "description": "Optional description"
    }
  ],
  "estimated_expenses": 5000.00
}"""
        }
        return structures.get(stage, "{}")
