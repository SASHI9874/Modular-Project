from pydantic import BaseModel
from typing import Dict

class ProjectManifest(BaseModel):
    compiler_version: str = "1.0.0"
    # Maps Feature_ID -> Exact_Version_String (e.g., "pdf-loader" -> "1.2.0")
    feature_pins: Dict[str, str] = {}