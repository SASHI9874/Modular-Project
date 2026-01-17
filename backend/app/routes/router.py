from fastapi import APIRouter
from app.controllers import builder_controller
from app.controllers import features_controller
from app.controllers import workflow_controller
from app.controllers import module_builder_controller
from online_tester.router import router as tester_router

api_router = APIRouter()


api_router.include_router(features_controller.router, tags=["Marketplace"])
api_router.include_router(builder_controller.router, tags=["Builder"])
api_router.include_router(tester_router, tags=["Online Tester"])
api_router.include_router(workflow_controller.router, prefix="/workflow", tags=["Workflow Runner"])
api_router.include_router(module_builder_controller.router, tags=["Save Module"])