import os
from typing import Any, List
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from .errors import EmbeddingError, EmbeddingAuthError, EmbeddingQuotaError, EmbeddingConfigError
from .gemini_embeddings import create_gemini_embeddings


def get_embeddings_model(override_config: dict = None) -> Any:
    """
    Factory: Returns a LangChain Embeddings Object.
    """
    config = override_config or {}
    provider = config.get("provider") or os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    
    print(f" [Embeddings] Initializing provider: {provider}")
    
    try:
        if provider == "openai":
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EmbeddingConfigError("Missing OPENAI_API_KEY", provider)
            
            model = config.get("model") or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            
            return OpenAIEmbeddings(
                api_key=api_key,
                model=model
            )
        
        elif provider == "azure":
            api_key = config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = config.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = config.get("deployment") or os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
            
            if not all([api_key, endpoint, deployment]):
                raise EmbeddingConfigError(
                    "Missing required Azure config: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_EMBEDDING_DEPLOYMENT",
                    provider
                )
            
            return AzureOpenAIEmbeddings(
                azure_deployment=deployment,
                openai_api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
                azure_endpoint=endpoint,
                api_key=api_key
            )
        
        elif provider == "gemini":
            api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise EmbeddingConfigError("Missing GOOGLE_API_KEY", provider)
            
            # Use custom Gemini embeddings with new SDK
            model = config.get("model") or os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
            
            # Clean model name (remove models/ prefix if present)
            if model.startswith("models/"):
                model = model.replace("models/", "")
            
            print(f"🔍 [Embeddings] Using Gemini model: {model}")
            
            return create_gemini_embeddings(
                api_key=api_key,
                model=model
            )
        
        else:
            raise EmbeddingConfigError(f"Unsupported provider: {provider}. Use 'openai', 'azure', or 'gemini'", provider)
    
    except EmbeddingConfigError:
        raise
    
    except Exception as e:
        error_str = str(e).lower()
        
        # Map common errors
        if "api key" in error_str or "401" in error_str or "unauthorized" in error_str:
            raise EmbeddingAuthError(str(e), provider)
        elif "429" in error_str or "quota" in error_str or "rate limit" in error_str:
            raise EmbeddingQuotaError(str(e), provider)
        else:
            raise EmbeddingError(f"Failed to initialize embeddings: {str(e)}", provider)


def embed_text(text: str, override_config: dict = None) -> List[float]:
    """
    Embed a single text string.
    
    Args:
        text: Text to embed
        override_config: Optional config overrides
        
    Returns:
        List of floats (embedding vector)
    """
    try:
        embeddings = get_embeddings_model(override_config)
        vector = embeddings.embed_query(text)
        print(f" [Embeddings] Generated vector of dimension {len(vector)}")
        return vector
    
    except Exception as e:
        print(f" [Embeddings] Error: {str(e)}")
        raise


def embed_documents(texts: List[str], override_config: dict = None) -> List[List[float]]:
    """
    Embed multiple text strings (batch operation).
    
    Args:
        texts: List of texts to embed
        override_config: Optional config overrides
        
    Returns:
        List of embedding vectors
    """
    try:
        embeddings = get_embeddings_model(override_config)
        vectors = embeddings.embed_documents(texts)
        print(f" [Embeddings] Generated {len(vectors)} vectors")
        return vectors
    
    except Exception as e:
        print(f" [Embeddings] Error: {str(e)}")
        raise


def get_provider_info() -> dict:
    """Get information about the current embedding provider"""
    provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    
    return {
        "provider": provider,
        "model": os.getenv("EMBEDDING_MODEL", "default"),
        "available": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "azure": bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
            "gemini": bool(os.getenv("GOOGLE_API_KEY"))
        }
    }