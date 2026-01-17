import json
from fastapi import APIRouter, Form, HTTPException
from app.services.module_generator import USER_MODULES_DIR

router = APIRouter(prefix="/builder", tags=["Save Module"])

@router.post("/save-module")
async def save_module(
    name: str = Form(...),
    graph_json: str = Form(...),
    reqs_json: str = Form(...)
):
    try:
        graph = json.loads(graph_json)
        nodes = graph['nodes']
        edges = graph['edges']
        
        # --- 1. SMART METADATA GENERATION ---
        # We need to calculate what inputs/outputs this new 'Super Node' should have.
        
        # A. Find Inputs: (Inputs of internal nodes that are NOT connected to anything internal)
        # Set of all target handles filled by internal edges
        filled_inputs = set()
        for edge in edges:
            # edge['target'] is the node ID, edge['targetHandle'] is the input name
            filled_inputs.add(f"{edge['target']}.{edge['targetHandle']}")

        module_inputs = []
        for node in nodes:
            # For each node, look at its defined inputs
            # Note: In a real app, we'd look up the node's feature_id meta. 
            # For prototype, we check node['data']['inputs'] definition if available, 
            # or we rely on the generic 'inputs' list passed from frontend.
            
            # Simplified Strategy: 
            # If the node is a "Input" type (like File Uploader), it defines the module's behavior.
            # If it's a processing node, its unconnected inputs become module inputs.
            
            node_inputs = node.get('data', {}).get('inputs', [])
            for inp in node_inputs:
                input_id = f"{node['id']}.{inp['name']}"
                if input_id not in filled_inputs:
                    # This input is exposed!
                    # Rename it nicely: "NodeName_InputName"
                    module_inputs.append({
                        "name": f"{node['data']['label']}_{inp['name']}".replace(" ", "_").lower(),
                        "type": inp['type'],
                        "internal_node": node['id'], # Save mapping for runner
                        "internal_input": inp['name']
                    })

        # B. Find Outputs: (Outputs of nodes that are not source of any edge? Or just Terminal nodes?)
        # Simplest: The output of the LAST node in the list (assuming topological sort) or specific types.
        # Let's just expose the outputs of ALL nodes for now to be safe/flexible.
        module_outputs = []
        for node in nodes:
             outputs = node.get('data', {}).get('outputs', [])
             for out in outputs:
                 module_outputs.append({
                     "name": f"{node['data']['label']}_{out['name']}".replace(" ", "_").lower(),
                     "type": out['type']
                 })


        # --- 2. CREATE FOLDER STRUCTURE ---
        safe_name = name.lower().replace(" ", "_")
        feature_id = f"user_defined.{safe_name}"
        module_dir = USER_MODULES_DIR / safe_name
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "__init__.py").touch()

        # Save Graph
        with open(module_dir / "graph.json", "w") as f:
            json.dump(graph, f, indent=2)

        # Save Meta
        meta = {
            "id": feature_id,
            "name": name,
            "description": "User created module",
            "category": "Custom",
            "inputs": module_inputs,
            "outputs": module_outputs, 
            "class_name": "WrapperModule" # Generic wrapper class
        }
        with open(module_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        # Create Wrapper Source Code
        # This wrapper uses WorkflowRunner to execute the saved graph.
        source_code = f"""
from app.services.workflow_runner import WorkflowRunner
import json
from pathlib import Path

class WrapperModule:
    def __init__(self):
        self.runner = WorkflowRunner()
        # Load the graph relative to this file
        base_path = Path(__file__).parent
        with open(base_path / "graph.json", "r") as f:
            self.graph = json.load(f)

    def run(self, **kwargs):
        # 1. Map External Inputs to Internal Context
        # (This simplistic runner assumes inputs match exactly or passed to context)
        # In a real impl, we would map 'file_uploader_file_path' -> node_id.input
        
        # For V1: We pass kwargs directly into the context
        initial_context = kwargs
        
        # 2. Run the Sub-Workflow
        print(f"🔄 Running Custom Module: {name}")
        result = self.runner.run_sub_workflow_sync(self.graph, [], initial_context)
        
        if result['status'] == 'COMPLETED':
            # Flatten results: Return all node outputs
            # In V2 we would filter this based on meta['outputs']
            final_output = {{}}
            for node_id, res in result['results'].items():
                if isinstance(res, dict):
                    final_output.update(res)
                else:
                    final_output[node_id] = res
            return final_output
            
        elif result['status'] == 'PAUSED':
            # BUBBLE UP PAUSE
            # This is critical for File Uploads inside saved modules!
            return result
            
        else:
            raise RuntimeError(f"Custom Module Failed: {{result.get('message')}}")
"""
        with open(module_dir / "source.py", "w",encoding="utf-8") as f:
            f.write(source_code)

        return {"status": "success", "module_id": f"user_defined.{safe_name}"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))