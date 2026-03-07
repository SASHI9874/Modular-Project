from typing import Dict, Any
from ..core.service import extract_text_from_bytes

def run(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runtime Adapter for the Visual Builder.
    
    In 'Simulation Mode', we often don't have a real file upload from the UI yet.
    We return a mock response or process a debug file if provided.
    """
    print(f"--- [Runtime] Executing PDF Loader ---")
    
    # Simulation Logic: Return dummy data so the user can test the FLOW
    # In a real polishment, you'd allow uploading a test file in the Node Config panel.
    return {
        "file_text": "SIMULATION MODE: This is sample text extracted from a dummy PDF. In the generated app, this will be real extracted text.",
        "filename": "simulation_sample.pdf"
    }