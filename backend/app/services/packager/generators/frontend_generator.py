import os
from typing import Dict, Any, List, Optional
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class FrontendGenerator:
    """Generates React frontend code"""

    def __init__(self, project_name: str, graph_data: Dict[str, Any] = None):
        self.project_name = project_name
        self.graph_data = graph_data or {}

    # Public entry point
    # -------------------------------------------------------------------------

    def generate(
        self, feature_keys: List[str], mode: str = 'generated_ui') -> Dict[str, str]:
        """
        Generate frontend files based on mode.
        Returns dict: {filepath: content}
        """
        print(f" [FrontendGen] Generating frontend (mode: {mode})...")

        files = {}

        try:
            if mode == 'headless':
                print("     Skipping frontend (headless mode)")
                return files

            elif mode == 'external_extension':
                print("     Extension mode - no frontend")
                return files

            elif mode == 'generated_ui':
                files.update(self._generate_react_ui(feature_keys))

            print(f" [FrontendGen] Generated {len(files)} files")
            return files

        except Exception as e:
            print(f" [FrontendGen] Error: {e}")
            raise CodeGenerationError(f"Frontend generation failed: {e}")

    # React UI orchestration
    # -------------------------------------------------------------------------

    def _generate_react_ui(self, feature_keys: List[str]) -> Dict[str, str]:
        """Generate all React UI files"""
        files = {}

        #  config.ts — extracted from graph at package time
        files['frontend/src/config.ts'] = self._generate_config_ts()

        #  App.tsx — trigger nodes excluded, ChatInterface injected
        files['frontend/src/App.tsx'] = self._generate_app_tsx(feature_keys)

        # Store — typed context from feature contracts
        files['frontend/src/store.tsx'] = self._generate_store(feature_keys)

        #  API client — rebuilt from contract, not manifest.api
        files['frontend/src/client/api.ts'] = self._generate_api_client(feature_keys)

        #  ChatInterface static template
        files['frontend/src/components/ChatInterface.tsx'] = self._get_chat_interface_tsx()

        #  Copy feature components (trigger nodes excluded)
        component_files = self._copy_components(feature_keys)
        files.update(component_files)

        # Boilerplate
        files.update(self._generate_boilerplate())

        return files

    #  — config.ts
    # -------------------------------------------------------------------------

    def _generate_config_ts(self) -> str:
        """
        Generate config.ts from graph data at package time.
        Extracts trigger node id and input ports so ChatInterface
        never has hardcoded values.
        """
        trigger_node = self._find_trigger_node()

        entry_node_id = ""
        input_key = "message"       # safe default
        all_input_keys: List[str] = ["message"]

        if trigger_node:
            entry_node_id = trigger_node.get("id", "")
            outputs = trigger_node.get("data", {}).get("outputs", [])

            if outputs:
                all_input_keys = outputs
                # Primary key: prefer "message" if present, else first port
                input_key = "message" if "message" in outputs else outputs[0]

        all_input_keys_ts = (
            "[" + ", ".join(f'"{k}"' for k in all_input_keys) + "]"
        )

        return f"""// AUTO-GENERATED at package time — do not edit manually
// Re-download from the platform to update these values.

export const config = {{
  projectName: "{self.project_name}",
  apiUrl: import.meta.env.VITE_API_URL || "",
  entryNodeId: "{entry_node_id}",
  inputKey: "{input_key}",
  allInputKeys: {all_input_keys_ts},
  streamEndpoint: "/api/run/stream",
  runEndpoint: "/api/run",
}} as const;
"""

    def _find_trigger_node(self) -> Optional[Dict[str, Any]]:
        """Find the first trigger node in the graph."""
        nodes = (
            self.graph_data.get("nodes")
            or self.graph_data.get("graph", {}).get("nodes", [])
        )
        for node in nodes:
            if node.get("data", {}).get("featureType") == "trigger":
                return node
        return None

    # — ChatInterface.tsx static template
    # -------------------------------------------------------------------------

    def _get_chat_interface_tsx(self) -> str:
        """
        Static ChatInterface template.
        - Reads entryNodeId and endpoints from config.ts (never hardcoded)
        - Tries SSE streaming first, falls back to POST /api/run
        - Abort controller for stop generation
        """
        return '''import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, StopCircle } from "lucide-react";
import { config } from "../config";

interface Message {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const appendToken = (token: string) => {
    setMessages((prev) => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + token };
      }
      return msgs;
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userText = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userText },
      { role: "assistant", content: "", isStreaming: true },
    ]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    // Build payload using config — nothing hardcoded
    const inputs = { [config.inputKey]: userText };
    const streamUrl =
      `${config.apiUrl}${config.streamEndpoint}` +
      `?entry_node_id=${encodeURIComponent(config.entryNodeId)}` +
      `&inputs=${encodeURIComponent(JSON.stringify(inputs))}`;

    let streamSucceeded = false;

    // ── Attempt 1: SSE streaming ─────────────────────────────────────────────
    try {
      const res = await fetch(streamUrl, { signal: controller.signal });

      if (res.ok && res.body) {
        streamSucceeded = true;
        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\\n");

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;
            const raw = line.slice(5).trim();
            if (raw === "[DONE]") break;
            try {
              const parsed = JSON.parse(raw);
              if (parsed.token) appendToken(parsed.token);
            } catch {
              // non-JSON line — skip
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        setIsStreaming(false);
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 ? { ...m, isStreaming: false } : m
          )
        );
        return;
      }
      // Stream failed — fall through to POST fallback
    }

    // ── Attempt 2: POST fallback ─────────────────────────────────────────────
    if (!streamSucceeded) {
      try {
        const res = await fetch(`${config.apiUrl}${config.runEndpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            entry_node_id: config.entryNodeId,
            inputs,
          }),
          signal: controller.signal,
        });

        if (res.ok) {
          const data = await res.json();
          const output =
            data.output ||
            data.results?.[Object.keys(data.results || {})[0]]?.response ||
            "No response";
          setMessages((prev) => {
            const msgs = [...prev];
            msgs[msgs.length - 1] = {
              role: "assistant",
              content: output,
              isStreaming: false,
            };
            return msgs;
          });
        } else {
          throw new Error(`HTTP ${res.status}`);
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          setMessages((prev) => {
            const msgs = [...prev];
            msgs[msgs.length - 1] = {
              role: "assistant",
              content: "Connection failed. Is the backend running?",
              isStreaming: false,
            };
            return msgs;
          });
        }
      }
    }

    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m, i) =>
        i === prev.length - 1 ? { ...m, isStreaming: false } : m
      )
    );
    abortRef.current = null;
  };

  const handleStop = () => {
    abortRef.current?.abort();
  };

  return (
    <div className="flex flex-col h-[600px] w-full bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-white p-4 border-b flex items-center gap-3 shadow-sm">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Bot className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-800">{config.projectName}</h3>
          <p className="text-xs text-gray-400">AI Agent</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-300 space-y-3">
            <Bot className="w-10 h-10 opacity-30" />
            <p className="text-sm">Send a message to start</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-white border border-gray-100 text-gray-800 rounded-bl-none shadow-sm"
              }`}
            >
              {m.content || (m.isStreaming && (
                <span className="animate-pulse text-gray-400">▍</span>
              ))}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !isStreaming && handleSend()}
            placeholder="Type a message..."
            disabled={isStreaming}
            className="flex-1 bg-gray-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
          {isStreaming ? (
            <button
              onClick={handleStop}
              className="p-3 bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-colors"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-40"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
'''

    #  — App.tsx (trigger nodes excluded, ChatInterface injected)
    # -------------------------------------------------------------------------

    def _generate_app_tsx(self, feature_keys: List[str]) -> str:
        """
        Generate App.tsx.
        Rules:
        - Trigger nodes (featureType == 'trigger') are never rendered
        - ChatInterface is always injected in the main area
        - Feature components go in sidebar or main based on placement
        """
        imports = []
        sidebar_components = []
        main_components = []

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            # Change 6: skip trigger nodes entirely
            if manifest.classification.capability == 'trigger':
                continue

            # Skip interface nodes — they have no UI component
            if manifest.classification.capability == 'interface':
                continue

            has_component = getattr(manifest.ui, 'has_component', False)
            if not has_component:
                continue

            safe_key = key.replace('-', '_')
            component_name = f"{safe_key.title().replace('_', '')}Widget"
            imports.append(
                f"import {component_name} from './features/{safe_key}/component';"
            )

            placement = getattr(manifest.ui, 'placement', 'main')
            if placement == 'sidebar':
                sidebar_components.append(f"<{component_name} />")
            else:
                main_components.append(f"<{component_name} />")

        imports_str = "\n".join(imports)
        sidebar_str = "\n            ".join(sidebar_components)
        main_str = "\n            ".join(main_components)

        return f"""import React from 'react';
import {{ AppProvider }} from './store';
import ChatInterface from './components/ChatInterface';
{imports_str}

export default function App() {{
  return (
    <AppProvider>
      <div className="flex h-screen bg-gray-50 font-sans">

        {{/* Sidebar — feature config widgets */}}
        <div className="w-80 bg-white border-r border-gray-200 p-6 flex flex-col gap-6 overflow-y-auto">
          <h1 className="text-xl font-semibold text-gray-800">{self.project_name}</h1>
          <div className="space-y-6">
            {sidebar_str or "<!-- no sidebar widgets -->"}
          </div>
        </div>

        {{/* Main — ChatInterface always present, then feature main widgets */}}
        <div className="flex-1 p-8 overflow-y-auto flex flex-col items-center gap-8">
          <div className="max-w-3xl w-full space-y-8">
            <ChatInterface />
            {main_str}
          </div>
        </div>

      </div>
    </AppProvider>
  );
}}
"""

    #  — API client rebuilt from contract
    # -------------------------------------------------------------------------

    def _generate_api_client(self, feature_keys: List[str]) -> str:
        """
        Generate typed API client from feature contracts.
        Execution always goes through config.ts endpoints (ChatInterface).
        This client provides typed helpers for health checks and feature info only.
        """
        health_methods = []

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            safe_key = key.replace('-', '_')
            health_methods.append(f"""
  {safe_key}: {{
    async health(): Promise<any> {{
      const res = await fetch(`${{API_BASE}}/api/{key}/health`);
      if (!res.ok) throw new ApiError(res.status, 'Health check failed');
      return res.json();
    }},
    async info(): Promise<any> {{
      const res = await fetch(`${{API_BASE}}/api/{key}/info`);
      if (!res.ok) throw new ApiError(res.status, 'Info fetch failed');
      return res.json();
    }},
  }},""")

        health_methods_str = "\n".join(health_methods)

        return f"""// AUTO-GENERATED — feature health-check client
// Execution (chat, agent runs) goes through ChatInterface → config.ts endpoints.

const API_BASE = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {{
  constructor(public status: number, message: string) {{
    super(message);
    this.name = "ApiError";
  }}
}}

export const api = {{
{health_methods_str}
}};
"""

    # _copy_components (trigger + interface nodes excluded)
    # -------------------------------------------------------------------------

    def _copy_components(self, feature_keys: List[str]) -> Dict[str, str]:
        """
        Copy feature components into the zip.
        Trigger and interface nodes are excluded — they have no UI
        in the downloaded project. ChatInterface replaces the trigger.
        """
        files = {}

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            # Change 6: exclude trigger and interface nodes
            capability = manifest.classification.capability
            if capability in ('trigger', 'interface'):
                continue

            if not manifest.paths.generator_frontend:
                continue

            comp_path = os.path.join(
                manifest.base_path, manifest.paths.generator_frontend
            )
            if os.path.exists(comp_path):
                safe_key = key.replace('-', '_')
                with open(comp_path, 'r', encoding='utf-8') as f:
                    files[f'frontend/src/features/{safe_key}/component.tsx'] = f.read()

        return files

    # Store
    # -------------------------------------------------------------------------

    def _generate_store(self, feature_keys: List[str]) -> str:
        """Generate typed React Context store from feature contracts"""
        state_fields = []
        initial_states = []
        context_values = []

        ts_type_map = {
            'string': 'string',
            'number': 'number',
            'boolean': 'boolean',
            'array': 'any[]',
            'object': 'any',
        }

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            # Skip triggers and interfaces — no state needed
            capability = manifest.classification.capability
            if capability in ('trigger', 'interface'):
                continue

            if not manifest.contract or not manifest.contract.outputs:
                continue

            safe_key = key.replace('-', '_')

            for out_key, field in manifest.contract.outputs.items():
                var_name = f"{safe_key}_{out_key}"
                ts_type = ts_type_map.get(getattr(field, 'type', 'object'), 'any')

                state_fields.append(f"  {var_name}: {ts_type} | null;")
                state_fields.append(
                    f"  set_{var_name}: (val: {ts_type} | null) => void;"
                )
                initial_states.append(
                    f"  const [{var_name}, set_{var_name}]"
                    f" = useState<{ts_type} | null>(null);"
                )
                context_values.append(f"    {var_name},")
                context_values.append(f"    set_{var_name},")

        if not state_fields:
            return """import React, { createContext, useContext } from 'react';

interface AppState {}
const AppContext = createContext<AppState>({});
export const AppProvider = ({ children }: { children: React.ReactNode }) => (
  <AppContext.Provider value={{}}>{children}</AppContext.Provider>
);
export const useAppStore = () => useContext(AppContext);
"""

        state_fields_str = "\n".join(state_fields)
        initial_states_str = "\n  ".join(initial_states)
        context_values_str = "\n".join(context_values)

        return f"""import React, {{ createContext, useContext, useState }} from 'react';

interface AppState {{
{state_fields_str}
}}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
  {initial_states_str}

  return (
    <AppContext.Provider value={{{{
{context_values_str}
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

    # Boilerplate
    # -------------------------------------------------------------------------

    def _generate_boilerplate(self) -> Dict[str, str]:
        return {
            'frontend/package.json': self._get_package_json(),
            'frontend/index.html': self._get_index_html(),
            'frontend/vite.config.ts': self._get_vite_config(),
            'frontend/src/main.tsx': self._get_main_tsx(),
            'frontend/src/index.css': (
                '@tailwind base;\n@tailwind components;\n@tailwind utilities;'
            ),
            'frontend/tailwind.config.js': (
                'export default { content: ["./index.html",'
                ' "./src/**/*.{js,ts,jsx,tsx}"], theme: { extend: {} }, plugins: [] }'
            ),
            'frontend/postcss.config.js': (
                'export default { plugins: { tailwindcss: {}, autoprefixer: {} } }'
            ),
        }

    def _get_package_json(self) -> str:
        safe_name = self.project_name.lower().replace(' ', '-')
        return f'''{{
  "name": "{safe_name}",
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