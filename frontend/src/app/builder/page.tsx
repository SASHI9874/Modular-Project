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
import DownloadProgressModal from "@/services/DownloadProgressModal";

function BuilderContent() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project, toObject, getNodes } = useReactFlow();
  const { addNode, setExecutionResults, executionResults } = useBuilderStore();

  // --- UI STATE ---
  const [isRunning, setIsRunning] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const [compiledCode, setCompiledCode] = useState("");
  const [isDownloading, setIsDownloading] = useState(false); // Used for legacy download button
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [savedProjectId, setSavedProjectId] = useState<string | null>(null);

  // Modal State
  const [showRunModal, setShowRunModal] = useState(false);

  // --- HANDLERS ---

  /**
   * Saves the current flow to the backend.
   * Updates savedProjectId so other modals can reference the most recent version.
   */
  const handleSave = async () => {
    try {
      const graphData = toObject();
      const response = await apiClient.post("/projects/", {
        name: `Project ${new Date().toLocaleString()}`,
        graph: graphData,
      });

      const newId = response.data.id.toString();
      console.log(`Saved! Project ID: ${newId}`);

      // Update state so the rest of the app knows the current Project ID
      setSavedProjectId(newId);
      return newId;
    } catch (e) {
      console.error(e);
      alert("Failed to save project");
      return null;
    }
  };

  /**
   * Triggers the Streaming Download Modal
   */
  const handleDownloadWithProgress = async () => {
    // 1. Ensure project is saved first to get a valid ID
    const projectId = await handleSave();

    if (projectId) {
      // 2. Open the modal (The modal handles the SSE connection)
      setShowDownloadModal(true);
    }
  };

  const handleRun = async (runConfig: {
    entry_node_id?: string;
    payload: Record<string, any>;
  }) => {
    setIsRunning(true);
    setShowRunModal(false);
    setShowCode(false);
    setExecutionResults(null);

    const projectId = await handleSave();

    if (projectId) {
      try {
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

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-900">
      {/* Header */}
      <header className="h-14 border-b flex items-center px-6 bg-white z-10 shrink-0 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Code className="text-white w-5 h-5" />
          </div>
          <h1 className="font-bold text-lg text-gray-900 tracking-tight">
            AI Builder
          </h1>
        </div>

        <div className="ml-auto flex gap-3">
          <button
            type="button"
            onClick={handleSave}
            className="bg-gray-100 text-gray-700 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-gray-200 transition-all"
          >
            Save Flow
          </button>

          <button
            type="button"
            onClick={() => setShowRunModal(true)}
            disabled={isRunning}
            className="bg-blue-600 text-white font-semibold px-4 py-2 rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 transition-all shadow-md shadow-blue-100"
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
            className="text-gray-600 px-4 py-2 rounded-lg border border-gray-200 text-sm hover:bg-gray-50 font-semibold flex items-center gap-2 transition-all"
          >
            <Code className="w-4 h-4" />
            View Code
          </button>

          <button
            type="button"
            onClick={handleDownloadWithProgress}
            className="px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg text-sm hover:bg-emerald-700 flex items-center gap-2 transition-all shadow-md shadow-emerald-100"
          >
            <Download className="w-4 h-4" />
            Download App
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div
          className="flex-1 h-full relative bg-gray-50"
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

      {/* --- MODALS & OVERLAYS --- */}

      {/* RUN CONFIG MODAL */}
      <RunWorkflowModal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        onRun={handleRun}
        nodes={getNodes()}
      />

      {/* EXECUTION RESULTS PANEL */}
      <ExecutionResultsPanel
        results={executionResults}
        onClose={() => setExecutionResults(null)}
      />

      {/* STREAMING DOWNLOAD MODAL */}
      {showDownloadModal && savedProjectId && (
        <DownloadProgressModal
          isOpen={showDownloadModal}
          onClose={() => setShowDownloadModal(false)}
          projectId={savedProjectId}
          projectName={`AI-App-${savedProjectId}`}
          graphData={toObject()}
        />
      )}

      {/* CODE PREVIEW MODAL */}
      {showCode && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center backdrop-blur-sm p-10">
          <div className="bg-gray-900 w-full max-w-5xl h-full rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-700">
            <div className="bg-gray-800 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
              <span className="font-bold text-gray-200 flex items-center gap-2">
                <Code className="w-4 h-4 text-blue-400" />
                Generated Python Source
              </span>

              <div className="flex gap-4 items-center">
                <button
                  onClick={() => setShowRunModal(true)}
                  className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-bold hover:bg-blue-700 flex items-center gap-2 transition-colors"
                >
                  <Play className="w-4 h-4 fill-current" />
                  Run Now
                </button>
                <button
                  onClick={() => setShowCode(false)}
                  className="p-1 hover:bg-gray-700 rounded-full transition-colors"
                >
                  <X className="w-6 h-6 text-gray-400 hover:text-white" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto bg-[#1e1e1e] p-6 font-mono text-sm leading-relaxed">
              <pre className="text-emerald-400">{compiledCode}</pre>
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
