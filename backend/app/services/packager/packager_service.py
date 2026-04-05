# import io
# import zipfile
# import os
# from typing import Any, Dict, Set, List
# from jinja2 import Environment, FileSystemLoader
# from app.services.library_service import library_service

# class AppPackager:
#     def __init__(self, graph_data: Dict[str, Any], project_name: str):
#         self.graph = graph_data
#         self.project_name = project_name
        
#         # Setup Templates
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         template_dir = os.path.join(os.path.dirname(current_dir), "templates")
#         self.env = Environment(loader=FileSystemLoader(template_dir))

#     def _read_file(self, base_path: str, relative_path: str) -> str:
#         """Helper to read source code from the library disk"""
#         full_path = os.path.join(base_path, relative_path)
#         if os.path.exists(full_path):
#             with open(full_path, "r", encoding="utf-8") as f:
#                 return f.read()
#         return f"# Error: File not found {relative_path}"
    
#     def _generate_api_client(self, used_keys: List[str]) -> str:
#         """
#         Generates a strongly-typed TypeScript client.
#         Output: client/api.ts
#         """
#         methods_code = []
        
#         for key in used_keys:
#             manifest = library_service.get_feature(key)
#             if not manifest or not manifest.api.methods:
#                 continue

#             # Generate methods for this feature
#             feature_methods = []
#             for method in manifest.api.methods:
#                 if method.has_file:
#                     # File Upload Logic
#                     ts_func = f"""
#         async {method.name}(file: File) {{
#             const formData = new FormData();
#             formData.append('file', file);
#             const res = await fetch(`${{API_BASE}}/api/{key}{method.path}`, {{
#                 method: '{method.verb}',
#                 body: formData
#             }});
#             return res.json();
#         }}"""
#                 else:
#                     # JSON Logic
#                     ts_func = f"""
#         async {method.name}(data: any) {{
#             const res = await fetch(`${{API_BASE}}/api/{key}{method.path}`, {{
#                 method: '{method.verb}',
#                 headers: {{ 'Content-Type': 'application/json' }},
#                 body: JSON.stringify(data)
#             }});
#             return res.json();
#         }}"""
#                 feature_methods.append(ts_func)
            
#             # Group into a namespace
#             methods_code.append(f"""
#     {key}: {{
#         {",".join(feature_methods)}
#     }},""")

#         # Final TypeScript File Content
#         return f"""
# const API_BASE = "";

# export const api = {{
#     { "".join(methods_code) }
# }};
# """


#     def _generate_app_tsx(self, used_keys: List[str]) -> str:
#         """
#         Generates the main React entry point (App.tsx).
#         It orchestrates where components sit on the screen.
#         """
#         imports = []
#         sidebar_components = []
#         main_components = []

#         for key in used_keys:
#             manifest = library_service.get_feature(key)
#             if not manifest:
#                 continue

#             # 1. Create Import Statement
#             # Assumes we copied component.tsx to src/features/{key}/component.tsx
#             component_name = f"{key.replace('-', '').capitalize()}Widget"
#             imports.append(f"import {component_name} from './features/{key}/component';")

#             # 2. Sort by Placement
#             placement = manifest.ui.placement
#             if placement == "sidebar":
#                 sidebar_components.append(f"<{component_name} />")
#             elif placement == "main":
#                 main_components.append(f"<{component_name} />")
#             # 'hidden' components are ignored in UI

#         # 3. Generate JSX
#         return f"""
# import React from 'react';
# import {{ AppProvider }} from './store';
# {''.join(imports)}

# export default function App() {{
# return (
#     <AppProvider>
#         <div className="flex h-screen bg-gray-50 font-sans">
        
#             {{/* SIDEBAR ZONE */}}
#             <div className="w-80 bg-white border-r border-gray-200 p-6 flex flex-col gap-6 overflow-y-auto">
#                 <h1 className="text-xl font-bold text-gray-800 mb-2">My AI App</h1>
#                     <div className="space-y-6">
#                         {''.join(sidebar_components)}
#                     </div>
#             </div>

