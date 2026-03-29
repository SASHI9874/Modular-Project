import * as vscode from 'vscode';

// --- 1. Code Actions (Lightbulb) ---
export class AgentCodeActionProvider implements vscode.CodeActionProvider {
    provideCodeActions(document: vscode.TextDocument, range: vscode.Range | vscode.Selection): vscode.CodeAction[] {
        // Only show the lightbulb if the user actually highlighted text
        if (range.isEmpty) {
            return [];
        }

        const explainAction = new vscode.CodeAction('💡 Explain with AI Agent', vscode.CodeActionKind.Refactor);
        explainAction.command = { command: 'aiAgent.explainCode', title: 'Explain Code' };

        const refactorAction = new vscode.CodeAction('🛠️ Refactor with AI Agent', vscode.CodeActionKind.Refactor);
        refactorAction.command = { command: 'aiAgent.refactor', title: 'Refactor Code' };

        return [explainAction, refactorAction];
    }
}

// --- 2. Ghost Text (Inline Completions) ---
export class AgentInlineCompletionProvider implements vscode.InlineCompletionItemProvider {
    // We pass in a function so the provider can talk to your WebSocket
    private requestCompletion: (prefix: string, suffix: string) => Promise<string | null>;

    constructor(requestCompletionFn: (prefix: string, suffix: string) => Promise<string | null>) {
        this.requestCompletion = requestCompletionFn;
    }

    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionItem[] | null> {
        
        // 1. Get the code before and after the cursor for context
        const prefixRange = new vscode.Range(new vscode.Position(0, 0), position);
        const prefix = document.getText(prefixRange);
        
        const suffixRange = new vscode.Range(position, new vscode.Position(document.lineCount, 0));
        const suffix = document.getText(suffixRange);

        // 2. Request completion from our backend via WebSocket
        try {
            const completionText = await this.requestCompletion(prefix, suffix);
            
            // If the user kept typing and cancelled the request, or backend returned null
            if (!completionText || token.isCancellationRequested) {
                return null;
            }

            // 3. Render the ghost text!
            return [new vscode.InlineCompletionItem(completionText, new vscode.Range(position, position))];
        } catch (error) {
            console.error("Autocomplete failed:", error);
            return null;
        }
    }
}