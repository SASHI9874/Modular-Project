import os
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
from app.schemas.payload import BuildRequest 
from app.services.builder.service import BuilderService

router = APIRouter()

@router.post("/download/wheel")
def generate_wheel(request: BuildRequest):
    try:
        if not request.features:
            raise HTTPException(status_code=400, detail="No features selected")

        # 1. Instantiate the Service
        builder = BuilderService()

        # 2. Call the new method (returns the file path string)
        wheel_path = builder.build_wheel(request.features)

        # 3. Validation (Good practice for enterprise code)
        if not os.path.exists(wheel_path):
            raise HTTPException(status_code=500, detail="Build failed: Output file not found")

        filename = os.path.basename(wheel_path)
        
        # 4. Return the file
        return FileResponse(
            path=wheel_path, 
            filename=filename, 
            media_type="application/octet-stream"
        )
    except Exception as e:
        # In production, log 'e' here before raising
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download/zip")
def generate_zip(request: BuildRequest):
    try:
        if not request.features:
            raise HTTPException(status_code=400, detail="No features selected")

        # 1. Instantiate the Service
        builder = BuilderService()

        # 2. Call the new method
        zip_path = builder.build_standalone_zip(request.features)
        
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=500, detail="Build failed: Output file not found")

        filename = os.path.basename(zip_path)
        
        # 4. Return the file
        return FileResponse(
            path=zip_path, 
            filename=filename, 
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wheels", response_model=List[str])
def list_available_wheels():
    """Returns a list of generated .whl files from the server."""
    if not settings.OUTPUT_DIR.exists():
        return []
    
    # Return only .whl files
    return [f.name for f in settings.OUTPUT_DIR.glob("*.whl")]

