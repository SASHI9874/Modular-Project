"use client";
import React, { useState } from "react";
import { Handle, Position } from "reactflow";
import {
  Brain,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Database,
  Wrench,
  MessageSquare,
} from "lucide-react";

interface AgentNodeProps {
  data: {
    label: string;
    featureKey: string;
    connectedModel?: string;
    connectedMemory?: string;
    connectedTools?: Array<{ id: string; name: string }>;
  };
  selected: boolean;
}

export default function AgentNode({ data, selected }: AgentNodeProps) {
  const [expanded, setExpanded] = useState(true);

  // Increased size slightly and pushed further out from the border
  const handleSize = 12;
  const leftOffset = "2px";

  const toolCount = data.connectedTools?.length || 0;
  const isMemoryConnected = !!data.connectedMemory;
  const isModelConnected = !!data.connectedModel;

  const rowBaseClass =
    "relative flex items-center pl-6 pr-4 py-2 hover:bg-gray-50 transition-colors cursor-default";

  return (
    <div
      className={`
        relative bg-white rounded-xl shadow-lg border-2 w-[280px] transition-all
        ${selected ? "border-amber-500 ring-4 ring-amber-500/20" : "border-gray-200"}
      `}
    >
      {/* Header */}
      <div className="bg-amber-500 h-10 px-4 flex items-center justify-between text-white rounded-t-lg">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4" />
          <span className="font-semibold text-sm tracking-wide">
            {data.label || "ReAct Agent"}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-white hover:bg-white/20 rounded p-1 transition-colors"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {expanded && (
        <div className="relative flex flex-col bg-white py-1 rounded-b-lg">
          {/* Message Row */}
          <div
            className={`${rowBaseClass} border-b border-gray-100 pb-2.5 mb-1`}
          >
            {/* Forced inline color to bypass React Flow's gray override */}
            <Handle
              type="target"
              position={Position.Left}
              id="message"
              className="border-2 border-white"
              style={{
                backgroundColor: "#64748b",
                width: handleSize,
                height: handleSize,
                left: leftOffset,
              }}
            />
            <div className="flex items-center gap-3 w-full">
              <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
              <div className="flex flex-col">
                <span className="text-[13px] font-medium text-gray-800">
                  Message
                </span>
                <span className="text-[11px] text-gray-400">Trigger input</span>
              </div>
            </div>
          </div>

          {/* Chat Model Row */}
          <div className={rowBaseClass}>
            <Handle
              type="target"
              position={Position.Left}
              id="model"
              className="border-2 border-white"
              style={{
                backgroundColor: "#3b82f6",
                width: handleSize,
                height: handleSize,
                left: leftOffset,
              }}
            />
            <div className="flex items-center gap-3 w-full">
              <Sparkles className="w-3.5 h-3.5 text-blue-500" />
              <div className="flex flex-col">
                <span className="text-[13px] font-medium text-gray-800">
                  Chat Model*
                </span>
                <span
                  className={`text-[11px] ${isModelConnected ? "text-blue-600 font-medium" : "text-gray-400"}`}
                >
                  {isModelConnected ? data.connectedModel : "Connect LLM node"}
                </span>
              </div>
            </div>
          </div>

          {/* Memory Row */}
          <div
            className={`${rowBaseClass} ${isMemoryConnected ? "opacity-100" : "opacity-60"}`}
          >
            <Handle
              type="target"
              position={Position.Left}
              id="memory"
              className="border-2 border-white"
              style={{
                backgroundColor: "#22c55e",
                width: handleSize,
                height: handleSize,
                left: leftOffset,
              }}
            />
            <div className="flex items-center gap-3 w-full">
              <Database className="w-3.5 h-3.5 text-green-500" />
              <div className="flex flex-col">
                <span className="text-[13px] font-medium text-gray-800">
                  Memory
                </span>
                <span
                  className={`text-[11px] ${isMemoryConnected ? "text-green-600 font-medium" : "text-gray-400"}`}
                >
                  {isMemoryConnected ? data.connectedMemory : "Optional"}
                </span>
              </div>
            </div>
          </div>

          {/* Tools Row */}
          <div className={rowBaseClass}>
            <Handle
              type="target"
              position={Position.Left}
              id="tools"
              className="border-2 border-white"
              style={{
                backgroundColor: "#a855f7",
                width: handleSize,
                height: handleSize,
                left: leftOffset,
              }}
            />
            <div className="flex items-center gap-3 w-full">
              <Wrench className="w-3.5 h-3.5 text-purple-500" />
              <div className="flex flex-col">
                <span className="text-[13px] font-medium text-gray-800">
                  Tools {toolCount > 0 && `(${toolCount})`}
                </span>
                <span
                  className={`text-[11px] ${toolCount > 0 ? "text-purple-600 font-medium" : "text-gray-400"}`}
                >
                  {toolCount > 0 ? "Tools connected" : "Connect tool nodes"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- GLOBAL OUTPUT HANDLE --- */}
      {/* Placed outside the rows, vertically centered on the entire node */}
      <Handle
        type="source"
        position={Position.Right}
        id="response"
        className="border-2 border-white"
        style={{
          backgroundColor: "#f59e0b",
          width: handleSize,
          height: handleSize,
          right: "2px",
          top: "50%",
        }}
      />
    </div>
  );
}
