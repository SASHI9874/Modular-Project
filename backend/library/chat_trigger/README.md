# Chat Trigger

Entry point for conversational flows.

## Usage

Drag this node onto the canvas as the starting point for agent workflows.

## Outputs

- `message`: User's chat message
- `session_id`: Unique session identifier
- `timestamp`: When the message was sent
- `user_id`: Optional user identifier

## Example Flow

```
[Chat Trigger] → [Agent] → [Tool]
```

User types a message → Triggers the workflow → Agent processes it
