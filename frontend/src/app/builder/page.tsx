"use client";
import React, { useRef, useCallback, useState } from "react";
import ReactFlow, { ReactFlowProvider, useReactFlow } from "reactflow";
import FlowCanvas from "@/components/features/canvas/FlowCanvas";
import Sidebar from "@/components/features/sidebar/Sidebar";
import { useBuilderStore } from "@/core/store/useBuilderStore";
import { apiClient } from "@/core/api/client";
import { Play, Loader2, X, Code, Download } from "lucide-react";

// We need to wrap the logic in a component that has access to ReactFlow context
function BuilderContent() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project, toObject } = useReactFlow();
  const { addNode, setExecutionResults, executionResults } = useBuilderStore();
  const [isRunning, setIsRunning] = useState(false); // Loading state
  const [showCode, setShowCode] = useState(false);
  const [compiledCode, setCompiledCode] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  const handleSave = async () => {
    try {
      // 1. Extract the current graph state
      const graphData = toObject();

      // 2. Send to Backend
      const response = await apiClient.post("/projects/", {
        name: `Project ${new Date().toLocaleString()}`, // Auto-name for now
        graph: graphData,
      });

      alert(`Saved! Project ID: ${response.data.id}`);
      return response.data.id;
    } catch (e) {
      console.error(e);
      alert("Failed to save project");
      return null;
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    setExecutionResults(null); // Clear previous results

    // 1. Auto-save first (so backend has latest version)
    const projectId = await handleSave();

    if (projectId) {
      try {
        // 2. Trigger Run
        const { data } = await apiClient.post(`/projects/${projectId}/run`);
        setExecutionResults(data.results);
      } catch (e) {
        alert("Run failed");
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
      const { data } = await apiClient.get(`/projects/${projectId}/compile`);
      setCompiledCode(data);
      setShowCode(true);
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    const projectId = await handleSave(); // Auto-save first
    if (!projectId) {
      setIsDownloading(false);
      return;
    }

    try {
      // Request the file as a 'blob' (binary large object)
      const response = await apiClient.get(`/projects/${projectId}/download`, {
        responseType: "blob",
      });

      // Create a hidden link to trigger the browser download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `ai-app-${projectId}.zip`);
      document.body.appendChild(link);
      link.click();

      // Cleanup
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
          {/* Attach onClick handler */}
          <button
            type="button"
            onClick={handleSave}
            className="bg-black text-white px-4 py-2 rounded text-sm hover:bg-gray-800"
          >
            Save Flow
          </button>
          <button
            type="button"
            onClick={handleRun}
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
            className="text-gray-600 px-4 py-2 rounded border-1 text-sm hover:bg-gray-100 font-medium flex items-center gap-2"
          >
            <Code className="w-4 h-4" />
            View Code
          </button>
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="text-gray-600 px-4 py-2 rounded text-sm hover:bg-gray-100 font-medium flex items-center gap-2 disabled:opacity-50"
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
        {/* Sidebar */}
        <Sidebar />

        {/* Canvas Area */}
        <div
          className="flex-1 h-full relative bg-gray-100"
          ref={reactFlowWrapper}
        >
          {/* We pass drop handlers to the container DIV, not the Canvas component itself */}
          <div
            className="h-full w-full"
            onDragOver={onDragOver}
            onDrop={onDrop}
          >
            <FlowCanvas />
          </div>
        </div>
      </div>
      {/* RESULTS PANEL (Floating) */}
      {executionResults && (
        <div className="absolute bottom-4 right-4 w-96 bg-white border rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
          <div className="bg-gray-100 px-4 py-2 border-b flex justify-between items-center">
            <span className="font-bold text-sm text-gray-700">
              Execution Results
            </span>
            <button onClick={() => setExecutionResults(null)}>
              <X className="w-4 h-4 text-gray-500 hover:text-black" />
            </button>
          </div>
          <div className="p-4 max-h-96 overflow-y-auto bg-slate-900 text-slate-50 font-mono text-xs">
            <pre>{JSON.stringify(executionResults, null, 2)}</pre>
          </div>
        </div>
      )}
      {/* CODE PREVIEW MODAL */}
      {showCode && (
        <div className="absolute inset-0 bg-black/50 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="bg-gray-800 w-2/3 h-3/4 rounded-xl shadow-2xl flex flex-col overflow-hidden">
            <div className="bg-gray-100 px-4 py-3 border-b flex justify-between items-center">
              <span className="font-bold text-gray-700">
                Generated Python Code
              </span>
              <button onClick={() => setShowCode(false)}>
                <X className="w-5 h-5 text-gray-500 hover:text-red-500" />
              </button>

              <button
                onClick={() => {
                  /* handleRun logic */
                }}
                className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 flex items-center gap-2"
              >
                <Play className="w-4 h-4 fill-current" />
                Run Flow
              </button>
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

// Wrap everything in ReactFlowProvider so 'useReactFlow' works
export default function BuilderPage() {
  return (
    <ReactFlowProvider>
      <BuilderContent />
    </ReactFlowProvider>
  );
}
