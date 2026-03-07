"use client";
import React from "react";
import { Handle, Position } from "reactflow";
import { MessageCircle, Zap } from "lucide-react";

interface TriggerNodeProps {
  data: {
    label: string;
  };
  selected: boolean;
}

export default function TriggerNode({ data, selected }: TriggerNodeProps) {
  return (
    <div
      className={`
        bg-white rounded-lg shadow-md border-2 min-w-[180px]
        ${selected ? "border-blue-500 ring-2 ring-blue-200" : "border-blue-300"}
      `}
    >
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-3 rounded-t-lg">
        <div className="flex items-center gap-2 text-white">
          <MessageCircle className="w-5 h-5" />
          <span className="font-bold text-sm">{data.label}</span>
        </div>
      </div>

      <div className="p-3 bg-blue-50">
        <div className="flex items-center gap-2 text-blue-700 text-xs">
          <Zap className="w-4 h-4" />
          <span>Entry Point</span>
        </div>
      </div>

      {/* Output Handles */}
      <Handle
        type="source"
        position={Position.Right}
        id="message"
        style={{ top: "40%", background: "#3b82f6" }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="session_id"
        style={{ top: "60%", background: "#3b82f6" }}
      />
    </div>
  );
}
