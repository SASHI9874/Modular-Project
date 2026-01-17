import os
import sys
import subprocess
import shutil
import uuid
import time
import json
from pathlib import Path

# Keep your existing constants
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "temp_workspaces"
GLOBAL_VENV_PATH = WORKSPACE_DIR / "global_venv"
CACHE_DIR = BASE_DIR / "cached_libs"
CACHED_LIBRARIES = ["requests", "numpy", "pandas", "matplotlib"]

class VenvExecutor:
    def __init__(self):
        self.WORKSPACE_DIR = WORKSPACE_DIR 
        self.WORKSPACE_DIR.mkdir(exist_ok=True)
        self.python_exe, self.pip_exe = self._ensure_global_venv()
        self._ensure_cache_layer()

    def _ensure_global_venv(self):
        """Creates the master python environment if missing."""
        if not GLOBAL_VENV_PATH.exists():
            print("⚙️  Creating base global venv...")
            GLOBAL_VENV_PATH.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, "-m", "venv", str(GLOBAL_VENV_PATH)], check=True)
            
            # Install pip update
            if os.name == 'nt':
                python = GLOBAL_VENV_PATH / "Scripts" / "python.exe"
            else:
                python = GLOBAL_VENV_PATH / "bin" / "python"
                
            subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)

        if os.name == 'nt':
            return GLOBAL_VENV_PATH / "Scripts" / "python.exe", GLOBAL_VENV_PATH / "Scripts" / "pip.exe"
        else:
            return GLOBAL_VENV_PATH / "bin" / "python", GLOBAL_VENV_PATH / "bin" / "pip"

    def _ensure_cache_layer(self):
        """Pre-installs heavy libraries into a shared folder."""
        if not CACHE_DIR.exists():
            print(f"📦 Building Shared Library Cache in {CACHE_DIR}...")
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [str(self.pip_exe), "install"] + CACHED_LIBRARIES + ["--target", str(CACHE_DIR)],
                check=True
            )

    def _safe_delete(self, path: Path):
        """Robust deletion helper."""
        if not path.exists(): return
        for i in range(3):
            try:
                shutil.rmtree(path, ignore_errors=True)
                return
            except Exception:
                time.sleep(0.5)

    # ==========================================
    #  PHASE 1 UPGRADE: SESSION MANAGEMENT
    # ==========================================

    def create_session(self, requirements: list) -> str:
        """
        1. Creates a workspace folder.
        2. Installs requirements ONCE.
        3. Returns session_id.
        """
        session_id = str(uuid.uuid4())
        session_dir = WORKSPACE_DIR / session_id
        local_site_packages = session_dir / "site_packages"
        local_site_packages.mkdir(parents=True, exist_ok=True)

        # Filter and install specific requirements for this workflow
        to_install = []
        if requirements:
            for req in requirements:
                clean_name = req.split("==")[0].lower()
                if clean_name not in CACHED_LIBRARIES:
                    to_install.append(req)

        if to_install:
            try:
                subprocess.run(
                    [str(self.pip_exe), "install"] + to_install + ["--target", str(local_site_packages)],
                    check=True, capture_output=True
                )
            except subprocess.CalledProcessError as e:
                # If install fails, cleanup and raise
                self._safe_delete(session_dir)
                raise RuntimeError(f"Failed to install requirements: {e.stderr.decode()}")

        return session_id

    def run_in_session(self, session_id: str, code: str, inputs: dict = None) -> dict:
        """
        Runs a specific snippet of code inside an EXISTING session.
        Does NOT delete the session afterwards.
        """
        session_dir = WORKSPACE_DIR / session_id
        if not session_dir.exists():
            return {"status": "error", "stderr": "Session expired or not found"}

        local_site_packages = session_dir / "site_packages"
        
        # 1. Write Code to a step file
        # We use a unique name so we don't overwrite previous steps
        step_id = uuid.uuid4().hex[:8]
        script_path = session_dir / f"step_{step_id}.py"
        script_path.write_text(code, encoding="utf-8")

        # 2. Serialize Inputs (Pass inputs as a JSON string argument)
        input_json = json.dumps(inputs) if inputs else "{}"

        # 3. Prepare Environment
        # Inject the session's local packages + global cache + modules_repo
        repo_path = BASE_DIR / "modules_repo"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        
        env["PYTHONPATH"] = (
            f"{str(local_site_packages)}"
            f"{os.pathsep}{str(CACHE_DIR)}"
            f"{os.pathsep}{str(repo_path)}" # IMPORTANT: Allows importing your modules
            f"{os.pathsep}{existing_pythonpath}"
        )

        # 4. Execute
        try:
            result = subprocess.run(
                [str(self.python_exe), str(script_path), input_json],
                cwd=str(session_dir), # Run inside the session folder
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30 # Safety limit
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
             return {"status": "error", "stderr": "Execution timed out (30s limit)."}
        except Exception as e:
            return {"status": "error", "stderr": str(e)}

    def close_session(self, session_id: str):
        """Clean up the folder when the user is done."""
        session_dir = WORKSPACE_DIR / session_id
        self._safe_delete(session_dir)