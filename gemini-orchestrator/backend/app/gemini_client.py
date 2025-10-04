"""
Gemini client module for AI integration.
Handles initialization and configuration of Google Generative AI client.
"""

import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiClient:
    """
    Wrapper for Google Gemini API client.
    Requirements: 7.3
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client with API key and model configuration.
        
        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model to use (default: gemini-2.0-flash-exp)
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize model with temperature 0.3 for deterministic responses
        self.model_name = model_name
        self.generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
    
    def get_model(self):
        """Get the configured Gemini model instance."""
        return self.model


# Global client instance
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get or create the global Gemini client instance.
    
    Returns:
        GeminiClient: Configured Gemini client
    """
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
