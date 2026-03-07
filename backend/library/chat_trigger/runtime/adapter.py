from typing import Dict, Any
from datetime import datetime
import uuid


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for chat trigger.
    Extracts user input from execution context.
    """
    print(f"--- [Runtime] Executing Chat Trigger ---")
    
    # Extract from context (provided by executor)
    user_message = context.get("user_input", "")
    session_id = context.get("session_id") or str(uuid.uuid4())
    user_id = context.get("user_id")
    
    print(f"   Message: {user_message[:50]}...")
    print(f"   Session: {session_id}")
    
    return {
        "message": user_message,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "success": True
    }