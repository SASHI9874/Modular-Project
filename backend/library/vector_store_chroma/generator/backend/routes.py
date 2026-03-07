from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core import service

router = APIRouter()

class VectorRequest(BaseModel):
    file_text: Optional[str] = None
    query: Optional[str] = None

@router.post("/process")
async def process_endpoint(req: VectorRequest):
    """
    Endpoint for the Generated App.
    Accepts text to index, OR a query to search.
    """
    try:
        result = service.process(req.file_text, req.query)
        return {"context": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))