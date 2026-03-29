import os
import json
from pathlib import Path
from typing import Dict, Any, List
from .indexer import CodeIndexer
from .semantic_search import SemanticSearch
from .errors import IndexNotFoundError, IndexingError, SearchError


class CodeIntelligenceService:
    """Code intelligence service"""
    
    def __init__(self, workspace_path: str = None, index_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.index_path = Path(index_path) if index_path else self.workspace_path / '.code_index.json'
        self.index = None
    
    def _load_index(self) -> Dict[str, Any]:
        """Load existing index"""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                return json.load(f)
        raise IndexNotFoundError("Index not found. Run 'index' operation first.")
    
    def _save_index(self, index: Dict[str, Any]):
        """Save index to disk"""
        with open(self.index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    def index_workspace(self) -> str:
        """Index the workspace"""
        print(f"📇 [Intelligence] Indexing workspace")
        
        try:
            indexer = CodeIndexer(str(self.workspace_path))
            self.index = indexer.index_workspace()
            self._save_index(self.index)
            
            return f"Indexed {self.index['total_files']} files"
        
        except Exception as e:
            raise IndexingError(f"Indexing failed: {e}")
    
    def search(self, query: str, max_results: int = 5) -> List[str]:
        """Semantic search"""
        print(f"🔍 [Intelligence] Searching: {query}")
        
        try:
            if not self.index:
                self.index = self._load_index()
            
            searcher = SemanticSearch(self.index)
            results = searcher.search(query, max_results)
            
            return results
        
        except Exception as e:
            raise SearchError(f"Search failed: {e}")
    
    def get_context(self, file_path: str) -> Dict[str, Any]:
        """Build context for a file"""
        print(f"📄 [Intelligence] Context for: {file_path}")
        
        full_path = self.workspace_path / file_path
        
        if not full_path.exists():
            return {"error": "File not found"}
        
        # Read file
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Find related files (simple: same directory)
        related = []
        for sibling in full_path.parent.iterdir():
            if sibling.is_file() and sibling != full_path:
                related.append(str(sibling.relative_to(self.workspace_path)))
        
        return {
            "file": file_path,
            "lines": content.count('\n'),
            "size": len(content),
            "related_files": related[:5]
        }
    
    def analyze_deps(self, file_path: str) -> List[str]:
        """Analyze file dependencies"""
        print(f"🔗 [Intelligence] Analyzing deps: {file_path}")
        
        full_path = self.workspace_path / file_path
        
        if not full_path.exists():
            return []
        
        # Simple: find import statements
        deps = []
        with open(full_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    deps.append(line)
        
        return deps[:10]
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute operation"""
        operations = {
            'index': lambda: {"result": self.index_workspace(), "success": True},
            'search': lambda: {"files": self.search(kwargs.get('query', '')), "success": True},
            'get_context': lambda: {**self.get_context(kwargs.get('query', '')), "success": True},
            'analyze_deps': lambda: {"files": self.analyze_deps(kwargs.get('query', '')), "success": True}
        }
        
        if operation not in operations:
            return {"result": f"Unknown operation: {operation}", "success": False}
        
        try:
            return operations[operation]()
        except Exception as e:
            print(f" [Intelligence] Error: {e}")
            return {"result": str(e), "success": False, "error": str(e)}