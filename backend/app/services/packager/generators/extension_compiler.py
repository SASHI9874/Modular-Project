import os
import subprocess
import tempfile
import shutil
import platform
from typing import Dict, Optional
from pathlib import Path
from ..errors.packager_errors import CodeGenerationError
from ..cache.extension_cache import ExtensionCache


class ExtensionCompiler:
    """Compiles VS Code extensions to .vsix packages with caching"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.is_windows = platform.system() == 'Windows'
        self.cache = ExtensionCache()  #  Initialize cache
    
    def compile_vscode_extension(
        self, 
        extension_source: Dict[str, str],
        backend_url: str = "ws://localhost:8000",
        feature_key: str = "interface-vscode",
        feature_version: str = "1.0.0"
    ) -> Optional[bytes]:
        """
        Compile VS Code extension to .vsix (with caching)
        
        Args:
            extension_source: Dict of {filepath: content} for extension files
            backend_url: Backend WebSocket URL to configure
            feature_key: Feature key for cache lookup
            feature_version: Feature version for cache invalidation
        
        Returns:
            .vsix file bytes, or None if compilation fails
        """
        print(" [ExtensionCompiler] Compiling VS Code extension...")
        
        # Calculate source hash
        source_hash = ExtensionCache.hash_source_files(extension_source)
        
        # Check cache first
        print("    Checking cache...")
        cached_vsix = self.cache.get_cached_extension(
            feature_key,
            feature_version,
            source_hash
        )
        
        if cached_vsix:
            print(f"    Using cached extension (skipped npm install & compile)")
            return cached_vsix
        
        # Cache miss - compile from scratch
        print("    Cache miss - compiling extension...")
        
        # Check if Node.js is available
        if not self._check_nodejs():
            print("     Node.js not found - skipping extension compilation")
            return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='vscode_ext_')
        
        try:
            # Step 1: Write extension files
            print("    Writing extension files...")
            self._write_extension_files(temp_dir, extension_source, backend_url)
            
            # Step 2: Install dependencies
            print("    Installing dependencies...")
            self._npm_install(temp_dir)
            
            # Step 3: Compile TypeScript
            print("    Compiling TypeScript...")
            self._compile_typescript(temp_dir)
            
            # Step 4: Package as .vsix
            print("    Creating .vsix package...")
            vsix_path = self._package_vsix(temp_dir)
            
            # Step 5: Read .vsix binary
            with open(vsix_path, 'rb') as f:
                vsix_bytes = f.read()
            
            # Step 6: Store in cache
            self.cache.store_extension(
                feature_key,
                feature_version,
                source_hash,
                vsix_bytes
            )
            
            print(f" [ExtensionCompiler] Extension compiled: {len(vsix_bytes) / 1024:.1f} KB")
            return vsix_bytes
        
        except subprocess.CalledProcessError as e:
            print(f" [ExtensionCompiler] Compilation failed: {e}")
            print(f"   Output: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
            return None
        
        except Exception as e:
            print(f" [ExtensionCompiler] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"  Failed to cleanup temp directory: {e}")
    
    # ... rest of existing methods remain the same ...
    
    def _check_nodejs(self) -> bool:
        """Check if Node.js is available"""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                shell=self.is_windows,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _write_extension_files(
        self, 
        temp_dir: str, 
        source_files: Dict[str, str],
        backend_url: str
    ):
        """Write extension files to temp directory"""
        for filepath, content in source_files.items():
            filepath = filepath.replace('vscode-extension/', '')
            
            if filepath == 'extension.ts' and isinstance(content, str):
                content = content.replace('ws://localhost:8000', backend_url)
            
            full_path = os.path.join(temp_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if isinstance(content, bytes):
                with open(full_path, 'wb') as f:
                    f.write(content)
            else:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _npm_install(self, temp_dir: str):
        """Run npm install"""
        result = subprocess.run(
            ['npm', 'install'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            shell=self.is_windows,
            timeout=300
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                'npm install',
                stderr=result.stderr
            )
    
    def _compile_typescript(self, temp_dir: str):
        """Run TypeScript compilation"""
        result = subprocess.run(
            ['npm', 'run', 'compile'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            shell=self.is_windows,
            timeout=120
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                'npm run compile',
                stderr=result.stderr
            )
    
    def _package_vsix(self, temp_dir: str) -> str:
        """Package extension as .vsix"""
        subprocess.run(
            ['npm', 'install', '-g', '@vscode/vsce'],
            capture_output=True,
            shell=self.is_windows,
            timeout=120
        )
        
        result = subprocess.run(
            ['vsce', 'package', '--no-git-tag-version'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            shell=self.is_windows,
            timeout=60
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                'vsce package',
                stderr=result.stderr
            )
        
        vsix_files = list(Path(temp_dir).glob('*.vsix'))
        if not vsix_files:
            raise FileNotFoundError("No .vsix file created")
        
        return str(vsix_files[0])
    
    def generate_extension_source(self, feature_keys: list) -> Dict[str, str]:
        """Generate VS Code extension source files"""
        from app.services.library_service import library_service
        
        vscode_manifest = None
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if manifest and 'vscode' in key.lower():
                vscode_manifest = manifest
                break
        
        if not vscode_manifest:
            return {}
        
        files = {}
        base_path = vscode_manifest.base_path
        generator_path = os.path.join(base_path, 'generator', 'frontend')
        
        if not os.path.exists(generator_path):
            return {}
        
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.vsix', '.zip', '.ttf', '.woff', '.woff2'}
        
        for root, dirs, filenames in os.walk(generator_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, generator_path)
                _, ext = os.path.splitext(filename)
                
                try:
                    if ext.lower() in binary_extensions:
                        with open(file_path, 'rb') as f:
                            files[rel_path] = f.read()
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[rel_path] = f.read()
                except Exception as e:
                    print(f"     Skipping file {rel_path}: {e}")
                    continue
        
        return files