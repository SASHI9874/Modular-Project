from typing import Dict, Any
from ..core.service import calculate


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for calculator tool
    """
    print(f"--- [Runtime] Executing Calculator ---")
    
    expression = inputs.get("expression", "")
    
    if not expression:
        return {
            "result": None,
            "expression": "",
            "error": "No expression provided",
            "success": False
        }
    
    print(f"   Expression: {expression}")
    
    result = calculate(expression)
    
    return result