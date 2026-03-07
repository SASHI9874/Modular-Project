import os
from typing import List, Dict, Iterator
from langchain_openai import ChatOpenAI
from ..utils import convert_to_langchain_messages
from .base import BaseLLMProvider, LLMResponse
from ..errors import AuthenticationError, RateLimitError, ProviderUnavailableError, LLMError, ContextWindowError

class OpenAIProvider(BaseLLMProvider):
    def validate_config(self):
        if not os.getenv("OPENAI_API_KEY"):
            # Fallback: Check if config dict has it (useful for runtime overrides)
            if "api_key" not in self.config:
                raise ValueError("Missing OPENAI_API_KEY for OpenAI Provider")

    def _get_client(self):
        return ChatOpenAI(
            model=self.config.get("model", "gpt-4-turbo"),
            api_key=self.config.get("api_key") or os.getenv("OPENAI_API_KEY"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 2000),
            request_timeout=self.config.get("timeout", 60)
        )

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        client = self._get_client()
        lc_msgs = convert_to_langchain_messages(messages)
        
        try:
            # Invoke LangChain
            response = client.invoke(lc_msgs)
            
            return LLMResponse(
                content=str(response.content),
                token_usage=response.response_metadata.get("token_usage", {}),
                raw_response=response
            )
        
        except Exception as e:
            # Map OpenAI exceptions to our error taxonomy
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Authentication errors
            if "authentication" in error_str or "api key" in error_str or "401" in error_str:
                raise AuthenticationError(str(e), "openai")
            
            # Rate limit errors
            elif "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                raise RateLimitError(str(e), "openai")
            
            # Context length errors
            elif "context length" in error_str or "maximum context" in error_str or "too long" in error_str:
                raise ContextWindowError(str(e), "openai")
            
            # Server errors (5xx)
            elif "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
                raise ProviderUnavailableError(str(e), "openai")
            
            # Connection errors
            elif "timeout" in error_str or "connection" in error_str:
                raise ProviderUnavailableError(str(e), "openai")
            
            # Unknown error
            else:
                raise LLMError(f"OpenAI Error ({error_type}): {str(e)}", "openai")

    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        client = self._get_client()
        lc_msgs = convert_to_langchain_messages(messages)
        
        try:
            for chunk in client.stream(lc_msgs):
                if chunk.content:
                    yield str(chunk.content)
        
        except Exception as e:
            # Map errors same as chat()
            error_str = str(e).lower()
            
            if "authentication" in error_str or "api key" in error_str:
                raise AuthenticationError(str(e), "openai")
            elif "rate limit" in error_str or "429" in error_str:
                raise RateLimitError(str(e), "openai")
            elif "context length" in error_str or "maximum context" in error_str:
                raise ContextWindowError(str(e), "openai")
            elif "500" in error_str or "502" in error_str or "503" in error_str:
                raise ProviderUnavailableError(str(e), "openai")
            else:
                raise LLMError(f"OpenAI Streaming Error: {str(e)}", "openai")
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD based on current OpenAI pricing (as of 2024)"""
        model = self.config.get("model", "gpt-4-turbo")
        
        # Pricing per 1K tokens
        pricing = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
        
        # Find matching model (handle versioned models like gpt-4-0613)
        rates = None
        for model_key in pricing:
            if model_key in model:
                rates = pricing[model_key]
                break
        
        if not rates:
            rates = {"input": 0, "output": 0}
        
        cost = (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])
        return round(cost, 6)