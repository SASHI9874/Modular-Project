import shutil
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.workflow_runner import WorkflowRunner
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

router = APIRouter()
runner = WorkflowRunner()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_UPLOAD_DIR = BASE_DIR / "temp_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

class WorkflowRequest(BaseModel):
    graph: Dict[str, Any]
    requirements: List[str] = []

@router.post("/run")
async def run_workflow(request: WorkflowRequest):
    """
    Starts a new workflow session locally.
    """
    try:
        result = runner.start_workflow(request.graph, request.requirements)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume")
async def resume_workflow(
    session_id: str = Form(...),
    node_id: str = Form(...),
    # We accept EITHER a text string OR a binary file blob
    text_input: Optional[str] = Form(None), 
    file_input: Optional[UploadFile] = File(None) 
):
    """
    Resumes execution. 
    - Saves uploaded files to 'backend/temp_uploads/{session_id}/'
    """
    try:
        if session_id not in runner.sessions:
            raise HTTPException(status_code=404, detail="Session expired or not found")

        final_input_data = None

        # A. HANDLE BINARY BLOB (File Upload)
        if file_input:
            # 1. Create a folder for this session to keep things organized
            session_upload_dir = TEMP_UPLOAD_DIR / session_id
            session_upload_dir.mkdir(exist_ok=True)
            
            # 2. Define Path
            filename = file_input.filename or "uploaded_file.bin"
            file_path = session_upload_dir / filename
            
            # 3. Save File
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file_input.file, buffer)
            
            # 4. Pass Absolute Path to the Runner
            final_input_data = str(file_path.absolute())

        elif text_input is not None:
            import json
            try:
                final_input_data = json.loads(text_input)
            except (json.JSONDecodeError, TypeError):
                final_input_data = text_input

        # Resume the Orchestrator
        result = runner.resume_workflow(session_id, node_id, final_input_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def cancel_session(session_id: str):
    """
    Cleanup endpoint: If user closes the tab or clicks 'Stop'.
    """
    try:
        # 1. Remove from Memory
        if session_id in runner.sessions:
            del runner.sessions[session_id]
        
        # 2. Cleanup Uploads
        session_upload_dir = TEMP_UPLOAD_DIR / session_id
        if session_upload_dir.exists():
            shutil.rmtree(session_upload_dir)

        return {"status": "cancelled"}
    except Exception as e:
        return {"status": "cancelled", "note": str(e)}