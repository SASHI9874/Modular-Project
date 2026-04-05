import os
import json
from typing import Dict, Any, List, Set
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class BackendGenerator:
    """Generates FastAPI backend code"""

    def __init__(self, project_name: str):
        self.project_name = project_name

    def generate(
        self,
        feature_keys: List[str],
        frontend_mode: str = 'generated_ui',
        graph_data: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Generate all backend files.
        Returns dict: {filepath: content}
        """
        print(f" [BackendGen] Generating backend (mode: {frontend_mode})...")

        files = {}

        try:
            # Generate main app.py
            main_app = self._generate_main_app(feature_keys, frontend_mode)
            files['backend/app.py'] = main_app

            # Generate requirements.txt
            requirements = self._generate_requirements(feature_keys)
            files['backend/requirements.txt'] = requirements

            # Copy feature files into backend/library/
            feature_files = self._copy_feature_files(feature_keys)
            files.update(feature_files)

            # Package runtime engine + graph 
            runtime_files = self._package_runtime(graph_data)
            files.update(runtime_files)

            print(f" [BackendGen] Generated {len(files)} files")
            return files

        except Exception as e:
            print(f" [BackendGen] Error: {e}")
            raise CodeGenerationError(f"Backend generation failed: {e}")


    # app.py generation
    # -------------------------------------------------------------------------

    def _generate_main_app(
        self,
        feature_keys: List[str],
        frontend_mode: str
    ) -> str:
        """
        Generate main FastAPI app.py.
        The universal run endpoints vary by frontend_mode:
          generated_ui       → POST /api/run  +  GET /api/run/stream (SSE)
          external_extension → WS  /api/run/ws  +  POST /api/run (fallback)
          headless / cli     → POST /api/run only
        Feature routes are health-check only — all execution goes
        through GraphExecutor via /api/run.
        """
        imports = []
        registrations = []

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            safe_key = key.replace('-', '_')
            imports.append(
                f"from library.{safe_key} import routes as {safe_key}_routes"
            )
            registrations.append(
                f"app.include_router({safe_key}_routes.router, "
                f"prefix='/api/{key}', tags=['{key}'])"
            )

        imports_str = "\n".join(imports)
        registrations_str = "\n".join(registrations)

        # Build the transport-specific run endpoints
        run_endpoints = self._generate_run_endpoints(frontend_mode)

        return f'''import json
import asyncio
import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, Optional
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from executor import GraphExecutor
from library_service import LibraryService

load_dotenv()

# Feature routers (health-check endpoints only)
{imports_str}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="{self.project_name}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register feature health-check routes
{registrations_str}

# ── Graph setup ───────────────────────────────────────────────────────────────
with open("graph.json", "r") as f:
    _graph_data = json.load(f)

_graph = {{
    "nodes": _graph_data.get("nodes") or _graph_data.get("graph", {{}}).get("nodes", []),
    "edges": _graph_data.get("edges") or _graph_data.get("graph", {{}}).get("edges", []),
}}

# ── Payload schema ────────────────────────────────────────────────────────────
class RunPayload(BaseModel):
    entry_node_id: str
    inputs: Dict[str, Any]
    session_id: Optional[str] = None


# ── Universal run endpoints ───────────────────────────────────────────────────
{run_endpoints}

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    return {{"status": "running", "project": "{self.project_name}"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _generate_run_endpoints(self, frontend_mode: str) -> str:
        """
        Return the run endpoint block for app.py based on frontend_mode.
        All modes include POST /api/run.
        generated_ui       adds GET  /api/run/stream  (SSE)
        external_extension adds WS   /api/interface-vscode/ws/vscode (WebSocket)
        """

        # POST /api/run — always present in every mode
        base_run = '''
    @app.post("/api/run")
    async def run_graph(payload: RunPayload):
        """Execute the full graph and return the final result."""
        executor = GraphExecutor(_graph)
        results = executor.run(
            entry_node_id=payload.entry_node_id,
            initial_inputs=payload.inputs,
        )

        for node_id, data in results.items():
            if isinstance(data, dict) and data.get("is_final_output"):
                return {
                    "status": "success",
                    "output": data.get("final_text"),
                    "debug": results,
                }

        return {"status": "success", "results": results}
    '''

        # GET /api/run/stream — SSE streaming, added for generated_ui
        sse_stream = '''
    @app.get("/api/run/stream")
    async def stream_graph(entry_node_id: str, inputs: str, session_id: Optional[str] = None):
        """
        Execute the graph and stream output tokens via Server-Sent Events.
        `inputs` is a JSON-encoded string: e.g. {"message": "hello"}
        """
        parsed_inputs = json.loads(inputs)

        def event_stream():
            executor = GraphExecutor(_graph)
            results = executor.run(
                entry_node_id=entry_node_id,
                initial_inputs=parsed_inputs,
            )

            output = None
            for node_id, data in results.items():
                if isinstance(data, dict) and data.get("is_final_output"):
                    output = data.get("final_text", "")
                    break

            if output is None:
                for node_id, data in results.items():
                    if isinstance(data, dict) and data.get("response"):
                        output = data["response"]
                        break

            if output:
                for word in output.split(" "):
                    yield f"data: {json.dumps({'token': word + ' '})}\\'\\n\\n"

            yield "data: [DONE]\\'\\n\\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    '''

        # WS — VS Code extension protocol
        ws_endpoint = '''
    @app.websocket("/api/interface-vscode/ws/vscode")
    async def websocket_vscode(websocket: WebSocket):
        """
        VS Code extension WebSocket endpoint.

        Extension → Backend:
        user_message         { type, message, context }
        autocomplete_request { type, id, context: { prefix, suffix } }
        tool_response        { type, id, content?, error? }

        Backend → Extension:
        stream_chunk         { type, content }
        stream_end           { type }
        agent_response       { type, content }
        autocomplete_response { type, id, content }
        error                { type, content }
        """
        await websocket.accept()
        print(" VS Code extension connected")

        # Find trigger node id once at connection time
        trigger_node_id = next(
            (n["id"] for n in _graph["nodes"]
            if n.get("data", {}).get("featureType") == "trigger"),
            None
        )

        try:
            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                msg_type = payload.get("type")
                print(f"[WS] Received: {msg_type}")

                # ── user_message ──────────────────────────────────────────────────
                if msg_type == "user_message":
                    message = payload.get("message", "")
                    context = payload.get("context", {})

                    if not trigger_node_id:
                        await websocket.send_json({
                            "type": "error",
                            "content": "No trigger node found in graph"
                        })
                        continue

                    try:
                        executor = GraphExecutor(_graph)
                        results = executor.run(
                            entry_node_id=trigger_node_id,
                            initial_inputs={
                                "message": message,
                                "context": context,
                                "workspace_root": context.get("workspace_root", ""),
                                "file_path": context.get("file_path", ""),
                                "file_content": context.get("file_content", ""),
                            },
                        )

                        # Find output — prefer flagged final output, fallback to any response
                        output = None
                        for node_id, result_data in results.items():
                            if isinstance(result_data, dict):
                                if result_data.get("is_final_output"):
                                    output = result_data.get("final_text", "")
                                    break
                                if result_data.get("response") and output is None:
                                    output = result_data["response"]

                        output = output or "No response"

                        # Stream word by word
                        for word in output.split(" "):
                            await websocket.send_json({
                                "type": "stream_chunk",
                                "content": word + " "
                            })
                            await asyncio.sleep(0.01)

                        # Signal stream complete
                        await websocket.send_json({"type": "stream_end"})

                        # Send full response so extension saves to history
                        await websocket.send_json({
                            "type": "agent_response",
                            "content": output
                        })

                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        await websocket.send_json({
                            "type": "error",
                            "content": str(e)
                        })

                # ── autocomplete_request ──────────────────────────────────────────
                elif msg_type == "autocomplete_request":
                    request_id = payload.get("id")
                    ctx = payload.get("context", {})
                    prefix = ctx.get("prefix", "")
                    suffix = ctx.get("suffix", "")

                    try:
                        # Use FIM prompt through the graph
                        fim_prompt = (
                            f"Complete the following code. "
                            f"Only output the completion, nothing else.\\n\\n"
                            f"CODE BEFORE CURSOR:\\n{prefix[-500:]}\\n\\n"
                            f"CODE AFTER CURSOR:\\n{suffix[:200]}\\n\\n"
                            f"COMPLETION:"
                        )

                        executor = GraphExecutor(_graph)
                        results = executor.run(
                            entry_node_id=trigger_node_id,
                            initial_inputs={"message": fim_prompt},
                        )

                        completion = None
                        for node_id, result_data in results.items():
                            if isinstance(result_data, dict) and result_data.get("response"):
                                completion = result_data["response"]
                                break

                        await websocket.send_json({
                            "type": "autocomplete_response",
                            "id": request_id,
                            "content": completion or ""
                        })

                    except Exception as e:
                        # Always respond — extension has a 2.5s timeout waiting for this
                        print(f"[WS] Autocomplete error: {e}")
                        await websocket.send_json({
                            "type": "autocomplete_response",
                            "id": request_id,
                            "content": ""
                        })

                # ── tool_response ─────────────────────────────────────────────────
                elif msg_type == "tool_response":
                    # Extension executed a local tool (read_file, edit_file etc.)
                    # and is returning the result back to the agent loop.
                    # Logged for now — resuming a paused agent loop requires
                    # async executor state which is a future enhancement.
                    request_id = payload.get("id")
                    error = payload.get("error")
                    print(f"[WS] Tool response for {request_id}: error={error}")

                else:
                    print(f"[WS] Unknown message type: {msg_type}")

        except WebSocketDisconnect:
            print(" VS Code extension disconnected")
        except Exception as e:
            print(f"WebSocket error: {e}")
    '''

        # Assemble based on mode
        if frontend_mode == 'generated_ui':
            return base_run + sse_stream

        elif frontend_mode == 'external_extension':
            return base_run + ws_endpoint

        else:
            # headless, cli — POST /api/run only
            return base_run

    # Requirements
    # -------------------------------------------------------------------------

    def _generate_requirements(self, feature_keys: List[str]) -> str:
        """
        Merge requirements.txt from all activated features.
        Base deps always included.
        """
        requirements: Set[str] = {
            "fastapi",
            "uvicorn",
            "python-multipart",
            "networkx",   # GraphExecutor uses this
            "pydantic",
            "python-dotenv",
        }

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            req_path = os.path.join(manifest.base_path, "requirements.txt")
            if os.path.exists(req_path):
                with open(req_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            requirements.add(line)

        return "\n".join(sorted(requirements))

    # -------------------------------------------------------------------------
    # Feature file copying
    # -------------------------------------------------------------------------

    def _copy_feature_files(self, feature_keys: List[str]) -> Dict[str, str]:
        """
        Copy feature source files into backend/library/{safe_key}/.
        Structure preserved:
          backend/library/{key}/feature.spec.json
          backend/library/{key}/runtime/adapter.py
          backend/library/{key}/core/...
          backend/library/{key}/routes.py   ← health-check only
          backend/library/{key}/__init__.py
        """
        files = {}

        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue

            safe_key = key.replace('-', '_')
            dest_base = f'backend/library/{safe_key}'

            # Copy feature.spec.json
            spec_path = os.path.join(manifest.base_path, "feature.spec.json")
            if os.path.exists(spec_path):
                with open(spec_path, "r", encoding="utf-8") as f:
                    files[f'{dest_base}/feature.spec.json'] = f.read()

            # Copy runtime/adapter.py
            if manifest.paths.runtime:
                runtime_path = os.path.join(
                    manifest.base_path, manifest.paths.runtime
                )
                if os.path.exists(runtime_path):
                    with open(runtime_path, "r", encoding="utf-8") as f:
                        files[f'{dest_base}/runtime/adapter.py'] = f.read()
                    files[f'{dest_base}/runtime/__init__.py'] = ''

            # Copy entire core/ directory
            if manifest.paths.core:
                core_target = os.path.join(manifest.base_path, manifest.paths.core)
                core_dir = (
                    os.path.dirname(core_target)
                    if os.path.isfile(core_target)
                    else core_target
                )

                if os.path.isdir(core_dir):
                    parent_dir = os.path.dirname(os.path.normpath(core_dir))

                    for root, _, filenames in os.walk(core_dir):
                        for filename in filenames:
                            if (
                                filename.endswith('.pyc')
                                or '__pycache__' in root
                                or filename.startswith('.')
                            ):
                                continue

                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, parent_dir)
                            dest_path = f'{dest_base}/{rel_path}'

                            with open(file_path, "r", encoding="utf-8") as f:
                                files[dest_path] = f.read()

            # Generate health-check only routes.py
            # Execution always goes through /api/run → GraphExecutor
            files[f'{dest_base}/routes.py'] = self._generate_health_routes(
                key, manifest
            )

            # __init__.py
            files[f'{dest_base}/__init__.py'] = (
                f'"""{manifest.name} Feature"""\nfrom . import routes\n'
                f'__all__ = ["routes"]\n'
            )

        # Empty __init__.py at library root so it's importable
        files['backend/library/__init__.py'] = ''

        return files

    def _generate_health_routes(self, feature_key: str, manifest) -> str:
        """
        Generate health-check only routes for a feature.
        All execution goes through /api/run → GraphExecutor.
        No /execute route.
        """
        capability = manifest.classification.capability

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
        "version": "{manifest.version}",
    }}

@router.get("/info")
async def info():
    """Feature information"""
    return {{
        "key": "{feature_key}",
        "name": "{manifest.name}",
        "version": "{manifest.version}",
        "capability": "{capability}",
        "description": "{manifest.description}",
    }}
'''
    
    def _package_runtime(self, graph_data: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Package the runtime engine files into the zip.
        These are the three files that make the downloaded project
        executable without any platform dependency:
        - executor.py       (GraphExecutor — the orchestration engine)
        - library_service.py (LibraryService — dynamic feature loader)
        - feature_spec.py   (Pydantic models — shared schema)
        - graph.json        (the user's graph — the "program" being run)
        """
        files = {}

        # Resolve platform source root
        # executor_service.py is at backend/app/services/executor_service.py
        # So platform root is 3 levels up from this file's location.
        # __file__ here is BackendGenerator's file inside the platform.
        platform_root = self._get_platform_root()

        # ── executor.py ───────────────────────────────────────────────────────────
        executor_src = platform_root / "app" / "services" / "executor_service.py"

        if executor_src.exists():
            content = executor_src.read_text(encoding="utf-8")

            #  platform import → standalone import
            content = content.replace(
                "from app.services.library_service import library_service",
                "from library_service import library_service"
            )

            files['backend/executor.py'] = content
            print("    [BackendGen] Packaged executor.py")
        else:
            print(f"    [BackendGen] WARNING: executor_service.py not found at {executor_src}")

        # ── library_service.py ────────────────────────────────────────────────────
        library_src = platform_root / "app" / "services" / "library_service.py"

        if library_src.exists():
            content = library_src.read_text(encoding="utf-8")

            #  platform schema import → standalone import
            content = content.replace(
                "from app.schemas.feature_spec import FeatureManifest",
                "from feature_spec import FeatureManifest"
            )

            #  path resolution — 3-level parent → sibling library/ folder
            content = content.replace(
                "base_dir = FilePath(__file__).resolve().parent.parent.parent\n"
                "        self.library_path = base_dir / \"library\"",
                "self.library_path = FilePath(\n"
                "            os.getenv(\"LIBRARY_PATH\",\n"
                "            str(FilePath(__file__).resolve().parent / \"library\"))\n"
                "        )"
            )

            files['backend/library_service.py'] = content
            print("    [BackendGen] Packaged library_service.py")
        else:
            print(f"    [BackendGen] WARNING: library_service.py not found at {library_src}")

        # ── feature_spec.py ───────────────────────────────────────────────────────
        spec_src = platform_root / "app" / "schemas" / "feature_spec.py"

        if spec_src.exists():
            # No rewrites needed — only standard library imports
            files['backend/feature_spec.py'] = spec_src.read_text(encoding="utf-8")
            print("    [BackendGen] Packaged feature_spec.py")
        else:
            print(f"    [BackendGen] WARNING: feature_spec.py not found at {spec_src}")

        # ── graph.json ────────────────────────────────────────────────────────────
        if graph_data:
            files['backend/graph.json'] = json.dumps(graph_data, indent=2)
            print("    [BackendGen] Packaged graph.json")
        else:
            print("    [BackendGen] WARNING: graph_data is None — graph.json not packaged")

        return files


    def _get_platform_root(self):
        """
        Resolve the platform's backend root directory.
        This file (backend_generator.py) lives somewhere inside
        backend/app/services/packager/...
        Walking up to backend/ gives us the platform root.
        """
        from pathlib import Path
        # Walk up until we find a directory containing 'app/'
        current = Path(__file__).resolve().parent
        for _ in range(6):  # safety limit
            if (current / "app").is_dir() and (current / "app" / "services").is_dir():
                return current
            current = current.parent

        raise RuntimeError(
            f"Could not resolve platform root from {Path(__file__).resolve()}. "
            "Expected to find backend/ containing app/services/."
        )