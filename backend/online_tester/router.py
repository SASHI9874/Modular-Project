from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from .executor import VenvExecutor
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
import os
from pathlib import Path

# Define paths (Ensure these match your project structure)
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_WHEELS_DIR = BASE_DIR / "output_wheels"

router = APIRouter(prefix="/test-runner", tags=["Online Tester"])
executor = VenvExecutor()
thread_pool = ThreadPoolExecutor(max_workers=5)

class Submission(BaseModel):
    code: str
    requirements: list[str] = []

@router.post("/run")
async def run_code(submission: Submission):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        thread_pool, 
        executor.execute, 
        submission.code, 
        submission.requirements
    )
    return result

@router.post("/run-wheel")
async def run_wheel(
    code: str = Form(...),
    file: UploadFile = File(None),       # Case A: User uploads a file
    existing_wheel: str = Form(None)     # Case B: User selects a generated file
):
    """
    Installs a wheel and runs code against it.
    """
    temp_wheel_path = None
    
    try:
        # 1. Resolve the Wheel File
        if file:
            # Save uploaded file temporarily so the thread can access it
            temp_dir = BASE_DIR / "temp_uploads"
            temp_dir.mkdir(exist_ok=True)
            temp_wheel_path = temp_dir / file.filename
            
            with open(temp_wheel_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
        elif existing_wheel:
            # Look for the file in your output folder
            source_path = OUTPUT_WHEELS_DIR / existing_wheel
            if not source_path.exists():
                return {"error": "Selected wheel file not found on server"}
            temp_wheel_path = source_path
            
        else:
            return {"error": "No wheel provided. Upload a file or select an existing one."}

        # 2. Run in Executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool, 
            executor.execute_with_wheel, 
            code, 
            temp_wheel_path
        )
        
        return result

    except Exception as e:
        return {"error": str(e)}
        
    finally:
        # Cleanup uploaded temp file if we created one (but NOT the existing generated wheel)
        if file and temp_wheel_path and temp_wheel_path.exists():
            os.remove(temp_wheel_path)