import networkx as nx
from typing import Dict, Any, List
from app.services.library_service import library_service

class GraphExecutor:
    def __init__(self, graph_data: Dict[str, Any]):
        self.nodes = {n['id']: n for n in graph_data.get('nodes', [])}
        self.edges = graph_data.get('edges', [])
        self.execution_state = {} 

    def build_dag(self):
        """Build execution order - agents need special handling"""
        G = nx.DiGraph()
        
        # Add nodes
        for node_id in self.nodes:
            G.add_node(node_id)
        
        # Add only DATA edges (skip TOOL edges for topological sort)
        for edge in self.edges:
            edge_type = edge.get('type', 'data')
            if edge_type == 'data':
                G.add_edge(edge['source'], edge['target'])
        
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Graph contains cycles!")
            
        return list(nx.topological_sort(G))

    def get_connected_tools(self, agent_node_id: str) -> List[Dict]:
        """Get tools connected to an agent via the 'tools' or 'tool' handle"""
        # Look for edges where the TARGET is the Agent, and the handle is 'tools'
        tool_edges = [
            e for e in self.edges 
            if e['target'] == agent_node_id 
            and e.get('targetHandle') in ['tool', 'tools']
        ]
        
        tools = []
        for edge in tool_edges:
            # The Tool is the source of the edge
            tool_node_id = edge['source']
            tool_node = self.nodes.get(tool_node_id)
            
            if tool_node:
                feature_key = tool_node['data'].get('icon')
                feature = library_service.get_feature(feature_key)
                
                # Verify the feature actually has a tool schema defined
                if feature and hasattr(feature, 'tool_definition') and feature.tool_definition:
                    # Handle both Pydantic models and standard dicts just in case
                    tool_def = feature.tool_definition.dict() if hasattr(feature.tool_definition, 'dict') else feature.tool_definition
                    
                    tool_def['node_id'] = tool_node_id
                    tool_def['feature_key'] = feature_key
                    tools.append(tool_def)
                else:
                    print(f"⚠️ [Executor] Node '{feature_key}' is connected as a tool, but has no tool_definition in its spec!")
        
        return tools

    def execute_tool_for_agent(self, tool_name: str, args: Dict, available_tools: List[Dict]) -> Dict:
        """Execute a tool on behalf of an agent"""
        # Find the tool
        tool_def = next((t for t in available_tools if t['name'] == tool_name), None)
        
        if not tool_def:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in connected tools"
            }
        
        tool_node_id = tool_def['node_id']
        feature_key = tool_def['feature_key']
        
        print(f"   🔧 [Executor] Executing tool: {tool_name}")
        
        try:
            adapter_module = library_service.import_runtime_adapter(feature_key)
            
            context = {
                "execution_mode": "tool_call",
                "execution_state": self.execution_state
            }
            
            result = adapter_module.run(args, context)
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

    def get_connected_llm(self, agent_node_id: str):
        """Get LLM connected to agent via 'llm' or 'model' handle"""
        llm_edges = [
            e for e in self.edges 
            if e['target'] == agent_node_id 
            and e.get('targetHandle') in ['llm', 'model']
        ]
        
        if llm_edges:
            llm_node_id = llm_edges[0]['source']
            return llm_node_id, self.nodes.get(llm_node_id)
        
        return None, None


    def create_llm_callable(self, agent_node_id: str):
        """Create LLM callable for specific agent"""
        llm_node_id, llm_node = self.get_connected_llm(agent_node_id)
        
        if not llm_node:
            return None
        
        def llm_call(messages: List[Dict]) -> Dict:
            """Call LLM with messages"""
            feature_key = llm_node['data'].get('icon')
            adapter_module = library_service.import_runtime_adapter(feature_key)
            
            # Pass the ReAct messages natively!
            inputs = {
                "messages": messages
            }
            
            context = {
                "execution_state": self.execution_state,
                "node_config": llm_node['data']
            }
            
            result = adapter_module.run(inputs, context)
            
            return {
                "content": result.get("response", ""),
                "success": result.get("success", True)
            }
        
        return llm_call
    
    def execute_node(self, node_id: str):
        node = self.nodes[node_id]
        feature_key = node['data'].get('icon')
        node_label = node['data'].get('label', feature_key)
        
        # Get feature info
        feature = library_service.get_feature(feature_key)
        is_agent = feature and feature.classification.capability == "agent"
        
        # GATHER INPUTS
        inputs = {}
        incoming_edges = [e for e in self.edges if e['target'] == node_id and e.get('type') == 'data']
        
        for edge in incoming_edges:
            source_id = edge['source']
            source_handle = edge.get('sourceHandle')
            target_handle = edge.get('targetHandle')
            
            previous_output = self.execution_state.get(source_id, {})
            
            if target_handle:
                if isinstance(previous_output, dict) and source_handle in previous_output:
                    inputs[target_handle] = previous_output[source_handle]
                else:
                    inputs[target_handle] = previous_output

        # EXECUTE
        print(f"--- [Executor] Running {node_label} ({feature_key}) ---")
        
        try:
            adapter_module = library_service.import_runtime_adapter(feature_key)
            
            context = {
                "execution_state": self.execution_state,
                "node_config": node['data']
            }
            
            # AGENT-SPECIFIC SETUP
            if is_agent:
                print(f"   🤖 [Executor] Agent detected - setting up tools")
                
                # Get connected tools
                available_tools = self.get_connected_tools(node_id)
                context['available_tools'] = available_tools
                
                print(f"   🔧 [Executor] Available tools: {[t['name'] for t in available_tools]}")
                
                # Create LLM callable
                llm_callable = self.create_llm_callable(node_id)
                context['llm_callable'] = llm_callable
                
                # Override agent's tool executor with our executor
                original_run = adapter_module.run
                
                def agent_run_with_tools(inputs, context):
                    # Patch the orchestrator's _execute_tool method
                    result = original_run(inputs, context)
                    return result
                
                # Inject tool executor into context
                context['tool_executor'] = lambda tool_name, args: self.execute_tool_for_agent(
                    tool_name, args, available_tools
                )
            
            output = adapter_module.run(inputs, context)
            
        except ImportError:
            output = {"error": f"Feature '{feature_key}' not found", "success": False}
        except Exception as e:
            import traceback
            print(f"❌ [Executor] Error:")
            traceback.print_exc()
            output = {"error": str(e), "success": False}

        self.execution_state[node_id] = output
        return output

    def run(self, entry_node_id: str = None, initial_inputs: Dict[str, Any] = None):
        """
        Executes the graph in topological order. 
        If an entry node and initial inputs are provided, it seeds the execution state.
        """
        execution_order = self.build_dag()
        results = {}
        
        # Seed the Graph Memory
        if entry_node_id and initial_inputs:
            print(f"🌱 [Executor] Seeding '{entry_node_id}' with payload: {initial_inputs}")
            self.execution_state[entry_node_id] = initial_inputs
            results[entry_node_id] = initial_inputs
            
            if entry_node_id in execution_order:
                execution_order.remove(entry_node_id)

        # Identify Subordinate Nodes (Tools and Models)
        # We find any node that is acting as a tool or model input for an agent.
        subordinate_nodes = set()
        for edge in self.edges:
            target_handle = edge.get('targetHandle', '')
            edge_type = edge.get('type', '')
            
            # If the edge plugs into a tool or model port, the source node is a subordinate!
            if target_handle in ['llm', 'model', 'tools', 'tool'] or edge_type == 'tool':
                subordinate_nodes.add(edge['source'])

        # Execute the rest of the nodes
        for node_id in execution_order:
            # SKIP subordinate nodes! Let the Agent orchestrate them.
            if node_id in subordinate_nodes:
                print(f"⏭️  [Executor] Skipping '{node_id}' (Orchestrated by Agent)")
                continue
                
            results[node_id] = self.execute_node(node_id)
            
        return results