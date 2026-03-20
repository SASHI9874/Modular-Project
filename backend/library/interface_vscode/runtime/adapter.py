from typing import Dict, Any


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for VS Code interface
    
    In platform execution, this is just a passthrough.
    Real VS Code logic is in the generated extension.
    """
    print(f"--- [Runtime] VS Code Interface ---")
    
    agent_response = inputs.get("agent_response", "")
    
    # In platform, we just return success
    # In downloaded app, the generated extension will handle actual VS Code I/O
    
    return {
        "user_message": "",
        "context": {},
        "success": True
    }