from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json

router = APIRouter()


# WebSocket endpoint for CLI to connect to
@router.websocket("/ws/cli")
async def cli_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for CLI interface
    Handles bidirectional communication with terminal
    """
    await websocket.accept()
    print("✅ CLI interface connected")
    
    try:
        while True:
            # Receive message from CLI
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            print(f"📨 Received from CLI: {message_data}")
            
            # In generated app, this will trigger agent execution
            # For now, just echo back
            response = {
                "type": "agent_response",
                "content": f"Echo: {message_data.get('message', '')}"
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        print("❌ CLI interface disconnected")


@router.get("/cli/status")
async def cli_status():
    """Health check for CLI interface"""
    return {
        "status": "running",
        "interface": "cli",
        "websocket_url": "ws://localhost:8000/api/interface-cli/ws/cli"
    }