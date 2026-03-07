import os
from typing import Dict, Any

class LLMConfig:
    """
    Centralized configuration management.
    Reads from Environment Variables with sensible defaults.
    """
    
    @staticmethod
    def get_provider_config() -> Dict[str, Any]:
        """
        Returns a clean dictionary of config values based on the active provider.
        Validates that required fields are present.
        """
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        base_config = {
            "provider": provider,
            "model": os.getenv("LLM_MODEL"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
            "timeout": int(os.getenv("LLM_TIMEOUT", "60"))
        }

        # Provider-specific config
        if provider == "openai":
            base_config["api_key"] = os.getenv("OPENAI_API_KEY")
            if not base_config["model"]:
                base_config["model"] = "gpt-4-turbo"
            
        elif provider == "azure":
            base_config["api_key"] = os.getenv("AZURE_OPENAI_API_KEY")
            base_config["endpoint"] = os.getenv("AZURE_OPENAI_ENDPOINT")
            base_config["deployment_name"] = os.getenv("AZURE_DEPLOYMENT_NAME")
            base_config["api_version"] = os.getenv("AZURE_API_VERSION", "2023-05-15")
            
        elif provider == "gemini":
            base_config["api_key"] = os.getenv("GOOGLE_API_KEY")
            if not base_config["model"]:
                base_config["model"] = "gemini-1.5-flash"
            
        elif provider == "anthropic":
            base_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
            if not base_config["model"]:
                base_config["model"] = "claude-3-sonnet-20240229"
        
        # Validate configuration
        LLMConfig._validate_config(base_config, provider)
        
        return base_config
    
    @staticmethod
    def _validate_config(config: Dict, provider: str):
        """
        Ensure required fields are present and valid.
        Raises ValueError with helpful message if validation fails.
        """
        # Check API key
        if not config.get("api_key"):
            key_name = {
                "openai": "OPENAI_API_KEY",
                "azure": "AZURE_OPENAI_API_KEY",
                "gemini": "GOOGLE_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY"
            }.get(provider, "API_KEY")
            
            raise ValueError(
                f"Missing API key for provider '{provider}'. "
                f"Please set {key_name} in your environment variables."
            )
        
        # Azure-specific validation
        if provider == "azure":
            required_fields = {
                "endpoint": "AZURE_OPENAI_ENDPOINT",
                "deployment_name": "AZURE_DEPLOYMENT_NAME"
            }
            
            missing = []
            for field, env_var in required_fields.items():
                if not config.get(field):
                    missing.append(env_var)
            
            if missing:
                raise ValueError(
                    f"Missing Azure OpenAI configuration: {', '.join(missing)}. "
                    f"Please set these environment variables."
                )
        
        # Validate temperature range
        temp = config.get("temperature", 0.7)
        if not (0 <= temp <= 2):
            raise ValueError(f"Temperature must be between 0 and 2, got {temp}")
        
        # Validate max_tokens
        max_tokens = config.get("max_tokens", 2000)
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {max_tokens}")
        
        # Validate timeout
        timeout = config.get("timeout", 60)
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")

    @staticmethod
    def get_retry_config() -> Dict[str, int]:
        """Get retry configuration from environment"""
        return {
            "max_attempts": int(os.getenv("LLM_MAX_RETRIES", "3")),
            "min_seconds": int(os.getenv("LLM_RETRY_MIN_SECONDS", "1")),
            "max_seconds": int(os.getenv("LLM_RETRY_MAX_SECONDS", "10"))
        }