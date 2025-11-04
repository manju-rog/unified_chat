"""Adapter for interacting with the Absence Management service."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings
from ..models import SessionState


class AbsenceAdapter:
    """Performs absence operations against the Spring Boot backend."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._timeout = httpx.Timeout(20.0, connect=10.0)
        self._logger = logging.getLogger(__name__)

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

            normalized_dates = [
                self._normalize_date_value(value) for value in (dates or [date.today().isoformat()])
            ]

            payload = {
                "employeeId": employee_id,
                "dates": normalized_dates,
                "status": status,
                "reason": reason or "",
            }
            
            self._logger.info(f"Marking absence - Payload: {payload}")
            response = await client.post("/ai/mark-absence", json=payload)
            self._logger.info(f"Mark absence response - Status: {response.status_code}, Body: {response.text}")
            
            if response.status_code >= 400:
                error_detail = response.text if response.text else "Unknown error"
                self._logger.error(f"Absence service error: {error_detail}")
                return {
                    "success": False,
                    "message": f"Absence service returned an error: {error_detail}",
                }
            body = response.json()
            return {
                "success": body.get("success", False),
                "message": body.get("message", "Absence updated."),
                "details": {
                    "employeeName": employee_name,
                    "status": status,
                    "dates": normalized_dates,
                },
            }

    async def query_absence(
        self,
        query_type: str,
        dates: Optional[List[str]] = None,
        employee_name: Optional[str] = None,
        month: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            if query_type == "byDate":
                date_value = self._normalize_date_value(
                    (dates or [datetime.utcnow().date().isoformat()])[0]
                )
                details = await self._fetch_day_details(client, date_value)
                return self._format_day_details(date_value, details, employee_name)

            if query_type == "byDateRange":
                if not dates or len(dates) < 2:
                    return {
                        "success": False,
                        "message": "Please provide both start and end dates for the range query.",
                    }
                start = self._normalize_date_value(dates[0])
                end = self._normalize_date_value(dates[1])
                calendar = await self._fetch_calendar(client, start, end)
                return await self._format_calendar_with_details(client, start, end, calendar, employee_name)

            if query_type == "byMonth":
                if not month:
                    return {
                        "success": False,
                        "message": "Please provide a month in YYYY-MM format.",
                    }
                # Handle month name or YYYY-MM format
                if "-" in month:
                    start = date.fromisoformat(f"{month}-01")
                else:
                    # Month name provided, need to convert
                    month_map = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month_num = month_map.get(month.lower(), datetime.now().month)
                    year = datetime.now().year
                    start = date(year, month_num, 1)
                
                if start.month == 12:
                    next_month = start.replace(year=start.year + 1, month=1, day=1)
                else:
                    next_month = start.replace(month=start.month + 1, day=1)
                end = next_month - timedelta(days=1)
                calendar = await self._fetch_calendar(client, start.isoformat(), end.isoformat())
                return await self._format_calendar_with_details(client, start.isoformat(), end.isoformat(), calendar, employee_name)

            if query_type == "byStatus":
                target_status = (status or "A").upper()
                date_value = self._normalize_date_value(
                    (dates or [datetime.utcnow().date().isoformat()])[0]
                )
                details = await self._fetch_day_details(client, date_value)
                employees = details.get("employees", {}) if isinstance(details, dict) else {}
                status_map = {"A": "🚫 Absent", "V": "🏖️ On Vacation", "P": "✅ Present"}
                status_plain = {"A": "absent", "V": "on vacation", "P": "present"}
                matched = employees.get(target_status, [])
                status_label = status_map.get(target_status, target_status)

                if matched:
                    lines = [f"{status_label} on {date_value}:"]
                    for entry in matched:
                        reason = entry.get("reason", "").strip() or "No reason provided"
                        lines.append(f"  • {entry.get('name')} - {reason}")
                    message = "\n".join(lines)
                else:
                    message = f"✅ Nobody is {status_plain.get(target_status, status_label.lower())} on {date_value}."

                return {
                    "success": True,
                    "message": message,
                    "details": {
                        "date": date_value,
                        "status": target_status,
                        "employees": matched,
                    },
                }

            if query_type == "byEmployee":
                if not employee_name:
                    return {
                        "success": False,
                        "message": "Please specify which employee you want to check.",
                    }

                date_value = self._normalize_date_value(
                    (dates or [datetime.utcnow().date().isoformat()])[0]
                )
                details = await self._fetch_day_details(client, date_value)
                employees = details.get("employees", {}) if isinstance(details, dict) else {}

                matches = []
                for status_code, label in [("A", "Absent"), ("V", "On Vacation"), ("P", "Present")]:
                    for entry in employees.get(status_code, []):
                        if entry.get("name", "").strip().lower() == employee_name.strip().lower():
                            matches.append({"status": label, **entry})

                if matches:
                    lines = [f"📅 Status for {employee_name} on {date_value}:"]
                    for entry in matches:
                        reason = entry.get("reason", "").strip() or "No reason provided"
                        lines.append(f"  • {entry['status']}: {reason}")
                else:
                    lines = [f"{employee_name} has no recorded absences on {date_value}."]

                return {
                    "success": True,
                    "message": "\n".join(lines),
                    "details": {
                        "date": date_value,
                        "employee": employee_name,
                        "records": matches,
                    },
                }

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
        self._logger.info(f"Fetching day details for date: {date_value}")
        response = await client.get("/absences/calendar/day-details", params={"date": date_value})
        response.raise_for_status()
        data = response.json()
        self._logger.info(f"Day details response: {data}")
        return data

    def _normalize_date_value(self, value: str) -> str:
        """Convert human-friendly date tokens to ISO strings."""
        if not value:
            return date.today().isoformat()

        token = value.strip().lower()
        if token == "today":
            return date.today().isoformat()
        if token == "yesterday":
            return (date.today() - timedelta(days=1)).isoformat()
        if token == "tomorrow":
            return (date.today() + timedelta(days=1)).isoformat()

        formats = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y")
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue

        self._logger.warning("Unable to parse date value '%s'; defaulting to today().", value)
        return date.today().isoformat()

    @staticmethod
    def _resolve_employee_id(name: str, employees: List[Dict[str, Any]]) -> Optional[int]:
        if not name:
            return None

        query = name.strip().lower()
        best_id: Optional[int] = None
        best_score = 0.0

        for employee in employees:
            candidate_name = str(employee.get("name", "")).strip()
            if not candidate_name:
                continue

            candidate_lower = candidate_name.lower()
            if candidate_lower == query:
                return employee.get("id")

            score = SequenceMatcher(None, query, candidate_lower).ratio()
            if score > best_score:
                best_score = score
                best_id = employee.get("id")

        if best_score >= 0.8:
            return best_id
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

        # Format as beautiful structured message for display
        if not employee_absences:
            message = f"📅 **Absence Report for {start} to {end}**\n\n✅ No absences recorded during this period."
        else:
            # Create a beautiful formatted message
            message_lines = [f"📅 **Absence Report for {start} to {end}**\n"]
            
            # Group by status
            absent_employees = [emp for emp in employee_absences.values() if emp["status"] == "Absent"]
            vacation_employees = [emp for emp in employee_absences.values() if emp["status"] == "Vacation"]
            
            if absent_employees:
                message_lines.append("🚫 **Absent Employees:**")
                for emp in absent_employees:
                    dates_str = ", ".join(emp["dates"][:3])  # Show first 3 dates
                    if len(emp["dates"]) > 3:
                        dates_str += f" (and {len(emp['dates']) - 3} more)"
                    message_lines.append(f"  • **{emp['name']}** ({emp['department']}) - {dates_str}")
                message_lines.append("")
            
            if vacation_employees:
                message_lines.append("🏖️ **On Vacation:**")
                for emp in vacation_employees:
                    dates_str = ", ".join(emp["dates"][:3])  # Show first 3 dates
                    if len(emp["dates"]) > 3:
                        dates_str += f" (and {len(emp['dates']) - 3} more)"
                    message_lines.append(f"  • **{emp['name']}** ({emp['department']}) - {dates_str}")
                message_lines.append("")
            
            # Add summary
            message_lines.append(f"📊 **Summary:** {total_absent} absence days, {total_vacation} vacation days")
            
            message = "\n".join(message_lines)
        
        return {
            "success": True,
            "message": message,
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


    async def check_employee_status(
        self,
        employee_name: str,
        date: str = None,
        query_type: str = "specific_employee"
    ) -> Dict[str, Any]:
        """Check if a specific employee is absent on a specific date."""
        if not date:
            date = datetime.now().date().isoformat()
        
        async with httpx.AsyncClient(
            base_url=str(self._settings.absence_api_base), timeout=self._timeout
        ) as client:
            try:
                # Get employee info first
                employees = await self._fetch_employees(client)
                employee_id = self._resolve_employee_id(employee_name, employees)
                
                if employee_id is None:
                    return {
                        "success": False,
                        "message": f"I could not find an employee named {employee_name}.",
                    }
                
                # Get absence data for the specific date
                response = await client.get(
                    "/absences/calendar/day-details", params={"date": date}
                )
                response.raise_for_status()
                data = response.json()
                
                employees = data.get("employees", {}) if isinstance(data, dict) else {}
                absent_employees = employees.get("A", [])
                present_employees = employees.get("P", [])
                vacation_employees = employees.get("V", [])

                def _matches(entry: Dict[str, Any]) -> bool:
                    entry_id = entry.get("id") or entry.get("employeeId")
                    return (
                        str(entry_id) == str(employee_id)
                        or entry.get("name", "").strip().lower() == employee_name.lower()
                    )

                for absent_emp in absent_employees:
                    if _matches(absent_emp):
                        reason = absent_emp.get("reason", "No reason provided")
                        return {
                            "success": True,
                            "message": f"Yes, {employee_name} is absent on {date}. Reason: {reason or 'No reason provided'}.",
                            "status": "absent",
                            "reason": reason or ""
                        }
                
                for vacation_emp in vacation_employees:
                    if _matches(vacation_emp):
                        reason = vacation_emp.get("reason", "Vacation")
                        return {
                            "success": True,
                            "message": f"{employee_name} is on vacation on {date}. Reason: {reason or 'Vacation'}.",
                            "status": "vacation",
                            "reason": reason or ""
                        }
                
                for present_emp in present_employees:
                    if _matches(present_emp):
                        return {
                            "success": True,
                            "message": f"No, {employee_name} is present on {date}.",
                            "status": "present"
                        }
                
                # If not found in any list, report no record
                return {
                    "success": True,
                    "message": f"{employee_name} has no recorded absences on {date}.",
                    "status": "unknown"
                }
                
            except httpx.HTTPError as e:
                self._logger.error(f"HTTP error checking employee status: {e}")
                return {
                    "success": False,
                    "message": f"Error checking status for {employee_name}: {str(e)}"
                }
            except Exception as e:
                self._logger.error(f"Unexpected error checking employee status: {e}")
                return {
                    "success": False,
                    "message": f"Unexpected error checking {employee_name}'s status."
                }


absence_adapter = AbsenceAdapter()
