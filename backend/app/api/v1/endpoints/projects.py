import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from app.services.packager.packager_service import AppPackager
# from app.api import depss
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.entities.user_entity import User
from app.entities.project_entity import ProjectEntity
from app.services.executor_service import GraphExecutor
from app.services.compiler.compiler_service import GraphCompiler

router = APIRouter()

# Schema for the Request
class ProjectCreate(BaseModel):
    name: str
    graph: Dict[str, Any] # This holds { nodes: [...], edges: [...] }

@router.post("/", response_model=Dict[str, Any])
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save a new project with its graph.
    """
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Load project -> Execute Graph -> Return Results
    """
    # 1. Fetch Project
    project = db.query(ProjectEntity).filter(
        ProjectEntity.id == project_id,
        ProjectEntity.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Initialize Executor
    try:
        executor = GraphExecutor(project.graph_json)
        results = executor.run()
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
    """
    Returns the generated Python code for the project.
    """
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
    """
    Generates a full-stack AI application ZIP for the given project.
    """
    # 1. Fetch Project from DB
    project = db.query(ProjectEntity).filter(
        ProjectEntity.id == project_id,
        ProjectEntity.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # 2. Run the System Assembler
        # This uses the Library Service to scan features and build the ZIP
        packager = AppPackager(project.graph_json, project.name)
        zip_bytes = packager.create_zip()
        
        # 3. Return as File Download
        # The 'Content-Disposition' header tells the browser to "Save As"
        filename = f"{project.name.replace(' ', '_')}_App.zip"

        response = Response(
            content=zip_bytes,
            media_type="application/zip",
        )

        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        # Log the full error for debugging
        print(f"Export Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")