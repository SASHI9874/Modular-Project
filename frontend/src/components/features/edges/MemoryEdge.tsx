import React from "react";
import { EdgeProps, getBezierPath, BaseEdge } from "reactflow";

export const MemoryEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
}: EdgeProps) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      markerEnd={markerEnd}
      style={{
        stroke: "#10b981",
        strokeWidth: 2,
        strokeDasharray: "2,4",
        ...style,
      }}
    />
  );
};
