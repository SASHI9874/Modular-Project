from enum import Enum

class FeatureTrustLevel(str, Enum):
    SYSTEM = "system"       # Built-in, audited, full network access
    VERIFIED = "verified"   # Partner code, limited network
    USER = "user"           # Arbitrary code, NO network