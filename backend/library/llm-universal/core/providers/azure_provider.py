import os
from typing import List, Dict, Iterator
from langchain_openai import AzureChatOpenAI
from ..utils import convert_to_langchain_messages
from .base import BaseLLMProvider, LLMResponse
from ..errors import AuthenticationError, RateLimitError, ProviderUnavailableError, LLMError, ContextWindowError

class AzureProvider(BaseLLMProvider):
    def validate_config(self):
        required = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_DEPLOYMENT_NAME"]
        missing = [key for key in required if not os.getenv(key) and key.lower() not in self.config]
        if missing:
            raise ValueError(f"Missing config for Azure: {', '.join(missing)}")

    def _get_client(self):
        return AzureChatOpenAI(
            azure_deployment=self.config.get("deployment_name") or os.getenv("AZURE_DEPLOYMENT_NAME"),
            openai_api_version=self.config.get("api_version") or os.getenv("AZURE_API_VERSION", "2023-05-15"),
            azure_endpoint=self.config.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=self.config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 2000),
            request_timeout=self.config.get("timeout", 60)
        )

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        client = self._get_client()
        lc_msgs = convert_to_langchain_messages(messages)
        
        try:
            response = client.invoke(lc_msgs)
            
            return LLMResponse(
                content=str(response.content),
                token_usage=response.response_metadata.get("token_usage", {}),
                raw_response=response
            )
        
        except Exception as e:
            # Map Azure exceptions to our error taxonomy
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Authentication errors
            if "authentication" in error_str or "api key" in error_str or "401" in error_str or "unauthorized" in error_str:
                raise AuthenticationError(str(e), "azure")
            
            # Rate limit errors
            elif "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                raise RateLimitError(str(e), "azure")
            
            # Context length errors
            elif "context length" in error_str or "maximum context" in error_str or "too long" in error_str:
                raise ContextWindowError(str(e), "azure")
            
            # Server errors (5xx)
            elif "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
                raise ProviderUnavailableError(str(e), "azure")
            
            # Connection errors
            elif "timeout" in error_str or "connection" in error_str:
                raise ProviderUnavailableError(str(e), "azure")
            
            # Azure-specific: Deployment not found
            elif "deployment" in error_str and ("not found" in error_str or "does not exist" in error_str):
                raise LLMError(f"Azure deployment not found. Check AZURE_DEPLOYMENT_NAME. Error: {str(e)}", "azure")
            
            # Unknown error
            else:
                raise LLMError(f"Azure Error ({error_type}): {str(e)}", "azure")

    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        client = self._get_client()
        lc_msgs = convert_to_langchain_messages(messages)
        
        try:
            for chunk in client.stream(lc_msgs):
                if chunk.content:
                    yield str(chunk.content)
        
        except Exception as e:
            error_str = str(e).lower()
            
            if "authentication" in error_str or "api key" in error_str:
                raise AuthenticationError(str(e), "azure")
            elif "rate limit" in error_str or "429" in error_str:
                raise RateLimitError(str(e), "azure")
            elif "context length" in error_str or "maximum context" in error_str:
                raise ContextWindowError(str(e), "azure")
            elif "500" in error_str or "502" in error_str or "503" in error_str:
                raise ProviderUnavailableError(str(e), "azure")
            else:
                raise LLMError(f"Azure Streaming Error: {str(e)}", "azure")
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Azure OpenAI.
        Note: Azure pricing varies by region and commitment level.
        These are approximate pay-as-you-go rates.
        """
        model = self.config.get("model", "gpt-4")
        
        # Approximate Azure pricing per 1K tokens
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-35-turbo": {"input": 0.0015, "output": 0.002},
        }
        
        rates = pricing.get(model, {"input": 0.03, "output": 0.06})
        
        cost = (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])
        return round(cost, 6)