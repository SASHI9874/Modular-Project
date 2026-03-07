from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from app.schemas.feature_spec import FeatureManifest
from app.services.library_service import library_service
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from app.api.deps import get_db, get_current_user
from app.entities.user_entity import User
from app.entities.feature_entity import FeatureEntity
from app.services.feature_registry.storage_handler import storage
from app.domain.feature.trust_level import FeatureTrustLevel

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_feature(
    name: str = Form(...),
    version: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a new feature (Python file) to the registry.
    """
    # 1. Read file content
    content = file.file.read()
    
    # 2. Define Storage Path (Namespace by user or feature name)
    object_name = f"features/{name}/{version}/{file.filename}"
    
    # 3. Upload to MinIO
    try:
        s3_path = storage.upload_code(object_name, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # 4. Create DB Entry
    new_feature = FeatureEntity(
        name=name,
        version=version,
        description=description,
        author_id=current_user.id,
        trust_level=FeatureTrustLevel.USER, # Default to USER trust
        code_blob_ref=s3_path,
        inputs_json={}, # Todo: Parse this from code later
        outputs_json={}
    )
    
    try:
        db.add(new_feature)
        db.commit()
        db.refresh(new_feature)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="A feature with this name and version already exists."
        )

    return {"id": new_feature.id, "ref": s3_path, "msg": "Feature uploaded successfully"}

@router.get("/", response_model=List[FeatureManifest])
def get_features():
    """
    Returns the catalog of all available AI nodes.
    Used by the Frontend Sidebar to render the drag-and-drop list.
    """
    return library_service.get_all_features()

@router.post("/refresh")
def refresh_library():
    """
    Dev Tool: Forces a rescan of the disk without restarting the server.
    Useful when you add a new folder and want to see it immediately.
    """
    library_service.scan()
    return {"status": "refreshed", "count": len(library_service.get_all_features())}