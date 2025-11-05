import google.generativeai as genai
from typing import List, Dict, Optional, Any
import json
import logging
from ...config import get_settings
from ..utils.helpers import parse_json_response
from ..utils.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Gemini API"""

    def __init__(self):
        """Initialize Gemini service with API key"""
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=PromptTemplates.SYSTEM_INSTRUCTION
        )
        self.prompts = PromptTemplates()
    
    async def create_chat_session(self, history: List[Dict[str, str]] = None):
        """Create a new chat session with optional history"""
        # Convert history to Gemini format
        gemini_history = []
        if history:
            for msg in history:
                gemini_history.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })
        
        return self.model.start_chat(history=gemini_history)
    
    async def send_message(
        self, 
        chat_session, 
        message: str,
        expect_json: bool = False
    ) -> str:
        """Send message to Gemini and get response"""
        try:
            response = chat_session.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Error sending message to Gemini: {e}")
            raise
    
    async def extract_structured_data(
        self,
        user_message: str,
        stage: str
    ) -> Optional[Dict[str, Any]]:
        """Extract structured data from user message using Gemini"""
        try:
            # Create prompt for data extraction
            prompt = self.prompts.DATA_EXTRACTION_PROMPT.format(
                stage=stage,
                user_message=user_message,
                expected_structure=self.prompts.get_extraction_structure(stage)
            )
            
            # Create temporary chat for extraction
            chat = self.model.start_chat()
            response = chat.send_message(prompt)
            
            # Parse JSON response
            extracted_data = parse_json_response(response.text)
            
            if extracted_data:
                logger.info(f"Successfully extracted data for stage: {stage}")
                return extracted_data
            else:
                logger.warning(f"Failed to extract valid JSON for stage: {stage}")
                return None
                
        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            return None
    
    async def validate_data(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """Validate extracted data using Gemini"""
        try:
            prompt = self.prompts.VALIDATION_PROMPT.format(
                data=json.dumps(data, indent=2),
                required_fields=", ".join(required_fields)
            )
            
            chat = self.model.start_chat()
            response = chat.send_message(prompt)
            
            validation_result = parse_json_response(response.text)
            return validation_result or {
                "is_valid": False,
                "missing_fields": required_fields,
                "errors": ["Validation failed"],
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"Error in data validation: {e}")
            return {
                "is_valid": False,
                "missing_fields": [],
                "errors": [str(e)],
                "suggestions": []
            }
    
    async def generate_clarification(
        self,
        original_question: str,
        user_response: str,
        missing_info: str
    ) -> str:
        """Generate clarifying question when response is incomplete"""
        try:
            prompt = self.prompts.CLARIFICATION_PROMPT.format(
                original_question=original_question,
                user_response=user_response,
                missing_info=missing_info
            )
            
            chat = self.model.start_chat()
            response = chat.send_message(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating clarification: {e}")
            return f"Could you please provide more details about: {missing_info}?"
