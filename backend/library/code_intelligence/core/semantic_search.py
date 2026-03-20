from typing import List, Dict, Any


class SemanticSearch:
    """Simple keyword-based search (V1 - no embeddings yet)"""
    
    def __init__(self, index: Dict[str, Any]):
        self.index = index
    
    def search(self, query: str, max_results: int = 5) -> List[str]:
        """Search for relevant files"""
        print(f"🔍 [Search] Query: {query}")
        
        query_lower = query.lower()
        results = []
        
        for file_info in self.index.get('files', []):
            path = file_info['path']
            
            # Simple scoring: check if query words in path
            score = sum(1 for word in query_lower.split() if word in path.lower())
            
            if score > 0:
                results.append((path, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        matched = [path for path, score in results[:max_results]]
        print(f"✅ [Search] Found {len(matched)} files")
        
        return matched