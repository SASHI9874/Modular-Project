from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from typing import Dict

# CRITICAL: Relative import. 
# When generated, this file sits next to 'service.py' in the 'features/pdf_loader' folder.
from . import service 

router = APIRouter()

@router.post("/upload")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    """
    Production Endpoint: Receives file, runs core logic, saves to Session.
    """
    content = await file.read()
    
    # 1. Run Core Logic
    result = service.extract_text_from_bytes(content, file.filename)
    
    # 2. Handle State (Session Scope)
    # The Generator will have scaffolded a 'request.session' object (via Middleware)
    # We store the result there so subsequent steps (like LLM) can access it.
    if "file_text" in result:
        request.session["pdf_loader_text"] = result["file_text"]
        request.session["pdf_loader_filename"] = result["filename"]
    
    return {"status": "success", "filename": result["filename"], "preview": result["file_text"][:50]}