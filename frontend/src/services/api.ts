// frontend/src/services/api.ts
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// 1. Create and Export a configured instance
// This allows hooks to use 'api.post' or 'api.get' cleanly
export const api = axios.create({
  baseURL: API_URL,
});

export interface Feature {
    id: string;
    name: string;
    description: string;
    inputs: { name: string, type: string }[];
}

// --- EXISTING FUNCTIONS (Unchanged) ---

export const getFeatures = async () => {
    const response = await api.get<Feature[]>(`/features`);
    return response.data;
};

export const downloadWheel = async (features: string[]) => {
    const response = await api.post(`/download/wheel`, 
        { features }, 
        { responseType: 'blob' }
    );
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'my_custom_ai_sdk.whl');
    document.body.appendChild(link);
    link.click();
    link.remove();
};

export const downloadZip = async (features: string[]) => {
    const response = await api.post(`/download/zip`, 
        { features }, 
        { responseType: 'blob' }
    );
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'my_ai_app.zip');
    document.body.appendChild(link);
    link.click();
    link.remove();
};

export const getAvailableWheels = async () => {
  const response = await api.get<string[]>(`/wheels`); 
  return response.data;
};

export const runWheelTest = async (
  code: string, 
  file: File | null, 
  existingWheel: string | null
) => {
  const formData = new FormData();
  formData.append('code', code);
  
  if (file) {
    formData.append('file', file);
  } else if (existingWheel) {
    formData.append('existing_wheel', existingWheel);
  }

  const response = await api.post(`/test-runner/run-wheel`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  
  return response.data;
};

// --- NEW: INTERACTIVE WORKFLOW ENDPOINTS ---

export const runWorkflow = async (graph: any, requirements: string[]) => {
    const response = await api.post(`/workflow/run`, { graph, requirements });
    return response.data;
};

export const resumeWorkflow = async (sessionId: string, nodeId: string, inputData: any) => {
    
    // Check if inputData is a File or Blob (Binary)
    if (inputData instanceof File || inputData instanceof Blob) {
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('node_id', nodeId);
        // 'file_input' key matches the FastAPI function argument
        formData.append('file_input', inputData); 
        
        // Send as Multipart (Bytes)
        const response = await api.post(`/workflow/resume`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    } 
    
    // Otherwise, treat as standard Form Text
    else {
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('node_id', nodeId);
        
        // Ensure null/undefined doesn't break FormData
        if (inputData !== null && inputData !== undefined) {
             formData.append('text_input', String(inputData));
        }

        const response = await api.post(`/workflow/resume`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    }
};

// HELPER: You will need this for file inputs!
// We can't send a raw "File" object to the Python script JSON input.
// We must upload it first, get a path string, and send that string.
export const uploadTempFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // You likely need to create this endpoint in your backend later
    // For now, this is a placeholder or you can use your existing test-runner upload logic
    const response = await api.post(`/api/workflow/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.file_path; // The server returns "/tmp/uploads/file.pdf"
};