from pydantic import BaseModel, Field
from typing import Dict, Any

class Node(BaseModel):
    id: str
    type: str  # e.g., "feature_node"
    data: Dict[str, Any] = Field(default_factory=dict)