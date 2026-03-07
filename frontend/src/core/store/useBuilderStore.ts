import { create } from 'zustand';
import {
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Connection
} from 'reactflow';

type BuilderState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;
  addNode: (node: Node) => void;
  executionResults: any;
  setExecutionResults: (results: any) => void;
};

const determineConnectionType = (
  sourceNode: Node | undefined,
  targetNode: Node | undefined
): string => {
  if (!sourceNode || !targetNode) return 'data';

  const sourceType = sourceNode.data?.featureType;
  const targetType = targetNode.data?.featureType;

  // Agent → Tool = tool connection
  if (sourceType === 'agent' && targetType === 'tool') {
    return 'tool';
  }

  // Agent → Storage = memory connection
  if (sourceType === 'agent' && targetType === 'storage') {
    return 'memory';
  }

  // Everything else = data connection
  return 'data';
};

export const useBuilderStore = create<BuilderState>((set, get) => ({
  nodes: [],
  edges: [],
  onNodesChange: (changes) => set({
    nodes: applyNodeChanges(changes, get().nodes)
  }),
  onEdgesChange: (changes) => set({
    edges: applyEdgeChanges(changes, get().edges)
  }),
  onConnect: (connection) => {
    const { nodes } = get();
    const sourceNode = nodes.find((n) => n.id === connection.source);
    const targetNode = nodes.find((n) => n.id === connection.target);

    const connectionType = determineConnectionType(sourceNode, targetNode);

    const newEdge = {
      ...connection,
      type: connectionType,
      animated: true,
    };

    set({ edges: addEdge(newEdge, get().edges) });
  },
  executionResults: null,
  setExecutionResults: (results) => set({ executionResults: results }),
  addNode: (node) => set({
    nodes: [...get().nodes, node]
  }),
}));