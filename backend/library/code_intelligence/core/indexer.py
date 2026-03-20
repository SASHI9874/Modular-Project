import os
from pathlib import Path
from typing import List, Dict, Any


class CodeIndexer:
    """Simple code indexer (without tree-sitter for V1)"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
    
    def index_workspace(self) -> Dict[str, Any]:
        """Index workspace files"""
        print(f"📇 [Indexer] Indexing: {self.workspace_path}")
        
        files = []
        for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.go']:
            files.extend(self.workspace_path.rglob(f'*{ext}'))
        
        index = {
            'files': [],
            'total_files': len(files),
            'extensions': {}
        }
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                rel_path = str(file_path.relative_to(self.workspace_path))
                ext = file_path.suffix
                
                index['files'].append({
                    'path': rel_path,
                    'size': len(content),
                    'lines': content.count('\n'),
                    'extension': ext
                })
                
                index['extensions'][ext] = index['extensions'].get(ext, 0) + 1
            
            except Exception as e:
                print(f"⚠️  [Indexer] Skip {file_path}: {e}")
        
        print(f"✅ [Indexer] Indexed {len(index['files'])} files")
        return index