from typing import Dict, Any, List
import os
from ..core.orchestrator import AgentOrchestrator


def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Runtime adapter for ReAct agent"""
    print(f"--- [Runtime] Executing ReAct Agent ---")
    
    message = inputs.get("message", "")
    session_id = inputs.get("session_id")
    
    print(f"   Message: {message[:50]}...")
    print(f"   Session: {session_id}")
    
    # Get available tools from context
    available_tools = context.get("available_tools", [])
    print(f"   Available tools: {[t['name'] for t in available_tools]}")
    
    # Get LLM callable from context
    llm_callable = context.get("llm_callable")
    
    if not llm_callable:
        return {
            "response": "Error: No LLM configured for agent",
            "tool_calls_made": [],
            "iterations_used": 0,
            "success": False
        }
    
    # Get tool executor from context
    tool_executor = context.get("tool_executor")
    
    if not tool_executor:
        return {
            "response": "Error: Tool executor not configured",
            "tool_calls_made": [],
            "iterations_used": 0,
            "success": False
        }
    
    # Get config
    max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
    
    # Create and run agent
    agent = AgentOrchestrator(
        tools=available_tools,
        llm_callable=llm_callable,
        tool_executor=tool_executor,
        max_iterations=max_iterations
    )
    
    try:
        result = agent.run(message)
        return result
    
    except Exception as e:
        import traceback
        print(f"❌ [Agent] Error:")
        print(traceback.format_exc())
        
        return {
            "response": f"Agent error: {str(e)}",
            "tool_calls_made": [],
            "iterations_used": 0,
            "success": False,
            "error": str(e)
        }