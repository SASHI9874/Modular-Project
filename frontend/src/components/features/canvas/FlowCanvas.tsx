"use client";
import React, { useMemo } from "react";
import ReactFlow, { Background, Controls, ConnectionLineType } from "reactflow";
import "reactflow/dist/style.css";
import { useBuilderStore } from "@/core/store/useBuilderStore";
import FeatureNode from "./nodes/FeatureNode";
import AgentNode from "./nodes/AgentNode";
import ToolNode from "./nodes/ToolNode";
import TriggerNode from "./nodes/TriggerNode";
import { DataEdge, ToolEdge, MemoryEdge } from "../edges";
import { isValidConnection } from "./connectionRules";

export default function FlowCanvas() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect } =
    useBuilderStore();

  const nodeTypes = useMemo(
    () => ({
      featureNode: FeatureNode,
      agentNode: AgentNode,
      toolNode: ToolNode,
      triggerNode: TriggerNode,
    }),
    [],
  );

  const edgeTypes = useMemo(
    () => ({
      data: DataEdge,
      tool: ToolEdge,
      memory: MemoryEdge,
    }),
    [],
  );

  const defaultEdgeOptions = {
    type: "data",
    animated: true,
    style: {
      stroke: "#2563eb",
      strokeWidth: 2,
    },
  };

  return (
    <div className="h-full w-full bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionLineType={ConnectionLineType.SmoothStep}
        connectionLineStyle={{ stroke: "#2563eb", strokeWidth: 2 }}
        isValidConnection={(connection) =>
          isValidConnection(connection, nodes, edges)
        }
        fitView
      >
        <Background gap={16} size={1} color="#cbd5e1" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
