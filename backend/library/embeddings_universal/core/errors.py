class EmbeddingError(Exception):
    """Base error for embedding operations"""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message)
        self.provider = provider


class EmbeddingAuthError(EmbeddingError):
    """Invalid API key for embedding provider"""
    def __init__(self, message: str, provider: str):
        super().__init__(f"AUTH ERROR [{provider}]: {message}", provider)


class EmbeddingQuotaError(EmbeddingError):
    """Embedding quota exceeded"""
    def __init__(self, message: str, provider: str):
        super().__init__(f"QUOTA EXCEEDED [{provider}]: {message}", provider)


class EmbeddingConfigError(EmbeddingError):
    """Missing or invalid configuration"""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(f"CONFIG ERROR [{provider}]: {message}", provider)