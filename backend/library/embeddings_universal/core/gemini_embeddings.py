"""
Custom Gemini Embeddings using official google-genai SDK
"""

from typing import List
from langchain_core.embeddings import Embeddings


class GeminiEmbeddings(Embeddings):
    """Custom Gemini embeddings using official SDK"""

    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-genai not installed. "
                "Run: pip install google-genai"
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # DO NOT prefix with models/
        # Official docs show plain model name
        self.model = model

        print(f" [GeminiEmbeddings] Initialized with model: {self.model}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=texts  # pass list directly (batch)
            )

            # Official SDK returns result.embeddings
            print(" [GeminiEmbeddings] Generated embeddings")
            return [embedding.values for embedding in result.embeddings]

        except Exception as e:
            raise Exception(f"Gemini embedding failed: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def create_gemini_embeddings(
    api_key: str,
    model: str = "gemini-embedding-001"
) -> Embeddings:
    return GeminiEmbeddings(api_key=api_key, model=model)