#             {{/* MAIN CONTENT ZONE */}}
#             <div className="flex-1 p-10 overflow-y-auto flex flex-col items-center">
#                 <div className="max-w-4xl w-full space-y-8">
#                     {''.join(main_components)}
                    
#                     {{/* Placeholder if empty */}}
#                     {len(main_components) == 0 and '<div className="text-center text-gray-400 mt-20">Select a feature to see it here</div>'}
#                 </div>
#             </div>
#         </div>
#     </AppProvider>
#    );
# }}
# """
    
#     def _generate_global_store(self, used_keys: List[str]) -> str:
#         """
#         Generates a React Context to share state between components.
#         It looks at the 'outputs' of every feature to know what state to track.
#         """
#         state_interfaces = []
#         initial_states = []
#         context_values = []
        
#         for key in used_keys:
#             manifest = library_service.get_feature(key)
#             if not manifest or not manifest.contract.outputs:
#                 continue
                
#             # For each output defined in the spec, create a state variable
#             for out_key, field in manifest.contract.outputs.items():
#                 # Make the variable name unique (e.g., pdfLoader_fileText)
#                 var_name = f"{key.replace('-', '')}_{out_key}"
                
#                 # Determine TypeScript type based on spec
#                 ts_type = "string" if field.type == "string" else "any"
                
#                 # Add to Interface
#                 state_interfaces.append(f"{var_name}: {ts_type} | null;")
#                 state_interfaces.append(f"set_{var_name}: (val: {ts_type} | null) => void;")
                
#                 # Add to Implementation
#                 initial_states.append(f"const [{var_name}, set_{var_name}] = useState<{ts_type} | null>(null);")
                
#                 # Add to Context Value Provider
#                 context_values.append(var_name)
#                 context_values.append(f"set_{var_name}")

#         # If no outputs, provide a dummy store to prevent React errors
#         if not state_interfaces:
#             return """
# import React, { createContext, useContext } from 'react';
# export const AppContext = createContext<any>({});
# export const AppProvider = ({ children }: { children: React.ReactNode }) => <AppContext.Provider value={{}}>{children}</AppContext.Provider>;
# export const useAppStore = () => useContext(AppContext);
#             """

#         # Generate the full typed store
#         return f"""
# import React, {{ createContext, useContext, useState }} from 'react';

# interface AppState {{
#     {chr(10).join("    " + i for i in state_interfaces)}
# }}

# const AppContext = createContext<AppState | undefined>(undefined);

# export const AppProvider: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
#     {chr(10).join("    " + s for s in initial_states)}

#     return (
#             <AppContext.Provider value={{{{
#                 {", ".join(context_values)}
#             }}}}>
#                 {{children}}
#             </AppContext.Provider>
#         );
# }};

# export const useAppStore = () => {{
#     const context = useContext(AppContext);
#     if (context === undefined) {{
#         throw new Error('useAppStore must be used within an AppProvider');
#     }}
#     return context;
# }};
# """

#     def create_zip(self) -> bytes:
#         # 1. Identify Used Features
#         nodes = self.graph.get('nodes', [])
#         used_keys = list(set([n['data'].get('icon') for n in nodes if n['data'].get('icon')]))
        
#         # 2. Collections for Assembly
#         requirements: Set[str] = set(["fastapi", "uvicorn", "python-multipart"])
#         env_vars: Dict[str, str] = {}
#         router_registrations: List[tuple[str, str]] = [] # e.g. ("from ... import ...", "app.include_router(...)")
#         feature_files: Dict[str, str] = {}   # Map: "backend/features/pdf/service.py" -> Content

#         # 3. Iterate & Assemble
#         for key in used_keys:
#             manifest = library_service.get_feature(key)
#             if not manifest:
#                 continue

#             # A. Infrastructure (Requirements & Env)
#             for req in manifest.infrastructure.system_dependencies:
#                 # In real app, add to Dockerfile. For MVP, we skip.
#                 pass
            
