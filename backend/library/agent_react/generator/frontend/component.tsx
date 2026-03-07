import React from "react";
import { Brain, Zap } from "lucide-react";

export default function AgentWidget() {
  return (
    <div className="flex flex-col h-full w-full bg-white rounded-xl shadow-lg border border-amber-200 overflow-hidden">
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-4 text-white">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5" />
          <h3 className="font-bold">ReAct Agent</h3>
        </div>
      </div>

      <div className="flex-1 p-6 space-y-4">
        <div className="text-center">
          <Zap className="w-12 h-12 text-amber-500 mx-auto mb-3" />
          <h4 className="font-semibold text-gray-900 mb-2">
            Reasoning & Acting Agent
          </h4>
          <p className="text-sm text-gray-600">
            This agent can use connected tools to accomplish complex tasks
            through iterative reasoning.
          </p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
          <p className="text-xs font-medium text-amber-900">Capabilities:</p>
          <ul className="text-xs text-amber-800 space-y-1">
            <li>• Multi-step reasoning</li>
            <li>• Tool selection and usage</li>
            <li>• Context-aware responses</li>
            <li>• Error recovery</li>
          </ul>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
          <p className="text-xs text-gray-600">
            💡 Connect tools to this agent using the dashed purple connection
            type
          </p>
        </div>
      </div>
    </div>
  );
}
