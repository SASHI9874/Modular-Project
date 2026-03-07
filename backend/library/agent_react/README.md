# ReAct Agent

Reasoning and Acting agent with tool use capabilities.

## How It Works

1. Receives user message
2. Reasons about what tools to use
3. Calls tools as needed
4. Synthesizes final answer

## Configuration

- `MAX_ITERATIONS`: Max reasoning loops (default: 10)
- `AGENT_TEMPERATURE`: LLM temperature (default: 0.7)

## Usage
```
[Chat Trigger] → [Agent] ⤏ [Calculator]
                         ⤏ [Knowledge Search]
```

Agent will automatically select which tools to use based on the query.