#             # Load requirements.txt if exists
#             req_path = os.path.join(manifest.base_path, "requirements.txt")
#             if os.path.exists(req_path):
#                 with open(req_path, "r", encoding="utf-8") as f:
#                     for line in f:
#                         if line.strip(): requirements.add(line.strip())

#             # Load Env Config Defaults
#             for env_key, field in manifest.config.env.items():
#                 env_vars[env_key] = str(field.default) if field.default else ""

#             # B. Code Assembly (Namespacing)
#             # We copy 'core' -> 'backend/features/{key}/service.py'
#             core_code = self._read_file(manifest.base_path, manifest.paths.core)
#             feature_files[f"backend/features/{key}/service.py"] = core_code
            
#             # We copy 'routes' -> 'backend/features/{key}/routes.py'
#             routes_code = self._read_file(manifest.base_path, manifest.paths.generator_backend)
#             feature_files[f"backend/features/{key}/routes.py"] = routes_code
            
#             # Create __init__.py so python treats it as a package
#             feature_files[f"backend/features/{key}/__init__.py"] = ""

#             # C. Register Router
#             # We assume the routes.py file exposes a variable named 'router'
#             import_stmt = f"from features.{key} import routes as {key}_routes"
#             include_stmt = f"app.include_router({key}_routes.router, prefix='/api/{key}', tags=['{key}'])"
#             router_registrations.append((import_stmt, include_stmt))

#         # 4. Generate Main App Entry (app.py)
#         # We construct the main file dynamically based on registered routers
#         imports_code = "\n".join([r[0] for r in router_registrations])
#         includes_code = "\n    ".join([r[1] for r in router_registrations])
        
#         app_py_content = f"""
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# import os

# # --- FEATURE ROUTERS ---
# {imports_code}

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- REGISTER FEATURES ---
# {includes_code}

# @app.get("/")
# def health_check():
#     return {{"status": "running", "project": "{self.project_name}"}}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
# """

#         # --- Generate API Client ---
#         api_ts_content = self._generate_api_client(used_keys)
#         # --- Generate App.tsx ---
#         app_tsx_content = self._generate_app_tsx(used_keys)
#         store_tsx_content = self._generate_global_store(used_keys)

#         # 5. Create ZIP
#         zip_buffer = io.BytesIO()
#         with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
#             # Write Main App
#             zip_file.writestr("backend/app.py", app_py_content)
#             zip_file.writestr("backend/requirements.txt", "\n".join(requirements))
#             zip_file.writestr("backend/.env", "\n".join([f"{k}={v}" for k, v in env_vars.items()]))
            
#             # Write Feature Files (The isolated packages)
#             for path, content in feature_files.items():
#                 zip_file.writestr(path, content)
            
#             # Write the UI Orchestrator
#             zip_file.writestr("frontend/src/App.tsx", app_tsx_content)
#             # Write the Generated Client
#             zip_file.writestr("frontend/src/client/api.ts", api_ts_content)
#             zip_file.writestr("frontend/src/store.tsx", store_tsx_content)
#             # COPY COMPONENT FILES (The Missing Piece)
#             for key in used_keys:
#                 manifest = library_service.get_feature(key)
#                 if not manifest: continue
                
#                 # Check if this feature has a UI component
#                 if manifest.paths.generator_frontend:
#                     # Read from Library Disk
#                     # e.g. library/pdf-loader/generator/frontend/component.tsx
#                     fe_code = self._read_file(manifest.base_path, manifest.paths.generator_frontend)
                    
#                     # Write to ZIP
#                     # e.g. frontend/src/features/pdf-loader/component.tsx
#                     zip_path = f"frontend/src/features/{key}/component.tsx"
#                     zip_file.writestr(zip_path, fe_code)

