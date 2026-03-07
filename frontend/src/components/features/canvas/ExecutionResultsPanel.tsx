import React from "react";
import { X, Bot, Code2 } from "lucide-react";

interface ExecutionResultsPanelProps {
  results: any;
  onClose: () => void;
}

export default function ExecutionResultsPanel({
  results,
  onClose,
}: ExecutionResultsPanelProps) {
  if (!results) return null;

  // Determine if we have our clean output format from the new Output Node
  const hasCleanOutput = !!results.clean_output;
  const debugData = results.debug || results.results || results;

  return (
    <div className="absolute bottom-4 right-4 w-[450px] bg-white border border-gray-200 rounded-xl shadow-2xl z-40 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <span className="font-bold text-sm text-gray-700 flex items-center gap-2">
          {hasCleanOutput ? (
            <Bot className="w-4 h-4 text-emerald-600" />
          ) : (
            <Code2 className="w-4 h-4 text-blue-600" />
          )}
          {hasCleanOutput ? "Agent Response" : "Raw Execution Results"}
        </span>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded-md transition-colors"
        >
          <X className="w-4 h-4 text-gray-500 hover:text-gray-800" />
        </button>
      </div>

      {/* Body */}
      <div className="p-4 max-h-[500px] overflow-y-auto bg-gray-50">
        {hasCleanOutput ? (
          <div className="flex flex-col gap-4">
            {/* Clean Chat Bubble */}
            <div className="bg-white border border-emerald-200 p-4 rounded-xl shadow-sm">
              <p className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">
                {results.clean_output}
              </p>
            </div>

            {/* Collapsible Debug Section */}
            <details className="group">
              <summary className="text-xs text-gray-500 font-medium cursor-pointer hover:text-gray-800 transition-colors flex items-center gap-1 select-none">
                <span className="group-open:rotate-90 transition-transform">
                  ▶
                </span>
                View Debug Logs
              </summary>
              <div className="mt-2 p-3 bg-slate-900 rounded-lg overflow-x-auto">
                <pre className="text-[11px] text-emerald-400 font-mono">
                  {JSON.stringify(debugData, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        ) : (
          /* Fallback for flows without an Output Node */
          <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto shadow-inner">
            <pre className="text-xs font-mono text-slate-300">
              {JSON.stringify(debugData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
