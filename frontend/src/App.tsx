import { ReactFlowProvider } from 'reactflow';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layers, Terminal, Cpu } from 'lucide-react'; // Make sure you have lucide-react installed

import FlowBuilder from './components/FlowBuilder';
import CodePlayground from './components/CodePlayground';

// A sub-component for the Navigation Link to handle active states
function NavLink({ to, icon: Icon, label }: { to: string; icon: any; label: string }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'bg-indigo-600 text-white shadow-md'
          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <Icon size={18} />
      {label}
    </Link>
  );
}

function NavBar() {
  return (
    <nav className="h-16 bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 shrink-0 z-50 relative">
      <div className="flex items-center gap-3">
        <div className="bg-indigo-500 p-2 rounded-lg">
          <Cpu className="text-white" size={24} />
        </div>
        <span className="text-xl font-bold text-white tracking-tight">AI Platform</span>
      </div>

      <div className="flex items-center gap-4">
        <NavLink to="/" icon={Layers} label="Workflow Builder" />
        <NavLink to="/test" icon={Terminal} label="Online Tester" />
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <BrowserRouter>
        <div className="flex flex-col h-screen bg-slate-50 overflow-hidden">
          {/* 1. Global Navigation */}
          <NavBar />

          {/* 2. Content Area */}
          <div className="flex-1 overflow-hidden relative">
            <Routes>
              <Route path="/" element={<FlowBuilder />} />
              <Route path="/test" element={<CodePlayground />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </ReactFlowProvider>
  );
}