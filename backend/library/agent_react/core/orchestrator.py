import os
import re
import json
from typing import List, Dict, Any, Callable
from .prompts import build_system_prompt, build_tool_result_message


class AgentOrchestrator:
    """ReAct Agent that can use tools"""
    
    def __init__(
        self,
        tools: List[Dict],
        llm_callable: Callable,
        tool_executor: Callable = None,
        max_iterations: int = 10
    ):
        self.tools = {t['name']: t for t in tools}
        self.llm_callable = llm_callable
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
        self.system_prompt = build_system_prompt(tools)
    
    def run(self, message: str) -> Dict[str, Any]:
        """Execute agent loop"""
        print(f" [Agent] Starting with message: {message[:50]}...")
        
        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message}
        ]
        
        tool_calls_made = []
        
        for iteration in range(self.max_iterations):
            print(f"🔄 [Agent] Iteration {iteration + 1}/{self.max_iterations}")
            
            # 1. Get LLM response
            try:
                response = self.llm_callable(conversation)
                response_text = response.get("content", "")
            except Exception as e:
                print(f" [Agent] LLM call failed: {e}")
                return {
                    "response": f"Error: LLM call failed - {str(e)}",
                    "tool_calls_made": tool_calls_made,
                    "iterations_used": iteration + 1,
                    "success": False
                }
            
            print(f"💭 [Agent] Response: {response_text[:100]}...")
            
            # --- THE FIX: ALWAYS CHECK FOR THE FINAL ANSWER FIRST ---
            final_answer = self._parse_final_answer(response_text)
            
            if final_answer:
                print(f" [Agent]  {final_answer[:50]}...")
                return {
                    "response": final_answer,
                    "tool_calls_made": tool_calls_made,
                    "iterations_used": iteration + 1,
                    "success": True
                }

            # --- IF NO ANSWER, CHECK FOR A TOOL CALL ---
            tool_call = self._parse_tool_call(response_text)
            
            if tool_call:
                tool_name = tool_call['tool']
                tool_args = tool_call['args']
                
                print(f" [Agent] Calling tool: {tool_name} with {tool_args}")
                
                tool_result = self._execute_tool(tool_name, tool_args)
                tool_calls_made.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result
                })
                
                # Add the LLM's reasoning and the tool's result to the conversation
                conversation.append({"role": "assistant", "content": response_text})
                conversation.append({
                    "role": "user",
                    "content": build_tool_result_message(tool_name, tool_result)
                })
                
                # Loop back to let the LLM analyze the tool result
                continue
            
            # --- IF NEITHER, THE LLM IS CONFUSED ---
            # No tool call or answer found - nudge the LLM to follow the format
            print("  [Agent] No valid tool call or final answer found in response.")
            conversation.append({"role": "assistant", "content": response_text})
            conversation.append({
                "role": "user", 
                "content": "Please follow the format. Provide either a 'TOOL: [name]' block or an 'ANSWER: [response]' block."
            })
        
        # Max iterations reached without a final answer
        print(f"🛑 [Agent] Max iterations reached")
        return {
            "response": "I apologize, but I couldn't complete this task within the iteration limit.",
            "tool_calls_made": tool_calls_made,
            "iterations_used": self.max_iterations,
            "success": False
        }
    
    def _parse_tool_call(self, text: str) -> Dict | None:
        """Parse tool call from response"""
        tool_match = re.search(r'TOOL:\s*(\w+)', text, re.IGNORECASE)
        args_match = re.search(r'ARGS:\s*(\{.*?\})', text, re.IGNORECASE | re.DOTALL)
        
        if tool_match:
            tool_name = tool_match.group(1)
            args = {}
            
            if args_match:
                try:
                    args = json.loads(args_match.group(1))
                except Exception as e:
                    print(f"  [Agent] Failed to parse args: {e}")
            
            return {"tool": tool_name, "args": args}
        
        return None
    
    def _parse_final_answer(self, text: str) -> str | None:
        """Parse final answer from response"""
        answer_match = re.search(r'ANSWER:\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        
        if answer_match:
            return answer_match.group(1).strip()
        
        return None
    
    def _execute_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool using the provided executor"""
        tool = self.tools.get(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in available tools: {list(self.tools.keys())}"
            }
        
        if not self.tool_executor:
            return {
                "success": False,
                "error": "Tool executor not configured"
            }
        
        try:
            result = self.tool_executor(tool_name, args)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }