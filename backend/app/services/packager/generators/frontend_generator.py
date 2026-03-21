import os
from typing import Dict, Any, List
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class FrontendGenerator:
    """Generates React frontend code"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def generate(self, feature_keys: List[str], mode: str = 'generated_ui') -> Dict[str, str]:
        """
        Generate frontend files based on mode
        Returns dict: {filepath: content}
        """
        print(f" [FrontendGen] Generating frontend (mode: {mode})...")
        
        files = {}
        
        try:
            if mode == 'headless':
                print("     Skipping frontend (headless mode)")
                return files
            
            elif mode == 'external_extension':
                # Extension handled separately
                print("     Extension mode - minimal frontend")
                return files
            
            elif mode == 'generated_ui':
                # Generate full React UI
                files.update(self._generate_react_ui(feature_keys))
            
            print(f" [FrontendGen] Generated {len(files)} files")
            return files
        
        except Exception as e:
            print(f" [FrontendGen] Error: {e}")
            raise CodeGenerationError(f"Frontend generation failed: {e}")
    
    def _generate_react_ui(self, feature_keys: List[str]) -> Dict[str, str]:
        """Generate React UI files"""
        files = {}
        
        # Generate App.tsx
        files['frontend/src/App.tsx'] = self._generate_app_tsx(feature_keys)
        
        # Generate store
        files['frontend/src/store.tsx'] = self._generate_store(feature_keys)
        
        # Generate API client
        files['frontend/src/client/api.ts'] = self._generate_api_client(feature_keys)
        
        # Copy components
        component_files = self._copy_components(feature_keys)
        files.update(component_files)
        
        # Boilerplate
        files.update(self._generate_boilerplate())
        
        return files
    
    def _generate_app_tsx(self, feature_keys: List[str]) -> str:
        """Generate App.tsx"""
        imports = []
        sidebar_components = []
        main_components = []
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            # Check if has component
            has_component = True
            if hasattr(manifest.ui, 'has_component'):
                has_component = manifest.ui.has_component
            
            if not has_component:
                continue
            
            safe_key = key.replace('-', '_')
            component_name = f"{safe_key.capitalize()}Widget"
            imports.append(f"import {component_name} from './features/{safe_key}/component';")
            
            placement = manifest.ui.placement if hasattr(manifest.ui, 'placement') else 'main'
            
            if placement == 'sidebar':
                sidebar_components.append(f"<{component_name} />")
            elif placement == 'main':
                main_components.append(f"<{component_name} />")
        
        return f"""
import React from 'react';
import {{ AppProvider }} from './store';
{chr(10).join(imports)}

