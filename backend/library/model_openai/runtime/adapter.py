import os
from typing import Dict, Any
from ..core.service import generate_chat_completion

def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime adapter for the OpenAI Model feature.
    Translates workflow state into standard parameters for the core service.
    """
    print("🧠 [OpenAI Adapter] Preparing model call...")
    
    # 1. Extract configuration from the canvas node
    node_config = context.get("node_config", {})
    api_key = node_config.get("api_key") or os.getenv("OPENAI_API_KEY")
    model_name = node_config.get("model_name", "gpt-4o")
    
    # Safely parse temperature
    try:
        temperature = float(node_config.get("temperature", 0.7))
    except (TypeError, ValueError):
        temperature = 0.7

    if not api_key:
        return {
            "success": False,
            "response": "Error: OpenAI API key is missing. Please add it to the node config or .env file."
        }

    # 2. Format Messages
    messages = inputs.get("messages", [])
    
    # Graceful fallback: If the executor passed standard strings instead of an array 
    # (e.g., if used in a simple pipeline instead of an agent)
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

    # 3. Execute Core Service
    try:
        answer = generate_chat_completion(
            messages=messages,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        print(f"✅ [OpenAI Adapter] Received response successfully.")
        return {
            "success": True,
            "response": answer
        }
        
    except Exception as e:
        print(f"❌ [OpenAI Adapter] API Error: {str(e)}")
        return {
            "success": False,
            "response": f"OpenAI API Error: {str(e)}"
        }