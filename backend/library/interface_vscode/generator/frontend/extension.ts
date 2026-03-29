import * as vscode from 'vscode';
import WebSocket from 'ws';
import { SidebarProvider } from './SidebarProvider';
import { AgentCodeActionProvider, AgentInlineCompletionProvider } from './Providers';
let messageQueue: string[] = [];
const pendingRequests = new Map<string, (value: any) => void>();

let ws: WebSocket | null = null;
let sidebarProvider: SidebarProvider;
let globalContext: vscode.ExtensionContext;

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Coding Agent activated');
    globalContext = context;

    // 1. Initialize Sidebar
    sidebarProvider = new SidebarProvider(context.extensionUri, context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("aiAgent.chatView", sidebarProvider)
    );

    // 2. Connect to Backend
    const config = vscode.workspace.getConfiguration('aiAgent');
    if (config.get<boolean>('autoConnect', true)) {
        connectToBackend();
    }

    // 3. Register Internal Command (Triggered by the Webview 'Send' button)
    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent._internalSendMessage', (text: string) => {
            sendToAgent(text);
        })
    );

    // 4. Register Editor Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent.explainCode', async () => {
            handleEditorAction('Explain this code:\n');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent.refactor', async () => {
            handleEditorAction('Refactor this code:\n');
        })
    );

    // 5. Register Code Actions (Lightbulb)
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file', language: '*' }, // Triggers on all files
            new AgentCodeActionProvider(),
            { providedCodeActionKinds: [vscode.CodeActionKind.Refactor] }
        )
    );

    // 6. Register Ghost Text (Inline Completions)
    context.subscriptions.push(
        vscode.languages.registerInlineCompletionItemProvider(
            { scheme: 'file', language: '*' },
            new AgentInlineCompletionProvider(requestAutocomplete)
        )
    );

}

function requestAutocomplete(prefix: string, suffix: string): Promise<string | null> {
    return new Promise((resolve) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            resolve(null);
            return;
        }

        // Generate a random ID for this specific completion request
        const requestId = Math.random().toString(36).substring(7);
        
        // Timeout after 2.5 seconds. Ghost text should be fast, otherwise give up so it doesn't hang.
        const timeout = setTimeout(() => {
            pendingRequests.delete(requestId);
            resolve(null);
        }, 2500);

        // Store the resolve function so we can call it when the backend replies
        pendingRequests.set(requestId, (completionText: string) => {
            clearTimeout(timeout);
            resolve(completionText);
        });

        const payload = JSON.stringify({
            type: 'autocomplete_request',
            id: requestId,
            context: { prefix, suffix }
        });

        ws.send(payload);
    });
}


async function handleEditorAction(promptPrefix: string) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.document.getText(editor.selection);
    if (!selection) {
        vscode.window.showWarningMessage('Please select code first');
        return;
    }

    sidebarProvider.focus();

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "AI is processing...",
        cancellable: false
    }, async () => {
        sendToAgent(promptPrefix + selection);
        // Small delay to allow UI to catch up
        await new Promise(resolve => setTimeout(resolve, 500));
    });
}

function connectToBackend() {
    const config = vscode.workspace.getConfiguration('aiAgent');
    const backendUrl = config.get<string>('backendUrl', 'ws://localhost:8000');
    const wsUrl = `${backendUrl}/api/interface-vscode/ws/vscode`;
    
    ws = new WebSocket(wsUrl);

    ws.on('open', () => {
        console.log(' Connected to backend');
        vscode.window.showInformationMessage('AI Agent connected');
        
        //  Flush any pending messages that were queued while disconnected
        while (messageQueue.length > 0) {
            const payload = messageQueue.shift();
            if (payload) ws!.send(payload);
        }
    });

    ws.on('message', (data: WebSocket.Data) => {
        try {
            const message = JSON.parse(data.toString());
            
            //  NEW: Proper Message Routing
            switch (message.type) {
                case 'stream_chunk':
                    sidebarProvider._view?.webview.postMessage({ type: 'stream_chunk', content: message.content });
                    break;
                case 'agent_response':
                    // If your backend sends a final full message after streaming, we save it here
                    saveToHistory('agent', message.content);
                    sidebarProvider._view?.webview.postMessage({ type: 'stream_end' });
                    // Fallback in case your backend DOESN'T stream, it just sends the full text:
                    if (!message.is_streaming_complete_flag) {
                       sidebarProvider._view?.webview.postMessage({ type: 'agent_message', content: message.content, role: 'agent' });
                    }
                    break;
                case 'autocomplete_response':
                    // If we get a response and the promise is still waiting, resolve it!
                    if (message.id && pendingRequests.has(message.id)) {
                        const resolveFn = pendingRequests.get(message.id)!;
                        resolveFn(message.content); // Sends the text back to the Ghost Text provider
                        pendingRequests.delete(message.id);
                    }
                    break;
                    

                case 'error':
                    vscode.window.showErrorMessage(`AI Agent Error: ${message.content}`);
                    break;
                case 'tool_call':
                    handleBackendToolCall(message);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });

    ws.on('close', () => {
        console.log(' Disconnected from backend');
        ws = null;
        // Reconnect with a slight backoff
        setTimeout(connectToBackend, 5000);
    });
}

function sendToAgent(message: string) {
    // 1. Save to History & Update UI immediately
    saveToHistory('user', message);
    sidebarProvider.addMessage(message, 'user');

    // 2. Build Context
    const editor = vscode.window.activeTextEditor;
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const rootPath = workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0].uri.fsPath : null;

    const context = editor ? {
        workspace_root: rootPath,
        file_path: editor.document.fileName,
        file_content: editor.document.getText(),
        cursor_position: {
            line: editor.selection.active.line,
            character: editor.selection.active.character
        },
        selection: editor.document.getText(editor.selection),
        // Send the exact range so the backend knows what lines to replace
        selection_range: {
            startLine: editor.selection.start.line,
            endLine: editor.selection.end.line + 1 
        }
    } : { workspace_root: rootPath };

    const payload = JSON.stringify({
        type: 'user_message',
        message: message,
        context: context
    });

    // 3. Send or Queue
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        vscode.window.showWarningMessage('AI Agent offline. Message queued and will send when connected.');
        messageQueue.push(payload); 
        
        if (!ws) connectToBackend(); // Try to force a connection
        return;
    }

    ws.send(payload);
}

