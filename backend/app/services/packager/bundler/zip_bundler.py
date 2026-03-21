import io
import zipfile
from typing import Dict, Union
from ..errors.packager_errors import BundlingError


class ZipBundler:
    """Creates final ZIP package"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def create_zip(self, files: Dict[str, Union[str, bytes]]) -> bytes:
        """
        Bundle files into ZIP
        
        Args:
            files: Dict of {filepath: content (str or bytes)}
        
        Returns:
            ZIP file bytes
        """
        print(f" [Bundler] Creating ZIP package...")
        
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filepath, content in files.items():
                    # Determine if binary
                    is_binary = isinstance(content, bytes)
                    
                    # Convert content to bytes if needed
                    if isinstance(content, str):
                        content_bytes = content.encode('utf-8')
                    elif isinstance(content, bytes):
                        content_bytes = content
                    else:
                        # Fallback for other types
                        content_bytes = str(content).encode('utf-8')
                    
                    # Write to ZIP using writestr (handles both text and binary)
                    # For .vsix files, use STORED compression to avoid corruption
                    if filepath.endswith('.vsix'):
                        zip_file.writestr(
                            filepath, 
                            content_bytes,
                            compress_type=zipfile.ZIP_STORED  # No compression for .vsix
                        )
                    else:
                        zip_file.writestr(filepath, content_bytes)
                    
                    # Show size for binary files
                    size_kb = len(content_bytes) / 1024
                    if size_kb > 100:  # Show size for files > 100KB
                        print(f"   Added: {filepath} ({size_kb:.1f} KB)")
                    else:
                        print(f"   Added: {filepath}")
            
            zip_bytes = zip_buffer.getvalue()
            
            # Calculate size
            size_mb = len(zip_bytes) / (1024 * 1024)
            print(f"[Bundler] Package created: {size_mb:.2f} MB ({len(files)} files)")
            
            return zip_bytes
        
        except Exception as e:
            print(f" [Bundler] Error: {e}")
            import traceback
            traceback.print_exc()
            raise BundlingError(f"Failed to create ZIP: {e}")