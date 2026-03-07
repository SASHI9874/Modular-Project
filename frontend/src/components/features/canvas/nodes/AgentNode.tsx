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
  X,
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

  return (
    <div
      className={`
        bg-white rounded-lg shadow-lg border-2 min-w-[280px]
        ${selected ? "border-amber-500 ring-2 ring-amber-200" : "border-amber-300"}
      `}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-3 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Brain className="w-5 h-5" />
            <span className="font-bold">{data.label || "AI Agent"}</span>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-white hover:bg-white/20 rounded p-1"
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="p-4 space-y-3">
          {/* Chat Model Connection */}
          <div className="relative">
            <Handle
              type="target"
              position={Position.Left}
              id="model"
              style={{
                left: -8,
                top: 20,
                background: "#3b82f6",
                width: 12,
                height: 12,
              }}
            />
            <div className="flex items-center gap-2 text-sm">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span className="font-medium text-gray-700">Chat Model*</span>
            </div>
            {data.connectedModel ? (
              <div className="ml-6 mt-1 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                {data.connectedModel}
              </div>
            ) : (
              <div className="ml-6 mt-1 text-xs text-gray-400">
                Connect LLM node
              </div>
            )}
          </div>

          <div className="border-t border-gray-200" />

          {/* Memory Connection */}
          <div className="relative">
            <Handle
              type="target"
              position={Position.Left}
              id="memory"
              style={{
                left: -8,
                top: 85,
                background: "#10b981",
                width: 12,
                height: 12,
              }}
            />
            <div className="flex items-center gap-2 text-sm">
              <Database className="w-4 h-4 text-green-600" />
              <span className="font-medium text-gray-700">Memory</span>
            </div>
            {data.connectedMemory ? (
              <div className="ml-6 mt-1 text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                {data.connectedMemory}
              </div>
            ) : (
              <div className="ml-6 mt-1 text-xs text-gray-400">Optional</div>
            )}
          </div>

          <div className="border-t border-gray-200" />

          {/* Tools Section */}
          <div className="relative">
            <div className="flex items-center gap-2 text-sm mb-2">
              <Wrench className="w-4 h-4 text-purple-600" />
              <span className="font-medium text-gray-700">Tools</span>
            </div>

            {/* Tool Slots */}
            {[1, 2, 3, 4].map((slot) => {
              const tool = data.connectedTools?.[slot - 1];
              return (
                <div key={slot} className="relative mb-2">
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={`tool-${slot}`}
                    style={{
                      left: -8,
                      top: 150 + (slot - 1) * 30,
                      background: "#8b5cf6",
                      width: 12,
                      height: 12,
                    }}
                  />
                  {tool ? (
                    <div className="ml-6 flex items-center justify-between bg-purple-50 text-purple-700 px-2 py-1 rounded text-xs">
                      <span>◇ {tool.name}</span>
                      <X className="w-3 h-3 cursor-pointer hover:text-purple-900" />
                    </div>
                  ) : (
                    <div className="ml-6 text-xs text-gray-300 border border-dashed border-gray-300 rounded px-2 py-1">
                      Drop tool here
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        style={{
          right: -8,
          background: "#f59e0b",
          width: 12,
          height: 12,
        }}
      />
    </div>
  );
}
