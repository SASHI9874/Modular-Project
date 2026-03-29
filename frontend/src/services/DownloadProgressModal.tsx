import React, { useState, useEffect } from "react";
import { X, Download, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "@/core/api/client";

interface ProgressStep {
  step: string;
  progress: number;
  message: string;
  download_id?: string;
  size_mb?: number;
}

interface DownloadProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  graphData: any;
}

export default function DownloadProgressModal({
  isOpen,
  onClose,
  projectId,
  projectName,
  graphData,
}: DownloadProgressModalProps) {
  const apiBaseUrl = apiClient.defaults.baseURL?.replace(/\/$/, "") || "";

  // --- STATE MANAGEMENT ---
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<
    "idle" | "downloading" | "complete" | "error"
  >("idle");
  const [downloadId, setDownloadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Trigger download on open
  useEffect(() => {
    if (isOpen && status === "idle") {
      startDownload();
    }
  }, [isOpen]);

  const startDownload = async () => {
    setStatus("downloading");
    setProgress(0);
    setError(null);

    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

      // Connect to SSE endpoint
      const response = await fetch(
        `${apiBaseUrl}/projects/${projectId}/download/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            graph: graphData,
            project_name: projectName,
          }),
        },
      );

      if (!response.ok) throw new Error("Failed to start download stream");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body from server");

      // --- SSE STREAM PARSING LOOP ---
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // Fix: Split by double newline to handle multiple events in one chunk
        const lines = chunk.split("\n");

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith("data: ")) continue;

          try {
            const data: ProgressStep = JSON.parse(trimmedLine.slice(6));
            handleProgressEvent(data);
          } catch (e) {
            console.error("Error parsing SSE line:", trimmedLine, e);
          }
        }
      }
    } catch (err: any) {
      console.error("Download error:", err);
      setStatus("error");
      setError(err.message || "Download failed");
    }
  };

  const handleProgressEvent = (event: ProgressStep) => {
    setProgress(event.progress);
    setCurrentStep(event.step);
    setMessage(event.message);

    // The backend must yield this step specifically to trigger the actual file pull
    if (event.step === "download_ready" && event.download_id) {
      setDownloadId(event.download_id);
      setStatus("complete");
      downloadZip(event.download_id);
    }

    if (event.step === "error") {
      setStatus("error");
      setError(event.message);
    }
  };

  const downloadZip = async (id: string) => {
    try {
      const link = document.createElement("a");
      link.href = `${apiBaseUrl}/projects/${projectId}/download/${id}`;
      link.download = `${projectName}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Give user time to see success before closing
      setTimeout(() => {
        onClose();
        resetState();
      }, 3000);
    } catch (err) {
      setError("Failed to download file");
    }
  };

  const resetState = () => {
    setProgress(0);
    setCurrentStep("");
    setMessage("");
    setStatus("idle");
    setDownloadId(null);
    setError(null);
  };

  const handleClose = () => {
    if (status === "downloading") {
      if (
        window.confirm("Download in progress. Are you sure you want to cancel?")
      ) {
        onClose();
        resetState();
      }
    } else {
      onClose();
      resetState();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 backdrop-blur-md bg-white/30 flex items-center justify-center z-[100]">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-8 border border-gray-100">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {status === "complete"
                ? "Success!"
                : status === "error"
                  ? "Build Failed"
                  : "Building App"}
            </h2>
            <p className="text-gray-500 text-sm mt-1">{projectName}</p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Progress Circle/Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-1 rounded">
              {currentStep.replace(/_/g, " ") || "Initializing"}
            </span>
            <span className="text-sm font-mono font-bold text-gray-700">
              {progress}%
            </span>
          </div>

          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                status === "error"
                  ? "bg-red-500"
                  : status === "complete"
                    ? "bg-green-500"
                    : "bg-blue-600"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Status Area */}
        <div className="mb-8 p-4 rounded-lg bg-gray-50 border border-gray-100">
          <div className="flex items-start space-x-3">
            {status === "downloading" && (
              <Loader2
                className="text-blue-500 animate-spin shrink-0"
                size={18}
              />
            )}
            {status === "complete" && (
              <CheckCircle className="text-green-500 shrink-0" size={18} />
            )}
            {status === "error" && (
              <AlertCircle className="text-red-500 shrink-0" size={18} />
            )}

            <p
              className={`text-sm leading-relaxed ${
                status === "error"
                  ? "text-red-600 font-medium"
                  : "text-gray-600"
              }`}
            >
              {error || message || "Starting generation engine..."}
            </p>
          </div>
        </div>

        {/* Detailed Steps Indicator */}
        <div className="space-y-3 mb-8 px-1">
          <StepItem
            step="validation"
            current={currentStep}
            label="Graph Validation"
          />
          <StepItem
            step="analysis"
            current={currentStep}
            label="Structural Analysis"
          />
          <StepItem
            step="backend"
            current={currentStep}
            label="Backend Compilation"
          />
          <StepItem
            step="frontend"
            current={currentStep}
            label="UI Orchestration"
          />
          <StepItem
            step="bundling"
            current={currentStep}
            label="ZIP Compression"
          />
        </div>

        {/* Footer Actions */}
        <div className="flex gap-3">
          {status === "error" && (
            <button
              onClick={startDownload}
              className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200"
            >
              Retry Build
            </button>
          )}

          {status === "complete" && (
            <button
              onClick={() => downloadId && downloadZip(downloadId)}
              className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-green-200"
            >
              <Download size={18} />
              Download ZIP
            </button>
          )}

          <button
            onClick={handleClose}
            className={`py-3 rounded-lg font-bold transition-all border ${
              status === "complete" || status === "error"
                ? "flex-1 border-gray-200 text-gray-600 hover:bg-gray-50"
                : "w-full border-gray-200 text-gray-400 hover:text-gray-600"
            }`}
          >
            {status === "complete" ? "Close" : "Cancel"}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- SUB-COMPONENTS ---

function StepItem({
  step,
  current,
  label,
}: {
  step: string;
  current: string;
  label: string;
}) {
  const steps = [
    "validation",
    "analysis",
    "dependencies",
    "backend",
    "frontend",
    "extension",
    "bundling",
    "complete",
  ];
  const currentIndex = steps.indexOf(current);
  const stepIndex = steps.indexOf(step);

  const isPast = currentIndex > stepIndex || current === "complete";
  const isActive = current === step;

  return (
    <div className="flex items-center justify-between group">
      <div className="flex items-center space-x-3">
        <div
          className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
            isPast
              ? "bg-green-500 scale-125"
              : isActive
                ? "bg-blue-500 animate-pulse scale-150"
                : "bg-gray-200"
          }`}
        />
        <span
          className={`text-xs font-medium transition-colors ${
            isPast
              ? "text-gray-400"
              : isActive
                ? "text-blue-600 font-bold"
                : "text-gray-300"
          }`}
        >
          {label}
        </span>
      </div>
      {isPast && <CheckCircle size={12} className="text-green-500" />}
    </div>
  );
}
