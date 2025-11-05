from fastapi import WebSocket, WebSocketDisconnect
import logging
import json
from app.agents.orchestrator import OrchestratorAgent
from app.agents.data_collector import DataCollectorAgent
from app.models.sow_models import ConversationStage

logger = logging.getLogger(__name__)

# Initialize agents
orchestrator = OrchestratorAgent()
data_collector = DataCollectorAgent()

async def websocket_handler(websocket: WebSocket, session_id: str):
    """WebSocket handler for real-time conversation"""
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        # Send initial greeting
        initial_message = data_collector.get_initial_message()
        await websocket.send_json({
            "role": "assistant",
            "message": initial_message,
            "stage": ConversationStage.INITIAL.value,
            "progress": 0.0,
            "requires_input": True
        })
        
        # Main conversation loop
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if not user_message:
                    await websocket.send_json({
                        "role": "assistant",
                        "message": "Please provide a message.",
                        "error": True
                    })
                    continue
                
                bot_response = await orchestrator.handle_message(session_id, user_message)
                
                await websocket.send_json({
                    "role": "assistant",
                    "message": bot_response.message,
                    "stage": bot_response.stage.value,
                    "progress": bot_response.progress,
                    "is_complete": bot_response.is_complete,
                    "requires_input": bot_response.requires_input
                })
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from client")
                await websocket.send_json({
                    "role": "assistant",
                    "message": "Invalid message format. Please send valid JSON.",
                    "error": True
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "role": "assistant",
                    "message": "An error occurred while processing your message. Please try again.",
                    "error": True
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {e}")
        try:
            await websocket.close()
        except:
            pass
