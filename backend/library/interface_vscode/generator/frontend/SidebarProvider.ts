import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    _view?: vscode.WebviewView;
    private _historyLoaded = false;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private context: vscode.ExtensionContext
    ) { }

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        this._historyLoaded = false;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        // Load history only once per panel open
        // Guard prevents double-load if panel is revealed multiple times
        webviewView.onDidChangeVisibility(() => {
            if (webviewView.visible && !this._historyLoaded) {
                this._loadHistory();
            }
        });

        // Initial load
        setTimeout(() => {
            if (!this._historyLoaded) {
                this._loadHistory();
            }
        }, 100);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.type === 'send_message') {
                vscode.commands.executeCommand('aiAgent._internalSendMessage', data.text);
            } else if (data.type === 'clear_history') {
                this.context.workspaceState.update('aiChatHistory', []);
                this._historyLoaded = false;
                this._loadHistory();
            }
        });
    }

    private _loadHistory() {
        if (!this._view) return;
        const history = this.context.workspaceState.get<Array<{
            role: string, content: string
        }>>('aiChatHistory') || [];
        this._view.webview.postMessage({ type: 'load_history', history });
        this._historyLoaded = true;
    }

    public postMessage(message: any) {
        this._view?.webview.postMessage(message);
    }

    public setConnectionStatus(connected: boolean) {
        this._view?.webview.postMessage({
            type: 'connection_status',
            connected
        });
    }

    public focus() {
        this._view?.show?.(true);
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
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--vscode-font-family);
      font-size: 13px;
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* ── Header ── */
    #header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: var(--vscode-titleBar-activeBackground);
      border-bottom: 1px solid var(--vscode-widget-border);
      flex-shrink: 0;
    }
    #header-left { display: flex; align-items: center; gap: 8px; }
    #header h2 {
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--vscode-titleBar-activeForeground);
    }
    #status-dot {
      width: 7px; height: 7px;
      border-radius: 50%;
      background: #6b7280;
      transition: background 0.3s;
      flex-shrink: 0;
    }
    #status-dot.connected { background: #22c55e; }
    #status-dot.connecting { background: #f59e0b; }
    #clear-btn {
      background: none;
      border: none;
      color: var(--vscode-descriptionForeground);
      cursor: pointer;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 3px;
      opacity: 0.6;
    }
    #clear-btn:hover { opacity: 1; background: var(--vscode-toolbar-hoverBackground); }

    /* ── Messages ── */
    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px 10px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    #messages::-webkit-scrollbar { width: 4px; }
    #messages::-webkit-scrollbar-thumb { background: var(--vscode-scrollbarSlider-background); border-radius: 2px; }

    /* ── Empty state ── */
    #empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      gap: 10px;
      color: var(--vscode-descriptionForeground);
      opacity: 0.5;
    }
    #empty-state .icon { font-size: 28px; }
    #empty-state p { font-size: 12px; text-align: center; line-height: 1.5; }

    /* ── User bubble ── */
    .user-row {
      display: flex;
      justify-content: flex-end;
    }
    .user-bubble {
      max-width: 85%;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      padding: 8px 12px;
      border-radius: 12px 12px 2px 12px;
      font-size: 13px;
      line-height: 1.5;
      word-break: break-word;
    }

    /* ── Agent block ── */
    .agent-block { display: flex; flex-direction: column; gap: 6px; }

    /* ── Reasoning accordion ── */
    .reasoning-header {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      padding: 5px 8px;
      border-radius: 6px;
      background: var(--vscode-editor-inactiveSelectionBackground);
      border: 1px solid var(--vscode-widget-border);
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      user-select: none;
      width: fit-content;
    }
    .reasoning-header:hover { background: var(--vscode-list-hoverBackground); }
    .reasoning-arrow { transition: transform 0.2s; font-size: 10px; }
    .reasoning-arrow.open { transform: rotate(90deg); }
    .reasoning-body {
      display: none;
      flex-direction: column;
      gap: 4px;
      padding: 6px 8px;
      border-left: 2px solid var(--vscode-widget-border);
      margin-left: 8px;
    }
    .reasoning-body.open { display: flex; }

    /* ── Tool pill ── */
    .tool-pill {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 5px 8px;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 6px;
      font-size: 11px;
      font-family: var(--vscode-editor-font-family);
    }
    .tool-pill-icon { opacity: 0.7; flex-shrink: 0; margin-top: 1px; }
    .tool-pill-body { display: flex; flex-direction: column; gap: 2px; }
    .tool-pill-name { color: var(--vscode-symbolIcon-functionForeground, #dcdcaa); font-weight: 600; }
    .tool-pill-args { color: var(--vscode-descriptionForeground); font-size: 10px; }
    .tool-pill-result { color: #22c55e; font-size: 10px; }
    .tool-pill-error { color: var(--vscode-errorForeground); font-size: 10px; }

    /* ── Agent response bubble ── */
    .agent-bubble {
      background: var(--vscode-editor-inactiveSelectionBackground);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 2px 12px 12px 12px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.6;
      word-break: break-word;
      overflow-x: hidden;
    }

    /* Markdown inside agent bubble */
    .agent-bubble p { margin: 0 0 8px 0; }
    .agent-bubble p:last-child { margin: 0; }
    .agent-bubble code {
      font-family: var(--vscode-editor-font-family);
      background: var(--vscode-textCodeBlock-background);
      padding: 1px 4px;
      border-radius: 3px;
      font-size: 12px;
    }
    .agent-bubble pre {
      margin: 8px 0;
      position: relative;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 6px;
      overflow: hidden;
    }
    .agent-bubble pre code {
      display: block;
      overflow-x: auto;
      padding: 10px 12px;
      background: transparent;
      border-radius: 0;
      font-size: 12px;
    }
    .agent-bubble h1, .agent-bubble h2, .agent-bubble h3 {
      margin: 10px 0 6px;
      font-size: 13px;
      font-weight: 600;
    }
    .agent-bubble ul, .agent-bubble ol {
      padding-left: 18px;
      margin: 6px 0;
    }
    .agent-bubble li { margin: 3px 0; }
    .agent-bubble blockquote {
      border-left: 3px solid var(--vscode-focusBorder);
      padding-left: 10px;
      margin: 6px 0;
      opacity: 0.8;
    }

    /* Copy button */
    .copy-btn {
      position: absolute; top: 5px; right: 5px;
      padding: 3px 7px;
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      border: 1px solid var(--vscode-button-border);
      border-radius: 3px;
      cursor: pointer;
      font-size: 10px;
      opacity: 0;
      transition: opacity 0.15s;
    }
    .agent-bubble pre:hover .copy-btn { opacity: 1; }

    /* ── Streaming cursor ── */
    .cursor { display: inline-block; width: 7px; height: 13px; background: var(--vscode-foreground); animation: blink 1s step-end infinite; vertical-align: text-bottom; margin-left: 1px; opacity: 0.7; }
    @keyframes blink { 0%,100%{opacity:0.7} 50%{opacity:0} }

    /* ── Thinking indicator ── */
    .thinking {
      display: flex; align-items: center; gap: 6px;
      padding: 6px 10px;
      background: var(--vscode-editor-inactiveSelectionBackground);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 6px;
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      width: fit-content;
    }
    .thinking-dots span {
      display: inline-block; width: 4px; height: 4px;
      background: currentColor; border-radius: 50%; margin: 0 1px;
      animation: dot-bounce 1.2s ease-in-out infinite;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dot-bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-4px)} }

    /* ── Error message ── */
    .error-msg {
      padding: 8px 10px;
      background: var(--vscode-inputValidation-errorBackground);
      border: 1px solid var(--vscode-inputValidation-errorBorder);
      border-radius: 6px;
      font-size: 12px;
      color: var(--vscode-errorForeground);
    }

    /* ── Input area ── */
    #input-area {
      padding: 10px;
      border-top: 1px solid var(--vscode-widget-border);
      background: var(--vscode-sideBar-background);
      flex-shrink: 0;
    }
    #input-row { display: flex; gap: 6px; align-items: flex-end; }
    textarea {
      flex: 1;
      padding: 8px 10px;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: 6px;
      resize: none;
      min-height: 36px;
      max-height: 120px;
      font-family: inherit;
      font-size: 13px;
      line-height: 1.4;
      overflow-y: auto;
    }
    textarea:focus { outline: 1px solid var(--vscode-focusBorder); border-color: var(--vscode-focusBorder); }
    textarea::placeholder { color: var(--vscode-input-placeholderForeground); }
    #send-btn {
      padding: 7px 10px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
      flex-shrink: 0;
      align-self: flex-end;
      height: 36px;
      width: 36px;
      display: flex; align-items: center; justify-content: center;
    }
    #send-btn:hover { background: var(--vscode-button-hoverBackground); }
    #send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    #hint { font-size: 10px; color: var(--vscode-descriptionForeground); opacity: 0.5; margin-top: 5px; text-align: right; }
  </style>
