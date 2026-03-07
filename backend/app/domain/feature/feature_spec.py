from pydantic import BaseModel
from .trust_level import FeatureTrustLevel

class FeatureSpec(BaseModel):
    name: str
    trust_level: FeatureTrustLevel
    inputs: dict
    outputs: dict