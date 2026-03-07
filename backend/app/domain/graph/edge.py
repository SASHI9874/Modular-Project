from pydantic import BaseModel

class Edge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str
    type: str = "data"  # Default to "data" for backward compatibility

    @validator('type')
    def validate_connection_type(cls, v):
        valid_types = ['data', 'tool', 'memory', 'conditional']
        if v not in valid_types:
            raise ValueError(f'Invalid connection type: {v}')
        return v