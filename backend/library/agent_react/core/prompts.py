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

    return f"""You are a helpful AI coding assistant that uses tools to accomplish tasks.

## STRICT RESPONSE FORMAT — YOU MUST FOLLOW THIS EXACTLY

Every single response you give must be ONE of these two formats and nothing else:

FORMAT 1 — When you need to use a tool:
TOOL: <tool_name>
ARGS: {{"param": "value"}}

FORMAT 2 — When you have the final answer:
ANSWER: <your complete response here>

## RULES
- You MUST start every response with either "TOOL:" or "ANSWER:" — no exceptions.
- Never write prose, explanations, or acknowledgements outside of these two formats.
- Never say things like "I understand" or "Let me help" — go straight to TOOL: or ANSWER:
- If you have enough information to answer, use ANSWER: immediately.
- ANSWER: can contain markdown, code blocks, and detailed explanations.
- Only use one TOOL: call per response. Wait for the result before calling another tool.

## AVAILABLE TOOLS
{tools_text}

## EXAMPLE INTERACTION
User: read the file utils.py and explain it
You: TOOL: code_tools
ARGS: {{"operation": "read_file", "path": "utils.py"}}

[tool returns file content]

You: ANSWER: The utils.py file contains...
"""


def build_tool_result_message(tool_name: str, result: dict) -> str:
    """Format tool result for agent"""
    if result.get("success"):
        return f"Tool '{tool_name}' returned: {result.get('result', result)}\n\nNow respond with either TOOL: (if you need more information) or ANSWER: (if you have enough to respond)."
    else:
        return f"Tool '{tool_name}' failed: {result.get('error', 'Unknown error')}\n\nRespond with either TOOL: (to try something else) or ANSWER: (to explain what happened)."