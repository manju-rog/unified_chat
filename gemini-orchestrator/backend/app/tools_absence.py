"""
Absence Management Tool Endpoints.
Provides REST APIs for marking absences, presence, and checking status.
Requirements: 9.1, 9.2, 9.3
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
from datetime import datetime

from app.models import AbsenceRequest, PresenceRequest

# ============================================================================
# Router Setup (Subtask 4.1)
# ============================================================================

router = APIRouter(prefix="/absence", tags=["absence"])

# In-memory storage for absence records
# Key: (employee_id, date) -> Value: {employee_id, date, reason, status}
absence_storage: Dict[tuple, Dict] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def _get_absence_key(employee_id: str, date: str) -> tuple:
    """Generate storage key from employee_id and date"""
    return (employee_id, date)


# ============================================================================
# Endpoints (Subtasks 4.2, 4.3, 4.4)
# ============================================================================

@router.post("/mark_absent")
async def mark_absent(request: AbsenceRequest) -> Dict:
    """
    Mark an employee as absent for a specific date.
    
    Requirements: 3.1, 9.1
    
    Args:
        request: AbsenceRequest with employee_id, date, and optional reason
        
    Returns:
        {ok: bool, message: str}
    """
    try:
        key = _get_absence_key(request.employee_id, request.date)
        
        # Store absence record
        absence_storage[key] = {
            "employee_id": request.employee_id,
            "date": request.date,
            "reason": request.reason or "Not specified",
            "status": "absent",
            "recorded_at": datetime.now().isoformat()
        }
        
        message = f"Marked {request.employee_id} as absent on {request.date}"
        if request.reason:
            message += f" (Reason: {request.reason})"
        
        return {
            "ok": True,
            "message": message
        }
    
    except Exception as e:
        return {
            "ok": False,
            "reason": f"Failed to mark absent: {str(e)}"
        }


@router.post("/mark_present")
async def mark_present(request: PresenceRequest) -> Dict:
    """
    Mark an employee as present for a specific date.
    Removes or updates the absence record.
    
    Requirements: 3.2, 9.2
    
    Args:
        request: PresenceRequest with employee_id and date
        
    Returns:
        {ok: bool, message: str}
    """
    try:
        key = _get_absence_key(request.employee_id, request.date)
        
        # Remove absence record if it exists
        if key in absence_storage:
            del absence_storage[key]
            message = f"Marked {request.employee_id} as present on {request.date} (removed absence record)"
        else:
            message = f"Confirmed {request.employee_id} as present on {request.date} (no absence record found)"
        
        return {
            "ok": True,
            "message": message
        }
    
    except Exception as e:
        return {
            "ok": False,
            "reason": f"Failed to mark present: {str(e)}"
        }


@router.get("/status/{employee_id}")
async def get_absence_status(
    employee_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today if not provided")
) -> Dict:
    """
    Get absence status for an employee on a specific date.
    
    Requirements: 3.3, 9.3
    
    Args:
        employee_id: Employee identifier
        date: Optional date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        {employee_id: str, date: str, status: str, reason?: str}
    """
    try:
        # Use today's date if not provided
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        key = _get_absence_key(employee_id, date)
        
        # Check if absence record exists
        if key in absence_storage:
            record = absence_storage[key]
            return {
                "employee_id": employee_id,
                "date": date,
                "status": "absent",
                "reason": record.get("reason", "Not specified"),
                "recorded_at": record.get("recorded_at")
            }
        else:
            return {
                "employee_id": employee_id,
                "date": date,
                "status": "present"
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get absence status: {str(e)}"
        )
