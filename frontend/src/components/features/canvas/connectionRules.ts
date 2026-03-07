import { Connection, Node, Edge } from 'reactflow';

export const isValidConnection = (
    connection: Connection,
    nodes: Node[],
    edges: Edge[]
): boolean => {
    // Rule 1: Can't connect to self
    if (connection.source === connection.target) {
        return false;
    }

    // Rule 2: Check if connection already exists
    const exists = edges.some(
        (e) =>
            e.source === connection.source &&
            e.target === connection.target &&
            e.sourceHandle === connection.sourceHandle &&
            e.targetHandle === connection.targetHandle
    );
    if (exists) {
        return false;
    }

    // Rule 3: Get node types
    const sourceNode = nodes.find((n) => n.id === connection.source);
    const targetNode = nodes.find((n) => n.id === connection.target);

    if (!sourceNode || !targetNode) {
        return false;
    }

    // Rule 4: Type-specific validation
    const sourceType = sourceNode.data?.featureType;
    const targetType = targetNode.data?.featureType;

    // Tool connections: Only Agent → Tool
    if (sourceType === 'agent' && targetType === 'tool') {
        return true;
    }

    // Memory connections: Only Agent → Storage
    if (sourceType === 'agent' && targetType === 'storage') {
        return true;
    }

    // Trigger connections: Trigger → Any (except Trigger)
    if (sourceType === 'trigger' && targetType !== 'trigger') {
        return true;
    }

    // Data connections: All other combinations allowed
    return true;
};