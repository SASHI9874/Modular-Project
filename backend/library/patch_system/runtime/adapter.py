from typing import Dict, Any
from ..core.service import PatchSystemService


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Runtime adapter for patch system"""
    print(f"--- [Runtime] Executing Patch System ---")
    
    operation = inputs.get("operation", "")
    
    if not operation:
        return {
            "result": "No operation specified",
            "success": False
        }
    
    print(f"   Operation: {operation}")
    
    service = PatchSystemService()
    
    result = service.execute(
        operation=operation,
        file_path=inputs.get("file_path"),
        old_content=inputs.get("old_content"),
        new_content=inputs.get("new_content"),
        patch=inputs.get("patch"),
        task_description=inputs.get("task_description")
    )
    
    return result