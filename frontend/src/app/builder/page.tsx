"use client";
import React, { useRef, useCallback, useState } from "react";
import ReactFlow, { ReactFlowProvider, useReactFlow } from "reactflow";
import FlowCanvas from "@/components/features/canvas/FlowCanvas";
import Sidebar from "@/components/features/sidebar/Sidebar";
import RunWorkflowModal from "@/app/builder/RunWorkflowModal";
import { useBuilderStore } from "@/core/store/useBuilderStore";
import ExecutionResultsPanel from "@/components/features/canvas/ExecutionResultsPanel";
import { apiClient } from "@/core/api/client";
import { Play, Loader2, X, Code, Download } from "lucide-react";

function BuilderContent() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project, toObject, getNodes } = useReactFlow();
  const { addNode, setExecutionResults, executionResults } = useBuilderStore();

  const [isRunning, setIsRunning] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const [compiledCode, setCompiledCode] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  // Modal State
  const [showRunModal, setShowRunModal] = useState(false);

  const handleSave = async () => {
    try {
      const graphData = toObject();
      const response = await apiClient.post("/projects/", {
        name: `Project ${new Date().toLocaleString()}`,
        graph: graphData,
      });
      console.log(`Saved! Project ID: ${response.data.id}`);
      return response.data.id;
    } catch (e) {
      console.error(e);
      alert("Failed to save project");
      return null;
    }
  };

  // UPDATED: handleRun now accepts the dynamic payload from the modal
  const handleRun = async (runConfig: {
    entry_node_id?: string;
    payload: Record<string, any>;
  }) => {
    setIsRunning(true);
    setShowRunModal(false); // Close the modal
    setShowCode(false); // Close code preview if it was open
    setExecutionResults(null); // Clear previous results

    // Auto-save first
    const projectId = await handleSave();

    if (projectId) {
      try {
        // Pass the highly specific trigger ID and payload to the backend
        const { data } = await apiClient.post(`/projects/${projectId}/run`, {
          entry_node_id: runConfig.entry_node_id,
          inputs: runConfig.payload,
        });
        setExecutionResults(data);
      } catch (e) {
        console.error(e);
        alert("Run failed. Check backend logs.");
      }
    }
    setIsRunning(false);
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData("application/reactflow/type");
      const label = event.dataTransfer.getData("application/reactflow/label");
      const configStr = event.dataTransfer.getData(
        "application/reactflow/config",
      );

      if (!type || !configStr) return;

      const config = JSON.parse(configStr);
      const position = project({
        x:
          event.clientX -
          (reactFlowWrapper.current?.getBoundingClientRect().left || 0),
        y:
          event.clientY -
          (reactFlowWrapper.current?.getBoundingClientRect().top || 0),
      });

      addNode({
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: { label, ...config },
      });
    },
    [project, addNode],
  );

  const handleCompile = async () => {
    const projectId = await handleSave();
    if (projectId) {
      try {
        const { data } = await apiClient.get(`/projects/${projectId}/compile`);
        setCompiledCode(data);
        setShowCode(true);
      } catch (e) {
        console.error("Compilation failed", e);
        alert("Failed to compile code.");
      }
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    const projectId = await handleSave();
    if (!projectId) {
      setIsDownloading(false);
      return;
    }

    try {
      const response = await apiClient.get(`/projects/${projectId}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `ai-app-${projectId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("Download failed. Check backend logs.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-blue-900">
      {/* Header */}
      <header className="h-14 border-b flex items-center px-4 bg-gray-200 z-10 shrink-0">
        <h1 className="font-bold text-lg text-gray-900">AI Builder</h1>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            onClick={handleSave}
            className="bg-black text-white px-4 py-2 rounded text-sm hover:bg-gray-800 transition-colors"
          >
            Save Flow
          </button>

          {/* Main Run Button opens the Modal */}
          <button
            type="button"
            onClick={() => setShowRunModal(true)}
            disabled={isRunning}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 transition-colors"
          >
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            Run Flow
          </button>

          <button
            type="button"
            onClick={handleCompile}
            className="text-gray-600 px-4 py-2 rounded border border-gray-300 text-sm hover:bg-gray-100 font-medium flex items-center gap-2 transition-colors"
          >
            <Code className="w-4 h-4" />
            View Code
          </button>
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="text-gray-600 px-4 py-2 rounded border border-gray-300 text-sm hover:bg-gray-100 font-medium flex items-center gap-2 disabled:opacity-50 transition-colors"
          >
            {isDownloading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Download App
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div
          className="flex-1 h-full relative bg-gray-100"
          ref={reactFlowWrapper}
        >
          <div
            className="h-full w-full"
            onDragOver={onDragOver}
            onDrop={onDrop}
          >
            <FlowCanvas />
          </div>
        </div>
      </div>

      {/* NEW DYNAMIC RUN MODAL */}
      <RunWorkflowModal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        onRun={handleRun}
        nodes={getNodes()} // Pass canvas nodes so the modal can introspect triggers
      />

      {/* RESULTS PANEL */}
      <ExecutionResultsPanel
        results={executionResults}
        onClose={() => setExecutionResults(null)}
      />

      {/* CODE PREVIEW MODAL */}
      {showCode && (
        <div className="absolute inset-0 bg-black/50 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="bg-gray-800 w-2/3 h-3/4 rounded-xl shadow-2xl flex flex-col overflow-hidden">
            <div className="bg-gray-100 px-4 py-3 border-b flex justify-between items-center">
              <span className="font-bold text-gray-700">
                Generated Python Code
              </span>

              <div className="flex gap-4 items-center">
                {/* This button also opens the Run Modal! */}
                <button
                  onClick={() => setShowRunModal(true)}
                  className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 flex items-center gap-2 transition-colors"
                >
                  <Play className="w-4 h-4 fill-current" />
                  Run Flow
                </button>
                <button onClick={() => setShowCode(false)}>
                  <X className="w-5 h-5 text-gray-500 hover:text-red-500 transition-colors" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto bg-[#1e1e1e] p-4">
              <pre className="text-sm font-mono text-green-400">
                {compiledCode}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function BuilderPage() {
  return (
    <ReactFlowProvider>
      <BuilderContent />
    </ReactFlowProvider>
  );
}
