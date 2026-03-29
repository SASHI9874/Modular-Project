import os

# Define the root directory (assuming script is run inside ai-builder-frontend)
ROOT_DIR = "."

files = {
    # --- API Client ---
    "src/core/api/client.ts": """
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-attach JWT if it exists
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
""",
    
    # --- Store (Zustand) ---
    "src/core/store/useBuilderStore.ts": """
import { create } from 'zustand';
import { Node, Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges, addEdge, Connection } from 'reactflow';

type BuilderState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;
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
  onConnect: (connection) => set({ 
    edges: addEdge(connection, get().edges) 
  }),
}));
""",

    # --- Components: Canvas ---
    "src/components/features/canvas/FlowCanvas.tsx": """
'use client';
import React from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { useBuilderStore } from '@/core/store/useBuilderStore';

export default function FlowCanvas() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect } = useBuilderStore();

  return (
    <div className="h-full w-full bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
""",
    
    # --- Page: Builder ---
    "src/app/builder/page.tsx": """
import FlowCanvas from '@/components/features/canvas/FlowCanvas';

export default function BuilderPage() {
  return (
    <div className="h-screen w-screen flex flex-col">
      <header className="h-14 border-b flex items-center px-4 bg-white z-10">
        <h1 className="font-bold text-lg">AI Builder</h1>
        <div className="ml-auto">
          <button className="bg-black text-white px-4 py-2 rounded text-sm">Save Flow</button>
        </div>
      </header>
      <div className="flex-1 relative">
        <FlowCanvas />
      </div>
    </div>
  );
}
""",

    # --- Auth Page ---
    "src/app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { apiClient } from '@/core/api/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append('username', email); // FastAPI OAuth2 expects 'username'
      formData.append('password', password);
      
      const { data } = await apiClient.post('/auth/login', formData);
      localStorage.setItem('token', data.access_token);
      router.push('/builder');
    } catch (e) {
      alert('Login failed');
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="p-8 bg-white rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Login</h1>
        <input 
          className="w-full border p-2 mb-2 rounded" 
          placeholder="Email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)}
        />
        <input 
          className="w-full border p-2 mb-4 rounded" 
          placeholder="Password" 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)}
        />
        <button 
          onClick={handleLogin}
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
        >
          Sign In
        </button>
      </div>
    </div>
  );
}
"""
}

def create_structure():
    for file_path, content in files.items():
        dir_name = os.path.dirname(file_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
    print(" Frontend structure created!")

if __name__ == "__main__":
    create_structure()