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
        registrations_code = "\n    ".join(registrations)
        
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
            
            # Copy core/service.py
            if manifest.paths.core:
                core_path = os.path.join(manifest.base_path, manifest.paths.core)
                if os.path.exists(core_path):
                    with open(core_path, 'r', encoding='utf-8') as f:
                        files[f'backend/features/{safe_key}/service.py'] = f.read()
            
            # Copy generator/backend/routes.py
            if manifest.paths.generator_backend:
                routes_path = os.path.join(manifest.base_path, manifest.paths.generator_backend)
                if os.path.exists(routes_path):
                    with open(routes_path, 'r', encoding='utf-8') as f:
                        files[f'backend/features/{safe_key}/routes.py'] = f.read()
            
            # Create __init__.py
            files[f'backend/features/{safe_key}/__init__.py'] = ''
        
        return files