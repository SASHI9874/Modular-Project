import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FileText, Box, Database, Settings } from 'lucide-react';

// Map icon strings to actual Lucide components
const iconMap: Record<string, React.ReactNode> = {
  'pdf-loader': <FileText className="w-4 h-4" />,
  'gpt-4': <Box className="w-4 h-4" />,
  'vector-db': <Database className="w-4 h-4" />,
  'default': <Settings className="w-4 h-4" />
};

const FeatureNode = ({ data }: NodeProps) => {
  return (
    <div className="bg-white border-2 border-gray-200 rounded-lg shadow-md min-w-[150px] overflow-hidden">
      {/* 1. Header with Icon */}
      <div className="bg-gray-50 px-3 py-2 border-b border-gray-100 flex items-center gap-2">
        <span className="text-gray-500">
          {iconMap[data.icon] || iconMap['default']}
        </span>
        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
          {data.label}
        </span>
      </div>

      {/* 2. Body (Inputs & Outputs) */}
      <div className="p-3 relative">
        
        {/* Dynamic Input Handles (Left Side) */}
        {data.inputs && data.inputs.map((input: string, index: number) => (
          <div key={input} className="relative flex items-center mb-2 last:mb-0">
            <Handle
              type="target"
              position={Position.Left}
              id={input} // Crucial: This ID allows specific port connections
              className="!bg-blue-500 !w-3 !h-3 !-left-4"
            />
            <span className="text-xs text-gray-500 ml-1 capitalize">{input}</span>
          </div>
        ))}

        {/* Dynamic Output Handles (Right Side) */}
        {data.outputs && data.outputs.map((output: string, index: number) => (
          <div key={output} className="relative flex items-center justify-end mb-2 last:mb-0">
            <span className="text-xs text-gray-500 mr-1 capitalize">{output}</span>
            <Handle
              type="source"
              position={Position.Right}
              id={output}
              className="!bg-green-500 !w-3 !h-3 !-right-4"
            />
          </div>
        ))}

        {/* Fallback for generic nodes */}
        {!data.inputs && !data.outputs && (
             <div className="text-xs text-gray-400 italic text-center">Config Node</div>
        )}
      </div>
    </div>
  );
};

export default memo(FeatureNode);