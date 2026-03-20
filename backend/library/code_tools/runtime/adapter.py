from typing import Dict, Any
import os
from ..core.service import CodeToolsService


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Runtime adapter for code tools"""
    print(f"--- [Runtime] Executing Code Tools ---")
    
    operation = inputs.get("operation", "")
    
    if not operation:
        return {
            "result": "No operation specified",
            "success": False,
            "error": "operation is required"
        }
    
    # Get workspace root from env or context
    workspace_root = os.getenv("WORKSPACE_ROOT") or os.getcwd()
    max_file_size = int(os.getenv("MAX_FILE_SIZE", "1000000"))
    
    print(f"   Operation: {operation}")
    print(f"   Workspace: {workspace_root}")
    
    # Create service
    service = CodeToolsService(
        workspace_root=workspace_root,
        max_file_size=max_file_size
    )
    
    # Execute operation
    result = service.execute(
        operation=operation,
        path=inputs.get("path"),
        content=inputs.get("content"),
        query=inputs.get("query"),
        command=inputs.get("command")
    )
    
    return result