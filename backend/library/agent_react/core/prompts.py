def build_system_prompt(tools: list) -> str:
    """Build system prompt with available tools"""
    
    tool_descriptions = []
    for tool in tools:
        tool_desc = f"- {tool['name']}: {tool['description']}"
        if tool.get('parameters'):
            params = ', '.join(tool['parameters'].keys())
            tool_desc += f"\n  Parameters: {params}"
        tool_descriptions.append(tool_desc)
    
    tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
    
    return f"""You are a helpful AI assistant that can use tools to accomplish tasks.

When you need to use a tool, respond EXACTLY in this format:
TOOL: <tool_name>
ARGS: {{"param": "value"}}

When you have the final answer, respond with:
ANSWER: <your final response>

Available tools:
{tools_text}

Think step by step. Use tools when needed. Provide clear final answers."""


def build_tool_result_message(tool_name: str, result: dict) -> str:
    """Format tool result for agent"""
    if result.get("success"):
        return f"Tool '{tool_name}' returned: {result.get('result', result)}"
    else:
        return f"Tool '{tool_name}' failed: {result.get('error', 'Unknown error')}"