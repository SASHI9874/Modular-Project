import os
import json
import hashlib
from typing import Optional, Dict
from pathlib import Path


class ExtensionCache:
    """Manages cached compiled extensions"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # 1. Check environment variable first
            env_cache = os.getenv('EXTENSION_CACHE_DIR')
            
            if env_cache:
                cache_dir = env_cache
            else:
                # 2. Fallback to default backend/cache/extensions
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                cache_dir = os.path.join(base_dir, 'cache', 'extensions')
        
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f" [ExtensionCache] Cache directory: {cache_dir}")
    
    def get_cached_extension(
        self, 
        feature_key: str,
        feature_version: str,
        source_hash: str
    ) -> Optional[bytes]:
        """
        Get cached extension if valid
        
        Args:
            feature_key: Feature key (e.g., 'interface-vscode')
            feature_version: Feature version (e.g., '1.0.0')
            source_hash: Hash of source files
        
        Returns:
            .vsix bytes if cached and valid, None otherwise
        """
        cache_key = self._get_cache_key(feature_key, feature_version, source_hash)
        vsix_path = os.path.join(self.cache_dir, f"{cache_key}.vsix")
        meta_path = os.path.join(self.cache_dir, f"{cache_key}.meta.json")
        
        # Check if cache exists
        if not os.path.exists(vsix_path) or not os.path.exists(meta_path):
            print(f"     Cache miss: {feature_key} v{feature_version}")
            return None
        
        # Verify metadata
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            # Check if still valid
            if meta.get('version') != feature_version or meta.get('source_hash') != source_hash:
                print(f"    Cache invalid: {feature_key} (outdated)")
                self._remove_cache(cache_key)
                return None
        
        except Exception as e:
            print(f"    Cache metadata corrupted: {e}")
            self._remove_cache(cache_key)
            return None
        
        # Read cached .vsix
        try:
            with open(vsix_path, 'rb') as f:
                vsix_bytes = f.read()
            
            print(f"    Cache hit: {feature_key} v{feature_version} ({len(vsix_bytes) / 1024:.1f} KB)")
            return vsix_bytes
        
        except Exception as e:
            print(f"    Failed to read cache: {e}")
            self._remove_cache(cache_key)
            return None
    
    def store_extension(
        self,
        feature_key: str,
        feature_version: str,
        source_hash: str,
        vsix_bytes: bytes
    ):
        """
        Store compiled extension in cache
        
        Args:
            feature_key: Feature key
            feature_version: Feature version
            source_hash: Hash of source files
            vsix_bytes: Compiled .vsix binary
        """
        cache_key = self._get_cache_key(feature_key, feature_version, source_hash)
        vsix_path = os.path.join(self.cache_dir, f"{cache_key}.vsix")
        meta_path = os.path.join(self.cache_dir, f"{cache_key}.meta.json")
        
        try:
            # Write .vsix
            with open(vsix_path, 'wb') as f:
                f.write(vsix_bytes)
            
            # Write metadata
            meta = {
                'feature_key': feature_key,
                'version': feature_version,
                'source_hash': source_hash,
                'size_bytes': len(vsix_bytes),
                'cached_at': self._get_timestamp()
            }
            
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            
            print(f"    Cached: {feature_key} v{feature_version}")
        
        except Exception as e:
            print(f"    Failed to cache extension: {e}")
    
    def clear_cache(self, feature_key: str = None):
        """
        Clear cache
        
        Args:
            feature_key: If provided, clear only this feature. Otherwise clear all.
        """
        if feature_key:
            # Clear specific feature
            pattern = f"{feature_key}-*"
            cleared = 0
            
            for file in Path(self.cache_dir).glob(pattern):
                try:
                    os.remove(file)
                    cleared += 1
                except Exception as e:
                    print(f"    Failed to remove {file}: {e}")
            
            print(f"  Cleared {cleared} cached files for {feature_key}")
        else:
            # Clear all
            import shutil
            try:
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                print("  Cleared entire extension cache")
            except Exception as e:
                print(f"    Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'extensions': []
        }
        
        for file in Path(self.cache_dir).glob('*.vsix'):
            stats['total_files'] += 1
            size = os.path.getsize(file)
            stats['total_size_mb'] += size / (1024 * 1024)
            
            # Read metadata
            meta_file = file.with_suffix('.meta.json')
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    stats['extensions'].append({
                        'key': meta['feature_key'],
                        'version': meta['version'],
                        'size_kb': size / 1024,
                        'cached_at': meta.get('cached_at')
                    })
        
        return stats
    
    # Helper methods
    
    def _get_cache_key(self, feature_key: str, version: str, source_hash: str) -> str:
        """Generate cache key"""
        # Format: interface-vscode-v1.0.0-abc123
        return f"{feature_key}-v{version}-{source_hash[:8]}"
    
    def _remove_cache(self, cache_key: str):
        """Remove cache files"""
        vsix_path = os.path.join(self.cache_dir, f"{cache_key}.vsix")
        meta_path = os.path.join(self.cache_dir, f"{cache_key}.meta.json")
        
        try:
            if os.path.exists(vsix_path):
                os.remove(vsix_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except Exception as e:
            print(f"    Failed to remove cache: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @staticmethod
    def hash_source_files(source_files: Dict[str, any]) -> str:
        """
        Create hash of source files
        
        Args:
            source_files: Dict of {filepath: content}
        
        Returns:
            SHA256 hash
        """
        hasher = hashlib.sha256()
        
        # Sort files for consistent hashing
        for filepath in sorted(source_files.keys()):
            content = source_files[filepath]
            
            # Hash filepath
            hasher.update(filepath.encode('utf-8'))
            
            # Hash content
            if isinstance(content, bytes):
                hasher.update(content)
            else:
                hasher.update(content.encode('utf-8'))
        
        return hasher.hexdigest()