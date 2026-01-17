from app.services.workflow_runner import WorkflowRunner
import json
import uuid
from pathlib import Path

class WrapperModule:
    def __init__(self):
        self.runner = WorkflowRunner()
        base_path = Path(__file__).parent
        
        with open(base_path / "graph.json", "r") as f:
            self.graph = json.load(f)

        # Try loading meta.json for input mapping
        meta_path = base_path / "meta.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                self.meta = json.load(f)
        else:
            self.meta = {"inputs": []}

    def run(self, **kwargs):
        # 1. Create a specific session for this run
        sub_session_id = str(uuid.uuid4())
        self.runner.create_session(sub_session_id, self.graph)
        session = self.runner.sessions[sub_session_id]

        # 2. Map Inputs (External -> Internal Manual Inputs)
        if "manual_inputs" not in session:
            session["manual_inputs"] = {}

        mapped_keys = set()
        for input_def in self.meta.get("inputs", []):
            external_name = input_def["name"]
            
            if external_name in kwargs:
                internal_node = input_def.get("internal_node")
                internal_input = input_def.get("internal_input")
                
                if internal_node and internal_input:
                    if internal_node not in session["manual_inputs"]:
                        session["manual_inputs"][internal_node] = {}
                    
                    # Store in manual_inputs so node finds it
                    session["manual_inputs"][internal_node][internal_input] = kwargs[external_name]
                    mapped_keys.add(external_name)

        # 3. Fallback: Add unmapped inputs to context (for generic nodes)
        remaining_inputs = {k: v for k, v in kwargs.items() if k not in mapped_keys}
        
        # 4. Run the Sub-Workflow with the EXISTING ID
        print(f"🔄 Running Custom Module: {self.meta.get('name', 'Unknown')}")
        
        # ✅ FIX: Pass existing_session_id and remaining context
        result = self.runner.run_sub_workflow_sync(
            self.graph, 
            [], 
            remaining_inputs, 
            existing_session_id=sub_session_id
        )
        
        if result['status'] == 'COMPLETED':
            final_output = {}
            for node_id, res in result['results'].items():
                if isinstance(res, dict):
                    final_output.update(res)
                else:
                    final_output[node_id] = res
            return final_output
            
        elif result['status'] == 'PAUSED':
            return result
            
        else:
            raise RuntimeError(f"Custom Module Failed: {result.get('message')}")