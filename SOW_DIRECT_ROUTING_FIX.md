# SOW Direct Routing Fix - CRITICAL BUG FIXED

## Problem Identified
The SOW system was not working because **direct routing was not being called**. The system was going straight to Gemini AI instead of checking for SOW keywords first.

## Root Cause
In `main.py`, the `_maybe_route_without_llm()` function existed but was **never being called**. This function is responsible for:
- Detecting SOW keywords ("statement of work", "create a sow", etc.)
- Directly routing to `start_sow_session` without AI processing
- Bypassing Gemini for known intents

## The Fix
Added the missing direct routing call in the main chat handler:

```python
# Check for direct routing first (SOW, absence keywords)
direct_call = _maybe_route_without_llm(session, user_message)
if direct_call:
    tool_calls = [direct_call]
else:
    try:
        raw_response = gemini_client.generate(session, user_message, context=context)
        parsed = gemini_client.parse_response(raw_response)
        tool_calls = parsed.get("tool_calls", [])
```

## How It Works Now

### 1. **Direct Intent Detection**
When you say: `"I need to create a Statement of Work"`
- System immediately detects SOW keywords
- Calls `start_sow_session` directly
- No AI processing for intent detection

### 2. **SOW Session Starts**
- Initializes SOW conversation mode
- Sets `session.active_domain = "sow"`
- Shows first question: project basics

### 3. **Direct Data Collection**
- Takes whatever input you provide
- Stores it directly without AI validation
- Moves to next question immediately
- No "I need more information" responses

### 4. **AI Only at the End**
- AI processing only happens for final document generation
- Uses the proven new_sow system for document creation

## Keywords That Trigger SOW Mode
- "statement of work"
- "create a sow" 
- Messages starting with "sow"
- " need a sow"

## Testing
```bash
✅ Direct routing: Detects SOW intent immediately
✅ Session start: Initializes SOW conversation properly  
✅ Data collection: Accepts input without validation
✅ Document generation: Ready for final processing
```

## Impact
- **Before**: SOW requests went to general guidance instead of SOW mode
- **After**: SOW requests immediately start SOW conversation
- **Result**: SOW system now works as intended - direct data collection without AI interference

The critical missing piece has been fixed. SOW mode will now activate immediately when you request it.