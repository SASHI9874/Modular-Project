from typing import List
from openai import BaseModel
from .node import Node
from .edge import Edge

class DAG(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    def validate_structure(self):
        # TODO: Implement cycle detection
        pass