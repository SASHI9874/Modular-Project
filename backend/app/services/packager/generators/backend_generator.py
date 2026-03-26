import os
from typing import Dict, Any, List, Set, Tuple
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class BackendGenerator:
    """Generates Flask/FastAPI backend code"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def generate(self, feature_keys: List[str]) -> Dict[str, str]:
        """
        Generate all backend files
        Returns dict: {filepath: content}
        """
        print(" [BackendGen] Generating backend...")
        
        files = {}
        
        try:
            # Generate main app
            main_app = self._generate_main_app(feature_keys)
            files['backend/app.py'] = main_app
            
            # Generate requirements
            requirements = self._generate_requirements(feature_keys)
            files['backend/requirements.txt'] = requirements
            
            # Copy feature files
            feature_files = self._copy_feature_files(feature_keys)
            files.update(feature_files)
            
            print(f" [BackendGen] Generated {len(files)} files")
            return files
        
        except Exception as e:
            print(f" [BackendGen] Error: {e}")
            raise CodeGenerationError(f"Backend generation failed: {e}")
    
    def _generate_main_app(self, feature_keys: List[str]) -> str:
        """Generate main FastAPI app.py"""
        imports = []
        registrations = []
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            # Import route
            import_stmt = f"from features.{key.replace('-', '_')} import routes as {key.replace('-', '_')}_routes"
            imports.append(import_stmt)
            
            # Register route
            reg_stmt = f"app.include_router({key.replace('-', '_')}_routes.router, prefix='/api/{key}', tags=['{key}'])"
            registrations.append(reg_stmt)
        
        imports_code = "\n".join(imports)
        registrations_code = "\n".join(registrations)
        
        return f'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Feature routers
{imports_code}

app = FastAPI(title="{self.project_name}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register features
{registrations_code}

@app.get("/")
def health_check():
    return {{"status": "running", "project": "{self.project_name}"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_requirements(self, feature_keys: List[str]) -> str:
        """Generate requirements.txt"""
        requirements: Set[str] = {"fastapi", "uvicorn", "python-multipart"}
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            # Read feature requirements.txt
            req_path = os.path.join(manifest.base_path, "requirements.txt")
            if os.path.exists(req_path):
                with open(req_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            requirements.add(line)
        
        return "\n".join(sorted(requirements))
    
    def _copy_feature_files(self, feature_keys: List[str]) -> Dict[str, str]:
        """Copy feature source files"""
        files = {}
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            safe_key = key.replace('-', '_')
            
            # Determine which files to copy
            has_adapter = False
            has_service = False
            
            # Copy runtime/adapter.py
            if manifest.paths.runtime:
                runtime_path = os.path.join(manifest.base_path, manifest.paths.runtime)
                if os.path.exists(runtime_path):
                    with open(runtime_path, 'r', encoding='utf-8') as f:
                        files[f'backend/features/{safe_key}/adapter.py'] = f.read()
                        has_adapter = True

            # Copy entire core directory, preserving the folder itself
            if manifest.paths.core:
                core_target_path = os.path.join(manifest.base_path, manifest.paths.core)
                
                # Determine the directory to copy
                core_dir = os.path.dirname(core_target_path) if os.path.isfile(core_target_path) else core_target_path
                
                if os.path.exists(core_dir) and os.path.isdir(core_dir):
                    # NEW: Get the parent directory of 'core' so we preserve the folder name
                    parent_dir = os.path.dirname(os.path.normpath(core_dir))
                    
                    for root, _, filenames in os.walk(core_dir):
                        for filename in filenames:
                            # Skip compiled python files and hidden files
                            if filename.endswith('.pyc') or '__pycache__' in root or filename.startswith('.'):
                                continue
                                
                            file_path = os.path.join(root, filename)
                            
                            # NEW: Calculate the relative path from the parent directory
                            # This turns "/path/to/feature/core/service.py" into "core/service.py"
                            rel_path = os.path.relpath(file_path, parent_dir)
                            dest_path = f'backend/features/{safe_key}/{rel_path}'
                            
                            with open(file_path, 'r', encoding='utf-8') as f:
                                files[dest_path] = f.read()
                                
                                # Flag if we found the main service.py
                                if filename == 'service.py':
                                    has_service = True
            
            # Check if feature has custom routes
            has_custom_routes = False
            if manifest.paths.generator_backend:
                routes_path = os.path.join(manifest.base_path, manifest.paths.generator_backend)
                if os.path.exists(routes_path):
                    with open(routes_path, 'r', encoding='utf-8') as f:
                        files[f'backend/features/{safe_key}/routes.py'] = f.read()
                        has_custom_routes = True
            
            # Generate default routes if not present
            if not has_custom_routes:
                routes_content = self._generate_default_routes(key, manifest, safe_key)
                files[f'backend/features/{safe_key}/routes.py'] = routes_content
            
            # Create __init__.py that exposes routes
            init_content = f'''"""{manifest.name} Feature"""
from . import routes

__all__ = ['routes']
'''
            files[f'backend/features/{safe_key}/__init__.py'] = init_content
        
        return files

    def _generate_default_routes(self, feature_key: str, manifest, safe_key: str) -> str:
        """Generate default API routes for features without custom routes"""
        
        capability = manifest.classification.capability
        has_runtime = bool(manifest.paths.runtime)
        
        if has_runtime:
            # Generate execute route that calls adapter
            return f'''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from .adapter import run

router = APIRouter()

class ExecuteRequest(BaseModel):
    inputs: Dict[str, Any]
    context: Dict[str, Any] = {{}}

@router.post("/execute")
async def execute(request: ExecuteRequest):
    """Execute {manifest.name} - Capability: {capability}"""
    try:
        result = run(request.inputs, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """Health check for {manifest.name}"""
    return {{
        "status": "ok",
        "feature": "{feature_key}",
        "name": "{manifest.name}",
        "capability": "{capability}",
        "version": "{manifest.version}"
    }}
'''
        else:
            # Basic health check only
            return f'''from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    """Health check for {manifest.name}"""
    return {{
        "status": "ok",
        "feature": "{feature_key}",
        "name": "{manifest.name}",
        "capability": "{capability}",
        "version": "{manifest.version}"
    }}

@router.get("/info")
async def info():
    """Get feature information"""
    return {{
        "key": "{feature_key}",
        "name": "{manifest.name}",
        "version": "{manifest.version}",
        "capability": "{capability}",
        "description": "{manifest.description}"
    }}
'''