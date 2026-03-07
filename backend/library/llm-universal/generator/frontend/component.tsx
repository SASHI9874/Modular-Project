import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, StopCircle } from "lucide-react";
import { useAppStore } from "../../store";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function UniversalLlmWidget() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // --- GLOBAL STATE ---
  // Try to find context from PDF Loader or Vector Store
  const store = useAppStore();
  // Dynamic lookup: Check common keys or use a specific prop if passed
  const context = (store as any)["pdfloader_file_text"] || "";

  // --- SCROLL TO BOTTOM ---
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);

    // Create placeholder for AI response
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setIsStreaming(true);

    // Setup AbortController to stop generation
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // Direct Fetch for Streaming (Bypassing generated api.ts for better control)
      // Note: We use relative path '/api/llm-universal/stream' assuming proxy setup
      const response = await fetch("/api/llm-universal/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg, context: context }),
        signal: controller.signal,
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        aiResponse += chunk;

        // Update the last message (AI's message) with new chunk
        setMessages((prev) => {
          const newMsgs = [...prev];
          const lastMsg = newMsgs[newMsgs.length - 1];
          lastMsg.content = aiResponse; // Append text
          return newMsgs;
        });
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "⚠️ Error: Connection failed." },
        ]);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden relative">
      {/* HEADER */}
      <div className="bg-white p-4 border-b flex justify-between items-center z-10 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Bot className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-bold text-gray-800">Universal AI</h3>
            <p className="text-xs text-gray-500">Powered by LangChain</p>
          </div>
        </div>
        {context && (
          <span className="text-xs font-medium bg-green-100 text-green-700 px-3 py-1 rounded-full border border-green-200">
            📚 RAG Active
          </span>
        )}
      </div>

      {/* MESSAGES */}
      <div className="flex-1 p-4 overflow-y-auto space-y-6 bg-gray-50">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-4">
            <Bot className="w-12 h-12 opacity-20" />
            <p>Select a model in settings and start chatting.</p>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`
              max-w-[85%] p-4 rounded-2xl shadow-sm text-sm leading-relaxed
              ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-white border border-gray-100 text-gray-800 rounded-bl-none"
              }
            `}
            >
              {/* Simple Markdown Rendering logic could go here */}
              {m.content || <span className="animate-pulse">▍</span>}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <div className="p-4 bg-white border-t">
        <div className="relative flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !isStreaming && handleSend()}
            placeholder={
              context ? "Ask questions about your data..." : "Type a message..."
            }
            disabled={isStreaming}
            className="flex-1 bg-gray-100 border-0 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />

          {isStreaming ? (
            <button
              onClick={handleStop}
              className="p-3 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-colors"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-200"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
