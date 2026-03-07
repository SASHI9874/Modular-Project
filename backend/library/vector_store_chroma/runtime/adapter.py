from typing import Dict, Any
from ..core.service import process


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for vector store operations.
    
    Supports multiple operations:
    - index: Store documents in vector DB
    - retrieve: Search for relevant context
    - delete: Remove a collection
    - list: List all collections
    - stats: Get collection statistics
    """
    print(f"--- [Runtime] Executing Vector Store ---")
    
    # Extract inputs
    operation = inputs.get("operation", "retrieve")
    file_text = inputs.get("file_text", "")
    query = inputs.get("query", "")
    collection_name = inputs.get("collection_name", "default")
    metadata = inputs.get("metadata", {})
    k = inputs.get("k", 3)
    
    # Get node config
    node_config = context.get("node_config", {})
    
    # Override with node config if present
    if "collection_name" in node_config:
        collection_name = node_config["collection_name"]
    if "k" in node_config:
        k = int(node_config["k"])
    
    print(f"   Operation: {operation}")
    print(f"   Collection: {collection_name}")
    
    try:
        # Execute operation
        result = process(
            operation=operation,
            file_text=file_text,
            query=query,
            collection_name=collection_name,
            metadata=metadata,
            k=k
        )
        
        return {
            "result": result["result"],
            "metadata": result.get("metadata", {}),
            "success": "error" not in result.get("metadata", {})
        }
    
    except Exception as e:
        import traceback
        print(f"❌ [Runtime] Error:")
        print(traceback.format_exc())
        
        return {
            "result": f"❌ Runtime Error: {str(e)}",
            "metadata": {"error": str(e)},
            "success": False
        }