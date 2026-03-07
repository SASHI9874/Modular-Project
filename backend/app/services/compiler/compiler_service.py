import os
import networkx as nx
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, List
from app.core.config import settings

class GraphCompiler:
    def __init__(self, graph_data: Dict[str, Any]):
        self.graph = graph_data
        self.nodes = {n['id']: n for n in graph_data.get('nodes', [])}
        self.edges = graph_data.get('edges', [])

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Go up to "app" folder
        app_dir = os.path.dirname(os.path.dirname(current_dir))

        template_dir = os.path.join(app_dir, "templates")

        
        # Setup Jinja
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template("core/main.py.j2")

    def _clean_id(self, node_id: str) -> str:
        """Converts 'gpt-4-1738...' to 'gpt_4_1738' for valid variable names"""
        return node_id.replace("-", "_")

    def compile(self) -> str:
        # 1. Topological Sort (Determine Order)
        G = nx.DiGraph()
        for node_id in self.nodes:
            G.add_node(node_id)
        for edge in self.edges:
            G.add_edge(edge['source'], edge['target'])
            
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Graph contains cycles! Cannot compile.")
            
        execution_order_ids = list(nx.topological_sort(G))
        
        # 2. Prepare Data for Template
        compiled_nodes = []
        for node_id in execution_order_ids:
            node = self.nodes[node_id]
            
            # Find inputs for this node
            inputs_map = {}
            incoming_edges = [e for e in self.edges if e['target'] == node_id]
            for edge in incoming_edges:
                target_handle = edge.get('targetHandle', 'default')
                source_id = edge['source']
                source_handle = edge.get('sourceHandle', 'default')
                
                inputs_map[target_handle] = {
                    "node_id": source_id,
                    "output_key": source_handle
                }

            compiled_nodes.append({
                "id": node_id,
                "clean_id": self._clean_id(node_id),
                "type": node['data'].get('icon', 'default'), # utilizing icon as type key
                "label": node['data'].get('label', 'Unknown'),
                "inputs": inputs_map
            })

        # 3. Render Template
        return self.template.render(
            openai_key=settings.OPENAI_API_KEY, # In prod, don't hardcode this!
            execution_order=compiled_nodes
        )