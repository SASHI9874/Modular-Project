from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from . import service

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = ""

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Standard Sync Endpoint"""
    answer = service.chat(req.prompt, req.context)
    return {"response": answer}

@router.post("/stream")
async def stream_endpoint(req: ChatRequest):
    """
    Streaming Endpoint.
    Returns Server-Sent Events (SSE) style stream.
    """
    def event_stream():
        # Iterate over the generator
        for token in service.stream_chat(req.prompt, req.context):
            # Check for error prefix
            if token.startswith("[ERROR:"):
                 yield token # Send error as text
                 break
            yield token

    # Return a StreamingResponse with media_type="text/event-stream"
    return StreamingResponse(event_stream(), media_type="text/event-stream")