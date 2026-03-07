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
  const handleSize = 12;
  const rightOffset = "2px";

  return (
    <div
      className={`
        bg-white rounded-xl shadow-lg border-2 w-[280px] flex flex-col transition-all
        ${selected ? "border-blue-500 ring-4 ring-blue-500/20" : "border-gray-200"}
      `}
    >
      {/* --- 1. HEADER LAYER --- */}
      <div className="bg-blue-500 h-10 px-4 flex items-center justify-between text-white rounded-t-lg">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4" />
          <span className="font-semibold text-sm tracking-wide">
            {data.label || "Chat Input"}
          </span>
        </div>
        <div className="bg-blue-600/60 px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase border border-blue-400/30">
          Trigger
        </div>
      </div>

      {/* --- 2. BODY LAYER (Now relative so the handle centers on this part) --- */}
      <div className="relative flex flex-col bg-white py-4 px-5 rounded-b-lg">
        <div className="flex items-start gap-3">
          <Zap className="w-4 h-4 text-blue-500 mt-0.5" />
          <div className="flex flex-col">
            <span className="text-[13px] font-medium text-gray-800">
              Chat Trigger
            </span>
            <span className="text-[11px] text-gray-400 mt-0.5">
              Receives user message
            </span>
          </div>
        </div>

        {/* --- 3. OUTPUT LAYER (Moved inside the body) --- */}
        <Handle
          type="source"
          position={Position.Right}
          id="message"
          className="border-2 border-white transition-all hover:scale-125 hover:shadow-[0_0_8px_rgba(59,130,246,0.6)] cursor-crosshair"
          style={{
            backgroundColor: "#3b82f6",
            width: handleSize,
            height: handleSize,
            right: rightOffset,
            top: "50%", // Now calculates 50% of the white body section!
          }}
        />
      </div>
    </div>
  );
}
