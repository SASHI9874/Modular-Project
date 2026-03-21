from typing import Dict, Any, List, Tuple
from app.services.library_service import library_service
from ..errors.packager_errors import ValidationError


class GraphValidator:
    """Validates graph before download"""
    
    def __init__(self, graph_data: Dict[str, Any]):
        self.graph = graph_data
        self.nodes = graph_data.get('nodes', [])
        self.edges = graph_data.get('edges', [])
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate graph
        
        Returns:
            (is_valid, errors_list)
        """
        print(" [Validator] Validating graph...")
        
        errors = []
        
        # Check if graph is empty
        if not self.nodes:
            errors.append("Graph is empty - no nodes to download")
        
        # Check for unknown features
        unknown = self._check_unknown_features()
        if unknown:
            errors.append(f"Unknown features: {', '.join(unknown)}")
        
        # Check for disconnected nodes (optional warning)
        disconnected = self._check_disconnected_nodes()
        if disconnected:
            print(f"     Warning: {len(disconnected)} disconnected nodes")
        
        # Check if has at least one runtime node
        runtime_count = self._count_runtime_nodes()
        if runtime_count == 0:
            errors.append("No runtime nodes found - nothing to download")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            print(" [Validator] Graph is valid")
        else:
            print(f" [Validator] Found {len(errors)} errors")
            for error in errors:
                print(f"   - {error}")
        
        return is_valid, errors
    
    def _check_unknown_features(self) -> List[str]:
        """Check for unknown features"""
        unknown = []
        
        for node in self.nodes:
            data = node.get('data', {})
            feature_key = data.get('featureKey') or data.get('icon')
            
            if not feature_key:
                continue
            
            manifest = library_service.get_feature(feature_key)
            if not manifest:
                unknown.append(feature_key)
        
        return unknown
    
    def _check_disconnected_nodes(self) -> List[str]:
        """Check for disconnected nodes"""
        node_ids = {n['id'] for n in self.nodes}
        connected_ids = set()
        
        for edge in self.edges:
            connected_ids.add(edge.get('source'))
            connected_ids.add(edge.get('target'))
        
        disconnected = node_ids - connected_ids
        return list(disconnected)
    
    def _count_runtime_nodes(self) -> int:
        """Count runtime nodes"""
        count = 0
        
        for node in self.nodes:
            data = node.get('data', {})
            feature_key = data.get('featureKey') or data.get('icon')
            
            if not feature_key:
                continue
            
            manifest = library_service.get_feature(feature_key)
            if not manifest:
                continue
            
            visibility = 'runtime'
            if hasattr(manifest.ui, 'execution_visibility'):
                visibility = manifest.ui.execution_visibility
            
            if visibility in ['runtime', 'both']:
                count += 1
        
        return count