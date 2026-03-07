import io
import zipfile
import os
from typing import Any, Dict, Set, List
from jinja2 import Environment, FileSystemLoader
from app.services.library_service import library_service

class AppPackager:
    def __init__(self, graph_data: Dict[str, Any], project_name: str):
        self.graph = graph_data
        self.project_name = project_name
        
        # Setup Templates
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(os.path.dirname(current_dir), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def _read_file(self, base_path: str, relative_path: str) -> str:
        """Helper to read source code from the library disk"""
        full_path = os.path.join(base_path, relative_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                return f.read()
        return f"# Error: File not found {relative_path}"
    
    def _generate_api_client(self, used_keys: List[str]) -> str:
        """
        Generates a strongly-typed TypeScript client.
        Output: client/api.ts
        """
        methods_code = []
        
        for key in used_keys:
            manifest = library_service.get_feature(key)
            if not manifest or not manifest.api.methods:
                continue

            # Generate methods for this feature
            feature_methods = []
            for method in manifest.api.methods:
                if method.has_file:
                    # File Upload Logic
                    ts_func = f"""
        async {method.name}(file: File) {{
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(`${{API_BASE}}/api/{key}{method.path}`, {{
                method: '{method.verb}',
                body: formData
            }});
            return res.json();
        }}"""
                else:
                    # JSON Logic
                    ts_func = f"""
        async {method.name}(data: any) {{
            const res = await fetch(`${{API_BASE}}/api/{key}{method.path}`, {{
                method: '{method.verb}',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(data)
            }});
            return res.json();
        }}"""
                feature_methods.append(ts_func)
            
            # Group into a namespace
            methods_code.append(f"""
    {key}: {{
        {",".join(feature_methods)}
    }},""")

        # Final TypeScript File Content
        return f"""
const API_BASE = "";

export const api = {{
    { "".join(methods_code) }
}};
"""


    def _generate_app_tsx(self, used_keys: List[str]) -> str:
        """
        Generates the main React entry point (App.tsx).
        It orchestrates where components sit on the screen.
        """
        imports = []
        sidebar_components = []
        main_components = []

        for key in used_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            # 1. Create Import Statement
            # Assumes we copied component.tsx to src/features/{key}/component.tsx
            component_name = f"{key.replace('-', '').capitalize()}Widget"
            imports.append(f"import {component_name} from './features/{key}/component';")

            # 2. Sort by Placement
            placement = manifest.ui.placement
            if placement == "sidebar":
                sidebar_components.append(f"<{component_name} />")
            elif placement == "main":
                main_components.append(f"<{component_name} />")
            # 'hidden' components are ignored in UI

        # 3. Generate JSX
        return f"""
import React from 'react';
import {{ AppProvider }} from './store';
{''.join(imports)}

export default function App() {{
return (
    <AppProvider>
        <div className="flex h-screen bg-gray-50 font-sans">
        
            {{/* SIDEBAR ZONE */}}
            <div className="w-80 bg-white border-r border-gray-200 p-6 flex flex-col gap-6 overflow-y-auto">
                <h1 className="text-xl font-bold text-gray-800 mb-2">My AI App</h1>
                    <div className="space-y-6">
                        {''.join(sidebar_components)}
                    </div>
            </div>

            {{/* MAIN CONTENT ZONE */}}
            <div className="flex-1 p-10 overflow-y-auto flex flex-col items-center">
                <div className="max-w-4xl w-full space-y-8">
                    {''.join(main_components)}
                    
                    {{/* Placeholder if empty */}}
                    {len(main_components) == 0 and '<div className="text-center text-gray-400 mt-20">Select a feature to see it here</div>'}
                </div>
            </div>
        </div>
    </AppProvider>
   );
}}
"""
    
    def _generate_global_store(self, used_keys: List[str]) -> str:
        """
        Generates a React Context to share state between components.
        It looks at the 'outputs' of every feature to know what state to track.
        """
        state_interfaces = []
        initial_states = []
        context_values = []
        
        for key in used_keys:
            manifest = library_service.get_feature(key)
            if not manifest or not manifest.contract.outputs:
                continue
                
            # For each output defined in the spec, create a state variable
            for out_key, field in manifest.contract.outputs.items():
                # Make the variable name unique (e.g., pdfLoader_fileText)
                var_name = f"{key.replace('-', '')}_{out_key}"
                
                # Determine TypeScript type based on spec
                ts_type = "string" if field.type == "string" else "any"
                
                # Add to Interface
                state_interfaces.append(f"{var_name}: {ts_type} | null;")
                state_interfaces.append(f"set_{var_name}: (val: {ts_type} | null) => void;")
                
                # Add to Implementation
                initial_states.append(f"const [{var_name}, set_{var_name}] = useState<{ts_type} | null>(null);")
                
                # Add to Context Value Provider
                context_values.append(var_name)
                context_values.append(f"set_{var_name}")

        # If no outputs, provide a dummy store to prevent React errors
        if not state_interfaces:
            return """
import React, { createContext, useContext } from 'react';
export const AppContext = createContext<any>({});
export const AppProvider = ({ children }: { children: React.ReactNode }) => <AppContext.Provider value={{}}>{children}</AppContext.Provider>;
export const useAppStore = () => useContext(AppContext);
            """

        # Generate the full typed store
        return f"""
import React, {{ createContext, useContext, useState }} from 'react';

interface AppState {{
    {chr(10).join("    " + i for i in state_interfaces)}
}}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
    {chr(10).join("    " + s for s in initial_states)}

    return (
            <AppContext.Provider value={{{{
                {", ".join(context_values)}
            }}}}>
                {{children}}
            </AppContext.Provider>
        );
}};

export const useAppStore = () => {{
    const context = useContext(AppContext);
    if (context === undefined) {{
        throw new Error('useAppStore must be used within an AppProvider');
    }}
    return context;
}};
"""

    def create_zip(self) -> bytes:
        # 1. Identify Used Features
        nodes = self.graph.get('nodes', [])
        used_keys = list(set([n['data'].get('icon') for n in nodes if n['data'].get('icon')]))
        
        # 2. Collections for Assembly
        requirements: Set[str] = set(["fastapi", "uvicorn", "python-multipart"])
        env_vars: Dict[str, str] = {}
        router_registrations: List[tuple[str, str]] = [] # e.g. ("from ... import ...", "app.include_router(...)")
        feature_files: Dict[str, str] = {}   # Map: "backend/features/pdf/service.py" -> Content

        # 3. Iterate & Assemble
        for key in used_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            # A. Infrastructure (Requirements & Env)
            for req in manifest.infrastructure.system_dependencies:
                # In real app, add to Dockerfile. For MVP, we skip.
                pass
            
            # Load requirements.txt if exists
            req_path = os.path.join(manifest.base_path, "requirements.txt")
            if os.path.exists(req_path):
                with open(req_path, "r") as f:
                    for line in f:
                        if line.strip(): requirements.add(line.strip())

            # Load Env Config Defaults
            for env_key, field in manifest.config.env.items():
                env_vars[env_key] = str(field.default) if field.default else ""

            # B. Code Assembly (Namespacing)
            # We copy 'core' -> 'backend/features/{key}/service.py'
            core_code = self._read_file(manifest.base_path, manifest.paths.core)
            feature_files[f"backend/features/{key}/service.py"] = core_code
            
            # We copy 'routes' -> 'backend/features/{key}/routes.py'
            routes_code = self._read_file(manifest.base_path, manifest.paths.generator_backend)
            feature_files[f"backend/features/{key}/routes.py"] = routes_code
            
            # Create __init__.py so python treats it as a package
            feature_files[f"backend/features/{key}/__init__.py"] = ""

            # C. Register Router
            # We assume the routes.py file exposes a variable named 'router'
            import_stmt = f"from features.{key} import routes as {key}_routes"
            include_stmt = f"app.include_router({key}_routes.router, prefix='/api/{key}', tags=['{key}'])"
            router_registrations.append((import_stmt, include_stmt))

        # 4. Generate Main App Entry (app.py)
        # We construct the main file dynamically based on registered routers
        imports_code = "\n".join([r[0] for r in router_registrations])
        includes_code = "\n    ".join([r[1] for r in router_registrations])
        
        app_py_content = f"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# --- FEATURE ROUTERS ---
{imports_code}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER FEATURES ---
{includes_code}

@app.get("/")
def health_check():
    return {{"status": "running", "project": "{self.project_name}"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

        # --- Generate API Client ---
        api_ts_content = self._generate_api_client(used_keys)
        # --- Generate App.tsx ---
        app_tsx_content = self._generate_app_tsx(used_keys)
        store_tsx_content = self._generate_global_store(used_keys)

        # 5. Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Write Main App
            zip_file.writestr("backend/app.py", app_py_content)
            zip_file.writestr("backend/requirements.txt", "\n".join(requirements))
            zip_file.writestr("backend/.env", "\n".join([f"{k}={v}" for k, v in env_vars.items()]))
            
            # Write Feature Files (The isolated packages)
            for path, content in feature_files.items():
                zip_file.writestr(path, content)
            
            # Write the UI Orchestrator
            zip_file.writestr("frontend/src/App.tsx", app_tsx_content)
            # Write the Generated Client
            zip_file.writestr("frontend/src/client/api.ts", api_ts_content)
            zip_file.writestr("frontend/src/store.tsx", store_tsx_content)
            # COPY COMPONENT FILES (The Missing Piece)
            for key in used_keys:
                manifest = library_service.get_feature(key)
                if not manifest: continue
                
                # Check if this feature has a UI component
                if manifest.paths.generator_frontend:
                    # Read from Library Disk
                    # e.g. library/pdf-loader/generator/frontend/component.tsx
                    fe_code = self._read_file(manifest.base_path, manifest.paths.generator_frontend)
                    
                    # Write to ZIP
                    # e.g. frontend/src/features/pdf-loader/component.tsx
                    zip_path = f"frontend/src/features/{key}/component.tsx"
                    zip_file.writestr(zip_path, fe_code)

            # 4. Write Standard Boilerplate (index.html, package.json, main.tsx, vite.config.ts)
            zip_file.writestr("frontend/index.html", self._get_index_html(self.project_name))
            zip_file.writestr("frontend/package.json", self._get_package_json(self.project_name))
            zip_file.writestr("frontend/vite.config.ts", self._get_vite_config())
            zip_file.writestr("frontend/src/main.tsx", self._get_main_tsx())
            zip_file.writestr("frontend/src/index.css", "@tailwind base;\n@tailwind components;\n@tailwind utilities;")
            zip_file.writestr("frontend/postcss.config.js", "export default { plugins: { tailwindcss: {}, autoprefixer: {}, }, }")
            zip_file.writestr("frontend/tailwind.config.js", "/** @type {import('tailwindcss').Config} */\nexport default { content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'], theme: { extend: {}, }, plugins: [], }")
                
            # Create a simple README
            zip_file.writestr("README.md", f"# {self.project_name}\n\nGenerated by AI Builder.")

        return zip_buffer.getvalue()


# --- HELPER METHODS FOR BOILERPLATE ---
    def _get_index_html(self, title):
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""

    def _get_package_json(self, name):
        return f"""{{
  "name": "{name.lower().replace(' ', '-')}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.300.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }}
}}"""

    def _get_vite_config(self):
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})"""

    def _get_main_tsx(self):
        return """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
