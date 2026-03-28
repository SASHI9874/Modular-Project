import uuid
import json
import logging
import asyncio
from typing import Any, Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.entities.user_entity import User
from app.api.deps import get_db, get_current_user
from app.entities.project_entity import ProjectEntity
from app.services.executor_service import GraphExecutor
from app.services.compiler.compiler_service import GraphCompiler
from app.schemas.project_schema import ProjectCreate, RunPayload
from app.services.packager.packager_service import PackagerService

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a new project with its graph."""
    new_project = ProjectEntity(
        name=project_in.name,
        owner_id=current_user.id,
        graph_json=project_in.graph
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {"id": new_project.id, "msg": "Project saved successfully"}

@router.get("/")
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(ProjectEntity).filter(ProjectEntity.owner_id == current_user.id).all()

@router.post("/{project_id}/run")
def run_project(
    project_id: int,
    payload: RunPayload, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Load project -> Seed Graph Memory -> Execute Graph -> Return Results"""
    project = db.query(ProjectEntity).filter(
        ProjectEntity.id == project_id,
        ProjectEntity.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        executor = GraphExecutor(project.graph_json)
        # Pass the frontend's injected data to the executor
        results = executor.run(
            entry_node_id=payload.entry_node_id, 
            initial_inputs=payload.inputs
        )
        # ---  Look for the clean output! ---
        clean_output = None
        for node_id, data in results.items():
            if isinstance(data, dict) and data.get("is_final_output"):
                clean_output = data.get("final_text")
                break
        
        # If we found an Output Node, send the clean text back alongside the debug data
        if clean_output:
            return {
                "status": "success", 
                "clean_output": clean_output, 
                "debug": results
            }
            
        # Fallback if didn't connect an Output node on the canvas
        return {"status": "success", "results": results}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/compile", response_class=PlainTextResponse)
def compile_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the generated Python code for the project."""
    project = db.query(ProjectEntity).filter(
        ProjectEntity.id == project_id,
        ProjectEntity.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        compiler = GraphCompiler(project.graph_json)
        code = compiler.compile()
        return code
    except Exception as e:
        logging.exception("Exception occurred")
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/{project_id}/download")
def download_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a full-stack AI application ZIP for the given project."""
    project = db.query(ProjectEntity).filter(
        ProjectEntity.id == project_id,
        ProjectEntity.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        packager = PackagerService(project.graph_json, project.name)
        zip_bytes = packager.create_package()
        # zip_bytes = packager.create_package_streaming()
        
        filename = f"{project.name.replace(' ', '_')}_App.zip"

        response = Response(
            content=zip_bytes,
            media_type="application/zip",
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        print(f"Export Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")



# In-memory storage for completed downloads
pending_downloads: Dict[str, bytes] = {}


class DownloadRequest(BaseModel):
    graph: Dict[str, Any]
    project_name: str


@router.post("/download")
async def download_app(request: DownloadRequest):
    """
    Traditional synchronous download (no progress)
    """
    try:
        from app.services.packager.packager_service import PackagerServiceV2
        
        packager = PackagerServiceV2(
            graph_data=request.graph,
            project_name=request.project_name
        )
        
        zip_bytes = packager.create_package()
        
        filename = f"{request.project_name.replace(' ', '-').lower()}.zip"
        
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/download/stream")
async def download_with_progress(request: DownloadRequest):
    """
    Download with Server-Sent Events (SSE) progress updates
    
    Client receives events like:
    data: {"step": "validation", "progress": 10, "message": "Validating..."}
    data: {"step": "complete", "progress": 100, "download_id": "abc-123"}
    
    Then client calls GET /download/{download_id} to get ZIP
    """
    from app.services.packager.packager_service import PackagerServiceV2
    
    download_id = str(uuid.uuid4())
    
    async def event_generator():
        try:
            packager = PackagerServiceV2(
                graph_data=request.graph,
                project_name=request.project_name
            )
            
            # Stream progress events
            generator = packager.create_package_streaming()
            zip_bytes = None
            
            for event in generator:
                # Send progress event to client
                yield f"data: {json.dumps(event)}\n\n"
                
                # Wait a bit for smooth UI updates
                await asyncio.sleep(0.1)
            
            # Get the returned ZIP bytes from generator
            try:
                zip_bytes = generator.send(None)  # Get return value
            except StopIteration as e:
                zip_bytes = e.value  # Python generators return via StopIteration.value
            
            # Store ZIP for download
            if zip_bytes:
                pending_downloads[download_id] = zip_bytes
                
                # Send final event with download ID
                final_event = {
                    "step": "download_ready",
                    "progress": 100,
                    "download_id": download_id,
                    "size_mb": len(zip_bytes) / (1024 * 1024)
                }
                yield f"data: {json.dumps(final_event)}\n\n"
            else:
                error_event = {"step": "error", "message": "Failed to generate package"}
                yield f"data: {json.dumps(error_event)}\n\n"
        
        except Exception as e:
            error_event = {
                "step": "error",
                "progress": 0,
                "message": f"Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/download/{download_id}")
async def get_download(download_id: str):
    """
    Download the prepared ZIP file
    """
    if download_id not in pending_downloads:
        raise HTTPException(status_code=404, detail="Download not found or expired")
    
    zip_bytes = pending_downloads[download_id]
    
    if not zip_bytes:
        raise HTTPException(status_code=500, detail="Package generation failed")
    
    # Clean up after download
    del pending_downloads[download_id]
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=ai-app-{download_id[:8]}.zip"
        }
    )


@router.delete("/download/{download_id}")
async def cancel_download(download_id: str):
    """Cancel/cleanup a download"""
    if download_id in pending_downloads:
        del pending_downloads[download_id]
        return {"message": "Download cancelled"}
    
    return {"message": "Download not found"}