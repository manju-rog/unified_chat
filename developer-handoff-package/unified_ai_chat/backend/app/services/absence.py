"""Adapter for interacting with the Absence Management service."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings
from ..models import SessionState


class AbsenceAdapter:
    """Performs absence operations against the Spring Boot backend."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._timeout = httpx.Timeout(20.0, connect=10.0)

    async def mark_absence(
        self,
        employee_name: str,
        dates: List[str],
        status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            employees = await self._fetch_employees(client)
            employee_id = self._resolve_employee_id(employee_name, employees)
            if employee_id is None:
                return {
                    "success": False,
                    "message": f"I could not find an employee named {employee_name}.",
                }

            payload = {
                "employeeId": employee_id,
                "dates": dates,
                "status": status,
                "reason": reason or "",
            }
            response = await client.post("/ai/mark-absence", json=payload)
            if response.status_code >= 400:
                return {
                    "success": False,
                    "message": "Absence service returned an error while updating attendance.",
                }
            body = response.json()
            return {
                "success": body.get("success", False),
                "message": body.get("message", "Absence updated."),
                "details": {
                    "employeeName": employee_name,
                    "status": status,
                    "dates": dates,
                },
            }

    async def query_absence(
        self,
        query_type: str,
        dates: Optional[List[str]] = None,
        employee_name: Optional[str] = None,
        month: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            if query_type == "byDate":
                date_value = (dates or [datetime.utcnow().date().isoformat()])[0]
                details = await self._fetch_day_details(client, date_value)
                return self._format_day_details(date_value, details, employee_name)

            if query_type == "byDateRange":
                if not dates or len(dates) < 2:
                    return {
                        "success": False,
                        "message": "Please provide both start and end dates for the range query.",
                    }
                start, end = dates[0], dates[1]
                calendar = await self._fetch_calendar(client, start, end)
                return await self._format_calendar_with_details(client, start, end, calendar, employee_name)

            if query_type == "byMonth":
                if not month:
                    return {
                        "success": False,
                        "message": "Please provide a month in YYYY-MM format.",
                    }
                start = date.fromisoformat(f"{month}-01")
                if start.month == 12:
                    next_month = start.replace(year=start.year + 1, month=1, day=1)
                else:
                    next_month = start.replace(month=start.month + 1, day=1)
                end = next_month - timedelta(days=1)
                calendar = await self._fetch_calendar(client, start.isoformat(), end.isoformat())
                return await self._format_calendar_with_details(client, start.isoformat(), end.isoformat(), calendar, employee_name)

            return {
                "success": False,
                "message": "Unsupported query type provided to absence adapter.",
            }

    async def _fetch_employees(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        response = await client.get("/ai/employees")
        response.raise_for_status()
        body = response.json()
        return body.get("data", []) if isinstance(body, dict) else []

    async def _fetch_calendar(
        self, client: httpx.AsyncClient, start: str, end: str
    ) -> Dict[str, Any]:
        response = await client.get("/absences/calendar", params={"from": start, "to": end})
        response.raise_for_status()
        return response.json()

    async def _fetch_day_details(
        self, client: httpx.AsyncClient, date_value: str
    ) -> Dict[str, Any]:
        response = await client.get("/absences/calendar/day-details", params={"date": date_value})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _resolve_employee_id(name: str, employees: List[Dict[str, Any]]) -> Optional[int]:
        lower = name.strip().lower()
        for employee in employees:
            if str(employee.get("name", "")).strip().lower() == lower:
                return employee.get("id")
        return None

    @staticmethod
    def _format_day_details(
        date_value: str, details: Dict[str, Any], employee_name: Optional[str]
    ) -> Dict[str, Any]:
        employees = details.get("employees", {}) if isinstance(details, dict) else {}
        summary_lines: List[str] = []
        absences = employees.get("A", [])
        vacations = employees.get("V", [])

        if employee_name:
            matches = [
                entry
                for status_group in (absences, vacations)
                for entry in status_group
                if entry.get("name", "").lower() == employee_name.strip().lower()
            ]
            if matches:
                entry = matches[0]
                status = "Absent" if entry in absences else "On Vacation"
                summary_lines.append(
                    f"{entry.get('name')} was {status.lower()} on {date_value}."
                )
            else:
                summary_lines.append(
                    f"{employee_name} had no recorded absences on {date_value}."
                )
        else:
            summary_lines.append(f"📅 Absence Report for {date_value}:")
            if absences:
                summary_lines.append("\n🚫 Absent:")
                for entry in absences:
                    reason = entry.get('reason', '').strip() or 'No reason provided'
                    summary_lines.append(f"  • {entry.get('name')} - {reason}")
            if vacations:
                summary_lines.append("\n🏖️ On Vacation:")
                for entry in vacations:
                    reason = entry.get('reason', '').strip() or 'Vacation'
                    summary_lines.append(f"  • {entry.get('name')} - {reason}")
            if not absences and not vacations:
                summary_lines.append("✅ No absences recorded.")

        return {
            "success": True,
            "message": "\n".join(summary_lines),
            "details": {
                "date": date_value,
                "absences": absences,
                "vacations": vacations,
            },
        }

    async def _format_calendar_with_details(
        self,
        client: httpx.AsyncClient,
        start: str,
        end: str,
        calendar: Dict[str, Any],
        employee_name: Optional[str],
    ) -> Dict[str, Any]:
        days = calendar.get("days", []) if isinstance(calendar, dict) else []
        total_absent = 0
        total_vacation = 0
        
        # Group absences by employee
        employee_absences: Dict[str, Dict[str, Any]] = {}
        
        # Fetch details for days with absences
        for day in days:
            day_date = day.get("date")
            absent_count = day.get("A", 0)
            vacation_count = day.get("V", 0)
            
            if absent_count or vacation_count:
                try:
                    details = await self._fetch_day_details(client, day_date)
                    employees_data = details.get("employees", {})
                    absent_list = employees_data.get("A", [])
                    vacation_list = employees_data.get("V", [])
                    
                    # Group by employee
                    for emp in absent_list:
                        name = emp.get("name", "Unknown")
                        if name not in employee_absences:
                            employee_absences[name] = {
                                "name": name,
                                "status": "Absent",
                                "dates": [],
                                "department": emp.get("department", ""),
                            }
                        employee_absences[name]["dates"].append(day_date)
                        
                    for emp in vacation_list:
                        name = emp.get("name", "Unknown")
                        if name not in employee_absences:
                            employee_absences[name] = {
                                "name": name,
                                "status": "Vacation",
                                "dates": [],
                                "department": emp.get("department", ""),
                            }
                        employee_absences[name]["dates"].append(day_date)
                        
                except Exception:
                    pass
                
            total_absent += absent_count or 0
            total_vacation += vacation_count or 0

        # Format as structured data for rich UI
        return {
            "success": True,
            "message": "Absence report generated",
            "details": {
                "start": start,
                "end": end,
                "employee_absences": list(employee_absences.values()),
                "display_type": "absence_breakdown",  # Signal to frontend
                "totals": {
                    "absent": total_absent,
                    "vacation": total_vacation,
                },
            },
        }

    async def chat(self, session: SessionState, user_message: str) -> Dict[str, Any]:
        if not user_message or not user_message.strip():
            return {
                "success": False,
                "message": "I need a message to send to the absence assistant.",
                "action_type": "absence_error",
            }

        conversation_id = session.metadata.get("absence_conversation_id") or session.session_id

        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            payload = {
                "message": user_message,
                "conversationId": conversation_id,
            }
            response = await client.post("/ai/chat", json=payload)

            if response.status_code >= 400:
                return {
                    "success": False,
                    "message": "The absence assistant returned an error.",
                    "action_type": "absence_error",
                }

            data = response.json() if response.content else {}

            message = data.get("response") or data.get("error")
            if not message:
                message = "I could not retrieve a response from the absence assistant."

            return {
                "success": data.get("success", False),
                "message": message,
                "action_type": data.get("actionType", "absence_chat"),
                "action_data": data.get("actionData"),
                "conversation_id": data.get("conversationId") or conversation_id,
            }

    async def get_employees(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            return await self._fetch_employees(client)


absence_adapter = AbsenceAdapter()
