from typing import Dict, Any
import os
import traceback
from ..core.service import chat
from ..core.errors import AuthenticationError, LLMError

def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime Adapter for the Visual Builder.
    Attempts to call the real LLM if keys are present.
    Otherwise, returns a simulation mock.
    """
    print(f"--- [Runtime] Executing Universal LLM ---")
    
    # 1. Extract Inputs from previous nodes
    prompt = inputs.get("prompt", "Hello World")
    rag_context = inputs.get("context", "")
    
    # 2. Extract Config from the Node's Settings (if passed by Executor)
    node_config = context.get("node_config", {})
    
    # 3. Detect if this is RAG mode based on upstream node
    upstream_node_type = context.get("source_node_type", "")
    is_rag_context = upstream_node_type in ["vector-store", "retriever", "pdf-loader", "document-loader"]
    
    # Only use context if it actually came from a retrieval source
    actual_context = rag_context if (is_rag_context and rag_context) else ""
    
    # 4. Map UI settings to config format
    override_config = {}
    if "provider" in node_config:
        override_config["provider"] = node_config["provider"]
    if "model" in node_config:
        override_config["model"] = node_config["model"]
    if "temperature" in node_config:
        override_config["temperature"] = float(node_config["temperature"])
    
    # Log execution details
    print(f"   Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"   Prompt: {prompt}")
    print(f"   Context Length: {len(actual_context)} chars")
    print(f"   RAG Mode: {is_rag_context}")
    print(f"   Override Config: {override_config}")

    try:
        # Attempt Real Execution
        response_text = chat(prompt, actual_context, override_config)
        
        return {
            "response": response_text,
            "success": True,
            "provider": override_config.get("provider", "default"),
            "rag_mode": is_rag_context
        }
        
    except (ValueError, AuthenticationError) as e:
        # Fallback to Simulation Mode
        print(f"   [Runtime] Falling back to Simulation: {str(e)}")
        
        provider = override_config.get("provider", os.getenv("LLM_PROVIDER", "openai"))
        
        simulated_response = (
            f" **SIMULATION MODE**\n\n"
            f"Your prompt: \"{prompt}\"\n\n"
            f"**Configuration:**\n"
            f"- Provider: {provider}\n"
            f"- Model: {override_config.get('model', 'default')}\n"
            f"- RAG Mode: {' Active' if is_rag_context else ' Disabled'}\n"
            f"- Context: {len(actual_context)} characters\n\n"
            f"**To enable real AI:**\n"
            f"Set the appropriate API key in your backend .env file:\n"
            f"- OpenAI: OPENAI_API_KEY\n"
            f"- Azure: AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT + AZURE_DEPLOYMENT_NAME\n"
            f"- Gemini: GOOGLE_API_KEY\n\n"
            f"This simulation allows you to test your workflow logic without API keys."
        )
        
        return {
            "response": simulated_response,
            "success": False,
            "simulation": True,
            "provider": provider
        }

    except LLMError as e:
        # Known LLM error - return user-friendly message
        print(f"   [Runtime] LLM Error: {str(e)}")
        
        return {
            "response": f" AI Error: {str(e)}",
            "success": False,
            "error": True,
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    except Exception as e:
        # Unknown error - log full traceback for debugging
        print(f"   [Runtime] UNEXPECTED ERROR:")
        print(traceback.format_exc())
        
        return {
            "response": f" Runtime Error: {str(e)}",
            "success": False,
            "error": True,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }