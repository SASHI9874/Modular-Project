# AI Coding Agent

AI-powered coding assistant for VS Code.

## Features

- 💬 **Chat Interface** - Talk to your AI agent
- 🔍 **Code Explanation** - Select code and ask "what does this do?"
- ♻️ **Refactoring** - Get AI-powered refactoring suggestions

## Setup

1. Install the extension
2. Start the backend server
3. Extension auto-connects

## Configuration

- `aiAgent.backendUrl` - Backend WebSocket URL (default: `ws://localhost:8000`)
- `aiAgent.autoConnect` - Auto-connect on startup

## Usage

### Open Chat
`Ctrl+Shift+P` → "AI Agent: Open Chat"

### Explain Code
1. Select code
2. Right-click → "AI Agent: Explain Selected Code"

### Refactor
1. Select code
2. Right-click → "AI Agent: Refactor Code"

## Requirements

- Backend server running on configured port
- Node.js (for development)

## License

MIT