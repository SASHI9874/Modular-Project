import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// This component replaces the default "One Dot" node
const FeatureNode = ({ data }: NodeProps) => {
  // data.inputs comes from the meta.json we saved earlier
  const inputs = data.inputs || [];
  const outputs = data.outputs || [];

  return (
    <div className="bg-white border-2 border-gray-300 rounded-md min-w-[200px] shadow-sm hover:shadow-md transition-shadow">
      
      {/* HEADER */}
      <div className="bg-purple-50 px-3 py-2 border-b border-gray-200 rounded-t-md">
        <h3 className="font-bold text-sm text-gray-800">{data.label}</h3>
        <p className="text-[10px] text-gray-500">{data.feature_id}</p>
      </div>

      {/* BODY */}
      <div className="p-3 flex justify-between gap-4">
        
        {/* INPUTS (Left Side) */}
        <div className="flex flex-col gap-3">
          {inputs.map((input: any, index: number) => (
            <div key={input.name} className="relative flex items-center h-5">
              {/* The Handle ID MUST match the input name for the backend to work! */}
              <Handle
                type="target"
                position={Position.Left}
                id={input.name} 
                style={{ left: -14, top: '50%', background: '#555' }}
              />
              <span className="text-xs text-gray-700 ml-1">
                {input.name} <span className="text-[9px] text-gray-400">({input.type})</span>
              </span>
            </div>
          ))}
        </div>

        {/* OUTPUTS (Right Side) */}
        <div className="flex flex-col gap-3 items-end">
          {outputs.map((output: any, index: number) => (
            <div key={output.name} className="relative flex items-center h-5 justify-end">
              <span className="text-xs text-gray-700 mr-1 text-right">
                {output.name}
              </span>
              <Handle
                type="source"
                position={Position.Right}
                id={output.name}
                style={{ right: -14, top: '50%', background: '#555' }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default memo(FeatureNode);