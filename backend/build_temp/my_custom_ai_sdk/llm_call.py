import os
from typing import Optional, Dict, Any, Union
from openai import OpenAI, AzureOpenAI

class LLMClient:
    def __init__(
        self, 
        provider: Optional[str] = None, # "openai" or "azure"
        api_key: Optional[str] = None, 
        endpoint: Optional[str] = None, # Required for Azure
        api_version: Optional[str] = None, # Required for Azure
        model: Optional[str] = None, # Deployment Name for Azure
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initializes the LLM Client for either OpenAI or Azure OpenAI.
        
        Auto-detection Logic:
        1. If 'provider' arg is passed, use that.
        2. Else if AZURE_OPENAI_API_KEY is present, use 'azure'.
        3. Else use 'openai'.
        """
        # 1. Determine Provider
        self.provider = provider or os.getenv("LLM_PROVIDER")
        
        # Auto-detect if not specified
        if not self.provider:
            if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
                self.provider = "azure"
            else:
                self.provider = "openai"

        # 2. Configuration Defaults
        self.default_temp = float(os.getenv("OPENAI_TEMPERATURE", temperature))
        self.default_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", max_tokens))
        
        # 3. Client Initialization
        self.client: Union[OpenAI, AzureOpenAI]

        if self.provider == "azure":
            self._init_azure(api_key, endpoint, api_version, model)
        else:
            self._init_openai(api_key, model)

    def _init_azure(self, api_key, endpoint, api_version, model):
        """Setup Azure OpenAI Client"""
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        
        # In Azure, 'model' usually refers to the 'deployment_name'
        self.default_model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        if not self.api_key or not self.endpoint or not self.default_model:
            raise ValueError(
                "Missing Azure Config. Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME."
            )

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        print(f"LLM Client initialized (Provider: Azure, Deployment: {self.default_model})")

    def _init_openai(self, api_key, model):
        """Setup Standard OpenAI Client"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.default_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError("OpenAI API Key is missing. Set OPENAI_API_KEY env var.")

        self.client = OpenAI(api_key=self.api_key)
        print(f"LLM Client initialized (Provider: OpenAI, Model: {self.default_model})")

    def run(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        system_context: str = "You are a helpful AI assistant."
    ) -> str:
        """
        Executes a completion request. 
        """
        if not prompt:
            return "Error: Prompt cannot be empty."

        # Resolve effective parameters
        effective_model = model or self.default_model
        effective_temp = temperature if temperature is not None else self.default_temp

        try:
            response = self.client.chat.completions.create(
                model=effective_model, # Azure uses this as 'deployment_name'
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": prompt}
                ],
                temperature=effective_temp,
                max_tokens=self.default_max_tokens
            )
            return response.choices[0].message.content or ""
            
        except Exception as e:
            return f"LLM Execution Error: {str(e)}"