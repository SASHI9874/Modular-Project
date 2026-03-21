from typing import Dict, Any, List, Optional
from app.services.library_service import library_service
from ..errors.packager_errors import ModeDetectionError


class ModeDetector:
    """Detects frontend mode from graph"""
    
    def __init__(self, nodes: List[Dict[str, Any]]):
        self.nodes = nodes
    
    def detect_frontend_mode(self) -> str:
        """
        Detect frontend mode:
        - external_extension: Has VS Code/CLI interface
        - generated_ui: Auto-generate React UI
        - headless: API only, no frontend
        """
        print(" [ModeDetector] Analyzing frontend mode...")
        
        try:
            # Check for interface nodes
            interface_type = self._find_interface_type()
            
            if interface_type:
                if interface_type in ['vscode', 'cli']:
                    print(f" [ModeDetector] Mode: external_extension ({interface_type})")
                    return 'external_extension'
                elif interface_type == 'webchat':
                    print(f" [ModeDetector] Mode: generated_ui ({interface_type})")
                    return 'generated_ui'
            
            # No interface - check for triggers
            has_trigger = self._has_trigger()
            
            if has_trigger:
                print(" [ModeDetector] Mode: generated_ui (has trigger)")
                return 'generated_ui'
            
            # No interface, no trigger = headless API
            print(" [ModeDetector] Mode: headless")
            return 'headless'
        
        except Exception as e:
            print(f" [ModeDetector] Error: {e}")
            # Default to generated_ui on error
            return 'generated_ui'
    
    def get_interface_node(self) -> Optional[Dict[str, Any]]:
        """Get the interface node if exists"""
        for node in self.nodes:
            try:
                data = node.get('data', {})
                feature_key = data.get('featureKey') or data.get('icon')
                
                if not feature_key:
                    continue
                
                manifest = library_service.get_feature(feature_key)
                if manifest and manifest.classification.capability == 'interface':
                    return node
            
            except Exception:
                continue
        
        return None
    
    # Helper methods
    
    def _find_interface_type(self) -> Optional[str]:
        """Find interface type from nodes"""
        for node in self.nodes:
            try:
                data = node.get('data', {})
                feature_key = data.get('featureKey') or data.get('icon')
                
                if not feature_key:
                    continue
                
                manifest = library_service.get_feature(feature_key)
                
                if manifest and manifest.classification.capability == 'interface':
                    # Determine type from key
                    if 'vscode' in feature_key:
                        return 'vscode'
                    elif 'cli' in feature_key:
                        return 'cli'
                    elif 'webchat' in feature_key or 'web' in feature_key:
                        return 'webchat'
            
            except Exception:
                continue
        
        return None
    
    def _has_trigger(self) -> bool:
        """Check if graph has trigger node"""
        for node in self.nodes:
            try:
                data = node.get('data', {})
                feature_key = data.get('featureKey') or data.get('icon')
                
                if not feature_key:
                    continue
                
                manifest = library_service.get_feature(feature_key)
                
                if manifest and manifest.classification.capability == 'trigger':
                    return True
            
            except Exception:
                continue
        
        return False