export default function App() {{
  return (
    <AppProvider>
      <div className="flex h-screen bg-gray-50 font-sans">
        
        {{/* SIDEBAR */}}
        <div className="w-80 bg-white border-r border-gray-200 p-6 flex flex-col gap-6 overflow-y-auto">
          <h1 className="text-xl font-bold text-gray-800 mb-2">{self.project_name}</h1>
          <div className="space-y-6">
            {chr(10).join('            ' + c for c in sidebar_components)}
          </div>
        </div>

        {{/* MAIN CONTENT */}}
        <div className="flex-1 p-10 overflow-y-auto flex flex-col items-center">
          <div className="max-w-4xl w-full space-y-8">
            {chr(10).join('            ' + c for c in main_components)}
            {len(main_components) == 0 and '<div className="text-center text-gray-400 mt-20">No components</div>'}
          </div>
        </div>
      </div>
    </AppProvider>
  );
}}
"""
    
    def _generate_store(self, feature_keys: List[str]) -> str:
      """Generate React Context store with typed state"""
      
      state_fields = []
      initial_states = []
      context_values = []
      
      for key in feature_keys:
          manifest = library_service.get_feature(key)
          if not manifest or not manifest.contract.outputs:
              continue
          
          safe_key = key.replace('-', '_')
          
          for out_key, field in manifest.contract.outputs.items():
              var_name = f"{safe_key}_{out_key}"
              
              # Map types
              ts_type_map = {
                  'string': 'string',
                  'number': 'number',
                  'boolean': 'boolean',
                  'array': 'any[]',
                  'object': 'any'
              }
              ts_type = ts_type_map.get(field.type, 'any')
              
              # Add to interface
              state_fields.append(f"  {var_name}: {ts_type} | null;")
              state_fields.append(f"  set_{var_name}: (val: {ts_type} | null) => void;")
              
              # Add state hook
              initial_states.append(f"  const [{var_name}, set_{var_name}] = useState<{ts_type} | null>(null);")
              
              # Add to context
              context_values.append(f"    {var_name},")
              context_values.append(f"    set_{var_name},")
      
      if not state_fields:
          # Empty store
          return """
  import React, { createContext, useContext } from 'react';

  interface AppState {}

  const AppContext = createContext<AppState>({});

  export const AppProvider = ({ children }: { children: React.ReactNode }) => (
    <AppContext.Provider value={{}}>
      {children}
    </AppContext.Provider>
  );

  export const useAppStore = () => useContext(AppContext);
  """
      
      return f"""
  import React, {{ createContext, useContext, useState }} from 'react';

  interface AppState {{
  {chr(10).join(state_fields)}
  }}

  const AppContext = createContext<AppState | undefined>(undefined);

  export const AppProvider: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
  {chr(10).join(initial_states)}

    return (
      <AppContext.Provider value={{{{
  {chr(10).join(context_values)}
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
    
    def _generate_api_client(self, feature_keys: List[str]) -> str:
      """Generate strongly-typed TypeScript API client"""
      
      methods_code = []
      
      for key in feature_keys:
          manifest = library_service.get_feature(key)
          if not manifest or not manifest.api or not manifest.api.methods:
              continue
          
          safe_key = key.replace('-', '_')
          feature_methods = []
          
          for method in manifest.api.methods:
              method_name = method.name
              method_verb = method.verb
              method_path = method.path
              
              if method.has_file:
                  # File upload method
                  ts_method = f"""
      async {method_name}(file: File): Promise<any> {{
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('${{API_BASE}}/api/{key}{method_path}', {{
          method: '{method_verb}',
          body: formData
        }});
        if (!res.ok) throw new Error('API error: ${{res.status}}');
        return res.json();
      }}"""
              else:
                  # JSON method
                  ts_method = f"""
      async {method_name}(data: any): Promise<any> {{
        const res = await fetch('${{API_BASE}}/api/{key}{method_path}', {{
          method: '{method_verb}',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(data)
        }});
        if (!res.ok) throw new Error('API error: ${{res.status}}');
        return res.json();
      }}"""
              
              feature_methods.append(ts_method)
          
          methods_code.append(f"""
    {safe_key}: {{
      {','.join(feature_methods)}
    }}""")
      
      return f"""
  const API_BASE = import.meta.env.VITE_API_URL || "";

  export const api = {{
    {','.join(methods_code)}
  }};

  // Helper for error handling
  export class ApiError extends Error {{
    constructor(public status: number, message: string) {{
      super(message);
      this.name = 'ApiError';
    }}
  }}
  """
    
    def _copy_components(self, feature_keys: List[str]) -> Dict[str, str]:
        """Copy feature components"""
        files = {}
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest or not manifest.paths.generator_frontend:
                continue
            
            comp_path = os.path.join(manifest.base_path, manifest.paths.generator_frontend)
            if os.path.exists(comp_path):
                with open(comp_path, 'r', encoding='utf-8') as f:
                    safe_key = key.replace('-', '_')
                    files[f'frontend/src/features/{safe_key}/component.tsx'] = f.read()
        
        return files
    
    def _generate_boilerplate(self) -> Dict[str, str]:
        """Generate boilerplate files"""
        return {
            'frontend/package.json': self._get_package_json(),
            'frontend/index.html': self._get_index_html(),
            'frontend/vite.config.ts': self._get_vite_config(),
            'frontend/src/main.tsx': self._get_main_tsx(),
            'frontend/src/index.css': '@tailwind base;\n@tailwind components;\n@tailwind utilities;',
            'frontend/tailwind.config.js': 'export default { content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"], theme: { extend: {} }, plugins: [] }',
            'frontend/postcss.config.js': 'export default { plugins: { tailwindcss: {}, autoprefixer: {} } }'
        }
    
    def _get_package_json(self) -> str:
        return f'''{{
  "name": "{self.project_name.lower().replace(' ', '-')}",
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
}}'''
    
    def _get_index_html(self) -> str:
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{self.project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
    
    def _get_vite_config(self) -> str:
        return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})'''
    
    def _get_main_tsx(self) -> str:
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''