</head>
<body>

<!-- Header -->
<div id="header">
  <div id="header-left">
    <div id="status-dot" class="connecting"></div>
    <h2>AI Agent</h2>
  </div>
  <button id="clear-btn" title="Clear chat history">Clear</button>
</div>

<!-- Messages -->
<div id="messages">
  <div id="empty-state">
    <div class="icon">⬡</div>
    <p>Ask me anything about your code.<br>I can read, analyse, and edit files.</p>
  </div>
</div>

<!-- Input -->
<div id="input-area">
  <div id="input-row">
    <textarea id="input" placeholder="Ask the agent... (Ctrl+Enter)" rows="1"></textarea>
    <button id="send-btn" title="Send (Ctrl+Enter)">&#9654;</button>
  </div>
  <div id="hint">Ctrl+Enter to send</div>
</div>

<script>
  const vscode = acquireVsCodeApi();
  const messagesDiv = document.getElementById('messages');
  const emptyState = document.getElementById('empty-state');
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('send-btn');
  const statusDot = document.getElementById('status-dot');

  let isStreaming = false;
  let currentAgentBlock = null;
  let currentAgentBubble = null;
  let currentStreamText = '';
  let currentThinking = null;
  let messageCount = 0;

  // ── Marked config ──────────────────────────────────────────────────────────
  marked.setOptions({
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true,
  });

  // ── Message handler ────────────────────────────────────────────────────────
  window.addEventListener('message', event => {
    const msg = event.data;

    switch (msg.type) {

      case 'load_history':
        messagesDiv.innerHTML = '';
        messageCount = 0;
        if (msg.history.length === 0) {
          messagesDiv.appendChild(buildEmptyState());
          return;
        }
        msg.history.forEach(m => {
          if (m.role === 'user') addUserBubble(m.content);
          else addAgentBubble(m.content);
        });
        break;

      case 'connection_status':
        statusDot.className = msg.connected ? 'connected' : '';
        if (!msg.connected) statusDot.classList.add('connecting');
        break;

      case 'user_message':
        hideEmptyState();
        addUserBubble(msg.content);
        // Show thinking indicator
        currentAgentBlock = createAgentBlock();
        currentThinking = createThinking();
        currentAgentBlock.appendChild(currentThinking);
        messagesDiv.appendChild(currentAgentBlock);
        scrollBottom();
        isStreaming = true;
        sendBtn.disabled = true;
        break;

      case 'agent_reasoning':
        // Replace thinking with reasoning accordion
        if (currentAgentBlock && currentThinking) {
          currentThinking.remove();
          currentThinking = null;
        } else if (!currentAgentBlock) {
          currentAgentBlock = createAgentBlock();
          messagesDiv.appendChild(currentAgentBlock);
        }
        if (msg.tool_calls && msg.tool_calls.length > 0) {
          currentAgentBlock.appendChild(
            buildReasoningAccordion(msg.tool_calls, msg.iterations)
          );
        }
        // Create the bubble for streaming
        currentAgentBubble = createAgentBubble();
        currentStreamText = '';
        currentAgentBlock.appendChild(currentAgentBubble);
        scrollBottom();
        break;

      case 'stream_chunk':
        if (!currentAgentBubble) {
          // No reasoning event came — create bubble directly
          if (currentThinking) {
            currentThinking.remove();
            currentThinking = null;
          }
          if (!currentAgentBlock) {
            currentAgentBlock = createAgentBlock();
            messagesDiv.appendChild(currentAgentBlock);
          }
          currentAgentBubble = createAgentBubble();
          currentStreamText = '';
          currentAgentBlock.appendChild(currentAgentBubble);
        }
        currentStreamText += msg.content;
        currentAgentBubble.innerHTML =
          marked.parse(currentStreamText) + '<span class="cursor"></span>';
        addCopyButtons(currentAgentBubble);
        scrollBottom();
        break;

      case 'stream_end':
        if (currentAgentBubble) {
          currentAgentBubble.innerHTML = marked.parse(currentStreamText);
          addCopyButtons(currentAgentBubble);
        }
        currentAgentBubble = null;
        currentStreamText = '';
        break;

      case 'agent_response':
        // History is saved by extension.ts — nothing to do in UI
        // stream_end already finalised the bubble
        isStreaming = false;
        sendBtn.disabled = false;
        currentAgentBlock = null;
        currentThinking = null;
        scrollBottom();
        break;

      case 'error':
        if (currentThinking) { currentThinking.remove(); currentThinking = null; }
        if (currentAgentBlock) {
          const err = document.createElement('div');
          err.className = 'error-msg';
          err.textContent = '⚠ ' + msg.content;
          currentAgentBlock.appendChild(err);
        }
        isStreaming = false;
        sendBtn.disabled = false;
        currentAgentBlock = null;
        scrollBottom();
        break;
    }
  });

  // ── DOM builders ───────────────────────────────────────────────────────────

  function buildEmptyState() {
    const d = document.createElement('div');
    d.id = 'empty-state';
    d.innerHTML = '<div class="icon">⬡</div><p>Ask me anything about your code.<br>I can read, analyse, and edit files.</p>';
    return d;
  }

  function hideEmptyState() {
    const es = document.getElementById('empty-state');
    if (es) es.remove();
    messageCount++;
  }

  function addUserBubble(text) {
    const row = document.createElement('div');
    row.className = 'user-row';
    const bubble = document.createElement('div');
    bubble.className = 'user-bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
    messagesDiv.appendChild(row);
    scrollBottom();
  }

  function addAgentBubble(text) {
    const block = createAgentBlock();
    const bubble = createAgentBubble();
    bubble.innerHTML = marked.parse(text);
    addCopyButtons(bubble);
    block.appendChild(bubble);
    messagesDiv.appendChild(block);
    scrollBottom();
  }

  function createAgentBlock() {
    const d = document.createElement('div');
    d.className = 'agent-block';
    return d;
  }

  function createAgentBubble() {
    const d = document.createElement('div');
    d.className = 'agent-bubble';
    return d;
  }

  function createThinking() {
    const d = document.createElement('div');
    d.className = 'thinking';
    d.innerHTML = '<span>Agent is thinking</span><span class="thinking-dots"><span></span><span></span><span></span></span>';
    return d;
  }

  function buildReasoningAccordion(toolCalls, iterations) {
    const count = toolCalls.length;
    const label = count === 1
      ? '1 tool call'
      : count + ' tool calls';

    const wrapper = document.createElement('div');

    const header = document.createElement('div');
    header.className = 'reasoning-header';
    header.innerHTML = '<span class="reasoning-arrow">▶</span><span>🔧 ' + label + ' · ' + iterations + ' steps</span>';

    const body = document.createElement('div');
    body.className = 'reasoning-body';

    toolCalls.forEach(tc => {
      const pill = document.createElement('div');
      pill.className = 'tool-pill';

      const argsStr = tc.args
        ? Object.entries(tc.args).map(([k,v]) => k + '=' + JSON.stringify(v)).join(', ')
        : '';

      const resultStr = tc.result
        ? (tc.result.success === false
            ? '<span class="tool-pill-error">✗ ' + (tc.result.error || 'failed') + '</span>'
            : '<span class="tool-pill-result">✓ done</span>')
        : '';

      pill.innerHTML =
        '<span class="tool-pill-icon">⚙</span>' +
        '<span class="tool-pill-body">' +
          '<span class="tool-pill-name">' + tc.tool + '</span>' +
          (argsStr ? '<span class="tool-pill-args">' + argsStr + '</span>' : '') +
          resultStr +
        '</span>';

      body.appendChild(pill);
    });

    header.addEventListener('click', () => {
      const open = body.classList.toggle('open');
      header.querySelector('.reasoning-arrow').classList.toggle('open', open);
    });

    wrapper.appendChild(header);
    wrapper.appendChild(body);
    return wrapper;
  }

  function addCopyButtons(container) {
    container.querySelectorAll('pre').forEach(pre => {
      if (pre.querySelector('.copy-btn')) return;
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Copy';
      btn.onclick = () => {
        navigator.clipboard.writeText(pre.querySelector('code')?.innerText || '');
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
      };
      pre.appendChild(btn);
    });
  }

  function scrollBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // ── Input handlers ─────────────────────────────────────────────────────────

  function sendMessage() {
    const text = input.value.trim();
    if (!text || isStreaming) return;
    vscode.postMessage({ type: 'send_message', text });
    input.value = '';
    input.style.height = '36px';
  }

  sendBtn.addEventListener('click', sendMessage);

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      sendMessage();
    }
  });

  input.addEventListener('input', function() {
    this.style.height = '36px';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

  document.getElementById('clear-btn').addEventListener('click', () => {
    vscode.postMessage({ type: 'clear_history' });
    messagesDiv.innerHTML = '';
    messagesDiv.appendChild(buildEmptyState());
    messageCount = 0;
  });
</script>
</body>
</html>`;
    }
}