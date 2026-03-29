from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from . import service  # Your core LLM/Agent logic

router = APIRouter()

# --- Standard HTTP Routes (Kept for external API usage) ---

class ChatRequest(BaseModel):
    prompt: str
    context: Optional[dict] = None

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Standard Sync Endpoint"""
    answer = service.chat(req.prompt, req.context)
    return {"response": answer}

@router.post("/stream")
async def stream_endpoint(req: ChatRequest):
    """Streaming Endpoint (SSE)"""
    def event_stream():
        for token in service.stream_chat(req.prompt, req.context):
            if token.startswith("[ERROR:"):
                yield token
                break
            yield token
    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- The Agentic WebSocket Route (For VS Code) ---

@router.websocket("/ws/vscode")
async def vscode_websocket_endpoint(websocket: WebSocket):
    """
    Bidirectional WebSocket endpoint for the VS Code extension.
    Handles streaming chat, autocomplete, and tool execution loops.
    """
    await websocket.accept()
    print(" VS Code Extension connected")
    
    # Optional: If you are handling high-throughput queues elsewhere in your architecture,
    # you might want to register this connection state in a session manager here.

    try:
        while True:
            # 1. Wait for incoming messages from VS Code
            data = await websocket.receive_text()
            payload = json.loads(data)
            msg_type = payload.get("type")

            # 2. Route the message based on the protocol we defined in TypeScript
            if msg_type == 'user_message':
                # Trigger the main agent chat stream
                await handle_vscode_chat(websocket, payload)
                
            elif msg_type == 'autocomplete_request':
                # Trigger the fast ghost-text completion
                await handle_vscode_autocomplete(websocket, payload)
                
            elif msg_type == 'tool_response':
                # VS Code has successfully executed a local file operation.
                # Pass this data back into your agent's execution loop.
                await handle_tool_callback(websocket, payload)
                
            else:
                print(f" Unknown message type received: {msg_type}")

    except WebSocketDisconnect:
        print(" VS Code Extension disconnected")
    except Exception as e:
        print(f" WebSocket Error: {str(e)}")
        await websocket.send_json({"type": "error", "content": "Internal Server Error"})


# --- WebSocket Handlers ---

async def handle_vscode_chat(websocket: WebSocket, payload: dict):
    """Handles the main chat interface and streams responses chunk by chunk."""
    prompt = payload.get("message", "")
    context = payload.get("context", {})
    
    print(f"Processing chat for file: {context.get('file_path')}")

    try:
        # Example of how to structure your async generator from your service layer.
        # This allows you to stream Azure OpenAI chunks directly to the UI.
        full_response = ""
        
        # NOTE: service.stream_agent_response must be an async generator yielding text chunks
        async for chunk in service.stream_agent_response(prompt, context):
            full_response += chunk
            
            # Send the typing effect to VS Code
            await websocket.send_json({
                "type": "stream_chunk",
                "content": chunk
            })
            
            # Small sleep to yield control back to the event loop
            await asyncio.sleep(0.01)

        # Signal that the stream is done
        await websocket.send_json({"type": "stream_end"})
        
        # Send the final aggregated response so VS Code can save it to workspace history
        await websocket.send_json({
            "type": "agent_response",
            "content": full_response
        })

    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})


async def handle_vscode_autocomplete(websocket: WebSocket, payload: dict):
    """Handles Ghost Text requests. Needs to be extremely fast."""
    req_id = payload.get("id")
    context = payload.get("context", {})
    prefix = context.get("prefix", "")
    suffix = context.get("suffix", "")

    try:
        # Pass to your LLM specifically tuned for Fill-in-the-Middle (FIM) tasks
        suggestion = await service.generate_autocomplete(prefix, suffix)
        
        # Respond with the exact ID requested so VS Code can match the promise
        if suggestion:
            await websocket.send_json({
                "type": "autocomplete_response",
                "id": req_id,
                "content": suggestion
            })
    except Exception as e:
        print(f"Autocomplete failed: {str(e)}")
        # Send empty response on failure to unblock the VS Code promise
        await websocket.send_json({"type": "autocomplete_response", "id": req_id, "content": ""})


async def handle_tool_callback(websocket: WebSocket, payload: dict):
    """
    When the agent asks VS Code to read/edit a file, VS Code replies with a tool_response.
    You need to wake up your paused agent loop and feed it this result.
    """
    req_id = payload.get("id")
    content = payload.get("content")
    error = payload.get("error")

    print(f"Received tool response for {req_id}. Error: {error}")
    
    # Route this back to the specific agent execution thread that requested it
    # await service.resume_agent_loop(req_id, content, error)