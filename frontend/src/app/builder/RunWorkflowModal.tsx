import React, { useState, useEffect } from "react";
import { Node } from "reactflow";
import {
  Play,
  X,
  MessageSquare,
  UploadCloud,
  Webhook,
  File,
} from "lucide-react";

interface RunWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRun: (payload: {
    entry_node_id?: string;
    payload: Record<string, any>;
  }) => void;
  nodes: Node[];
}

export default function RunWorkflowModal({
  isOpen,
  onClose,
  onRun,
  nodes,
}: RunWorkflowModalProps) {
  // 1. Graph Introspection: Find all nodes that act as starting triggers
  // (You can adjust this filter based on exactly how you name your node types)
  const triggers = nodes.filter(
    (n) =>
      n.type?.includes("trigger") ||
      n.data?.label?.toLowerCase().includes("trigger") ||
      n.data?.label?.toLowerCase().includes("input"),
  );

  const [selectedTriggerId, setSelectedTriggerId] = useState<string>("");
  const [formData, setFormData] = useState<Record<string, any>>({});

  // 2. Auto-select the first trigger if it exists when the modal opens
  useEffect(() => {
    if (isOpen) {
      if (triggers.length > 0) {
        setSelectedTriggerId(triggers[0].id);
      } else {
        setSelectedTriggerId("");
      }
      setFormData({}); // Reset form
    }
  }, [isOpen, nodes]);

  if (!isOpen) return null;

  const selectedTrigger = triggers.find((t) => t.id === selectedTriggerId);

  const handleSubmit = () => {
    onRun({
      entry_node_id: selectedTrigger?.id,
      payload: formData,
    });
  };

  // 3. Dynamic Form Renderer: Renders different inputs based on trigger type
  const renderTriggerForm = () => {
    if (!selectedTrigger) {
      return (
        <div className="text-center py-6 px-4 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          <Play className="w-8 h-8 text-gray-400 mx-auto mb-2 opacity-50" />
          <p className="text-sm font-medium text-gray-700">
            No Trigger Node Found
          </p>
          <p className="text-xs text-gray-500 mt-1">
            This workflow will run with an empty starting context.
          </p>
        </div>
      );
    }

    // Identify the type of trigger to render the correct UI
    const label = selectedTrigger.data?.label?.toLowerCase() || "";

    // CASE A: Chat Trigger
    if (label.includes("chat") || label.includes("message")) {
      return (
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-gray-400" />
            Chat Message
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Inject a test message into this trigger.
          </p>
          <textarea
            autoFocus
            value={formData.message || ""}
            onChange={(e) =>
              setFormData({ ...formData, message: e.target.value })
            }
            placeholder="e.g., What is the weather like in Tokyo?"
            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none min-h-[100px]"
          />
        </div>
      );
    }

    // CASE B: File Upload Trigger (Future-proofing)
    if (
      label.includes("file") ||
      label.includes("upload") ||
      label.includes("document")
    ) {
      return (
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-gray-400" />
            Test File Upload
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Simulate a file drop to start the workflow.
          </p>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors cursor-pointer">
            <File className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <span className="text-sm text-blue-600 font-medium">
              Click to browse
            </span>
            <span className="text-sm text-gray-500"> or drag and drop</span>
            <input
              type="file"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file)
                  setFormData({
                    ...formData,
                    filename: file.name,
                    fileObject: file,
                  });
              }}
            />
          </div>
          {formData.filename && (
            <div className="mt-2 text-xs text-green-600 font-medium">
              Selected: {formData.filename}
            </div>
          )}
        </div>
      );
    }

    // CASE C: Webhook or Generic Trigger
    return (
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Webhook className="w-4 h-4 text-gray-400" />
          JSON Payload (Webhook Simulation)
        </label>
        <p className="text-xs text-gray-500 mb-2">
          Inject raw JSON data into this trigger.
        </p>
        <textarea
          value={formData.rawJson || "{\n  \n}"}
          onChange={(e) =>
            setFormData({ ...formData, rawJson: e.target.value })
          }
          className="w-full border border-gray-300 rounded-lg p-3 text-sm font-mono text-blue-600 focus:ring-2 focus:ring-blue-500 outline-none resize-none min-h-[120px] bg-gray-50"
        />
      </div>
    );
  };

  return (
    <div className="absolute inset-0 bg-black/40 z-50 flex items-center justify-center backdrop-blur-sm animate-in fade-in">
      <div className="bg-white w-[450px] rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95">
        {/* Header */}
        <div className="bg-gray-50 px-5 py-4 border-b flex justify-between items-center">
          <div className="flex items-center gap-2 text-gray-800 font-bold">
            <Play className="w-4 h-4 text-blue-600" />
            Execute Workflow
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-5">
          {/* Multi-Trigger Selector (Only shows if canvas has >1 trigger) */}
          {triggers.length > 1 && (
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Select Entry Point
              </label>
              <select
                value={selectedTriggerId}
                onChange={(e) => {
                  setSelectedTriggerId(e.target.value);
                  setFormData({}); // Reset form when switching triggers
                }}
                className="w-full border border-gray-300 rounded-md p-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {triggers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.data?.label || t.type} ({t.id.slice(-4)})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Dynamic Form Content */}
          {renderTriggerForm()}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-5 py-3 border-t flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
          >
            Execute
          </button>
        </div>
      </div>
    </div>
  );
}
