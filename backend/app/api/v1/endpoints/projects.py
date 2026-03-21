import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from app.services.packager.packager_service import PackagerService
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.entities.user_entity import User
from app.entities.project_entity import ProjectEntity
from app.services.executor_service import GraphExecutor
from app.services.compiler.compiler_service import GraphCompiler
from app.schemas.project_schema import ProjectCreate, RunPayload

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