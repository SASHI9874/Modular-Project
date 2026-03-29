import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .errors import (
    FileNotFoundError,
    FileTooBigError,
    PermissionError,
    InvalidPathError,
    CommandError
)


class CodeToolsService:
    """Service for file and code operations"""
    
    def __init__(self, workspace_root: Optional[str] = None, max_file_size: int = 1_000_000):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.max_file_size = max_file_size
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path within workspace"""
        full_path = (self.workspace_root / path).resolve()
        
        # Security: ensure path is within workspace
        if not str(full_path).startswith(str(self.workspace_root)):
            raise InvalidPathError(f"Path outside workspace: {path}")
        
        return full_path
    
    def read_file(self, path: str) -> str:
        """Read file contents"""
        print(f"📖 [CodeTools] Reading: {path}")
        
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not full_path.is_file():
            raise InvalidPathError(f"Not a file: {path}")
        
        # Check file size
        if full_path.stat().st_size > self.max_file_size:
            raise FileTooBigError(f"File too large: {path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f" [CodeTools] Read {len(content)} chars")
            return content
        
        except Exception as e:
            raise PermissionError(f"Cannot read file: {e}")
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        print(f"✍️  [CodeTools] Writing: {path}")
        
        full_path = self._validate_path(path)
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f" [CodeTools] Wrote {len(content)} chars")
            return f"File written: {path}"
        
        except Exception as e:
            raise PermissionError(f"Cannot write file: {e}")
    
    def search_code(self, query: str, file_pattern: str = "*.py") -> str:
        """Search for code patterns"""
        print(f"🔍 [CodeTools] Searching: {query}")
        
        try:
            # Use grep for search
            result = subprocess.run(
                ['grep', '-rn', '--include', file_pattern, query, str(self.workspace_root)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                print(f" [CodeTools] Found {len(lines)} matches")
                return result.stdout.strip()
            else:
                return "No matches found"
        
        except subprocess.TimeoutExpired:
            raise CommandError("Search timeout")
        except Exception as e:
            raise CommandError(f"Search failed: {e}")
    
    def list_directory(self, path: str = ".") -> str:
        """List directory contents"""
        print(f"📁 [CodeTools] Listing: {path}")
        
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not full_path.is_dir():
            raise InvalidPathError(f"Not a directory: {path}")
        
        try:
            items = []
            for item in sorted(full_path.iterdir()):
                item_type = "📁" if item.is_dir() else "📄"
                items.append(f"{item_type} {item.name}")
            
            result = "\n".join(items)
            print(f" [CodeTools] Listed {len(items)} items")
            return result
        
        except Exception as e:
            raise PermissionError(f"Cannot list directory: {e}")
    
    def run_command(self, command: str) -> str:
        """Run shell command"""
        print(f"⚡ [CodeTools] Running: {command}")
        
        # Security: basic validation
        dangerous = ['rm -rf', 'sudo', 'chmod 777', '> /dev/', 'mkfs']
        if any(danger in command for danger in dangerous):
            raise CommandError("Dangerous command blocked")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace_root)
            )
            
            output = result.stdout + result.stderr
            print(f" [CodeTools] Exit code: {result.returncode}")
            return output.strip()
        
        except subprocess.TimeoutExpired:
            raise CommandError("Command timeout")
        except Exception as e:
            raise CommandError(f"Command failed: {e}")
    
    def git_diff(self) -> str:
        """Get git diff of uncommitted changes"""
        print(f"📊 [CodeTools] Getting git diff")
        
        try:
            result = subprocess.run(
                ['git', 'diff'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.workspace_root)
            )
            
            if result.returncode == 0:
                diff = result.stdout.strip()
                if diff:
                    print(f" [CodeTools] Found changes")
                    return diff
                else:
                    return "No uncommitted changes"
            else:
                return "Not a git repository or git not available"
        
        except Exception as e:
            raise CommandError(f"Git diff failed: {e}")
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute operation"""
        operations = {
            'read_file': lambda: self.read_file(kwargs.get('path', '')),
            'write_file': lambda: self.write_file(kwargs.get('path', ''), kwargs.get('content', '')),
            'search_code': lambda: self.search_code(kwargs.get('query', '')),
            'list_directory': lambda: self.list_directory(kwargs.get('path', '.')),
            'run_command': lambda: self.run_command(kwargs.get('command', '')),
            'git_diff': lambda: self.git_diff()
        }
        
        if operation not in operations:
            return {
                "result": f"Unknown operation: {operation}",
                "success": False,
                "error": f"Valid operations: {list(operations.keys())}"
            }
        
        try:
            result = operations[operation]()
            return {
                "result": result,
                "success": True
            }
        except Exception as e:
            print(f" [CodeTools] Error: {e}")
            return {
                "result": str(e),
                "success": False,
                "error": str(e)
            }