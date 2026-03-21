from typing import List, Set
from app.services.library_service import library_service
from ..errors.packager_errors import DependencyResolutionError


class DependencyResolver:
    """Resolves feature dependencies"""
    
    def resolve(self, feature_keys: List[str]) -> List[str]:
        """
        Resolve all dependencies for given features
        Returns list including original keys + dependencies
        """
        print(" [DependencyResolver] Resolving dependencies...")
        
        resolved: Set[str] = set(feature_keys)
        to_process = list(feature_keys)
        
        try:
            while to_process:
                key = to_process.pop(0)
                
                manifest = library_service.get_feature(key)
                if not manifest:
                    print(f"     Feature not found: {key}")
                    continue
                
                # Check if has dependencies field
                if not hasattr(manifest, 'dependencies') or not manifest.dependencies:
                    continue
                
                # Add runtime dependencies
                if hasattr(manifest.dependencies, 'runtime'):
                    for dep in manifest.dependencies.runtime:
                        if dep not in resolved:
                            resolved.add(dep)
                            to_process.append(dep)
                            print(f"    Adding dependency: {dep} (required by {key})")
            
            result = list(resolved)
            print(f" [DependencyResolver] Resolved {len(result)} features (including deps)")
            return result
        
        except Exception as e:
            print(f" [DependencyResolver] Error: {e}")
            raise DependencyResolutionError(f"Failed to resolve dependencies: {e}")