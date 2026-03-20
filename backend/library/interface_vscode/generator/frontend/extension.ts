import * as vscode from 'vscode';
import WebSocket from 'ws';

let ws: WebSocket | null = null;
let chatPanel: vscode.WebviewPanel | null = null;

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Coding Agent activated');

    // Connect to backend
    connectToBackend();

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent.chat', () => {
            showChatPanel(context);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent.explainCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showWarningMessage('Please select code to explain');
                return;
            }

            sendToAgent('Explain this code:\n' + selection);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent.refactor', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showWarningMessage('Please select code to refactor');
                return;
            }

            sendToAgent('Refactor this code:\n' + selection);
        })
    );
}

function connectToBackend() {
    const config = vscode.workspace.getConfiguration('aiAgent');
    const backendUrl = config.get<string>('backendUrl', 'ws://localhost:8000');
    const wsUrl = `${backendUrl}/api/interface-vscode/ws/vscode`;
    
    ws = new WebSocket(wsUrl);

    ws.on('open', () => {
        console.log('✅ Connected to backend');
        vscode.window.showInformationMessage('AI Agent connected');
    });

    ws.on('message', (data: WebSocket.Data) => {
        const message = JSON.parse(data.toString());
        handleAgentResponse(message);
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        vscode.window.showErrorMessage('Failed to connect to AI Agent backend');
    });

    ws.on('close', () => {
        console.log('❌ Disconnected from backend');
        // Reconnect after 5 seconds
        setTimeout(connectToBackend, 5000);
    });
}

function sendToAgent(message: string) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        vscode.window.showErrorMessage('Not connected to AI Agent');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    const context = editor ? {
        file_path: editor.document.fileName,
        cursor_position: {
            line: editor.selection.active.line,
            character: editor.selection.active.character
        },
        selection: editor.document.getText(editor.selection)
    } : {};

    const payload = {
        type: 'user_message',
        message: message,
        context: context
    };

    ws.send(JSON.stringify(payload));
}

function handleAgentResponse(message: any) {
    console.log('Agent response:', message);

    if (message.type === 'agent_response') {
        // Show response in chat panel or notification
        if (chatPanel) {
            chatPanel.webview.postMessage({
                type: 'agent_message',
                content: message.content
            });
        } else {
            vscode.window.showInformationMessage(message.content);
        }
    }
}

function showChatPanel(context: vscode.ExtensionContext) {
    if (chatPanel) {
        chatPanel.reveal();
        return;
    }

    chatPanel = vscode.window.createWebviewPanel(
        'aiAgentChat',
        'AI Coding Agent',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true
        }
    );

    chatPanel.webview.html = getChatHtml();

    // Handle messages from webview
    chatPanel.webview.onDidReceiveMessage(
        message => {
            if (message.type === 'send_message') {
                sendToAgent(message.text);
            }
        },
        undefined,
        context.subscriptions
    );

    chatPanel.onDidDispose(() => {
        chatPanel = null;
    });
}

function getChatHtml(): string {
    return `<!DOCTYPE html>
    <html>
    <head>
        <style>
            body { 
                padding: 20px; 
                font-family: var(--vscode-font-family);
                color: var(--vscode-foreground);
            }
            #messages { 
                height: 400px; 
                overflow-y: auto; 
                border: 1px solid var(--vscode-input-border);
                padding: 10px;
                margin-bottom: 10px;
            }
            .message { 
                margin: 10px 0; 
                padding: 8px;
                border-radius: 4px;
            }
            .user { 
                background: var(--vscode-input-background);
                text-align: right;
            }
            .agent { 
                background: var(--vscode-editor-background);
            }
            #input { 
                width: 100%; 
                padding: 10px;
                background: var(--vscode-input-background);
                color: var(--vscode-input-foreground);
                border: 1px solid var(--vscode-input-border);
            }
            button {
                margin-top: 10px;
                padding: 8px 16px;
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div id="messages"></div>
        <textarea id="input" placeholder="Ask the AI agent..." rows="3"></textarea>
        <button onclick="sendMessage()">Send</button>

        <script>
            const vscode = acquireVsCodeApi();
            const messagesDiv = document.getElementById('messages');
            const input = document.getElementById('input');

            window.addEventListener('message', event => {
                const message = event.data;
                if (message.type === 'agent_message') {
                    addMessage(message.content, 'agent');
                }
            });

            function sendMessage() {
                const text = input.value.trim();
                if (!text) return;

                addMessage(text, 'user');
                
                vscode.postMessage({
                    type: 'send_message',
                    text: text
                });

                input.value = '';
            }

            function addMessage(text, sender) {
                const div = document.createElement('div');
                div.className = 'message ' + sender;
                div.textContent = text;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>`;
}

export function deactivate() {
    if (ws) {
        ws.close();
    }
}