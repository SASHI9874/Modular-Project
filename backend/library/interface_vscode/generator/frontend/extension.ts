import * as vscode from 'vscode';
import WebSocket from 'ws';
import { SidebarProvider } from './SidebarProvider';
import { AgentCodeActionProvider, AgentInlineCompletionProvider } from './Providers';

const pendingRequests = new Map<string, (value: any) => void>();
let messageQueue: string[] = [];
let ws: WebSocket | null = null;
let sidebarProvider: SidebarProvider;
let globalContext: vscode.ExtensionContext;
let isConnected = false;

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Coding Agent activated');
    globalContext = context;

    sidebarProvider = new SidebarProvider(context.extensionUri, context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("aiAgent.chatView", sidebarProvider)
    );

    const config = vscode.workspace.getConfiguration('aiAgent');
    if (config.get<boolean>('autoConnect', true)) {
        connectToBackend();
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('aiAgent._internalSendMessage', (text: string) => {
            sendToAgent(text);
        })
    );

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

    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file', language: '*' },
            new AgentCodeActionProvider(),
            { providedCodeActionKinds: [vscode.CodeActionKind.Refactor] }
        )
    );

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

        const requestId = Math.random().toString(36).substring(7);

        const timeout = setTimeout(() => {
            pendingRequests.delete(requestId);
            resolve(null);
        }, 2500);

        pendingRequests.set(requestId, (completionText: string) => {
            clearTimeout(timeout);
            resolve(completionText);
        });

        ws.send(JSON.stringify({
            type: 'autocomplete_request',
            id: requestId,
            context: { prefix, suffix }
        }));
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
        await new Promise(resolve => setTimeout(resolve, 500));
    });
}

function connectToBackend() {
    const config = vscode.workspace.getConfiguration('aiAgent');
    const backendUrl = config.get<string>('backendUrl', 'ws://localhost:8000');
    const wsUrl = `${backendUrl}/api/interface-vscode/ws/vscode`;

    ws = new WebSocket(wsUrl);

    ws.on('open', () => {
        console.log('Connected to backend');
        isConnected = true;
        sidebarProvider.setConnectionStatus(true);

        while (messageQueue.length > 0) {
            const payload = messageQueue.shift();
            if (payload) ws!.send(payload);
        }
    });

    ws.on('message', (data: WebSocket.Data) => {
        try {
            const message = JSON.parse(data.toString());

            switch (message.type) {
                case 'stream_chunk':
                    sidebarProvider.postMessage({
                        type: 'stream_chunk',
                        content: message.content
                    });
                    break;

                case 'stream_end':
                    sidebarProvider.postMessage({ type: 'stream_end' });
                    break;

                case 'agent_response':
                    // Save to history only here — NOT in sendToAgent
                    // This prevents duplicates
                    saveToHistory('agent', message.content);
                    sidebarProvider.postMessage({
                        type: 'agent_response',
                        content: message.content
                    });
                    break;

                case 'agent_reasoning':
                    // Tool calls summary sent before the answer
                    sidebarProvider.postMessage({
                        type: 'agent_reasoning',
                        tool_calls: message.tool_calls,
                        iterations: message.iterations
                    });
                    break;

                case 'autocomplete_response':
                    if (message.id && pendingRequests.has(message.id)) {
                        const resolveFn = pendingRequests.get(message.id)!;
                        resolveFn(message.content);
                        pendingRequests.delete(message.id);
                    }
                    break;

                case 'error':
                    sidebarProvider.postMessage({
                        type: 'error',
                        content: message.content
                    });
                    vscode.window.showErrorMessage(`AI Agent: ${message.content}`);
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
        console.log('Disconnected from backend');
        isConnected = false;
        ws = null;
        sidebarProvider.setConnectionStatus(false);
        setTimeout(connectToBackend, 5000);
    });
}

function sendToAgent(message: string) {
    // Save user message to history
    saveToHistory('user', message);

    // Tell UI to add user bubble — but NOT agent bubble yet
    sidebarProvider.postMessage({ type: 'user_message', content: message });

    const editor = vscode.window.activeTextEditor;
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const rootPath = workspaceFolders?.[0]?.uri.fsPath || null;

    const context = editor ? {
        workspace_root: rootPath,
        file_path: editor.document.fileName,
        file_content: editor.document.getText(),
        cursor_position: {
            line: editor.selection.active.line,
            character: editor.selection.active.character
        },
        selection: editor.document.getText(editor.selection),
        selection_range: {
            startLine: editor.selection.start.line,
            endLine: editor.selection.end.line + 1
        }
    } : { workspace_root: rootPath };

    const payload = JSON.stringify({
        type: 'user_message',
        message,
        context
    });

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        vscode.window.showWarningMessage('AI Agent offline. Message queued.');
        messageQueue.push(payload);
        if (!ws) connectToBackend();
        return;
    }

    ws.send(payload);
}

function saveToHistory(role: 'user' | 'agent', content: string) {
    const current = globalContext.workspaceState.get<Array<{ role: string, content: string }>>('aiChatHistory') || [];
    current.push({ role, content });
    globalContext.workspaceState.update('aiChatHistory', current);
}

async function handleBackendToolCall(message: any) {
    console.log(`Executing local tool: ${message.name}`);

    if (message.name === 'read_file') {
        try {
            const uris = await vscode.workspace.findFiles(message.arguments.path, null, 1);
            if (uris.length > 0) {
                const document = await vscode.workspace.openTextDocument(uris[0]);
                ws?.send(JSON.stringify({
                    type: 'tool_response',
                    id: message.id,
                    content: document.getText()
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
    } else if (message.name === 'edit_file') {
        try {
            const { path, newText, startLine, endLine } = message.arguments;
            const uris = await vscode.workspace.findFiles(path, null, 1);
            if (uris.length === 0) throw new Error(`File not found: ${path}`);

            const uri = uris[0];
            const edit = new vscode.WorkspaceEdit();
            const range = new vscode.Range(
                new vscode.Position(startLine, 0),
                new vscode.Position(endLine, 0)
            );
            edit.replace(uri, range, newText);
            const success = await vscode.workspace.applyEdit(edit);

            if (success) {
                await vscode.commands.executeCommand('editor.action.formatDocument', uri);
                ws?.send(JSON.stringify({
                    type: 'tool_response',
                    id: message.id,
                    content: 'Successfully updated the file.'
                }));
            } else {
                throw new Error('VS Code rejected the edit.');
            }
        } catch (error) {
            ws?.send(JSON.stringify({
                type: 'tool_response',
                id: message.id,
                error: `Failed to edit file: ${String(error)}`
            }));
        }
    } else {
        ws?.send(JSON.stringify({
            type: 'tool_response',
            id: message.id,
            error: `Unknown tool: ${message.name}`
        }));
    }
}

export function deactivate() {
    if (ws) ws.close();
}