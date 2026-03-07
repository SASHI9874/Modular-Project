import React, { useEffect, useState } from "react";
import {
  FileText,
  Box,
  Database,
  Terminal,
  Cpu,
  MessageSquare,
  Binary,
  Layers,
  Loader2,
  AlertCircle,
  Brain,
  Calculator,
  Wrench,
} from "lucide-react";
import { apiClient } from "@/core/api/client";

// --- Icon Mapper ---
const IconMap: Record<string, React.ElementType> = {
  "file-text": FileText,
  "gpt-4": Box,
  "vector-db": Database,
  terminal: Terminal,
  cpu: Cpu,
  "message-square": MessageSquare,
  "message-circle": MessageSquare,
  binary: Binary,
  database: Database,
  box: Box,
  layers: Layers,
  brain: Brain,
  calculator: Calculator,
  wrench: Wrench,
};

interface FeatureManifest {
  key: string;
  name: string;
  description: string;
  classification: {
    capability: string;
  };
  contract: {
    inputs: Record<string, any>;
    outputs: Record<string, any>;
  };
  ui: {
    icon: string;
    color: string;
    label?: string;
    category?: string;
  };
}

export default function Sidebar() {
  const [features, setFeatures] = useState<FeatureManifest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        const res = await apiClient.get<FeatureManifest[]>("/features/");
        setFeatures(res.data);
      } catch (err) {
        console.error("Failed to load library:", err);
        setError("Failed to load library");
      } finally {
        setLoading(false);
      }
    };

    fetchFeatures();
  }, []);

  const onDragStart = (event: React.DragEvent, feature: FeatureManifest) => {
    // Determine node type based on capability
    let nodeType = "featureNode";

    if (feature.classification.capability === "agent") {
      nodeType = "agentNode";
    } else if (feature.classification.capability === "tool") {
      nodeType = "toolNode";
    } else if (feature.classification.capability === "trigger") {
      nodeType = "triggerNode";
    }

    event.dataTransfer.setData("application/reactflow/type", nodeType);

    const label = feature.ui.label || feature.name;
    event.dataTransfer.setData("application/reactflow/label", label);

    const config = {
      inputs: Object.keys(feature.contract.inputs),
      outputs: Object.keys(feature.contract.outputs),
      icon: feature.key,
      featureKey: feature.key,
      featureType: feature.classification.capability,
      color: feature.ui.color,
      description: feature.description,
    };

    event.dataTransfer.setData(
      "application/reactflow/config",
      JSON.stringify(config),
    );
    event.dataTransfer.effectAllowed = "move";
  };

  if (loading)
    return (
      <aside className="w-64 bg-white border-r h-full flex flex-col items-center justify-center text-gray-400 gap-2">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="text-xs">Loading Library...</span>
      </aside>
    );

  // Group features by category
  const groupedFeatures = features.reduce(
    (acc, feature) => {
      const category = feature.ui.category || "General";
      if (!acc[category]) acc[category] = [];
      acc[category].push(feature);
      return acc;
    },
    {} as Record<string, FeatureManifest[]>,
  );

  return (
    <aside className="w-64 bg-white border-r h-full flex flex-col shadow-xl z-20">
      <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
        <h2 className="font-bold text-xs text-gray-500 uppercase tracking-wider">
          Feature Library
        </h2>
        <span className="text-[10px] bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
          {features.length} Nodes
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="p-3 bg-red-50 text-red-600 text-xs rounded border border-red-100 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Render by category */}
        {Object.entries(groupedFeatures).map(([category, categoryFeatures]) => (
          <div key={category}>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              {category}
            </h3>
            <div className="space-y-2">
              {categoryFeatures.map((feature) => {
                const IconComponent = IconMap[feature.ui.icon] || Box;

                return (
                  <div
                    key={feature.key}
                    className="group p-3 bg-white border border-gray-200 rounded-lg shadow-sm cursor-grab transition-all flex items-center gap-3 hover:shadow-md hover:border-gray-300"
                    onDragStart={(e) => onDragStart(e, feature)}
                    draggable
                  >
                    <div
                      className="w-8 h-8 rounded-md flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${feature.ui.color}20` }}
                    >
                      <IconComponent
                        className="w-5 h-5"
                        style={{ color: feature.ui.color }}
                      />
                    </div>

                    <div className="overflow-hidden flex-1">
                      <div className="text-sm font-bold text-gray-700 truncate">
                        {feature.ui.label || feature.name}
                      </div>
                      <div
                        className="text-[10px] text-gray-400 truncate"
                        title={feature.description}
                      >
                        {feature.description}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {features.length === 0 && !error && (
          <div className="text-center text-gray-400 text-xs mt-10">
            No features found in Library.
          </div>
        )}
      </div>
    </aside>
  );
}
