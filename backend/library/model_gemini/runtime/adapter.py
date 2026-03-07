import os
from typing import Dict, Any
from ..core.service import generate_chat_completion

def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for the Google Gemini Model feature.
    """
    print("🧠 [Gemini Adapter] Preparing model call...")
    
    node_config = context.get("node_config", {})
    api_key = node_config.get("api_key") or os.getenv("GOOGLE_API_KEY") # Updated to match your GOOGLE_API_KEY standard
    model_name = node_config.get("model_name", "gemini-2.5-flash")
    
    try:
        temperature = float(node_config.get("temperature", 0.7))
    except (TypeError, ValueError):
        temperature = 0.7

    if not api_key:
        return {
            "success": False,
            "response": "Error: GOOGLE_API_KEY is missing. Please add it to the node config or .env file."
        }

    # Format Messages
    messages = inputs.get("messages", [])
    if not messages:
        system_context = inputs.get("context", "")
        user_prompt = inputs.get("prompt", "")
        if system_context:
            messages.append({"role": "system", "content": system_context})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
            
    if not messages:
        return {
            "success": False,
            "response": "Error: No messages or prompt provided to the model."
        }

    # Execute
    try:
        answer = generate_chat_completion(
            messages=messages,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        print(f"✅ [Gemini Adapter] Received response successfully.")
        return {
            "success": True,
            "response": answer
        }
        
    except Exception as e:
        error_str = str(e).lower()
        print(f"❌ [Gemini Adapter] API Error: {error_str}")
        return {
            "success": False,
            "response": f"Gemini API Error: {str(e)}"
        }