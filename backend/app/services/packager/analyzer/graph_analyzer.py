from typing import Dict, Any, List
from app.services.library_service import library_service
from ..errors.packager_errors import GraphAnalysisError


class GraphAnalyzer:
    """Analyzes graph and filters nodes for download"""
    
    def __init__(self, graph_data: Dict[str, Any]):
        self.graph = graph_data
        self.nodes = graph_data.get('nodes', [])
        self.edges = graph_data.get('edges', [])
    
    def filter_runtime_nodes(self) -> List[Dict[str, Any]]:
        """
        Filter out editor-only nodes
        Returns only nodes that should be in downloaded backend
        """
        runtime_nodes = []
        
        print("[Analyzer] Filtering runtime nodes...")
        
        for node in self.nodes:
            try:
                feature_key = self._get_feature_key(node)
                if not feature_key:
                    continue
                
                manifest = library_service.get_feature(feature_key)
                if not manifest:
                    print(f"     Unknown feature: {feature_key}")
                    continue
                
                # Check execution visibility
                visibility = self._get_execution_visibility(manifest)
                
                if visibility in ['runtime', 'both']:
                    runtime_nodes.append(node)
                    print(f"    Including: {manifest.name} ({visibility})")
                else:
                    print(f"     Skipping: {manifest.name} ({visibility})")
            
            except Exception as e:
                print(f"    Error analyzing node: {e}")
                # Continue with other nodes instead of crashing
                continue
        
        print(f" [Analyzer] Filtered {len(runtime_nodes)}/{len(self.nodes)} nodes")
        return runtime_nodes
    
    def get_used_feature_keys(self, nodes: List[Dict[str, Any]] = None) -> List[str]:
        """Extract unique feature keys from nodes"""
        if nodes is None:
            nodes = self.nodes
        
        keys = []
        for node in nodes:
            key = self._get_feature_key(node)
            if key and key not in keys:
                keys.append(key)
        
        return keys
    
    def detect_execution_mode(self) -> str:
        """
        Detect graph execution mode:
        - pipeline: Sequential flow
        - agent: Agent with tools
        - conversational: Simple chat agent
        """
        has_agent = False
        has_tools = False
        has_trigger = False
        
        for node in self.nodes:
            try:
                feature_key = self._get_feature_key(node)
                if not feature_key:
                    continue
                
                manifest = library_service.get_feature(feature_key)
                if not manifest:
                    continue
                
                capability = manifest.classification.capability
                
                if capability == 'agent':
                    has_agent = True
                elif capability == 'tool':
                    has_tools = True
                elif capability == 'trigger':
                    has_trigger = True
            
            except Exception:
                continue
        
        # Determine mode
        if has_agent and has_tools:
            mode = "agent"
        elif has_agent:
            mode = "conversational"
        elif has_trigger:
            mode = "pipeline"
        else:
            mode = "api"
        
        print(f" [Analyzer] Execution mode: {mode}")
        return mode
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        runtime_nodes = self.filter_runtime_nodes()
        
        return {
            "total_nodes": len(self.nodes),
            "runtime_nodes": len(runtime_nodes),
            "editor_nodes": len(self.nodes) - len(runtime_nodes),
            "total_edges": len(self.edges),
            "execution_mode": self.detect_execution_mode()
        }
    
    # Helper methods
    
    def _get_feature_key(self, node: Dict[str, Any]) -> str:
        """Extract feature key from node data"""
        data = node.get('data', {})
        return data.get('featureKey') or data.get('icon') or ''
    
    def _get_execution_visibility(self, manifest) -> str:
        """Get execution visibility from manifest"""
        if hasattr(manifest.ui, 'execution_visibility'):
            return manifest.ui.execution_visibility
        return 'runtime'  # Default