from pydantic import BaseModel
from typing import List

class BuildRequest(BaseModel):
    features: List[str]