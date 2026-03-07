import os
from typing import Dict
from .providers.base import BaseLLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.azure_provider import AzureProvider
from .providers.gemini_provider import GeminiProvider

def get_llm_provider(override_config: Dict[str, str] = None) -> BaseLLMProvider:
    """
    Factory to instantiate the correct LLM Provider.
    """
    config = override_config or {}
    
    # 1. Determine Provider (Env var takes precedence if not passed in config)
    provider_name = config.get("provider") or os.getenv("LLM_PROVIDER", "openai").lower()
    
    # 2. Instantiate
    if provider_name == "openai":
        return OpenAIProvider(config)
    
    elif provider_name == "azure":
        return AzureProvider(config)
    
    elif provider_name == "gemini":
        return GeminiProvider(config)
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider_name}")