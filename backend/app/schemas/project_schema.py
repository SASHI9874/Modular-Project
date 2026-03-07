from typing import Any, Dict, Optional
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    graph: Dict[str, Any] # Holds { nodes: [...], edges: [...] }

class RunPayload(BaseModel):
    entry_node_id: Optional[str] = None
    inputs: Dict[str, Any] = {}