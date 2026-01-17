import { useState } from 'react';
import { useReactFlow, Node } from 'reactflow';
import { api, resumeWorkflow } from '../services/api';

interface ExecutionState {
  status: 'IDLE' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'ERROR';
  sessionId?: string;
  pausedNodeId?: string;
  requiredInput?: { name: string; type: string; label?: string };
  results?: Record<string, any>;
  error?: string;
}

export const useWorkflowExecution = () => {
  const [execution, setExecution] = useState<ExecutionState>({ status: 'IDLE' });
  const { getNodes, getEdges } = useReactFlow();

  // 1. Start the Run
  const startRun = async () => {
    setExecution({ status: 'RUNNING' });
    
    // Convert React Flow nodes to your Backend JSON format
    const graphPayload = {
      nodes: getNodes(),
      edges: getEdges()
    };
    
    // Gather Requirements (You might have a helper for this)
    const requirements = ["requests", "pandas"]; 

    try {
      const { data } = await api.post('/workflow/run', {
        graph: graphPayload,
        requirements: requirements
      });
      handleResponse(data);
    } catch (err: any) {
      setExecution({ status: 'ERROR', error: err.message });
    }
  };

  // 2. Resume after User Input
  const resumeRun = async (inputValue: any) => {
    if (!execution.sessionId || !execution.pausedNodeId) return;

    setExecution(prev => ({ ...prev, status: 'RUNNING' }));

    try {
      // CLEANER: Just pass the inputValue (whether File or Text).
      // The API layer handles the conversion to Blob/Bytes.
      const data = await resumeWorkflow(
        execution.sessionId, 
        execution.pausedNodeId, 
        inputValue
      );
      
      handleResponse(data);
    } catch (err: any) {
      setExecution({ status: 'ERROR', error: err.message });
    }
  };

  // 3. Central Response Handler
  const handleResponse = (data: any) => {
    if (data.status === 'COMPLETED') {
      setExecution({ 
        status: 'COMPLETED', 
        results: data.results 
      });
      alert("Workflow Finished Successfully!");
    } 
    else if (data.status === 'PAUSED') {
      setExecution({
        status: 'PAUSED',
        sessionId: data.session_id,
        pausedNodeId: data.node_id,
        requiredInput: data.required_input
      });
      
      // OPTIONAL: Auto-focus the node in the view
      // fitView({ nodes: [{ id: data.node_id }] });
    } 
    else if (data.status === 'ERROR') {
      setExecution({ status: 'ERROR', error: data.message });
    }
  };

  return { execution, startRun, resumeRun };
};