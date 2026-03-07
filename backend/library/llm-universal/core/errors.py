class LLMError(Exception):
    """Base class for all LLM errors."""
    def __init__(self, message: str, provider: str, retryable: bool = False):
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable

class AuthenticationError(LLMError):
    """Invalid API Key or Permissions."""
    def __init__(self, message: str, provider: str):
        super().__init__(f"AUTH ERROR [{provider}]: {message}", provider, retryable=False)

class RateLimitError(LLMError):
    """Quota exceeded or too many requests."""
    def __init__(self, message: str, provider: str):
        super().__init__(f"RATE LIMIT [{provider}]: {message}", provider, retryable=True)

class ContextWindowError(LLMError):
    """Prompt is too long for this model."""
    def __init__(self, message: str, provider: str):
        super().__init__(f"CONTEXT LENGTH [{provider}]: {message}", provider, retryable=False)

class ProviderUnavailableError(LLMError):
    """500 Errors or Connection Timeouts."""
    def __init__(self, message: str, provider: str):
        super().__init__(f"UNAVAILABLE [{provider}]: {message}", provider, retryable=True)