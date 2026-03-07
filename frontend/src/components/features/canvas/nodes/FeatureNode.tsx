"use client";
import React, { useState, memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import {
  FileText,
  Box,
  Database,
  Settings,
  ChevronDown,
  ChevronUp,
  ArrowRightCircle,
  Wrench,
  Sparkles,
  MessageSquare,
} from "lucide-react";

// 1. Dynamic Icon Mapper
const getIcon = (iconName?: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    "pdf-loader": <FileText className="w-4 h-4" />,
    "gpt-4": <Box className="w-4 h-4" />,
    sparkles: <Sparkles className="w-4 h-4" />,
    "vector-db": <Database className="w-4 h-4" />,
    calculator: <Wrench className="w-4 h-4" />,
    message: <MessageSquare className="w-4 h-4" />,
    tool: <Wrench className="w-4 h-4" />,
    default: <Settings className="w-4 h-4" />,
  };
  return iconMap[iconName || ""] || iconMap["default"];
};

// 2. Semantic Color Mapper based on Capability Type
const getTypeColor = (type?: string) => {
  switch (type?.toLowerCase()) {
    case "model":
      return "#3b82f6"; // Blue
    case "memory":
      return "#22c55e"; // Green
    case "tool":
      return "#a855f7"; // Purple
    case "data":
    case "string":
    case "number":
      return "#64748b"; // Slate
    default:
      return "#94a3b8"; // Light Slate
  }
};

const FeatureNode = ({ data, selected }: NodeProps) => {
  const [expanded, setExpanded] = useState(true);

  // Sizing for perfect alignment
  const handleSize = 14;
  const offset = "-8px";

  // Theme color for the node header/border (defaults to slate if none provided)
  const themeColor = data.color || "#64748b";
  const rowBaseClass =
    "relative flex items-center pl-6 pr-4 py-2 hover:bg-gray-50 transition-colors cursor-default border-b border-gray-100 last:border-0";

  // Safely parse objects (falling back to empty objects if undefined)
  const inputs = data.inputs || {};
  const outputs = data.outputs || {};

  return (
    <div
      className={`
        bg-white rounded-xl shadow-lg border-2 w-[280px] flex flex-col transition-all
        ${selected ? "ring-4" : "border-gray-200"}
      `}
      style={{
        borderColor: selected ? themeColor : "#e5e7eb",
        boxShadow: selected ? `0 0 0 4px ${themeColor}33` : "",
      }}
    >
      {/* --- 1. HEADER LAYER --- */}
      <div
        className="h-10 px-4 flex items-center justify-between text-white rounded-t-lg"
        style={{ backgroundColor: themeColor }}
      >
        <div className="flex items-center gap-2 truncate">
          <span className="shrink-0">{getIcon(data.icon)}</span>
          <span className="font-semibold text-sm tracking-wide truncate">
            {data.label || "Generic Feature"}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-white hover:bg-white/20 rounded p-1 transition-colors shrink-0"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* --- 2. BODY LAYER --- */}
      {expanded && (
        <div className="flex flex-col bg-white py-1 rounded-b-lg">
          {/* Optional Node Description */}
          {data.description && (
            <div className="px-4 py-2 text-[11px] text-gray-500 italic border-b border-gray-100 bg-gray-50/50">
              {data.description}
            </div>
          )}

          {/* --- DYNAMIC INPUTS --- */}
          {Object.entries(inputs).map(([key, spec]: [string, any]) => {
            const portColor = getTypeColor(spec?.type);
            return (
              <div key={`in-${key}`} className={rowBaseClass}>
                <Handle
                  type="target"
                  position={Position.Left}
                  id={key}
                  className="border-2 border-white"
                  style={{
                    backgroundColor: portColor,
                    width: handleSize,
                    height: handleSize,
                    left: offset,
                    top: "50%",
                  }}
                />
                <div className="flex items-center gap-3 w-full">
                  <ArrowRightCircle className="w-3.5 h-3.5 text-slate-400" />
                  <div className="flex flex-col">
                    <span className="text-[13px] font-medium text-gray-800">
                      {key}
                    </span>
                    <span
                      className="text-[11px] text-gray-400"
                      style={{ color: portColor }}
                    >
                      {spec?.type || "data"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}

          {/* --- DYNAMIC OUTPUTS --- */}
          {Object.entries(outputs).map(([key, spec]: [string, any]) => {
            const portColor = getTypeColor(spec?.type);
            return (
              <div
                key={`out-${key}`}
                className={`${rowBaseClass} justify-end pl-4 pr-6`}
              >
                <div className="flex items-center gap-3 text-right">
                  <div className="flex flex-col items-end">
                    <span className="text-[13px] font-medium text-gray-800">
                      {key}
                    </span>
                    <span
                      className="text-[11px] font-medium"
                      style={{ color: portColor }}
                    >
                      {spec?.type || "capability"}
                    </span>
                  </div>
                  <ArrowRightCircle className="w-3.5 h-3.5 text-slate-400 rotate-180" />
                </div>
                <Handle
                  type="source"
                  position={Position.Right}
                  id={key}
                  className="border-2 border-white transition-all hover:scale-125 hover:shadow-md cursor-crosshair"
                  style={{
                    backgroundColor: portColor,
                    width: handleSize,
                    height: handleSize,
                    right: offset,
                    top: "50%",
                  }}
                />
              </div>
            );
          })}

          {/* Fallback for nodes with no inputs/outputs */}
          {Object.keys(inputs).length === 0 &&
            Object.keys(outputs).length === 0 && (
              <div className="px-4 py-3 text-[11px] text-gray-400 text-center italic">
                Config-only node
              </div>
            )}
        </div>
      )}
    </div>
  );
};

export default memo(FeatureNode);
