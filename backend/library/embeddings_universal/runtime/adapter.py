from typing import Dict, Any
from ..core.service import embed_text, embed_documents, get_provider_info


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for embeddings operations.
    
    Supports two modes:
    - Single text embedding
    - Batch text embedding
    """
    print(f"--- [Runtime] Executing Embeddings ---")
    
    # Extract inputs
    text = inputs.get("text", "")
    texts = inputs.get("texts", [])
    
    # Get node config
    node_config = context.get("node_config", {})
    
    # Build override config from node settings
    override_config = {}
    if "provider" in node_config:
        override_config["provider"] = node_config["provider"]
    if "model" in node_config:
        override_config["model"] = node_config["model"]

    
    try:
        # Mode 1: Single text
        if text and not texts:
            print(f"   Mode: Single text embedding")
            print(f"   Text length: {len(text)} chars")
            
            vector = embed_text(text, override_config)
            
            return {
                "vector": vector,
                "dimension": len(vector),
                "success": True,
                "provider": override_config.get("provider", "default")
            }
        
        # Mode 2: Batch texts
        elif texts:
            print(f"   Mode: Batch embedding")
            print(f"   Number of texts: {len(texts)}")
            
            vectors = embed_documents(texts, override_config)
            
            return {
                "vectors": vectors,
                "count": len(vectors),
                "dimension": len(vectors[0]) if vectors else 0,
                "success": True,
                "provider": override_config.get("provider", "default")
            }
        
        # Mode 3: Get provider info
        else:
            print(f"   Mode: Provider info")
            info = get_provider_info()
            
            return {
                "info": info,
                "success": True
            }
    
    except Exception as e:
        import traceback
        print(f" [Runtime] Error:")
        print(traceback.format_exc())
        
        return {
            "error": str(e),
            "success": False,
            "error_type": type(e).__name__
        }