#             # 4. Write Standard Boilerplate (index.html, package.json, main.tsx, vite.config.ts)
#             zip_file.writestr("frontend/index.html", self._get_index_html(self.project_name))
#             zip_file.writestr("frontend/package.json", self._get_package_json(self.project_name))
#             zip_file.writestr("frontend/vite.config.ts", self._get_vite_config())
#             zip_file.writestr("frontend/src/main.tsx", self._get_main_tsx())
#             zip_file.writestr("frontend/src/index.css", "@tailwind base;\n@tailwind components;\n@tailwind utilities;")
#             zip_file.writestr("frontend/postcss.config.js", "export default { plugins: { tailwindcss: {}, autoprefixer: {}, }, }")
#             zip_file.writestr("frontend/tailwind.config.js", "/** @type {import('tailwindcss').Config} */\nexport default { content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'], theme: { extend: {}, }, plugins: [], }")
                
#             # Create a simple README
#             zip_file.writestr("README.md", f"# {self.project_name}\n\nGenerated by AI Builder.")

#         return zip_buffer.getvalue()


# # --- HELPER METHODS FOR BOILERPLATE ---
#     def _get_index_html(self, title):
#         return f"""<!doctype html>
# <html lang="en">
#   <head>
#     <meta charset="UTF-8" />
#     <meta name="viewport" content="width=device-width, initial-scale=1.0" />
#     <title>{title}</title>
#   </head>
#   <body>
#     <div id="root"></div>
#     <script type="module" src="/src/main.tsx"></script>
#   </body>
# </html>"""

#     def _get_package_json(self, name):
#         return f"""{{
#   "name": "{name.lower().replace(' ', '-')}",
#   "private": true,
#   "version": "0.0.0",
#   "type": "module",
#   "scripts": {{
#     "dev": "vite",
#     "build": "tsc && vite build",
#     "preview": "vite preview"
#   }},
#   "dependencies": {{
#     "react": "^18.2.0",
#     "react-dom": "^18.2.0",
#     "lucide-react": "^0.300.0"
#   }},
#   "devDependencies": {{
#     "@types/react": "^18.2.43",
#     "@types/react-dom": "^18.2.17",
#     "@vitejs/plugin-react": "^4.2.1",
#     "autoprefixer": "^10.4.16",
#     "postcss": "^8.4.32",
#     "tailwindcss": "^3.4.0",
#     "typescript": "^5.2.2",
#     "vite": "^5.0.0"
#   }}
# }}"""

#     def _get_vite_config(self):
#         return """import { defineConfig } from 'vite'
# import react from '@vitejs/plugin-react'

# export default defineConfig({
#   plugins: [react()],
#   server: {
#     proxy: {
#       '/api': 'http://localhost:8000'
#     }
#   }
# })"""

#     def _get_main_tsx(self):
#         return """import React from 'react'
# import ReactDOM from 'react-dom/client'
# import App from './App.tsx'
# import './index.css'

# ReactDOM.createRoot(document.getElementById('root')!).render(
#   <React.StrictMode>
#     <App />
#   </React.StrictMode>,
# )"""




import re
from typing import Dict, Any, Generator

from app.services.library_service import library_service
from .analyzer import GraphAnalyzer, DependencyResolver, ModeDetector
from .generators import ( BackendGenerator, 
                         FrontendGenerator, 
                         EnvGenerator, 
                         DockerGenerator, 
                         DocsGenerator,
                         ExtensionCompiler ,
                         InstallScriptsGenerator
                           )
from .bundler import ZipBundler
from .validators import GraphValidator
from .errors.packager_errors import PackagerError


