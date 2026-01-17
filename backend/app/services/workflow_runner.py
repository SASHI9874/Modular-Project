import importlib
import sys
import json
import uuid
import networkx as nx
from typing import List, Dict, Any, Tuple
from app.services.builder.utils import get_feature_metadata

GLOBAL_SESSIONS = {}

class WorkflowRunner:
    def __init__(self):
        # We NO LONGER initialize self.executor here
        self.sessions = GLOBAL_SESSIONS
    
    def create_session(self, session_id: str, graph: Dict) -> Dict:
        """
        Creates a session without running it. Used by WrapperModules to setup inputs.
        """
        nodes = {n['id']: n for n in graph['nodes']}
        edges = graph['edges']
        execution_order = self._get_execution_order(nodes, edges)

        self.sessions[session_id] = {
            "graph_nodes": nodes,
            "graph_edges": edges,
            "order": execution_order,
            "context": {}, 
            "manual_inputs": {}, 
            "status": "PENDING",
            "pending_input_name": None 
        }
        return self.sessions[session_id]

    def start_workflow(self, graph: Dict, requirements: List[str]) -> Dict:
        """
        Initializes a new workflow session and starts execution immediately.
        """
        # FIX: We generate ID directly. We DO NOT call self.executor.create_session() anymore.
        session_id = str(uuid.uuid4())

        nodes = {n['id']: n for n in graph['nodes']}
        edges = graph['edges']
        execution_order = self._get_execution_order(nodes, edges)

        self.sessions[session_id] = {
            "graph_nodes": nodes,
            "graph_edges": edges,
            "order": execution_order,
            "context": {}, 
            "manual_inputs": {}, 
            "status": "RUNNING",
            "pending_input_name": None 
        }

        # Run immediately
        return self.run_step(session_id)

    def resume_workflow(self, session_id: str, node_id: str, input_data: Any) -> Dict:
        """
        Resumes execution. Handles both Sub-Workflows and Standard Nodes.
        """
        if session_id not in self.sessions:
            return {"status": "ERROR", "message": "Session expired."}
        
        session = self.sessions[session_id]

        if "pending_sub_session_id" in session:
            sub_id = session["pending_sub_session_id"]

            if sub_id in self.sessions:
                child_session = self.sessions[sub_id]
                # Use the ID we saved in run_step, or fallback to the passed ID
                internal_node_id = child_session.get("pending_node_id", node_id)
            else:
                internal_node_id = node_id
            
            # Recursive call to resume the child session
            sub_result = self.resume_workflow(sub_id, node_id, input_data)
            
            if sub_result['status'] == 'COMPLETED':
                # Sub-workflow finished, clean up and flatten results
                del session["pending_sub_session_id"]
                return self.run_step(session_id)
            
            # If child is still running or paused again, just return its status
            return sub_result
        
        target_input = session.get("pending_input_name")
        
        if target_input:
            if node_id not in session.setdefault("manual_inputs", {}):
                session["manual_inputs"][node_id] = {}
            
            # Save the input specifically for the waiting field
            session["manual_inputs"][node_id][target_input] = input_data
            
            # Clear the flag so we don't get stuck
            session["pending_input_name"] = None
        
        # Resume the execution loop
        return self.run_step(session_id)
    def run_step(self, session_id: str) -> Dict:
        """
        The main execution loop. runs nodes one by one until finished or paused.
        """
        print("s id ",session_id)
        if session_id not in self.sessions:
            return {"status": "ERROR", "message": "Session not found"}

        session = self.sessions[session_id]
        context = session["context"]
        manual_inputs = session["manual_inputs"]

        for node_id in session["order"]:
            # Skip nodes already executed
            if node_id in context: continue

            node = session["graph_nodes"][node_id]
            feature_id = node['data']['feature_id']
            
            # 1. Load Metadata
            try:
                # Assuming get_feature_metadata is available in your scope
                meta = get_feature_metadata(feature_id)
            except Exception:
                meta = {"inputs": [], "class_name": "CustomWorkflow"}

            node_inputs = {}
            should_run = True
            used_generic_sources = set()

            # 2. Input Resolution Strategy
            for input_def in meta.get("inputs", []):
                input_name = input_def["name"]
                input_type = input_def.get("type", "any")
                is_optional = input_def.get("optional", False)
                
                # A. Check Manual Inputs
                if node_id in manual_inputs and input_name in manual_inputs[node_id]:
                     node_inputs[input_name] = manual_inputs[node_id][input_name]

                else:
                    # B. Check Connections
                    source_node_id, is_generic = self._find_source(
                        target_node=node_id, 
                        input_name=input_name, 
                        required_type=input_type,
                        edges=session["graph_edges"],
                        all_nodes=session["graph_nodes"]
                    )
                    
                    if source_node_id and is_generic and source_node_id in used_generic_sources:
                        source_node_id = None 

                    if source_node_id:
                        if is_generic: used_generic_sources.add(source_node_id)
                        source_val = context.get(source_node_id)
                        
                        if isinstance(source_val, dict) and input_name in source_val:
                            node_inputs[input_name] = source_val[input_name]
                        else:
                            node_inputs[input_name] = source_val

                        if source_val is None and not is_optional:
                            should_run = False 
                    
                    # C. Check Static Config
                    elif "inputs" in node["data"] and input_name in node["data"]["inputs"]:
                        node_inputs[input_name] = node["data"]["inputs"][input_name]

                    # D. Missing Required Input -> PAUSE
                    elif not is_optional:
                        session["pending_input_name"] = input_name
                        session["pending_node_id"] = node_id
                        return {
                            "status": "PAUSED",
                            "session_id": session_id,
                            "node_id": node_id,
                            "required_input": input_def
                        }
                    else:
                        node_inputs[input_name] = None

            if not should_run:
                context[node_id] = None 
                continue

            # 3. Direct Execution
            print(f"🚀 Executing {feature_id} locally with: {node_inputs}")
            
            class_name = meta.get("class_name", "WrapperModule") 

            try:
                import importlib
                
                # --- SMART IMPORT LOGIC ---
                try:
                    # 1. Try Core Module Import
                    module_path = f"modules_repo.{feature_id}.source"
                    module = importlib.import_module(module_path)
                except ImportError:
                    # 2. Try Custom Module Import (user_defined)
                    clean_id = feature_id.replace("user_defined.", "")
                    clean_id = clean_id.replace("-", "_")
                    print(f"@@@ Fallback to Custom: {clean_id}")
                    custom_path = f"modules_repo.user_defined.{clean_id}.source"
                    module = importlib.import_module(custom_path) 
                # Fallback: If metadata class name is wrong, try to find the class dynamically
                if not hasattr(module, class_name):
                    import inspect
                    classes = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__]
                    if classes:
                        class_name = classes[0]
                
                ProcessorClass = getattr(module, class_name)
                processor = ProcessorClass()
                
                # Run the node
                result = processor.run(**node_inputs)
                
                # CHECK FOR BUBBLED PAUSE
                if isinstance(result, dict) and result.get('status') == 'PAUSED':
                    session['pending_sub_session_id'] = result['sub_session_id']
                    return {
                        "status": "PAUSED",
                        "session_id": session_id,
                        "node_id": node_id, 
                        "required_input": result['required_input'], 
                        "sub_session_id": result['sub_session_id'] 
                    }

                # Store Result
                context[node_id] = result
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                # del self.sessions[session_id]
                return {"status": "ERROR", "message": f"Error in {feature_id}: {str(e)}"}

        # Execution Finished
        del self.sessions[session_id]
        return {"status": "COMPLETED", "results": context}
    
    # --- HELPER: Nested Workflow Execution ---
    def run_sub_workflow_sync(self, graph: Dict, requirements: List[str], inputs: Dict, existing_session_id: str = None) -> Dict:
        """
        Runs a nested workflow synchronously.
        """
        # 1. Determine Session ID
        if existing_session_id:
            session_id = existing_session_id
            # If session is missing (rare), recreate it
            if session_id not in self.sessions:
                self.create_session(session_id, graph)
        else:
            session_id = str(uuid.uuid4())
            self.create_session(session_id, graph)

        # 2. Inject Context Inputs
        if inputs:
            self.sessions[session_id]['context'].update(inputs)

        # 3. Execution Loop
        self.sessions[session_id]["status"] = "RUNNING"
        
        while True:
            print("Sub-Session ID:", session_id)
            result = self.run_step(session_id)
            
            if result['status'] in ['COMPLETED', 'ERROR']:
                return result
            elif result['status'] == 'PAUSED':
                result['sub_session_id'] = session_id
                return result

    # --- HELPERS ---
    def _get_execution_order(self, nodes, edges) -> List[str]:
        G = nx.DiGraph()
        G.add_nodes_from(nodes.keys())
        for edge in edges:
            G.add_edge(edge['source'], edge['target'])
        try:
            return list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            raise ValueError("Cycle detected in workflow graph!")

    def _find_source(self, target_node, input_name, required_type, edges, all_nodes) -> Tuple[str, bool]:
        """
        Returns (source_node_id, is_generic_match)
        """
        candidate_edges = [e for e in edges if e['target'] == target_node]

        # Priority 1: Exact Handle Match
        for edge in candidate_edges:
            if edge['targetHandle'] == input_name:
                return edge['source'], False

        # Priority 2: Generic (Null) Handle + Type Match
        for edge in candidate_edges:
            if edge['targetHandle'] is None:
                source_id = edge['source']
                source_node = all_nodes.get(source_id)
                if not source_node: continue

                try:
                    src_meta = get_feature_metadata(source_node['data']['feature_id'])
                except:
                    continue

                for output_def in src_meta.get("outputs", []):
                    source_type = output_def.get("type", "any")
                    
                    if (source_type == required_type) or \
                       (source_type == "any") or \
                       (required_type == "any"):
                        return source_id, True

        return None, False