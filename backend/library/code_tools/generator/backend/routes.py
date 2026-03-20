from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...core import service

router = APIRouter()


class CodeToolsRequest(BaseModel):
    operation: str
    path: Optional[str] = None
    content: Optional[str] = None
    query: Optional[str] = None
    command: Optional[str] = None


@router.post("/execute")
async def execute_code_tool(req: CodeToolsRequest):
    """Execute code tool operation"""
    try:
        code_service = service.CodeToolsService()
        
        result = code_service.execute(
            operation=req.operation,
            path=req.path,
            content=req.content,
            query=req.query,
            command=req.command
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace")
async def get_workspace():
    """Get workspace info"""
    code_service = service.CodeToolsService()
    return {
        "workspace_root": str(code_service.workspace_root),
        "max_file_size": code_service.max_file_size
    }