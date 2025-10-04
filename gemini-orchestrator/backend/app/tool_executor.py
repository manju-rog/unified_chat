"""
Tool executor for routing and executing tool calls.
Validates arguments and calls internal tool endpoints.
Requirements: 6.3, 6.4, 7.4
"""

import logging
from typing import Dict, Any, Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for internal tool endpoints
BASE_URL = "http://localhost:8000"


async def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call by routing to the appropriate endpoint.
    
    Args:
        tool_name: Name of the tool to execute
        tool_args: Arguments for the tool call
    
    Returns:
        Dict with tool execution result: {ok: bool, data: Any, error: Optional[str]}
    
    Requirements: 6.3, 6.4, 7.4
    """
    try:
        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
        
        # Route to appropriate endpoint based on tool name
        if tool_name == "mark_absent":
            return await _execute_mark_absent(tool_args)
        
        elif tool_name == "mark_present":
            return await _execute_mark_present(tool_args)
        
        elif tool_name == "get_absence_status":
            return await _execute_get_absence_status(tool_args)
        
        elif tool_name == "start_sow":
            return await _execute_start_sow(tool_args)
        
        elif tool_name == "update_sow":
            return await _execute_update_sow(tool_args)
        
        elif tool_name == "generate_sow":
            return await _execute_generate_sow(tool_args)
        
        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                "ok": False,
                "data": None,
                "error": f"Unknown tool: {tool_name}"
            }
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


# ============================================================================
# Absence Tool Executors
# ============================================================================

async def _execute_mark_absent(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute mark_absent tool."""
    try:
        # Validate required arguments
        if "employee_id" not in args or "date" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required arguments: employee_id and date"
            }
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/absence/mark_absent",
                json=args,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": result.get("ok", True),
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in mark_absent: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in mark_absent: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


async def _execute_mark_present(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute mark_present tool."""
    try:
        # Validate required arguments
        if "employee_id" not in args or "date" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required arguments: employee_id and date"
            }
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/absence/mark_present",
                json=args,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": result.get("ok", True),
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in mark_present: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in mark_present: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


async def _execute_get_absence_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute get_absence_status tool."""
    try:
        # Validate required arguments
        if "employee_id" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required argument: employee_id"
            }
        
        employee_id = args["employee_id"]
        date = args.get("date")  # Optional
        
        # Build URL with query params
        url = f"{BASE_URL}/absence/status/{employee_id}"
        params = {}
        if date:
            params["date"] = date
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": True,
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in get_absence_status: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in get_absence_status: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


# ============================================================================
# SOW Tool Executors
# ============================================================================

async def _execute_start_sow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute start_sow tool."""
    try:
        # Validate required arguments
        if "project_name" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required argument: project_name"
            }
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/sow/start",
                json=args,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": result.get("ok", True),
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in start_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in start_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


async def _execute_update_sow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute update_sow tool."""
    try:
        # Validate required arguments
        if "sow_id" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required argument: sow_id"
            }
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/sow/update",
                json=args,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": result.get("ok", True),
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in update_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in update_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


async def _execute_generate_sow(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute generate_sow tool."""
    try:
        # Validate required arguments
        if "sow_id" not in args:
            return {
                "ok": False,
                "data": None,
                "error": "Missing required argument: sow_id"
            }
        
        sow_id = args["sow_id"]
        
        # Call internal endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/sow/generate/{sow_id}",
                timeout=30.0  # Longer timeout for document generation
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "ok": result.get("ok", True),
            "data": result,
            "error": None
        }
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in generate_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": f"HTTP error: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"Error in generate_sow: {e}")
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }
