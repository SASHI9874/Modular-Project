import React, { useState } from "react";
import { Database, Save, Server, CheckCircle } from "lucide-react";
import { api } from "../../client/api";
import { useAppStore } from "../../store";

export default function VectorStoreWidget() {
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // --- STATE WIRING ---
  // Grab the text extracted by the PDF Loader from the Global Store
  const store = useAppStore();
  const rawText = (store as any)["pdfloader_file_text"] || "";

  const handleIndex = async () => {
    if (!rawText) {
      setStatus(" No text found. Please upload a PDF first.");
      return;
    }

    setLoading(true);
    setStatus("Chunking and embedding text into database...");

    try {
      // Call the generated API to process and save the text
      const res = await (api as any)["vector-store-chroma"].process({
        file_text: rawText,
      });
      setStatus(res.context); // Expecting: " Indexed X chunks successfully."
    } catch (err) {
      setStatus(" Failed to index data into ChromaDB.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full max-w-sm bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 p-4 border-b flex items-center gap-3">
        <div className="p-2 bg-green-100 rounded-lg">
          <Database className="w-5 h-5 text-green-600" />
        </div>
        <div>
          <h3 className="font-bold text-gray-800">Knowledge Base</h3>
          <p className="text-xs text-gray-500">Chroma Vector DB</p>
        </div>
      </div>

      {/* Body */}
      <div className="p-5 space-y-4">
        {/* Connection Status Indicator */}
        <div className="flex items-center justify-between text-sm p-3 bg-gray-50 rounded-lg border border-gray-100">
          <span className="text-gray-600 font-medium">Data Source:</span>
          {rawText ? (
            <span className="flex items-center gap-1 text-green-600 text-xs font-bold">
              <CheckCircle className="w-4 h-4" /> Text Available
            </span>
          ) : (
            <span className="text-gray-400 text-xs">Waiting for input...</span>
          )}
        </div>

        {/* Action Button */}
        <button
          onClick={handleIndex}
          disabled={loading || !rawText}
          className="w-full flex items-center justify-center gap-2 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Server className="w-5 h-5 animate-pulse" />
          ) : (
            <Save className="w-5 h-5" />
          )}
          {loading ? "Indexing Data..." : "Sync to Database"}
        </button>

        {/* Status Message Area */}
        {status && (
          <div className="text-xs text-center p-2 rounded bg-gray-50 text-gray-700 border border-gray-100">
            {status}
          </div>
        )}
      </div>
    </div>
  );
}
