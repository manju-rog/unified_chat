"""
SOW Service Adapter - Integration with standalone use_sow application
Similar to absence_adapter.py but for SOW generation
"""

import asyncio
import json
import logging
import aiohttp
import websockets
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UseSowAdapter:
    """Adapter to integrate with the standalone use_sow application"""
    
    def __init__(self, use_sow_base_url: str = "http://localhost:8002"):
        self.base_url = use_sow_base_url
        self.api_url = f"{self.base_url}/api"
        self.template_path = "sample_sow_template.docx"  # Use the template from project root
        
    async def generate_sow_document(self, sow_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Generate SOW document using the standalone use_sow application
        Direct API approach - no conversation simulation needed
        
        Args:
            sow_data: Collected SOW data from unified chat
            session_id: Session identifier
            
        Returns:
            Dict with success status, filename, and download info
        """
        try:
            logger.info(f"🎯 Starting direct SOW generation via use_sow API for session {session_id}")
            
            # Check if use_sow is running
            if not await self._check_use_sow_health():
                raise Exception("use_sow application is not running on port 8002")
            
            # Convert unified chat data to use_sow format
            use_sow_payload = self._convert_unified_data_to_use_sow_format(sow_data)
            use_sow_payload["session_id"] = session_id  # <<< CRUCIAL
            
            # Call use_sow direct generation API
            result = await self._call_direct_generation_api(use_sow_payload, session_id)
            
            if result["success"]:
                logger.info(f"✅ SOW document generated successfully: {result['filename']}")
                return {
                    "success": True,
                    "filename": result["filename"],
                    "download_url": f"/api/sow/documents/{session_id}/{result['filename']}",
                    "message": "SOW document generated successfully using use_sow application"
                }
            else:
                raise Exception(f"use_sow generation failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"❌ SOW generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"SOW generation failed: {str(e)}"
            }
    
    async def _check_use_sow_health(self) -> bool:
        """Check if use_sow application is running and healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ use_sow application is running and healthy")
                        return True
                    else:
                        logger.error(f"❌ use_sow health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ use_sow health check error: {e}")
            return False
    
    async def _call_direct_generation_api(self, payload: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Call use_sow direct generation API with collected data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Call the direct generation endpoint and WAIT for HTTP 200
                async with session.post(
                    f"{self.api_url}/generate-direct", 
                    json=payload,
                    timeout=180  # Allow up to 3 minutes for Gemini processing
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Direct generation failed: {response.status} - {error_text}")
                        return {"success": False, "error": f"API call failed: {response.status} - {error_text}"}
                    
                    data = await response.json()
                    
                    # Trust server session_id + url
                    job_sess = data.get("session_id", session_id)
                    dl_url = data.get("download_url") or f"/api/download/{job_sess}"
                    
                    # Poll download until the file exists (defensive)
                    full_dl_url = f"{self.base_url}{dl_url}"
                    ready = await self._wait_until_ready(full_dl_url, timeout=120)
                    if not ready:
                        return {"success": False, "error": "Document not ready after timeout"}
                    
                    return {
                        "success": True,
                        "session_id": job_sess,
                        "filename": data.get("filename"),
                        "download_url": dl_url
                    }
                        
        except Exception as e:
            logger.error(f"❌ Direct generation API error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _wait_until_ready(self, url: str, timeout: int = 120, interval: float = 1.5) -> bool:
        """Poll download URL until file is ready"""
        import asyncio
        
        logger.info(f"⏳ Waiting for document to be ready at: {url}")
        deadline = asyncio.get_event_loop().time() + timeout
        
        async with aiohttp.ClientSession() as session:
            while asyncio.get_event_loop().time() < deadline:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content_length = response.headers.get('content-length', '0')
                            logger.info(f"✅ Document ready! Size: {content_length} bytes")
                            return True
                        else:
                            logger.debug(f"   Still waiting... Status: {response.status}")
                except Exception as e:
                    logger.debug(f"   Polling error (normal): {e}")
                
                await asyncio.sleep(interval)
        
        logger.error(f"❌ Document not ready after {timeout}s timeout")
        return False
    

    

    
    async def _download_and_save_document(self, download_url: str, filename: str, session_id: str) -> Dict[str, Any]:
        """Download document from use_sow and save to unified system"""
        try:
            full_download_url = f"{self.base_url}{download_url}"
            logger.info(f"📥 Attempting to download from: {full_download_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(full_download_url) as response:
                    logger.info(f"📥 Download response status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save to unified system output directory
                        output_dir = Path("unified_ai_chat/backend/output") / session_id
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_path = output_dir / filename
                        
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Document saved to unified system: {output_path}")
                        return {
                            "success": True,
                            "filename": filename,
                            "path": str(output_path),
                            "size": len(content)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Document download failed: {response.status} - {error_text}")
                        return {"success": False, "error": f"Download failed: {response.status} - {error_text}"}
        except Exception as e:
            logger.error(f"❌ Document download error: {e}")
            return {"success": False, "error": str(e)}
    
    def _convert_unified_data_to_use_sow_format(self, sow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert unified chat collected data to use_sow direct API format
        Defensive parsing to handle various data formats
        """
        
        # Extract and normalize data from unified chat format
        project_info = sow_data.get("project_info", "") or ""
        services = sow_data.get("services", "standard") or "standard"
        deliverables = sow_data.get("deliverables", "") or ""
        timeline = sow_data.get("timeline", "") or ""
        resources = sow_data.get("resources", []) or []
        contacts = sow_data.get("contacts", {}) or {}
        budget = sow_data.get("budget", "") or ""
        
        # Ensure resources is a list
        if isinstance(resources, str):
            # Convert string to list format
            resources = [{"role": resources, "count": 1}]
        elif not isinstance(resources, list):
            resources = []
        
        # Format resources
        resources_text = ""
        if resources:
            resource_lines = []
            for resource in resources:
                role = resource.get("role", "Team Member")
                count = resource.get("count", 1)
                resource_lines.append(f"{role} - {count} person{'s' if count > 1 else ''} - 100% allocation")
            resources_text = "\\n".join(resource_lines)
        
        # Format contacts
        contacts_text = ""
        if contacts:
            contractor_info = f"""Contractor Contact:
Name: {contacts.get('contact_person', 'Project Manager')}
Company: {contacts.get('name', 'Professional Services Inc.')}
Role: Project Director
Email: {contacts.get('email', 'pm@company.com')}
Phone: {contacts.get('phone', '+1-555-0123')}
Address: {contacts.get('address', '123 Business St, City, State')}

Client Contact:
Name: {contacts.get('contact_person', 'Client Representative')}
Company: {contacts.get('name', 'Client Organization')}
Role: Project Sponsor
Email: {contacts.get('email', 'client@company.com')}
Phone: {contacts.get('phone', '+1-555-0456')}
Address: {contacts.get('address', '456 Client Ave, City, State')}"""
            contacts_text = contacts_text.replace('\n', '\\n')
        
        # Create the payload for direct API call
        payload = {
            "template_path": self.template_path,
            "project_data": {
                "project_info": project_info,
                "services": services,
                "deliverables": deliverables,
                "timeline": timeline,
                "resources": resources_text,
                "contacts": contacts_text,
                "budget": budget
            }
        }
        
        logger.info(f"🎯 Converted unified chat data to use_sow direct API format")
        logger.info(f"   Project: {project_info[:50]}...")
        logger.info(f"   Services: {services}")
        logger.info(f"   Resources: {len(resources)} roles")
        
        return payload
    
    # Removed complex formatting methods - using exact working data instead

# Create global adapter instance
use_sow_adapter = UseSowAdapter()