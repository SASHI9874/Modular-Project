import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any

# Where we save user modules. 
# We resolve path relative to this file to be safe.
USER_MODULES_DIR = Path(__file__).resolve().parent.parent.parent / "modules_repo" / "user_defined"

class ModuleGenerator:
    def save_module(self, name: str, graph: Dict, requirements: List[str]) -> Dict:
        """
        Saves a graph as a reusable module using the Wrapper Strategy.
        """
        # 1. Sanitize Name (e.g., "My Super Workflow" -> "my_super_workflow")
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(" ", "_"))
        module_dir = USER_MODULES_DIR / safe_name
        module_dir.mkdir(parents=True, exist_ok=True)

        # 2. Analyze Inputs & Outputs (The Interface)
        interface = self._detect_interface(graph, name, safe_name)

        # 3. Save Artifacts
        
        # A. graph.json (The Blueprint)
        with open(module_dir / "graph.json", "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2)

        # B. meta.json (The Definition)
        with open(module_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(interface, f, indent=2)

        # C. requirements.txt (Dependencies)
        with open(module_dir / "requirements.txt", "w", encoding="utf-8") as f:
            unique_reqs = list(set(requirements))
            f.write("\n".join(unique_reqs))

        # D. source.py (The Wrapper Code)
        # CRITICAL CHANGE: This now writes the "Wrapper" code, not linear logic
        source_code = self._generate_wrapper_code(safe_name)
        with open(module_dir / "source.py", "w", encoding="utf-8") as f:
            f.write(source_code)
        
        # E. __init__.py (Make it importable)
        (module_dir / "__init__.py").touch()

        return {"status": "success", "module_id": f"user_defined.{safe_name}"}

    def _detect_interface(self, graph: Dict, original_name: str, safe_name: str) -> Dict:
        """
        Defines how this module looks in the sidebar.
        """
        # For V1, we expose a single "workflow_inputs" dictionary.
        # In V2, you could scan the graph for specific 'Input Nodes' to make this granular.
        inputs = [{
            "name": "workflow_inputs",
            "type": "dict", 
            "label": "Workflow Inputs",
            "description": "Dictionary of inputs matching the unconnected nodes in the graph."
        }]

        return {
            "id": safe_name,
            "name": original_name,
            "description": "User-generated workflow module.",
            "class_name": "CustomWorkflowWrapper", 
            "inputs": inputs,
            "outputs": [{"name": "result", "type": "any"}]
        }

    def _generate_wrapper_code(self, module_name: str) -> str:
        """
        Generates the python code that bridges the Module -> WorkflowRunner.
        """
        return f"""
import json
import os
from pathlib import Path
import sys

# Import the centralized runner
from app.services.workflow_runner import WorkflowRunner

# Locate the graph.json relative to THIS file
CURRENT_DIR = Path(__file__).parent
GRAPH_PATH = CURRENT_DIR / "graph.json"
REQS_PATH = CURRENT_DIR / "requirements.txt"

class CustomWorkflowWrapper:
    def __init__(self):
        self.runner = WorkflowRunner()
        
        # Load the graph definition
        with open(GRAPH_PATH, "r") as f:
            self.graph = json.load(f)
            
        # Load requirements
        self.reqs = []
        if REQS_PATH.exists():
            with open(REQS_PATH, "r") as f:
                self.reqs = [line.strip() for line in f if line.strip()]

    def run(self, workflow_inputs: dict = None):
        if workflow_inputs is None:
            workflow_inputs = {{}}

        # Execute using the synchronous helper
        try:
            result = self.runner.run_sub_workflow_sync(self.graph, self.reqs, workflow_inputs)
            
            if result['status'] == 'COMPLETED':
                # Return the full context (outputs of all nodes)
                return result['results']
            else:
                return {{ "error": result.get('message', 'Unknown Error') }}

        except Exception as e:
            return {{ "error": str(e) }}
"""