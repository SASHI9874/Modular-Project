from pydantic import BaseModel

class ExecutionPolicy(BaseModel):
    max_memory: str
    allow_network: bool
    max_cpu: float