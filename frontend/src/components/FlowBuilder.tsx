import { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls, 
  Connection, 
  Node, 
  useNodesState, 
  useEdgesState,
  ReactFlowInstance
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Download, Package, Play, AlertCircle, CheckCircle } from 'lucide-react';

// ✅ Import getFeatures to fetch data here
import { downloadWheel, downloadZip, api, getFeatures, Feature } from '../services/api'; 
import { useWorkflowExecution } from '../hooks/useWorkflowExecution'; 
import Sidebar from './Sidebar'; 
import FeatureNode from './FeatureNode'; 

const initialNodes: Node[] = [];

const nodeTypes = {
  featureNode: FeatureNode, // Register custom node component
};

export default function FlowBuilder() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  // --- 1. STATE FOR SIDEBAR DATA ---
  const [sidebarFeatures, setSidebarFeatures] = useState<Feature[]>([]);

  // --- 2. FETCH FUNCTION ---
  const loadFeatures = useCallback(() => {
     getFeatures().then(setSidebarFeatures).catch(console.error);
  }, []);

  // --- 3. LOAD ON MOUNT ---
  useEffect(() => {
     loadFeatures();
  }, [loadFeatures]);

  const { execution, startRun, resumeRun, setExecution } = useWorkflowExecution();
  
  const [userInput, setUserInput] = useState<string | File | null>(null);

  // --- SMART CONNECTION LOGIC ---
  const onConnect = useCallback((params: Connection) => {
    const sourceNode = nodes.find(n => n.id === params.source);
    const targetNode = nodes.find(n => n.id === params.target);
    
    if (!sourceNode || !targetNode) return;

    const outputDef = sourceNode.data.outputs?.find((o: any) => o.name === params.sourceHandle);
    const inputDef = targetNode.data.inputs?.find((i: any) => i.name === params.targetHandle);

    if (outputDef && inputDef) {
        if (outputDef.type !== inputDef.type && outputDef.type !== 'any' && inputDef.type !== 'any') {
            alert(`Type Mismatch! Cannot connect ${outputDef.type} to ${inputDef.type}`);
            return; 
        }
    }

    setEdges((eds) => addEdge(params, eds));
  }, [nodes, setEdges]); 

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      
      const type = event.dataTransfer.getData('application/reactflow');
      
      if (!type || type === "undefined") {
          return;
      }

      const rawInputs = event.dataTransfer.getData('featureInputs');
      const rawOutputs = event.dataTransfer.getData('featureOutputs');

      let inputs = [];
      let outputs = [];

      try {
        if (rawInputs && rawInputs !== "undefined") {
            inputs = JSON.parse(rawInputs);
        }
        if (rawOutputs && rawOutputs !== "undefined") {
            outputs = JSON.parse(rawOutputs);
        }
      } catch (e) {
        console.error("Failed to parse node metadata:", e);
      }

      let position = { x: 0, y: 0 };
      if (reactFlowInstance) {
        position = reactFlowInstance.screenToFlowPosition({
            x: event.clientX,
            y: event.clientY,
        });
      }

      const newNode: Node = {
        id: `${type}_${nodes.length}`,
        type: 'featureNode', 
        position,
        data: { 
            label: event.dataTransfer.getData('featureName'), 
            feature_id: type,
            inputs: inputs,   
            outputs: outputs  
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, nodes, setNodes]
  );
  
  const getFeaturesList = () => Array.from(new Set(nodes.map((node: any) => node.data.feature_id)));
  
  const handleDownloadWheel = async () => {
    const features = getFeaturesList();
    if (features.length === 0) return alert("Please drag some nodes first!");
    try { await downloadWheel(features); } catch (e) { console.error(e); alert("Download failed."); }
  };

  const handleDownloadZip = async () => {
      const features = getFeaturesList(); 
      if (features.length === 0) return alert("Please drag some nodes first!");
      try { await downloadZip(features); } catch (e) { console.error(e); alert("Zip Download Failed"); }
  };

  // --- 4. UPDATED SAVE HANDLER ---
  const handleSaveModule = async () => {
    const name = prompt("Enter a name for this module:");
    if (!name) return;

    const graph = { nodes, edges };
    const reqs = ["requests", "pandas"]; 

    const formData = new FormData();
    formData.append('name', name);
    formData.append('graph_json', JSON.stringify(graph));
    formData.append('reqs_json', JSON.stringify(reqs));

    try {
        await api.post('/builder/save-module', formData);
        alert("Saved successfully!");
        
        // ✅ REFRESH THE SIDEBAR LIST IMMEDIATELY
        loadFeatures();
        
    } catch (e) {
        alert("Failed to save module");
        console.error(e);
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 60px)', width: '100vw', overflow: 'hidden' }}>
      
      {/* --- 5. PASS DATA TO SIDEBAR --- */}
      {/* Make sure your Sidebar.tsx is updated to accept 'features' as a prop! */}
      <Sidebar features={sidebarFeatures} />
      
      <div className="reactflow-wrapper" ref={reactFlowWrapper} style={{ flexGrow: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <Background />
          <Controls />
        </ReactFlow>

        {/* --- TOP RIGHT BUTTONS --- */}
        <div style={{ position: 'absolute', top: 20, right: 20, display: 'flex', gap: '10px', zIndex: 10 }}>
          <button 
            onClick={startRun}
            disabled={execution.status === 'RUNNING'}
            className={`flex items-center gap-2 px-4 py-2 text-white rounded shadow transition-colors ${
                execution.status === 'RUNNING' ? 'bg-gray-400 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
            }`}
          >
             {execution.status === 'RUNNING' ? 'Running...' : <><Play size={18} /> Run Test</>}
          </button>

          <button onClick={handleDownloadWheel} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 shadow">
            <Package size={18} /> SDK
          </button>
          
          <button onClick={handleDownloadZip} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 shadow">
            <Download size={18} /> App
          </button>

          <button onClick={handleSaveModule} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 shadow">
            <Package size={18} /> Save Module
          </button>
        </div>

        {/* --- INPUT MODAL (Handles PAUSE state) --- */}
        {execution.status === 'PAUSED' && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-2xl border border-yellow-400 z-50 w-96">
            <div className="flex items-center gap-2 mb-4 text-yellow-600">
               <AlertCircle size={24} />
               <h3 className="font-bold text-lg">Input Required</h3>
            </div>
            
            <p className="text-sm text-gray-600 mb-4">
              Node <span className="font-mono bg-gray-100 px-1 rounded">{execution.pausedNodeId}</span> needs 
              <span className="font-bold"> {execution.requiredInput?.name}</span>
            </p>

            {execution.requiredInput?.type === 'file_upload' ? (
                <div className="mb-4">
                   <label className="block text-sm font-medium text-gray-700 mb-1">Upload File</label>
                   <input 
                     type="file" 
                     className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
                     onChange={(e) => {
                         if (e.target.files && e.target.files[0]) {
                            setUserInput(e.target.files[0]);
                         }
                     }}
                   />
                </div>
            ) : (
                <input 
                  type="text" 
                  className="w-full border p-2 rounded mb-4 focus:ring-2 focus:ring-purple-500 outline-none"
                  placeholder="Enter value..."
                  onChange={(e) => setUserInput(e.target.value)}
                />
            )}

            <div className="flex justify-end gap-2">
              <button 
                onClick={() => { resumeRun(null); setUserInput(null); }}
                className="text-gray-500 hover:text-gray-700 text-sm px-3"
              >
                Skip (Pass None)
              </button>
              <button 
                onClick={() => { resumeRun(userInput); setUserInput(null); }}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* --- SUCCESS / ERROR TOAST --- */}
        {execution.status === 'COMPLETED' && (
             <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded flex items-center gap-2 shadow-lg">
                <CheckCircle size={20} />
                <div>
                    <p className="font-bold">Execution Finished!</p>
                    <p className="text-xs">Check console for full output object.</p>
                </div>
                <button onClick={() => setExecution({ status: 'IDLE' })} className="ml-4 text-green-800 font-bold">✕</button>
             </div>
        )}
        
        {execution.status === 'ERROR' && (
             <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2 shadow-lg">
                <AlertCircle size={20} />
                <div>
                    <p className="font-bold">Execution Error</p>
                    <p className="text-xs">{execution.error}</p>
                </div>
                <button onClick={() => setExecution({ status: 'IDLE' })} className="ml-4 text-red-800 font-bold">✕</button>
             </div>
        )}

      </div>
    </div>
  );
}