from fastapi import APIRouter, Form, HTTPException
from app.services.scanner import scan_available_features
from app.services.module_generator import ModuleGenerator

router = APIRouter()
generator = ModuleGenerator()

@router.get("/features")
def list_features():
    """Return available features from the repo."""
    return scan_available_features()

@router.post("/save-module")
async def save_module_endpoint(
    name: str = Form(...),
    graph_json: str = Form(...),
    reqs_json: str = Form(...)
):
    import json
    try:
        graph = json.loads(graph_json)
        reqs = json.loads(reqs_json)
        return generator.save_module(name, graph, reqs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))