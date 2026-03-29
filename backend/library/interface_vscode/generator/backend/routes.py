from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

router = APIRouter()


class VSCodeMessage(BaseModel):
    type: str
    message: Optional[str] = None
    file_path: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    selection: Optional[str] = None


@router.websocket("/ws/vscode")
async def vscode_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for VS Code extension
    Handles bidirectional communication
    """
    await websocket.accept()
    print(" VS Code extension connected")
    
    try:
        while True:
            # Receive message from VS Code
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            print(f"📨 Received from VS Code: {message_data.get('type')}")
            
            # In generated app, this will trigger agent execution
            # For now, just echo back
            response = {
                "type": "agent_response",
                "content": f"Echo: {message_data.get('message', '')}",
                "suggestions": []
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        print(" VS Code extension disconnected")


@router.get("/vscode/status")
async def vscode_status():
    """Health check for VS Code interface"""
    return {
        "status": "running",
        "interface": "vscode",
        "websocket_url": "ws://localhost:8000/api/interface-vscode/ws/vscode"
    }