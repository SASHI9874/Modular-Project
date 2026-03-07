from typing import Dict, Any

def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Catches the final output and flags it for the API response."""
    
    # The agent returns a dictionary with 'response'. We extract it here.
    final_text = inputs.get("response") or inputs.get("message") or str(inputs)
    
    print(f"[Output Node] Final Result: {final_text[:50]}...")
    
    return {
        "is_final_output": True,
        "final_text": final_text,
        "success": True
    }