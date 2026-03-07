from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, features, sandbox

api_router = APIRouter()

# Register routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
# api_router.include_router(sandbox.router, prefix="/sandbox", tags=["sandbox"])