import { useState } from 'react'; // Removed useEffect
import { Feature } from '../services/api'; // Removed getFeatures
import { Layers, Package, Box } from 'lucide-react';

// Define props to accept data from Parent
interface SidebarProps {
  features: Feature[];
}

export default function Sidebar({ features }: SidebarProps) {
  // REMOVED: const [features, setFeatures] = useState...
  // REMOVED: useEffect(...)

  const [activeTab, setActiveTab] = useState<'core' | 'custom'>('core');

  // Filter features based on the ID prefix
  const coreFeatures = features.filter(f => !f.id.startsWith('user_defined.'));
  const customFeatures = features.filter(f => f.id.startsWith('user_defined.'));

  const onDragStart = (event: React.DragEvent, feature: any) => {
    event.dataTransfer.setData('application/reactflow', feature.id);
    event.dataTransfer.setData('featureName', feature.name);
    event.dataTransfer.setData('featureInputs', JSON.stringify(feature.inputs || [])); 
    event.dataTransfer.setData('featureOutputs', JSON.stringify(feature.outputs || []));
    event.dataTransfer.effectAllowed = 'move';
  };

  const renderList = (list: Feature[]) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {list.length === 0 && <p className="text-gray-400 text-xs p-2">No modules found.</p>}
      {list.map((feature, index) => (
        <div
          key={feature.id || index}
          onDragStart={(event) => onDragStart(event, feature)}
          draggable
          className="p-3 border border-gray-300 rounded-lg bg-white cursor-grab flex items-center gap-3 font-medium shadow-sm hover:border-purple-400 hover:shadow-md transition-all"
        >
          {activeTab === 'core' ? <Layers size={18} className="text-purple-600" /> : <Box size={18} className="text-indigo-600" />}
          <span className="text-gray-700 text-sm">{feature.name}</span>
        </div>
      ))}
    </div>
  );

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* HEADER & TABS */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h3 className="font-bold text-gray-800 mb-4">Modules</h3>
        <div className="flex p-1 bg-gray-100 rounded-lg">
            <button 
                onClick={() => setActiveTab('core')}
                className={`flex-1 py-1 text-xs font-semibold rounded-md transition-colors ${
                    activeTab === 'core' ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
            >
                Core
            </button>
            <button 
                onClick={() => setActiveTab('custom')}
                className={`flex-1 py-1 text-xs font-semibold rounded-md transition-colors ${
                    activeTab === 'custom' ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
            >
                Custom
            </button>
        </div>
      </div>

      {/* LIST */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'core' ? renderList(coreFeatures) : renderList(customFeatures)}
      </div>
    </aside>
  );
}