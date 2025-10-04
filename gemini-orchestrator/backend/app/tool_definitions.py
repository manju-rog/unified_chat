"""
Tool definitions for Gemini function calling.
Converts Pydantic schemas to Gemini-compatible tool format.
"""

from typing import List
import google.generativeai as genai


def get_absence_tools() -> List:
    """
    Get Gemini tool definitions for Absence domain.
    
    Returns:
        List of Gemini Tool objects for absence operations
    
    Requirements: 6.1
    """
    absence_tool = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="mark_absent",
                description="Mark an employee as absent for a specific date with optional reason",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "employee_id": {
                            "type_": "STRING",
                            "description": "Employee identifier (lowercase first name, e.g., 'manju', 'john')"
                        },
                        "date": {
                            "type_": "STRING",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "reason": {
                            "type_": "STRING",
                            "description": "Optional reason for absence (e.g., 'sick', 'vacation', 'personal')"
                        }
                    },
                    "required": ["employee_id", "date"]
                }
            ),
            genai.protos.FunctionDeclaration(
                name="mark_present",
                description="Mark an employee as present for a specific date (removes absence record)",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "employee_id": {
                            "type_": "STRING",
                            "description": "Employee identifier (lowercase first name)"
                        },
                        "date": {
                            "type_": "STRING",
                            "description": "Date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["employee_id", "date"]
                }
            ),
            genai.protos.FunctionDeclaration(
                name="get_absence_status",
                description="Check if an employee is absent or present on a specific date",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "employee_id": {
                            "type_": "STRING",
                            "description": "Employee identifier (lowercase first name)"
                        },
                        "date": {
                            "type_": "STRING",
                            "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                        }
                    },
                    "required": ["employee_id"]
                }
            )
        ]
    )
    
    return [absence_tool]


def get_sow_tools() -> List:
    """
    Get Gemini tool definitions for SOW domain.
    
    Returns:
        List of Gemini Tool objects for SOW operations
    
    Requirements: 6.2
    """
    sow_tool = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="start_sow",
                description="Start a new SOW (Statement of Work) session with a project name",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "project_name": {
                            "type_": "STRING",
                            "description": "Name of the project for the SOW"
                        }
                    },
                    "required": ["project_name"]
                }
            ),
            genai.protos.FunctionDeclaration(
                name="update_sow",
                description="Update SOW session with collected information (contacts, services, deliverables, acceptance criteria)",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "sow_id": {
                            "type_": "STRING",
                            "description": "SOW session identifier"
                        },
                        "oracle_rep": {
                            "type_": "OBJECT",
                            "description": "Oracle representative contact information",
                            "properties": {
                                "name": {"type_": "STRING", "description": "Contact name"},
                                "email": {"type_": "STRING", "description": "Email address"},
                                "phone": {"type_": "STRING", "description": "Phone number"},
                                "address": {"type_": "STRING", "description": "Physical address"}
                            }
                        },
                        "billing_contact": {
                            "type_": "OBJECT",
                            "description": "Billing contact information",
                            "properties": {
                                "name": {"type_": "STRING", "description": "Contact name"},
                                "email": {"type_": "STRING", "description": "Email address"},
                                "phone": {"type_": "STRING", "description": "Phone number"},
                                "address": {"type_": "STRING", "description": "Physical address"}
                            }
                        },
                        "services": {
                            "type_": "ARRAY",
                            "description": "List of services to be provided",
                            "items": {
                                "type_": "OBJECT",
                                "properties": {
                                    "name": {"type_": "STRING", "description": "Service name"},
                                    "description": {"type_": "STRING", "description": "Service description"}
                                }
                            }
                        },
                        "deliverables": {
                            "type_": "ARRAY",
                            "description": "List of deliverables",
                            "items": {
                                "type_": "OBJECT",
                                "properties": {
                                    "name": {"type_": "STRING", "description": "Deliverable name"},
                                    "description": {"type_": "STRING", "description": "Deliverable description"}
                                }
                            }
                        },
                        "acceptance": {
                            "type_": "STRING",
                            "description": "Acceptance criteria for the SOW"
                        }
                    },
                    "required": ["sow_id"]
                }
            ),
            genai.protos.FunctionDeclaration(
                name="generate_sow",
                description="Generate final DOCX document from SOW session data",
                parameters={
                    "type_": "OBJECT",
                    "properties": {
                        "sow_id": {
                            "type_": "STRING",
                            "description": "SOW session identifier"
                        }
                    },
                    "required": ["sow_id"]
                }
            )
        ]
    )
    
    return [sow_tool]


def get_all_tools() -> List:
    """
    Get all tool definitions (Absence + SOW).
    
    Returns:
        List of all Gemini Tool objects
    """
    return get_absence_tools() + get_sow_tools()
