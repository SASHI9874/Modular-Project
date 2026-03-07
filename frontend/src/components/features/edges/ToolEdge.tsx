import React from "react";
import { EdgeProps, getBezierPath, BaseEdge } from "reactflow";

export const ToolEdge = ({
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
        stroke: "#8b5cf6",
        strokeWidth: 2,
        strokeDasharray: "5,5",
        ...style,
      }}
    />
  );
};