class PackagerService:
    """
    Modular packager orchestrator
    Coordinates all download steps with error isolation
    """
    
    def __init__(self, graph_data: Dict[str, Any], project_name: str):
        self.graph = graph_data
        self.project_name = project_name
        # Initialize modules
        self.analyzer = GraphAnalyzer(graph_data)
        self.validator = GraphValidator(graph_data)
        self.dependency_resolver = DependencyResolver()
        self.backend_gen = BackendGenerator(project_name)
        self.frontend_gen = FrontendGenerator(project_name, graph_data)
        self.extension_compiler = ExtensionCompiler(project_name)
        self.env_gen = EnvGenerator()
        self.docker_gen = DockerGenerator(project_name)
        self.docs_gen = DocsGenerator(project_name)
        self.install_scripts_gen = InstallScriptsGenerator(project_name)
        
        
        self.bundler = ZipBundler(project_name)
    
    def create_package(self) -> bytes:
        """
        Main entry point - orchestrates entire download process
        
        Returns:
            ZIP file bytes
        
        Raises:
            PackagerError: If any step fails critically
        """
        print("=" * 60)
        print(f" Starting package generation: {self.project_name}")
        print("=" * 60)
        
        try:
            #  Validate
            print("\n  Validation")
            is_valid, errors = self.validator.validate()
            if not is_valid:
                raise PackagerError(f"Validation failed: {'; '.join(errors)}")
            
            #  Analyze graph
            print("\n  Graph Analysis")
            runtime_nodes = self.analyzer.filter_runtime_nodes()
            used_keys = self.analyzer.get_used_feature_keys(runtime_nodes)
            execution_mode = self.analyzer.detect_execution_mode()
            
            #  Resolve dependencies
            print("\n  Dependency Resolution")
            resolved_keys = self.dependency_resolver.resolve(used_keys)
            
            #  Detect frontend mode
            print("\n  Frontend Mode Detection")
            mode_detector = ModeDetector(runtime_nodes)
            frontend_mode = mode_detector.detect_frontend_mode()
            
            #  Generate backend
            print("\n  Backend Generation")
            backend_files = self.backend_gen.generate(resolved_keys)
            
            #  Generate frontend
            print("\n  Frontend Generation")
            frontend_files = self.frontend_gen.generate(resolved_keys, frontend_mode)

            vsix_bytes = None
            vsix_filename = None
            if frontend_mode == 'external_extension':
                print("\n : VS Code Extension Compilation")
                
                # Find VS Code feature
                vscode_feature_key = None
                vscode_feature_name = "vscode-agent"
                vscode_version = "1.0.0"
                
                for key in resolved_keys:
                    if 'vscode' in key.lower():
                        vscode_feature_key = key
                        manifest = library_service.get_feature(key)
                        if manifest:
                            vscode_feature_name = manifest.name
                            vscode_version = manifest.version
                        break
                
                extension_source = self.extension_compiler.generate_extension_source(resolved_keys)
                
                if extension_source:
                    vsix_bytes = self.extension_compiler.compile_vscode_extension(
                        extension_source,
                        backend_url="ws://localhost:8000",
                        feature_key=vscode_feature_key or "interface-vscode",
                        feature_version=vscode_version
                    )
                    
                    if vsix_bytes:
                        safe_name = sanitize_filename(vscode_feature_name)
                        vsix_filename = f"{safe_name}-v{vscode_version}.vsix"
                        print(f" {vsix_filename}   Extension compiled successfully")
                    else:
                        print("     Extension compilation failed - including source instead")
                else:
                    print("     No VS Code extension to compile")
            
            print("\n  Environment Files")
            env_files = self.env_gen.generate(resolved_keys)
            
            #  Add DOCKER files
            print("\n  Docker Configuration")
            docker_files = self.docker_gen.generate(resolved_keys)

            #  Add README
            print("\n  Documentation")
            readme = self.docs_gen.generate_readme(
                resolved_keys,
                execution_mode,
                frontend_mode,
                has_docker=True
            )

            #  Generate install scripts
            print("\n Install Scripts")
            extension_name = None
            if vsix_bytes:
                extension_name = f"{vsix_filename}"

            install_scripts = self.install_scripts_gen.generate(
                has_frontend=(frontend_mode == 'generated_ui'),
                has_extension=(vsix_bytes is not None),
                extension_name=extension_name
            )
            
            #  Bundle everything
            print("\n : Bundling")
            all_files = {
                **backend_files,
                **frontend_files,
                **env_files,
                **docker_files,
                **install_scripts,
                'README.md': readme
            }

            # Add .vsix if compiled
            if vsix_bytes and vsix_filename :
                all_files[vsix_filename] = vsix_bytes
                print(f"    Including compiled extension: {vsix_filename}")
            
            zip_bytes = self.bundler.create_zip(all_files)
            
            print("\n" + "=" * 60)
            print(f" Package generation complete!")
            print(f"    Files: {len(all_files)}")
            print(f"    README: LLM-generated")
            if vsix_bytes:
                print(f"    Extension: Compiled")
            print(f"    Install scripts: Included")
            print("=" * 60)
            
            return zip_bytes
        
        except PackagerError as e:
            print(f"\n Packaging failed: {e}")
            raise
        
        except Exception as e:
            print(f"\n Unexpected error: {e}")
            raise PackagerError(f"Packaging failed: {e}")
    
    def create_package_streaming(self) -> Generator[Dict[str, Any], None, bytes]:
        """
        Stream progress events during package generation
        
        Yields progress events, returns final ZIP bytes
        """
        yield {"step": "validation", "progress": 5, "message": "Validating graph..."}
        
        try:
            # Step 1: Validate
            is_valid, errors = self.validator.validate()
            if not is_valid:
                yield {"step": "error", "progress": 0, "message": f"Validation failed: {'; '.join(errors)}"}
                raise PackagerError(f"Validation failed: {'; '.join(errors)}")
            
            yield {"step": "validation", "progress": 10, "message": " Graph validated"}
            
            # Step 2: Analyze
            yield {"step": "analysis", "progress": 15, "message": "Analyzing graph structure..."}
            runtime_nodes = self.analyzer.filter_runtime_nodes()
            used_keys = self.analyzer.get_used_feature_keys(runtime_nodes)
            execution_mode = self.analyzer.detect_execution_mode()
            yield {"step": "analysis", "progress": 20, "message": f" Found {len(runtime_nodes)} runtime nodes"}
            
            # Step 3: Dependencies
            yield {"step": "dependencies", "progress": 25, "message": "Resolving dependencies..."}
            resolved_keys = self.dependency_resolver.resolve(used_keys)
            yield {"step": "dependencies", "progress": 30, "message": f" Resolved {len(resolved_keys)} features"}
            
            # Step 4: Frontend mode
            yield {"step": "mode_detection", "progress": 35, "message": "Detecting frontend mode..."}
            mode_detector = ModeDetector(runtime_nodes)
            frontend_mode = mode_detector.detect_frontend_mode()
            yield {"step": "mode_detection", "progress": 40, "message": f" Mode: {frontend_mode}"}
            
            # Step 5: Backend
            yield {"step": "backend", "progress": 45, "message": "Generating backend code..."}
            # backend_files = self.backend_gen.generate(resolved_keys)
            backend_files = self.backend_gen.generate(  resolved_keys,
                                                        frontend_mode=frontend_mode,
                                                        graph_data=self.graph
                                                    )
            yield {"step": "backend", "progress": 55, "message": f" Generated {len(backend_files)} backend files"}
            
            # Step 6: Frontend
            yield {"step": "frontend", "progress": 60, "message": "Generating frontend..."}
            frontend_files = self.frontend_gen.generate(resolved_keys, frontend_mode)
            yield {"step": "frontend", "progress": 65, "message": f" Generated {len(frontend_files)} frontend files"}
            
            # Step 6.5: Extension
            vsix_bytes = None
            vsix_filename = None
            if frontend_mode == 'external_extension':
                yield {"step": "extension", "progress": 70, "message": "Compiling VS Code extension..."}
                
                # Find VS Code feature
                vscode_feature_key = None
                vscode_feature_name = "vscode-agent"
                vscode_version = "1.0.0"
                
                for key in resolved_keys:
                    if 'vscode' in key.lower():
                        vscode_feature_key = key
                        from app.services.library_service import library_service
                        manifest = library_service.get_feature(key)
                        if manifest:
                            vscode_feature_name = manifest.name
                            vscode_version = manifest.version
                        break
                
                extension_source = self.extension_compiler.generate_extension_source(resolved_keys)
                
                if extension_source:
                    vsix_bytes = self.extension_compiler.compile_vscode_extension(
                        extension_source,
                        backend_url="ws://localhost:8000",
                        feature_key=vscode_feature_key or "interface-vscode",
                        feature_version=vscode_version
                    )
                    
                    if vsix_bytes:
                        safe_name = sanitize_filename(vscode_feature_name)
                        vsix_filename = f"{safe_name}-v{vscode_version}.vsix"
                        yield {"step": "extension", "progress": 75, "message": f" Extension compiled: {vsix_filename}"}
                    else:
                        yield {"step": "extension", "progress": 75, "message": " Extension compilation failed"}
                else:
                    yield {"step": "extension", "progress": 75, "message": " No extension to compile"}
            
            # Step 7: Environment
            yield {"step": "environment", "progress": 80, "message": "Generating environment files..."}
            env_files = self.env_gen.generate(resolved_keys)
            yield {"step": "environment", "progress": 82, "message": " Environment files created"}
            
            # Step 8: Docker
            yield {"step": "docker", "progress": 84, "message": "Generating Docker configuration..."}
            docker_files = self.docker_gen.generate(resolved_keys)
            yield {"step": "docker", "progress": 86, "message": " Docker files created"}
            
            # Step 9: Documentation
            try:
                yield {"step": "documentation", "progress": 88, "message": "Generating README with AI..."}
                readme = self.docs_gen.generate_readme(resolved_keys, execution_mode, frontend_mode, has_docker=True)
                yield {"step": "documentation", "progress": 92, "message": " README generated"}
            except Exception as e:
                # FALLBACK: If llm failed use a basic template instead of crashing
                print(f"AI Documentation failed: {e}")
                readme = self._generate_readme_fallback(execution_mode, frontend_mode)
                yield {"step": "documentation", "progress": 92, "message": " README prepared (Fallback used)"}

            # Step 10: Install scripts
            yield {"step": "install_scripts", "progress": 94, "message": "Creating install scripts..."}
            extension_name = vsix_filename if vsix_bytes and vsix_filename else None
            install_scripts = self.install_scripts_gen.generate(
                has_frontend=(frontend_mode == 'generated_ui'),
                has_extension=(vsix_bytes is not None),
                extension_name=extension_name
            )
            yield {"step": "install_scripts", "progress": 96, "message": " Install scripts created"}
            
            # Step 11: Bundle
            yield {"step": "bundling", "progress": 98, "message": "Creating ZIP package..."}
            all_files = {
                **backend_files,
                **frontend_files,
                **env_files,
                **docker_files,
                **install_scripts,
                'README.md': readme
            }
            
            if vsix_bytes and vsix_filename:
                all_files[vsix_filename] = vsix_bytes
            
            zip_bytes = self.bundler.create_zip(all_files)
            
            yield {"step": "complete", "progress": 100, "message": f" Package ready ({len(zip_bytes) / (1024*1024):.2f} MB)"}
            
            return zip_bytes
        
        except Exception as e:
            yield {"step": "error", "progress": 0, "message": f" Error: {str(e)}"}
            raise

    def _generate_readme(self, execution_mode: str, frontend_mode: str) -> str:
        """Generate basic README"""
        return f"""# {self.project_name}

Generated by AI Builder Platform

## Architecture

- **Execution Mode:** {execution_mode}
- **Frontend Mode:** {frontend_mode}

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your API keys
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Access

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## Documentation

See individual feature folders for more details.
"""


def sanitize_filename(name: str) -> str:
    """Remove characters forbidden in Windows filenames"""
    # Remove: < > : " / \ | ? *
    forbidden = r'[<>:"/\\|?*]'
    sanitized = re.sub(forbidden, '-', name)
    # Remove multiple consecutive dashes
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing dashes
    sanitized = sanitized.strip('-')
    return sanitized


# Keep old packager for compatibility
# from .packager_service_old import AppPackager  # Rename your old file

__all__ = ['PackagerService', 'AppPackager']