function handleAgentResponse(message: any) {
    if (message.type === 'agent_response') {
        saveToHistory('agent', message.content);
        sidebarProvider.addMessage(message.content, 'agent');
    }
}

function saveToHistory(role: 'user' | 'agent', content: string) {
    // Retrieve current history, append, and save back to workspace state
    const currentHistory = globalContext.workspaceState.get<Array<{role: string, content: string}>>('aiChatHistory') || [];
    currentHistory.push({ role, content });
    globalContext.workspaceState.update('aiChatHistory', currentHistory);
}

async function handleBackendToolCall(message: any) {
    // Expected message format from your backend:
    // { type: 'tool_call', id: 'call_abc123', name: 'read_file', arguments: { path: 'src/utils.ts' } }

    console.log(`Executing local tool: ${message.name}`);

    if (message.name === 'read_file') {
        try {
            // Ask VS Code to find the file in the current workspace
            const uris = await vscode.workspace.findFiles(message.arguments.path, null, 1);
            
            if (uris.length > 0) {
                // Read the file content natively
                const document = await vscode.workspace.openTextDocument(uris[0]);
                const content = document.getText();
                
                // Send the result BACK to the agent's execution loop
                ws?.send(JSON.stringify({
                    type: 'tool_response',
                    id: message.id,
                    content: content
                }));
            } else {
                ws?.send(JSON.stringify({
                    type: 'tool_response',
                    id: message.id,
                    error: `File not found: ${message.arguments.path}`
                }));
            }
        } catch (error) {
            ws?.send(JSON.stringify({
                type: 'tool_response',
                id: message.id,
                error: `Failed to read file: ${String(error)}`
            }));
        }
    } 
    else if (message.name === 'list_directory') {
        // You can easily expand this to handle directory listings, applying diffs, etc.
        // ...
    }
    else if (message.name === 'edit_file') {
        try {
            // Expected arguments from backend: 
            // { path: "src/utils.ts", newText: "...", startLine: 10, endLine: 20 }
            const { path, newText, startLine, endLine } = message.arguments;

            const uris = await vscode.workspace.findFiles(path, null, 1);
            if (uris.length === 0) {
                throw new Error(`File not found: ${path}`);
            }

            const uri = uris[0];
            const edit = new vscode.WorkspaceEdit();
            
            // Define the range of text to replace. 
            // If replacing the whole file, startLine is 0 and endLine is the document line count.
            const range = new vscode.Range(
                new vscode.Position(startLine, 0),
                new vscode.Position(endLine, 0)
            );

            // Queue the replacement
            edit.replace(uri, range, newText);

            // Apply the edit to the workspace
            const success = await vscode.workspace.applyEdit(edit);

            if (success) {
                // Optionally format the document after the AI edits it
                await vscode.commands.executeCommand('editor.action.formatDocument', uri);
                
                ws?.send(JSON.stringify({
                    type: 'tool_response',
                    id: message.id,
                    content: "Successfully updated the file."
                }));
            } else {
                throw new Error("VS Code rejected the workspace edit.");
            }
        } catch (error) {
            ws?.send(JSON.stringify({
                type: 'tool_response',
                id: message.id,
                error: `Failed to edit file: ${String(error)}`
            }));
        }
    }
    else {
        ws?.send(JSON.stringify({
            type: 'tool_response',
            id: message.id,
            error: `Unknown tool: ${message.name}`
        }));
    }
}


export function deactivate() {
    if (ws) {
        ws.close();
    }
}