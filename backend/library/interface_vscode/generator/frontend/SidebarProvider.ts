import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    _view?: vscode.WebviewView;
    _doc?: vscode.TextDocument;

    constructor(private readonly _extensionUri: vscode.Uri, private context: vscode.ExtensionContext) { }

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        // Load history from VS Code's storage when the panel opens
        const history = this.context.workspaceState.get<Array<{ role: string, content: string }>>('aiChatHistory') || [];
        webviewView.webview.postMessage({ type: 'load_history', history });

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'send_message': {
                    // Route message back to extension.ts
                    vscode.commands.executeCommand('aiAgent._internalSendMessage', data.text);
                    break;
                }
            }
        });
    }

    public addMessage(message: string, role: 'user' | 'agent') {
        if (this._view) {
            this._view.webview.postMessage({ type: 'agent_message', content: message, role: role });
        }
    }

    public focus() {
        if (this._view) {
            this._view.show?.(true);
        } else {
            vscode.commands.executeCommand('aiAgent.chatView.focus');
        }
    }

    private _getHtmlForWebview() {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://cdnjs.cloudflare.com; script-src 'unsafe-inline' https://cdnjs.cloudflare.com;">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/11.1.1/marked.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

            <style>
                body { padding: 15px; font-family: var(--vscode-font-family); color: var(--vscode-foreground); display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; margin: 0;}
                #messages { flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; margin-bottom: 10px; padding-right: 5px;}
                
                .message { padding: 12px; border-radius: 6px; line-height: 1.5; font-size: 13px; }
                .user { background: var(--vscode-button-background); color: var(--vscode-button-foreground); align-self: flex-end; max-width: 85%; }
                .agent { background: var(--vscode-editor-inactiveSelectionBackground); align-self: flex-start; max-width: 95%; width: 100%; overflow-x: hidden; }
                
                /* Markdown Styles */
                .agent p { margin: 0 0 10px 0; }
                .agent p:last-child { margin: 0; }
                .agent code { font-family: var(--vscode-editor-font-family); background: var(--vscode-textCodeBlock-background); padding: 2px 4px; border-radius: 3px; }
                
                /* Code Block Styles */
                .agent pre { margin: 10px 0; position: relative; background: var(--vscode-editor-background); border-radius: 6px; border: 1px solid var(--vscode-widget-border); }
                .agent pre code { display: block; overflow-x: auto; padding: 12px; background: transparent; border-radius: 0; }
                
                /* Copy Button */
                .copy-btn { position: absolute; top: 5px; right: 5px; padding: 4px 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 11px; opacity: 0; transition: opacity 0.2s; }
                .agent pre:hover .copy-btn { opacity: 1; }
                .copy-btn:hover { background: var(--vscode-button-secondaryHoverBackground); }

                .input-container { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;}
                textarea { width: 100%; padding: 10px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; resize: none; min-height: 60px; box-sizing: border-box; font-family: inherit;}
                textarea:focus { outline: 1px solid var(--vscode-focusBorder); }
                button.send-btn { padding: 8px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-weight: bold;}
                button.send-btn:hover { background: var(--vscode-button-hoverBackground); }
            </style>
        </head>
        <body>
            <div id="messages"></div>
            <div class="input-container">
                <textarea id="input" placeholder="Ask the AI agent... (Ctrl+Enter to send)"></textarea>
                <button class="send-btn" onclick="sendMessage()">Send</button>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                const messagesDiv = document.getElementById('messages');
                const input = document.getElementById('input');
                
                let currentStreamingDiv = null;
                let currentStreamingRawText = ""; // Keep track of raw markdown

                // Configure Marked.js to use Highlight.js
                marked.setOptions({
                    highlight: function(code, lang) {
                        if (lang && hljs.getLanguage(lang)) {
                            return hljs.highlight(code, { language: lang }).value;
                        }
                        return hljs.highlightAuto(code).value;
                    }
                });

                window.addEventListener('message', event => {
                    const message = event.data;
                    
                    if (message.type === 'load_history') {
                        messagesDiv.innerHTML = ''; 
                        message.history.forEach(msg => {
                            addMessage(msg.content, msg.role, false);
                        });
                    } 
                    else if (message.type === 'agent_message') {
                        addMessage(message.content, message.role, false);
                        currentStreamingDiv = null;
                    }
                    else if (message.type === 'stream_chunk') {
                        handleStreamChunk(message.content);
                    }
                    else if (message.type === 'stream_end') {
                        currentStreamingDiv = null;
                        currentStreamingRawText = "";
                    }
                });

                function sendMessage() {
                    const text = input.value.trim();
                    if (!text) return;
                    vscode.postMessage({ type: 'send_message', text: text });
                    addMessage(text, 'user', true);
                    input.value = '';
                    // Reset text area height
                    input.style.height = '60px';
                }

                function addMessage(text, sender, isRawText) {
                    const div = document.createElement('div');
                    div.className = 'message ' + sender;
                    
                    if (sender === 'agent') {
                        // Parse markdown for agent messages
                        div.innerHTML = marked.parse(text);
                        addCopyButtons(div);
                    } else {
                        // Plain text for user messages
                        div.textContent = text;
                    }
                    
                    messagesDiv.appendChild(div);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    return div;
                }

                function handleStreamChunk(chunk) {
                    if (!currentStreamingDiv) {
                        currentStreamingDiv = document.createElement('div');
                        currentStreamingDiv.className = 'message agent';
                        messagesDiv.appendChild(currentStreamingDiv);
                        currentStreamingRawText = "";
                    }
                    
                    // Append raw text and re-parse the whole thing
                    currentStreamingRawText += chunk;
                    currentStreamingDiv.innerHTML = marked.parse(currentStreamingRawText);
                    
                    // Add copy buttons to the newly rendered code blocks
                    addCopyButtons(currentStreamingDiv);
                    
                    // Auto-scroll as text streams in
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function addCopyButtons(container) {
                    const preBlocks = container.querySelectorAll('pre');
                    preBlocks.forEach(pre => {
                        // Avoid adding multiple buttons to the same block during streaming
                        if (pre.querySelector('.copy-btn')) return;

                        const btn = document.createElement('button');
                        btn.className = 'copy-btn';
                        btn.textContent = 'Copy';
                        
                        btn.onclick = () => {
                            const code = pre.querySelector('code').innerText;
                            navigator.clipboard.writeText(code);
                            btn.textContent = 'Copied!';
                            setTimeout(() => btn.textContent = 'Copy', 2000);
                        };
                        
                        pre.appendChild(btn);
                    });
                }

                // Auto-resize textarea
                input.addEventListener('input', function() {
                    this.style.height = '60px';
                    this.style.height = (this.scrollHeight) + 'px';
                });

                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
            </script>
        </body>
        </html>`;
    }
}