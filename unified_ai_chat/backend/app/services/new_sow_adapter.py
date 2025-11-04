"""
Adapter to integrate unified_ai_chat with new_sow document generation
Converts unified_chat collected data to new_sow format and calls new_sow API
"""

import logging
import aiohttp
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class NewSowAdapter:
    """Adapter to convert unified_chat data to new_sow format and generate documents"""
    
    def __init__(self, new_sow_base_url: str = "http://localhost:8002"):
        self.base_url = new_sow_base_url
        self.api_url = f"{self.base_url}/api"
        # Use the sample template from project root
        # Path: unified_ai_chat/backend/app/services/new_sow_adapter.py
        # Go up 4 levels: services -> app -> backend -> unified_ai_chat -> project root
        project_root = Path(__file__).resolve().parents[4]
        self.template_path = str(project_root / "sample_sow_template.docx")
        
    async def generate_sow_document(self, unified_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Generate SOW document using new_sow application
        
        Args:
            unified_data: Data collected from unified_chat (7 stages)
            session_id: Session identifier
            
        Returns:
            Dict with success status, filename, and download info
        """
        try:
            logger.info(f"🎯 Converting unified_chat data to new_sow format for session {session_id}")
            
            # Check if new_sow is running
            if not await self._check_new_sow_health():
                raise Exception("new_sow application is not running on port 8002")
            
            # Convert unified_chat data to new_sow raw_responses format
            # new_sow will handle ALL processing including Gemini enhancement
            raw_responses = self._convert_to_raw_responses(unified_data)
            
            # Call new_sow direct generation API
            result = await self._call_new_sow_generation(raw_responses, session_id)
            
            if result["success"]:
                logger.info(f"✅ SOW document generated successfully via new_sow: {result['filename']}")
                
                # Copy file to generated_docs_sow folder (synchronously)
                self._copy_to_generated_docs_sow_sync(result['filename'], session_id)
                
                return {
                    "success": True,
                    "filename": result["filename"],
                    "download_url": f"/api/sow/download/{result['filename']}",
                    "message": "SOW document generated successfully using new_sow application"
                }
            else:
                raise Exception(f"new_sow generation failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"❌ new_sow generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"SOW generation failed: {str(e)}"
            }
    
    async def _check_new_sow_health(self) -> bool:
        """Check if new_sow application is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ new_sow application is running and healthy")
                        return True
                    else:
                        logger.error(f"❌ new_sow health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ new_sow health check error: {e}")
            return False
    
    async def _call_new_sow_generation(self, raw_responses: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Call new_sow direct generation API - let new_sow handle ALL processing including Gemini"""
        try:
            logger.info(f"📤 Calling new_sow direct generation API...")
            logger.info(f"   new_sow will process data with Gemini using its own prompts")
            
            # Prepare request payload for new_sow API
            # Pass raw_responses so new_sow can process with Gemini
            payload = {
                "template_path": self.template_path,
                "project_data": raw_responses,  # Raw string responses
                "session_id": session_id
            }
            
            # Call new_sow direct generation endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/generate-direct",
                    json=payload,
                    timeout=60  # Allow time for Gemini processing
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ new_sow generation successful: {result.get('filename')}")
                        logger.info(f"   Document processed with new_sow's Gemini prompts")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ new_sow API error ({response.status}): {error_text}")
                        return {
                            "success": False,
                            "error": f"new_sow API returned {response.status}: {error_text}"
                        }
                
        except Exception as e:
            logger.error(f"❌ new_sow API call error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    

    
    def _copy_to_generated_docs_sow_sync(self, filename: str, session_id: str):
        """Copy generated document from new_sow/output to generated_docs_sow"""
        try:
            import shutil
            project_root = Path(__file__).resolve().parents[4]
            
            # Source: new_sow/output/
            source = project_root / "new_sow" / "output" / filename
            
            # Destination: generated_docs_sow/
            dest_dir = project_root / "generated_docs_sow"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
            
            if source.exists():
                shutil.copy2(source, dest)
                logger.info(f"✅ Copied document to generated_docs_sow: {filename}")
                logger.info(f"   Source: {source}")
                logger.info(f"   Destination: {dest}")
            else:
                logger.warning(f"⚠️ Source file not found: {source}")
        except Exception as e:
            logger.error(f"❌ Error copying document: {e}")
    
    def _convert_to_raw_responses(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert unified_chat data to new_sow raw_responses format
        new_sow will process this data with Gemini and extract structured information
        
        Unified Chat Format -> new_sow raw_responses format (strings)
        """
        
        # Format project info
        project_info_str = unified_data.get("project_info", "")
        
        # Format services
        services_str = unified_data.get("services", "")
        
        # Format deliverables
        deliverables_str = unified_data.get("deliverables", "")
        
        # Format timeline
        timeline_str = unified_data.get("timeline", "")
        
        # Format resources - handle both structured list and manual text
        resources_list = unified_data.get("resources", [])
        resources_text = unified_data.get("resources_text", "")
        
        if resources_text:
            # User typed manual text
            resources_str = resources_text
        elif resources_list:
            # User used resource builder
            resources_str = ", ".join([f"{r.get('role', 'Team Member')}: {r.get('count', 1)} person(s)" for r in resources_list])
        else:
            resources_str = ""
        
        # Format contacts
        contacts_dict = unified_data.get("contacts", {})
        contacts_str = f"Client: {contacts_dict.get('name', 'N/A')}, Contact: {contacts_dict.get('contact_person', 'N/A')}, Email: {contacts_dict.get('email', 'N/A')}, Phone: {contacts_dict.get('phone', 'N/A')}, Address: {contacts_dict.get('address', 'N/A')}"
        
        # Format budget
        budget_str = unified_data.get("budget", "")
        
        raw_responses = {
            "project_info": project_info_str,
            "services": services_str,
            "deliverables": deliverables_str,
            "timeline": timeline_str,
            "resources": resources_str,
            "contacts": contacts_str,
            "budget": budget_str
        }
        
        logger.info(f"✅ Converted unified_chat data to new_sow raw_responses format")
        logger.info(f"   Project: {project_info_str[:50]}...")
        logger.info(f"   Services: {services_str[:50]}...")
        
        return raw_responses


# Create global adapter instance
new_sow_adapter = NewSowAdapter()
