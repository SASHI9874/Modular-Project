from typing import Dict, Any
import os
from ..core.service import CodeIntelligenceService


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Runtime adapter for code intelligence"""
    print(f"--- [Runtime] Executing Code Intelligence ---")
    
    operation = inputs.get("operation", "")
    
    if not operation:
        return {
            "result": "No operation specified",
            "success": False
        }
    
    workspace_path = inputs.get("workspace_path") or os.getcwd()
    index_path = os.getenv("INDEX_PATH")
    
    print(f"   Operation: {operation}")
    print(f"   Workspace: {workspace_path}")
    
    service = CodeIntelligenceService(
        workspace_path=workspace_path,
        index_path=index_path
    )
    
    result = service.execute(
        operation=operation,
        query=inputs.get("query")
    )
    
    return result