import os
import requests
from typing import Any

class GeminiClient:
    """Real Gemini integration using REST API."""
    
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_sow_text(self, prompt: str) -> str:
        """Generate comprehensive SOW content using Gemini AI - matches original use_sow behavior."""
        if not self.api_key:
            print("⚠️  No Gemini API key found - using fallback content")
            return self._generate_fallback_content(prompt)
        
        try:
            print(f"🤖 Calling Gemini API for SOW content generation...")
            url = f"{self.base_url}/{self.model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            # Enhanced prompt for professional SOW generation
            enhanced_prompt = f"""
You are an expert business analyst and technical writer specializing in Statement of Work (SOW) documents.

Based on the following project information, generate professional, comprehensive content for a Statement of Work:

{prompt}

Please provide detailed, professional content for each section:

**EXECUTIVE SUMMARY:**
Write a compelling 2-3 sentence executive summary that captures the project's value proposition and key outcomes.

**PROJECT SCOPE & OBJECTIVES:**
Provide a detailed paragraph explaining the project scope, key objectives, and expected business outcomes.

**SERVICES DESCRIPTION:**
Create a comprehensive description of the services to be provided, including methodologies and approaches.

**DELIVERABLES & ACCEPTANCE CRITERIA:**
Enhance the deliverables with professional descriptions and clear acceptance criteria.

**TIMELINE & MILESTONES:**
Structure the timeline into professional milestones with clear dependencies and deliverables.

**RESOURCE ALLOCATION:**
Provide professional descriptions of team roles and responsibilities.

**BUDGET JUSTIFICATION:**
Create a value-based justification for the proposed budget.

**ASSUMPTIONS & CONSTRAINTS:**
List key project assumptions and potential constraints.

**TERMS & CONDITIONS:**
Suggest standard professional terms and conditions.

Format the response as structured sections with professional business language suitable for client presentation.
Use clear headings and bullet points where appropriate.
Ensure all content is client-ready and reflects industry best practices.
"""
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": enhanced_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048
                }
            }
            
            import time
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            end_time = time.time()
            
            print(f"⏱️  Gemini API response time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"✅ Gemini generated {len(content)} characters of professional SOW content")
                    return content
                else:
                    print("❌ Gemini API returned no candidates")
                    return self._generate_fallback_content(prompt)
            else:
                print(f"❌ Gemini API Error: {response.status_code} - {response.text}")
                return self._generate_fallback_content(prompt)
                
        except Exception as e:
            print(f"❌ Gemini API Exception: {e}")
            return self._generate_fallback_content(prompt)
    
    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate fallback content when Gemini API is unavailable"""
        return f"""
**EXECUTIVE SUMMARY**
This Statement of Work outlines the professional services to be provided for the specified project, ensuring delivery of high-quality solutions within the agreed timeline and budget.

**PROJECT SCOPE & OBJECTIVES**
The project aims to deliver comprehensive solutions based on the requirements outlined in the initial consultation. Our team will work closely with the client to ensure all objectives are met with the highest standards of quality and professionalism.

**SERVICES DESCRIPTION**
Our professional services include comprehensive project planning, implementation, testing, and delivery. We follow industry best practices and proven methodologies to ensure successful project outcomes.

**DELIVERABLES & ACCEPTANCE CRITERIA**
All deliverables will be provided according to the agreed specifications and will undergo thorough quality assurance before client delivery. Acceptance criteria will be clearly defined for each deliverable.

**TIMELINE & MILESTONES**
The project will be executed in structured phases with clearly defined milestones and deliverables. Regular progress reviews will ensure timely completion and quality delivery.

**RESOURCE ALLOCATION**
A dedicated professional team will be assigned to this project, with appropriate skills and experience to ensure successful delivery.

**BUDGET JUSTIFICATION**
The proposed budget reflects the professional expertise, time investment, and resources required to deliver exceptional results that provide significant value to the client organization.

**Note: This is fallback content. For AI-enhanced professional content, please configure Gemini API key.**

Original Requirements:
{prompt[:1000]}
"""