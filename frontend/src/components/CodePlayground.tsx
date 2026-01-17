import { useState, useEffect } from 'react';
import { Play, Loader2, AlertCircle, Terminal, Upload, Server } from 'lucide-react';
import { runWheelTest, getAvailableWheels } from '../services/api'; 

interface ExecutionResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  error?: string;
}

export default function CodePlayground() {
  const [mode, setMode] = useState<'standard' | 'wheel'>('standard');
  const [code, setCode] = useState<string>('import my_custom_ai_sdk\n\nprint("Testing SDK...")');
  
  // Wheel Test State
  const [wheelSource, setWheelSource] = useState<'upload' | 'server'>('server');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [serverWheels, setServerWheels] = useState<string[]>([]);
  const [selectedServerWheel, setSelectedServerWheel] = useState<string>('');

  // Execution State
  const [requirements, setRequirements] = useState<string>('');
  const [output, setOutput] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Load server wheels on mount
  useEffect(() => {
    getAvailableWheels().then(setServerWheels).catch(console.error);
  }, []);

  const handleRun = async () => {
    setLoading(true);
    setOutput(null);

    try {
      let data;
      if (mode === 'standard') {
         // ... Existing Standard Logic ...
         const reqList = requirements ? requirements.split(',').map(r => r.trim()).filter(r => r) : [];
         const response = await fetch('http://localhost:8000/test-runner/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, requirements: reqList })
         });
         data = await response.json();
      } else {
         // ... NEW Wheel Logic ...
         // Validation
         if (wheelSource === 'upload' && !uploadedFile) {
            alert("Please upload a .whl file first");
            setLoading(false); return;
         }
         if (wheelSource === 'server' && !selectedServerWheel) {
            alert("Please select a wheel from the server list");
            setLoading(false); return;
         }

         data = await runWheelTest(
            code, 
            wheelSource === 'upload' ? uploadedFile : null,
            wheelSource === 'server' ? selectedServerWheel : null
         );
      }
      setOutput(data);
    } catch (err) {
      setOutput({ stdout: "", stderr: "Connection Failed", exit_code: 1, error: String(err) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full w-full bg-slate-50 p-6 md:p-10 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header & Mode Switcher */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-800">Runner Playground</h2>
            <p className="text-slate-500">Test your generated SDKs immediately.</p>
          </div>

          <div className="flex bg-slate-200 p-1 rounded-lg">
             <button 
                onClick={() => setMode('standard')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${mode === 'standard' ? 'bg-white shadow text-slate-800' : 'text-slate-600'}`}
             >
                Standard Pip
             </button>
             <button 
                onClick={() => setMode('wheel')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${mode === 'wheel' ? 'bg-white shadow text-indigo-600' : 'text-slate-600'}`}
             >
                Test .whl File
             </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT: Config Panel */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Context-Aware Configuration Box */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm transition-all">
               {mode === 'standard' ? (
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Pip Requirements</label>
                    <input 
                      value={requirements} 
                      onChange={e => setRequirements(e.target.value)}
                      placeholder="numpy, pandas" 
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
               ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 mb-2">
                       <label className="flex items-center gap-2 cursor-pointer">
                          <input type="radio" checked={wheelSource === 'server'} onChange={() => setWheelSource('server')} />
                          <span className="text-sm font-medium">Use Server Build</span>
                       </label>
                       <label className="flex items-center gap-2 cursor-pointer">
                          <input type="radio" checked={wheelSource === 'upload'} onChange={() => setWheelSource('upload')} />
                          <span className="text-sm font-medium">Upload File</span>
                       </label>
                    </div>

                    {wheelSource === 'server' ? (
                       <div className="relative">
                          <Server className="absolute left-3 top-2.5 text-slate-400" size={18} />
                          <select 
                            className="w-full pl-10 pr-4 py-2 border rounded-lg appearance-none bg-white"
                            value={selectedServerWheel}
                            onChange={(e) => setSelectedServerWheel(e.target.value)}
                          >
                             <option value="">-- Select a generated wheel --</option>
                             {serverWheels.map(w => <option key={w} value={w}>{w}</option>)}
                          </select>
                       </div>
                    ) : (
                       <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 transition-colors cursor-pointer relative">
                          <input 
                            type="file" 
                            accept=".whl" 
                            className="absolute inset-0 opacity-0 cursor-pointer"
                            onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                          />
                          <div className="flex flex-col items-center gap-2 text-slate-500">
                             <Upload size={24} />
                             <span className="text-sm font-medium">
                                {uploadedFile ? uploadedFile.name : "Click to upload .whl file"}
                             </span>
                          </div>
                       </div>
                    )}
                  </div>
               )}
            </div>

            {/* Code Editor */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm h-[400px] flex flex-col">
               <div className="bg-slate-900 text-slate-300 px-4 py-2 text-xs font-mono flex justify-between">
                  <span>main.py</span>
                  <span className="text-slate-500">{mode === 'wheel' ? 'Environment: Sandbox + Wheel' : 'Environment: Standard Venv'}</span>
               </div>
               <textarea 
                  className="flex-1 w-full bg-slate-900 text-emerald-400 p-4 font-mono text-sm outline-none resize-none"
                  value={code}
                  onChange={e => setCode(e.target.value)}
                  spellCheck={false}
               />
            </div>
            
            <button
               onClick={handleRun}
               disabled={loading}
               className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold shadow-lg flex items-center justify-center gap-2 transition-all"
            >
               {loading ? <Loader2 className="animate-spin" /> : <Play size={20} />}
               {loading ? 'Running...' : 'Execute Code'}
            </button>

          </div>

          {/* RIGHT: Output Terminal */}
          <div className="h-full min-h-[500px] bg-black rounded-xl border border-slate-800 shadow-xl p-4 font-mono text-sm text-slate-300 overflow-y-auto whitespace-pre-wrap">
             <div className="flex items-center gap-2 text-slate-500 mb-4 pb-2 border-b border-slate-800">
                <Terminal size={16} /> <span>Output Console</span>
             </div>
             
             {loading && <span className="text-yellow-500 animate-pulse">Initializing Environment...</span>}
             
             {!loading && !output && <span className="text-slate-600 italic">Waiting for execution...</span>}

             {output && (
                <>
                   {output.stdout && <div className="text-green-400">{output.stdout}</div>}
                   {output.stderr && <div className="text-red-400 mt-4 border-t border-slate-800 pt-2">{output.stderr}</div>}
                   {output.error && <div className="text-red-500 font-bold bg-red-900/20 p-2 mt-2 rounded">System Error: {output.error}</div>}
                   <div className="mt-4 text-xs text-slate-600">Exit Code: {output.exit_code}</div>
                </>
             )}
          </div>

        </div>
      </div>
    </div>
  );
}