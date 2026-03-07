from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Iterator, Any

class LLMMessage(Dict):
    """Standardized message format: {'role': 'user'|'system'|'assistant', 'content': '...'}"""
    role: str
    content: str

class LLMResponse:
    """Standardized response object to decouple from provider-specific JSON"""
    def __init__(self, content: str, token_usage: Optional[Dict[str, int]] = None, raw_response: Any = None):
        self.content = content
        self.token_usage = token_usage or {}
        self.raw_response = raw_response

class BaseLLMProvider(ABC):
    """
    The Contract. All providers (OpenAI, Azure, Gemini) MUST inherit from this.
    This ensures the 'Universal' promise is kept.
    """

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self):
        """
        Check if required keys (API_KEY, ENDPOINT) exist. 
        Raise ValueError if missing.
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """
        Synchronous chat.
        Args:
            messages: List of dicts [{'role': 'user', 'content': 'hi'}]
        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        Streaming chat.
        Returns:
            Generator yielding string chunks.
        """
        pass

    # Optional Capability Check
    def supports_embeddings(self) -> bool:
        return False