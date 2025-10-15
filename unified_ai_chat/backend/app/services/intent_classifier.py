"""
Advanced Intent Classification System for Unified AI Chat
Handles all scenarios for absence management and SOW generation with intelligent routing.
"""
from __future__ import annotations

import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class IntentType(Enum):
    # Absence Management Intents
    MARK_ABSENCE = "mark_absence"
    MARK_MULTIPLE_ABSENCE = "mark_multiple_absence"
    QUERY_ABSENCE_TODAY = "query_absence_today"
    QUERY_ABSENCE_MONTH = "query_absence_month"
    QUERY_ABSENCE_SPECIFIC_MONTH = "query_absence_specific_month"
    QUERY_ABSENCE_WEEK = "query_absence_week"
    QUERY_ABSENCE_DATE_RANGE = "query_absence_date_range"
    QUERY_VACATION = "query_vacation"
    CHECK_EMPLOYEE_SPECIFIC_DAY = "check_employee_specific_day"
    CHECK_EMPLOYEE_LEAVE = "check_employee_leave"
    
    # SOW Generation Intents
    GENERATE_SOW = "generate_sow"
    CREATE_SOW = "create_sow"
    SOW_REPORT = "sow_report"
    PROJECT_DETAILS_SOW = "project_details_sow"
    
    # Mixed/Confused Intents
    MIXED_ABSENCE_SOW = "mixed_absence_sow"
    CONFUSED_REQUEST = "confused_request"
    
    # General Intents
    GREETING = "greeting"
    HELP = "help"
    CAPABILITIES = "capabilities"
    
    # Mode Switching
    SWITCH_TO_SOW = "switch_to_sow"
    SWITCH_TO_ABSENCE = "switch_to_absence"
    EXIT_SOW = "exit_sow"
    
    # Confirmation/Response
    CONFIRMATION_YES = "confirmation_yes"
    CONFIRMATION_NO = "confirmation_no"
    REASON_PROVIDED = "reason_provided"

@dataclass
class IntentResult:
    intent_type: IntentType
    confidence: float
    extracted_data: Dict[str, Any]
    suggested_response: str
    action_type: str
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    disambiguation_needed: bool = False
    disambiguation_options: Optional[List[str]] = None

