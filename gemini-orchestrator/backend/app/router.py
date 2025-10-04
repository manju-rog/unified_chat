"""Domain router for intent detection and routing."""
from typing import Literal

# Domain constants
IDLE = "IDLE"
ABSENCE = "ABSENCE"
SOW = "SOW"

# Keyword sets for domain detection
ABSENCE_KEYWORDS = {
    "absent", "absence", "absences",
    "present", "presence",
    "leave", "leaves",
    "sick", "sickness",
    "pto", "time off",
    "attendance",
    "vacation",
    "off work"
}

SOW_KEYWORDS = {
    "sow", "statement of work",
    "deliverable", "deliverables",
    "milestone", "milestones",
    "acceptance", "acceptance criteria",
    "project", "services",
    "generate sow", "create sow",
    "oracle rep", "billing contact"
}


def route_intent(
    user_text: str,
    current_mode: str = IDLE
) -> Literal["IDLE", "ABSENCE", "SOW"]:
    """
    Determine which domain (ABSENCE/SOW/IDLE) a message belongs to.
    
    Args:
        user_text: The user's message text
        current_mode: The current session mode (IDLE, ABSENCE, or SOW)
    
    Returns:
        Domain string: IDLE, ABSENCE, or SOW
    
    Logic:
        1. Check for absence keywords
        2. Check for SOW keywords
        3. If in active mode (ABSENCE/SOW), maintain unless explicit switch
        4. Default to IDLE if no match
    """
    # Normalize text for matching
    text_lower = user_text.lower()
    
    # Check for explicit exit/cancel commands
    exit_keywords = {"exit", "cancel", "quit", "stop", "finish", "done"}
    if any(keyword in text_lower for keyword in exit_keywords):
        # If user wants to exit, return to IDLE
        return IDLE
    
    # Check for absence keywords
    has_absence_keywords = any(keyword in text_lower for keyword in ABSENCE_KEYWORDS)
    
    # Check for SOW keywords
    has_sow_keywords = any(keyword in text_lower for keyword in SOW_KEYWORDS)
    
    # Mode persistence logic: maintain current mode unless user explicitly changes domain
    if current_mode == ABSENCE:
        # Stay in ABSENCE mode unless SOW keywords are detected
        if has_sow_keywords and not has_absence_keywords:
            return SOW
        return ABSENCE
    
    if current_mode == SOW:
        # Stay in SOW mode unless absence keywords are detected
        if has_absence_keywords and not has_sow_keywords:
            return ABSENCE
        return SOW
    
    # If in IDLE mode, route based on keywords
    if has_absence_keywords and not has_sow_keywords:
        return ABSENCE
    
    if has_sow_keywords and not has_absence_keywords:
        return SOW
    
    # If both or neither keywords detected, stay in current mode
    if has_absence_keywords and has_sow_keywords:
        # Ambiguous - maintain current mode
        return current_mode
    
    # Default to IDLE
    return IDLE
