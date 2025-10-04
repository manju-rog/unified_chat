"""
Integration tests for end-to-end wiring verification.
Tests the complete flow from orchestrator through Gemini to tools.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from app.orchestrator import orchestrate
from app.session_manager import get_session, clear_session
from app.models import ChatResponse


class TestIntegrationWiring:
    """Test suite for verifying all components are wired together correctly."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_creates_session(self):
        """Verify orchestrator creates session if not exists."""
        session_id = "test_session_1"
        
        # Clear any existing session
        clear_session(session_id)
        
        response = await orchestrate(
            user_msg="Hello",
            session_id=session_id
        )
        
        # Verify response structure
        assert isinstance(response, ChatResponse)
        assert response.mode in ["IDLE", "ABSENCE", "SOW"]
        assert response.message_to_user is not None
        
        # Verify session was created
        session = get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_absence(self):
        """Verify orchestrator routes absence-related messages correctly."""
        session_id = "test_session_2"
        
        response = await orchestrate(
            user_msg="mark manju absent today",
            session_id=session_id
        )
        
        # Verify routing to ABSENCE mode
        assert response.mode == "ABSENCE"
        assert response.message_to_user is not None
        
        # Verify session state updated
        session = get_session(session_id)
        assert session.mode == "ABSENCE"
    
    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_sow(self):
        """Verify orchestrator routes SOW-related messages correctly."""
        session_id = "test_session_3"
        
        response = await orchestrate(
            user_msg="generate sow for Predictive Maintenance",
            session_id=session_id
        )
        
        # Verify routing to SOW mode
        assert response.mode == "SOW"
        assert response.message_to_user is not None
        
        # Verify session state updated
        session = get_session(session_id)
        assert session.mode == "SOW"
    
    @pytest.mark.asyncio
    async def test_orchestrator_maintains_mode(self):
        """Verify orchestrator maintains mode across turns."""
        session_id = "test_session_4"
        
        # First message - enter SOW mode
        response1 = await orchestrate(
            user_msg="start sow for Test Project",
            session_id=session_id
        )
        assert response1.mode == "SOW"
        
        # Second message - should stay in SOW mode
        response2 = await orchestrate(
            user_msg="the oracle rep is John Doe",
            session_id=session_id
        )
        assert response2.mode == "SOW"
        
        # Verify session maintained mode
        session = get_session(session_id)
        assert session.mode == "SOW"
    
    @pytest.mark.asyncio
    async def test_orchestrator_handles_out_of_scope(self):
        """Verify orchestrator refuses out-of-scope requests."""
        session_id = "test_session_5"
        
        response = await orchestrate(
            user_msg="what's the weather today?",
            session_id=session_id
        )
        
        # Should stay in IDLE and refuse
        assert response.mode == "IDLE"
        assert "sorry" in response.message_to_user.lower() or "help" in response.message_to_user.lower()
    
    @pytest.mark.asyncio
    async def test_session_state_flow(self):
        """Verify session state flows through entire stack."""
        session_id = "test_session_6"
        
        # Clear session
        clear_session(session_id)
        
        # First turn
        response1 = await orchestrate(
            user_msg="mark john absent today",
            session_id=session_id
        )
        
        session = get_session(session_id)
        assert len(session.conversation_history) >= 1
        
        # Second turn
        response2 = await orchestrate(
            user_msg="mark sarah present today",
            session_id=session_id
        )
        
        session = get_session(session_id)
        # Should have accumulated conversation history
        assert len(session.conversation_history) >= 2
    
    @pytest.mark.asyncio
    async def test_tool_execution_in_orchestrator(self):
        """Verify orchestrator executes tools when Gemini requests them."""
        session_id = "test_session_7"
        
        response = await orchestrate(
            user_msg="mark employee123 absent on 2025-10-05",
            session_id=session_id
        )
        
        # If Gemini decided to call a tool, verify it was executed
        # (This depends on Gemini's decision, so we check conditionally)
        if response.tool_call:
            assert response.tool_call.get("name") in ["mark_absent", "mark_present", "get_absence_status"]
            # Message should reflect tool execution
            assert response.message_to_user is not None


class TestAbsenceFlowIntegration:
    """Test suite for Absence flow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_mark_absent_flow(self):
        """Test complete flow for marking employee absent."""
        session_id = "test_absence_1"
        
        response = await orchestrate(
            user_msg="mark manju absent today because of sick leave",
            session_id=session_id
        )
        
        # Verify response
        assert response.mode == "ABSENCE"
        assert response.message_to_user is not None
        
        # If tool was called, verify it's the right one
        if response.tool_call:
            assert response.tool_call.get("name") == "mark_absent"


class TestSOWFlowIntegration:
    """Test suite for SOW flow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_sow_start_flow(self):
        """Test SOW initiation flow."""
        session_id = "test_sow_1"
        
        response = await orchestrate(
            user_msg="generate sow for Predictive Maintenance System",
            session_id=session_id
        )
        
        # Verify SOW mode activated
        assert response.mode == "SOW"
        assert response.message_to_user is not None
        
        # If tool was called, verify it's start_sow
        if response.tool_call:
            assert response.tool_call.get("name") == "start_sow"


class TestOutOfScopeHandling:
    """Test suite for out-of-scope request handling."""
    
    @pytest.mark.asyncio
    async def test_weather_request_refused(self):
        """Test that weather requests are politely refused."""
        session_id = "test_oos_1"
        
        response = await orchestrate(
            user_msg="what's the weather?",
            session_id=session_id
        )
        
        # Should stay in IDLE
        assert response.mode == "IDLE"
        
        # Should contain refusal message
        message_lower = response.message_to_user.lower()
        assert any(word in message_lower for word in ["sorry", "can't", "cannot", "help", "only"])
    
    @pytest.mark.asyncio
    async def test_general_question_refused(self):
        """Test that general questions are politely refused."""
        session_id = "test_oos_2"
        
        response = await orchestrate(
            user_msg="tell me a joke",
            session_id=session_id
        )
        
        # Should stay in IDLE
        assert response.mode == "IDLE"
        
        # Should contain refusal or clarification
        assert response.message_to_user is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
