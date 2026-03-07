"use client";
import React from "react";
import { Handle, Position } from "reactflow";
import * as Icons from "lucide-react";

interface ToolNodeProps {
  data: {
    label: string;
    icon?: string;
    color?: string;
  };
  selected: boolean;
}

export default function ToolNode({ data, selected }: ToolNodeProps) {
  const IconComponent = (Icons as any)[data.icon || "Wrench"] || Icons.Wrench;
  const color = data.color || "#8b5cf6";

  return (
    <div
      className={`
        bg-white rounded-lg shadow-md border-2 min-w-[160px]
        ${selected ? "border-purple-500 ring-2 ring-purple-200" : "border-purple-300"}
      `}
    >
      {/* Output Handle (connects to agent) */}
      <Handle
        type="source"
        position={Position.Right}
        id="tool-output"
        style={{
          right: -8,
          background: color,
          width: 10,
          height: 10,
        }}
      />

      {/* Content */}
      <div className="p-3 text-center">
        <div className="flex justify-center mb-2">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center"
            style={{ backgroundColor: `${color}20` }}
          >
            <IconComponent className="w-5 h-5" style={{ color }} />
          </div>
        </div>
        <div className="font-semibold text-sm text-gray-800">{data.label}</div>
        <div className="text-xs text-gray-500 mt-1">Tool</div>
      </div>
    </div>
  );
}