class AdvancedIntentClassifier:
    """
    Comprehensive intent classification system that handles all scenarios
    for absence management and SOW generation.
    """
    
    def __init__(self):
        self.absence_keywords = {
            'mark': ['mark', 'set', 'record', 'log', 'update'],
            'absent': ['absent', 'absence', 'away', 'not here', 'missing'],
            'present': ['present', 'here', 'available', 'in office'],
            'vacation': ['vacation', 'holiday', 'leave', 'off', 'pto', 'time off'],
            'query': ['who', 'check', 'show', 'list', 'get', 'find', 'tell me'],
            'today': ['today', 'now', 'currently'],
            'dates': ['yesterday', 'tomorrow', 'this week', 'next week', 'last week', 
                     'this month', 'next month', 'last month', 'between'],
        }
        
        self.sow_keywords = {
            'generate': ['generate', 'create', 'make', 'build', 'produce'],
            'sow': ['sow', 'statement of work', 'document', 'contract', 'agreement'],
            'report': ['report', 'document', 'file', 'paper'],
            'project': ['project', 'details', 'requirements', 'specifications'],
        }
        
        self.mixed_patterns = [
            r'(absence|absent).*sow',
            r'sow.*absence',
            r'(leave|vacation).*sow',
            r'sow.*(leave|vacation)',
            r'both.*absence.*sow',
            r'both.*sow.*absence',
        ]
        
        self.months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        self.time_patterns = {
            'today': r'\btoday\b',
            'yesterday': r'\byesterday\b',
            'tomorrow': r'\btomorrow\b',
            'this_week': r'\bthis week\b',
            'next_week': r'\bnext week\b',
            'last_week': r'\blast week\b',
            'this_month': r'\bthis month\b',
            'next_month': r'\bnext month\b',
            'last_month': r'\blast month\b',
            'between_dates': r'\bbetween\b.*\band\b',
        }
        
        self.generic_employee_tokens = {
            'someone',
            'somebody',
            'anyone',
            'anybody',
            'employee',
            'staff',
            'person',
            'people',
            'member',
            'team member',
            'personnel',
            'them',
            'him',
            'her',
            'they',
        }

    def classify_intent(self, message: str, session_context: Optional[Dict] = None) -> IntentResult:
        """
        Main method to classify user intent with comprehensive scenario handling.
        """
        message_lower = message.lower().strip()
        session_context = session_context or {}
        
        # Handle reason provision first (if waiting for reason)
        if session_context.get('waiting_for_reason'):
            return self._handle_reason_provision(message, session_context)
        
        # Check for mixed/confused intents early
        mixed_result = self._check_mixed_intents(message_lower)
        if mixed_result:
            return mixed_result
        
        # Check for SOW intents
        sow_result = self._classify_sow_intent(message_lower)
        if sow_result:
            return sow_result
        
        # Check for absence intents
        absence_result = self._classify_absence_intent(message_lower)
        if absence_result:
            return absence_result
        
        # Check for general intents
        general_result = self._classify_general_intent(message_lower)
        if general_result:
            return general_result
        
        # Handle confirmation responses (only if no other pattern matches)
        if self._is_confirmation_response(message_lower):
            return self._handle_confirmation(message_lower, session_context)
        
        # Default fallback
        return self._create_fallback_response(message)

    def _is_confirmation_response(self, message: str) -> bool:
        """Check if message is a yes/no confirmation response."""
        message_clean = message.strip().lower()
        
        # Only consider it a confirmation if it's a short, direct response
        if len(message_clean.split()) > 3:
            return False
            
        yes_patterns = ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay', 'add reason']
        no_patterns = ['no', 'n', 'nope', 'cancel', 'skip', 'don\'t']
        
        # Must be exact match or very close for short responses
        return (message_clean in yes_patterns or 
                message_clean in no_patterns or
                message_clean.startswith('yes ') or
                message_clean.startswith('no '))

    def _handle_confirmation(self, message: str, context: Dict) -> IntentResult:
        """Handle yes/no confirmation responses."""
        is_yes = any(pattern in message for pattern in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay', 'add reason'])
        
        intent_type = IntentType.CONFIRMATION_YES if is_yes else IntentType.CONFIRMATION_NO
        
        return IntentResult(
            intent_type=intent_type,
            confidence=0.95,
            extracted_data={'confirmation': is_yes, 'context': context},
            suggested_response="Processing your confirmation...",
            action_type="confirmation_response"
        )

    def _handle_reason_provision(self, message: str, context: Dict) -> IntentResult:
        """Handle when user provides a reason for absence."""
        return IntentResult(
            intent_type=IntentType.REASON_PROVIDED,
            confidence=0.95,
            extracted_data={'reason': message.strip(), 'context': context},
            suggested_response=f"Thank you for providing the reason: {message.strip()}",
            action_type="reason_provided"
        )

    def _check_mixed_intents(self, message: str) -> Optional[IntentResult]:
        """Check for mixed absence/SOW intents that cause confusion."""
        
        # Specific confused patterns that should be CONFUSED_REQUEST
        confused_patterns = [
            r'\bmake\s+absence\s+sow\b',
            r'\babsence\s+sow\s+report\b',
            r'\bleave\s+sow\b',
        ]
        
        for pattern in confused_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return IntentResult(
                    intent_type=IntentType.CONFUSED_REQUEST,
                    confidence=0.9,
                    extracted_data={'original_message': message},
                    suggested_response="I'm confused about what you need help with. I can assist with absence tracking OR SOW generation. Please clarify which one you'd like help with.",
                    action_type="confusion_clarification",
                    disambiguation_needed=True,
                    disambiguation_options=["Absence Management", "SOW Generation"]
                )
        
        # Clear mixed patterns that should be MIXED_ABSENCE_SOW
        clear_mixed_patterns = [
            r'\babsence\s+and\s+sow\b',
            r'\bsow\s+and\s+absence\b',
            r'\bboth\s+absence\s+and\s+sow\b',
        ]
        
        for pattern in clear_mixed_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return IntentResult(
                    intent_type=IntentType.MIXED_ABSENCE_SOW,
                    confidence=0.9,
                    extracted_data={'original_message': message},
                    suggested_response="I can help with both absence management and SOW generation. Which would you like to focus on first?",
                    action_type="disambiguation_needed",
                    disambiguation_needed=True,
                    disambiguation_options=["Absence Management", "SOW Generation"]
                )
        
        # Check for other confusing combinations
        has_absence = any(keyword in message for keyword in ['absence', 'absent', 'leave', 'vacation'])
        has_sow = any(keyword in message for keyword in ['sow', 'statement', 'document'])
        
        if has_absence and has_sow:
            # If it's a clear "and" combination, treat as mixed
            if ' and ' in message.lower():
                return IntentResult(
                    intent_type=IntentType.MIXED_ABSENCE_SOW,
                    confidence=0.85,
                    extracted_data={'original_message': message},
                    suggested_response="I can help with both absence management and SOW generation. Which would you like to focus on first?",
                    action_type="disambiguation_needed",
                    disambiguation_needed=True,
                    disambiguation_options=["Absence Management", "SOW Generation"]
                )
            else:
                # Otherwise treat as confused
                return IntentResult(
                    intent_type=IntentType.CONFUSED_REQUEST,
                    confidence=0.8,
                    extracted_data={'original_message': message},
                    suggested_response="I'm confused about what you need help with. I can assist with absence tracking OR SOW generation. Please clarify which one you'd like help with.",
                    action_type="confusion_clarification",
                    disambiguation_needed=True,
                    disambiguation_options=["Absence Management", "SOW Generation"]
                )
        
        return None

    def _classify_sow_intent(self, message: str) -> Optional[IntentResult]:
        """Classify SOW-related intents."""
        
        # Check if message contains SOW-related keywords
        sow_indicators = ['sow', 'statement of work', 'document', 'generate', 'create', 'make']
        if not any(indicator in message for indicator in sow_indicators):
            return None
        
        # Specific "create sow" pattern (distinguish from generate)
        if re.search(r'\bcreate\s+sow\b', message, re.IGNORECASE):
            return IntentResult(
                intent_type=IntentType.CREATE_SOW,
                confidence=0.95,
                extracted_data={'request_type': 'create'},
                suggested_response="I'll help you create a Statement of Work. Let me start the SOW creation process.",
                action_type="sow_creation_start",
                requires_confirmation=True,
                confirmation_message="Do you want to create a SOW document?"
            )
        
        # Generate SOW patterns
        generate_patterns = [
            r'\bgenerate\s+sow\b',
            r'\bmake\s+sow\b',
            r'\bsow\s+generation\b',
            r'\bstart\s+sow\b',
            r'\bgenerate\s+statement\s+of\s+work\b',
        ]
        
        for pattern in generate_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return IntentResult(
                    intent_type=IntentType.GENERATE_SOW,
                    confidence=0.95,
                    extracted_data={'request_type': 'generate'},
                    suggested_response="I'll help you create a Statement of Work. Let me start the SOW generation process.",
                    action_type="sow_generation_start",
                    requires_confirmation=True,
                    confirmation_message="Do you want to generate a SOW document?"
                )
        
        # SOW report requests
        if (re.search(r'\bsow.*report\b', message, re.IGNORECASE) or 
            'make a sow' in message or 
            'sow i want to make' in message):
            return IntentResult(
                intent_type=IntentType.SOW_REPORT,
                confidence=0.9,
                extracted_data={'request_type': 'report'},
                suggested_response="Do you want to generate a SOW document?",
                action_type="sow_confirmation_needed",
                requires_confirmation=True,
                confirmation_message="Do you want to generate a SOW document?"
            )
        
        # Project details for SOW
        if 'project details' in message and 'sow' in message:
            return IntentResult(
                intent_type=IntentType.PROJECT_DETAILS_SOW,
                confidence=0.85,
                extracted_data={'request_type': 'project_details'},
                suggested_response="I'll help you create a SOW with project details. Let's start the process.",
                action_type="sow_project_details_start"
            )
        
        # Generic SOW mentions that need confirmation
        if ('sow' in message or 'statement of work' in message) and len(message.split()) <= 5:
            return IntentResult(
                intent_type=IntentType.CREATE_SOW,
                confidence=0.7,
                extracted_data={'request_type': 'generic'},
                suggested_response="It looks like you want to work with SOW documents. Do you want to generate a new SOW?",
                action_type="sow_confirmation_needed",
                requires_confirmation=True,
                confirmation_message="Do you want to generate a SOW document?"
            )
        
        return None

    def _classify_absence_intent(self, message: str) -> Optional[IntentResult]:
        """Classify absence-related intents with comprehensive scenario handling."""
        
        # Check if message contains absence-related keywords
        absence_indicators = ['absent', 'absence', 'vacation', 'leave', 'present', 'attendance', 'sick', 'off']
        if not any(indicator in message for indicator in absence_indicators):
            return None
        
        # Check specific employee queries FIRST (before general patterns)
        specific_check = self._extract_specific_employee_check(message, None)  # Pass None, it will extract internally
        if specific_check:
            return specific_check
        
        # Query absences for week (check BEFORE general today patterns)
        week_result = self._extract_week_query(message)
        if week_result:
            return week_result
        
        # Query absences between dates (check BEFORE general today patterns)
        date_range_result = self._extract_date_range_query(message)
        if date_range_result:
            return date_range_result
        
        # Check vacation queries
        if self._matches_vacation_query(message):
            return IntentResult(
                intent_type=IntentType.QUERY_VACATION,
                confidence=0.85,
                extracted_data={'query_type': 'vacation'},
                suggested_response="Let me check who is on vacation.",
                action_type="query_vacation"
            )
        
        # Query who is absent (check this AFTER week/date range patterns)
        if self._matches_query_today_pattern(message):
            return IntentResult(
                intent_type=IntentType.QUERY_ABSENCE_TODAY,
                confidence=0.9,
                extracted_data={'date': 'today'},
                suggested_response="Let me check who is absent today.",
                action_type="query_absence_today"
            )
        
        # Query absences for specific month
        month_result = self._extract_month_query(message)
        if month_result:
            return month_result
        
        # Extract employee names (basic pattern matching) for mark operations
        employee_name = self._extract_employee_name(message)
        
        # Mark specific employee absent
        if self._matches_mark_absence_pattern(message):
            return self._handle_mark_absence(message, employee_name)
        
        # Mark multiple employees absent
        if self._matches_mark_multiple_pattern(message):
            return self._handle_mark_multiple_absence(message)
        
        # Check if employee is on leave
        if employee_name and ('leave' in message or 'on leave' in message):
            return IntentResult(
                intent_type=IntentType.CHECK_EMPLOYEE_LEAVE,
                confidence=0.8,
                extracted_data={'employee_name': employee_name, 'query_type': 'leave'},
                suggested_response=f"Let me check if {employee_name} is on leave.",
                action_type="check_employee_leave"
            )
        
        # Generic absence query if contains absence keywords but no specific pattern
        if any(word in message for word in ['who', 'get', 'show', 'check']):
            return IntentResult(
                intent_type=IntentType.QUERY_ABSENCE_TODAY,
                confidence=0.7,
                extracted_data={'date': 'today'},
                suggested_response="Let me check the absence information.",
                action_type="query_absence_today"
            )
        
        return None

    def _matches_mark_absence_pattern(self, message: str) -> bool:
        """Check if message matches mark absence patterns."""
        mark_patterns = [
            r'\bmark\s+\w+\s+(absent|present|vacation)',
            r'\bset\s+\w+\s+(absent|present|vacation)',
            r'\w+\s+is\s+(absent|present|on\s+vacation)',
            r'\w+\s+(absent|present)\s+(today|tomorrow|yesterday)',
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in mark_patterns)

    def _handle_mark_absence(self, message: str, employee_name: Optional[str]) -> IntentResult:
        """Handle marking employee absence."""
        status = 'A'  # Default to absent
        if 'present' in message.lower():
            status = 'P'
        elif 'vacation' in message.lower() or 'leave' in message.lower():
            status = 'V'
        
        date_str = self._extract_date_from_message(message)
        
        return IntentResult(
            intent_type=IntentType.MARK_ABSENCE,
            confidence=0.9,
            extracted_data={
                'employee_name': employee_name,
                'status': status,
                'date': date_str,
                'requires_reason': True
            },
            suggested_response=f"I'll mark {employee_name or 'the employee'} as {'absent' if status == 'A' else 'present' if status == 'P' else 'on vacation'}.",
            action_type="mark_absence",
            requires_confirmation=True,
            confirmation_message="Would you like to add a reason?"
        )

    def _matches_mark_multiple_pattern(self, message: str) -> bool:
        """Check if message matches mark multiple employees pattern."""
        multiple_patterns = [
            r'\bmultiple\s+employees?\s+(absent|present)',
            r'\bmark\s+several\s+employees?',
            r'\bmark\s+all\s+employees?',
            r'\beveryone\s+(absent|present)',
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in multiple_patterns)

    def _handle_mark_multiple_absence(self, message: str) -> IntentResult:
        """Handle marking multiple employees absent."""
        status = 'A'  # Default to absent
        if 'present' in message.lower():
            status = 'P'
        elif 'vacation' in message.lower():
            status = 'V'
        
        return IntentResult(
            intent_type=IntentType.MARK_MULTIPLE_ABSENCE,
            confidence=0.85,
            extracted_data={'status': status, 'multiple': True},
            suggested_response="I'll help you mark multiple employees. Please provide the list of employee names.",
            action_type="mark_multiple_absence"
        )

    def _matches_query_today_pattern(self, message: str) -> bool:
        """Check if message matches query today patterns."""
        today_patterns = [
            r'\bwho\s+is\s+absent\s+today\b',
            r'\bwho.*absent.*today\b',
            r'\bwho\s+is\s+absent\b',  # Default to today
            r'\bwho.*absent\b',  # General who absent query
            r'\bshow.*absent\b',
            r'\blist.*absent\b',
            r'\bget.*absent\b',
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in today_patterns)

    def _extract_month_query(self, message: str) -> Optional[IntentResult]:
        """Extract month-based queries."""
        # Check for "this month" or "current month"
        if re.search(r'\bthis month\b|\bcurrent month\b', message, re.IGNORECASE):
            return IntentResult(
                intent_type=IntentType.QUERY_ABSENCE_MONTH,
                confidence=0.9,
                extracted_data={'month': 'current', 'year': datetime.now().year},
                suggested_response="Let me get the absence records for this month.",
                action_type="query_absence_month"
            )
        
        # Check for specific months
        for month in self.months:
            if month in message.lower():
                year = self._extract_year_from_message(message) or datetime.now().year
                return IntentResult(
                    intent_type=IntentType.QUERY_ABSENCE_SPECIFIC_MONTH,
                    confidence=0.85,
                    extracted_data={'month': month, 'year': year},
                    suggested_response=f"Let me get the absence records for {month.title()} {year}.",
                    action_type="query_absence_specific_month"
                )
        
        return None

    def _extract_week_query(self, message: str) -> Optional[IntentResult]:
        """Extract week-based queries."""
        message_lower = message.lower()
        
        # Explicit week patterns with absence context
        week_absence_patterns = [
            (r'\bwho\s+is\s+absent\s+this\s+week\b', 'this_week'),
            (r'\bwho\s+is\s+absent\s+next\s+week\b', 'next_week'),
            (r'\bwho\s+is\s+absent\s+(?:previous|last)\s+week\b', 'last_week'),
            (r'\babsent\s+this\s+week\b', 'this_week'),
            (r'\babsent\s+next\s+week\b', 'next_week'),
            (r'\babsent\s+(?:previous|last)\s+week\b', 'last_week'),
        ]
        
        for pattern, week_type in week_absence_patterns:
            if re.search(pattern, message_lower):
                return IntentResult(
                    intent_type=IntentType.QUERY_ABSENCE_WEEK,
                    confidence=0.95,
                    extracted_data={'week_type': week_type},
                    suggested_response=f"Let me check who is absent {week_type.replace('_', ' ')}.",
                    action_type="query_absence_week"
                )
        
        return None

    def _extract_date_range_query(self, message: str) -> Optional[IntentResult]:
        """Extract date range queries."""
        message_lower = message.lower()
        
        # Explicit "between X and Y" patterns with absence context
        between_absence_patterns = [
            r'\bwho\s+is\s+absent\s+between\b.*\band\b',
            r'\babsent\s+between\b.*\band\b',
            r'\bget.*absent.*between\b.*\band\b',
            r'\bshow.*absent.*between\b.*\band\b',
        ]
        
        for pattern in between_absence_patterns:
            if re.search(pattern, message_lower):
                # Try to extract month and day information
                month_matches = []
                for month in self.months:
                    if month in message_lower:
                        month_matches.append(month)
                
                # Look for day numbers
                day_matches = re.findall(r'\b\d{1,2}\b', message)
                
                # Try to extract actual dates
                date_matches = re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b', message)
                
                return IntentResult(
                    intent_type=IntentType.QUERY_ABSENCE_DATE_RANGE,
                    confidence=0.95,
                    extracted_data={
                        'date_range': date_matches if len(date_matches) >= 2 else None,
                        'month_range': month_matches if len(month_matches) >= 1 else None,
                        'day_range': day_matches if len(day_matches) >= 2 else None,
                        'raw_query': message
                    },
                    suggested_response="Let me check absences for the specified date range.",
                    action_type="query_absence_date_range"
                )
        
        return None

    def _matches_vacation_query(self, message: str) -> bool:
        """Check if message matches vacation query patterns."""
        vacation_patterns = [
            r'\bwho.*vacation\b',
            r'\bwho.*on vacation\b',
            r'\bwho are.*vacation\b',
            r'\bwho.*leave\b',
            r'\bwho.*on leave\b',
            r'\bshow.*vacation\b',
            r'\blist.*vacation\b',
            r'\bget.*vacation\b',
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in vacation_patterns)

    def _extract_specific_employee_check(self, message: str, employee_name: Optional[str]) -> Optional[IntentResult]:
        """Extract specific employee day checks."""
        # Check for "is [name] on leave" patterns first (higher priority)
        leave_patterns = [
            r'\bis\s+(\w+)\s+on\s+leave\b',
            r'\bis\s+(\w+)\s+on\s+vacation\b',
        ]
        
        for pattern in leave_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                emp_name = match.group(1)
                return IntentResult(
                    intent_type=IntentType.CHECK_EMPLOYEE_LEAVE,
                    confidence=0.9,
                    extracted_data={'employee_name': emp_name, 'query_type': 'leave'},
                    suggested_response=f"Let me check if {emp_name} is on leave.",
                    action_type="check_employee_leave"
                )
        
        # Check for "is [name] absent" patterns
        absent_check_patterns = [
            r'\bis\s+(\w+)\s+absent\s+(today|tomorrow|yesterday)\b',
            r'\bis\s+(\w+)\s+absent\b',  # Default to today
        ]
        
        for pattern in absent_check_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                emp_name = match.group(1)
                day = match.group(2) if len(match.groups()) > 1 else 'today'
                
                return IntentResult(
                    intent_type=IntentType.CHECK_EMPLOYEE_SPECIFIC_DAY,
                    confidence=0.85,
                    extracted_data={'employee_name': emp_name, 'day': day},
                    suggested_response=f"Let me check if {emp_name} is absent {day}.",
                    action_type="check_employee_specific_day"
                )
        
        # Fallback to original logic if employee_name was extracted
        if not employee_name:
            return None
        
        day_patterns = {
            'today': r'\btoday\b',
            'tomorrow': r'\btomorrow\b',
            'yesterday': r'\byesterday\b',
        }
        
        for day, pattern in day_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return IntentResult(
                    intent_type=IntentType.CHECK_EMPLOYEE_SPECIFIC_DAY,
                    confidence=0.85,
                    extracted_data={'employee_name': employee_name, 'day': day},
                    suggested_response=f"Let me check if {employee_name} is absent {day}.",
                    action_type="check_employee_specific_day"
                )
        
        return None

    def _classify_general_intent(self, message: str) -> Optional[IntentResult]:
        """Classify general intents like greetings, help requests."""
        # Greetings
        greeting_patterns = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        if any(greeting in message for greeting in greeting_patterns):
            return IntentResult(
                intent_type=IntentType.GREETING,
                confidence=0.9,
                extracted_data={},
                suggested_response="Hello! I can help you with absence management and SOW generation. What would you like to do?",
                action_type="greeting"
            )
        
        # Help requests
        help_patterns = ['help', 'what can you do', 'capabilities', 'options', 'menu']
        if any(help_word in message for help_word in help_patterns):
            return IntentResult(
                intent_type=IntentType.HELP,
                confidence=0.9,
                extracted_data={},
                suggested_response="I can help you with absence management (tracking employee attendance) and SOW generation (creating Statement of Work documents). What would you like to work on?",
                action_type="help"
            )
        
        return None

    def _create_fallback_response(self, message: str) -> IntentResult:
        """Create fallback response for unrecognized intents."""
        return IntentResult(
            intent_type=IntentType.CONFUSED_REQUEST,
            confidence=0.3,
            extracted_data={'original_message': message},
            suggested_response="I'm not sure how to help with that. I can assist with absence management or SOW generation. Could you please clarify what you need?",
            action_type="clarification_needed",
            disambiguation_needed=True,
            disambiguation_options=["Absence Management", "SOW Generation"]
        )

    def _extract_employee_name(self, message: str) -> Optional[str]:
        """Extract employee name from message using basic patterns."""
        # Skip if it's a query (starts with who, what, etc.)
        if re.match(r'\b(who|what|which|show|get|list)\b', message, re.IGNORECASE):
            return None
            
        # Look for "mark [name]" or "[name] is absent" patterns
        mark_pattern = r'\bmark\s+([\w\-]+)'
        name_match = re.search(mark_pattern, message, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            if candidate.lower() not in self.generic_employee_tokens:
                return candidate
       
        # Look for "[name] absent" or "[name] is absent" but not "who is absent"
        absent_pattern = r'(?<!who\s)(?<!what\s)([\w\-]+)\s+(?:is\s+)?absent'
        name_match = re.search(absent_pattern, message, re.IGNORECASE)
        if name_match and name_match.group(1).lower() not in ['who', 'what', 'which']:
            candidate = name_match.group(1).strip()
            if candidate.lower() not in self.generic_employee_tokens:
                return candidate
       
        return None

    def _extract_date_from_message(self, message: str) -> str:
        """Extract date from message, defaulting to today."""
        if 'today' in message.lower():
            return 'today'
        elif 'tomorrow' in message.lower():
            return 'tomorrow'
        elif 'yesterday' in message.lower():
            return 'yesterday'
        else:
            return 'today'  # Default

    def _extract_year_from_message(self, message: str) -> Optional[int]:
        """Extract year from message."""
        year_match = re.search(r'\b(20\d{2})\b', message)
        if year_match:
            return int(year_match.group(1))
        return None

# Global instance
intent_classifier = AdvancedIntentClassifier()
