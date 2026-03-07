from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...core import service

router = APIRouter()


class CalculateRequest(BaseModel):
    expression: str


@router.post("/calculate")
async def calculate_endpoint(req: CalculateRequest):
    """Calculate mathematical expression"""
    try:
        result = service.calculate(req.expression)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))