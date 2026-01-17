import os
from typing import List, Dict, Any

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', device: str = None):
        """
        Init wrapper. Models are loaded LAZILY to keep startup fast.
        """
        self.model_name = model_name
        self.device = device
        self._model = None  # Placeholder for lazy loading

    def _load_model(self):
        """Loads the model only when first used."""
        if self._model is not None:
            return

        print(f"⏳ Loading Embedding Model: {self.model_name}...")
        from sentence_transformers import SentenceTransformer
        import torch

        # Auto-detect device if not specified
        if not self.device:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps" 
            else:
                self.device = "cpu"
        
        try:
            self._model = SentenceTransformer(self.model_name, device=self.device)
            print(f"✅ Model loaded on {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Splits text into chunks with overlap to preserve context.
        Production App: Use 'RecursiveCharacterTextSplitter' from LangChain here.
        This is a lightweight python-only fallback.
        """
        if not text: return []
        
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1 # +1 for space
            
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                # Keep the last 'overlap' words for the next chunk
                overlap_words = int(overlap / 10) # rough heuristic
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def run(self, text: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        Chunk text -> Generate Embeddings -> Return Structured Data.
        Output: [{'text': '...', 'vector': [0.1, ...]}, ...]
        """
        if not text or not isinstance(text, str):
            return []

        # 1. Lazy Load
        self._load_model()

        # 2. Pre-process & Chunk
        # Standardize whitespace
        text = " ".join(text.split())
        chunks = self._chunk_text(text, chunk_size=chunk_size)

        if not chunks:
            return []

        try:
            # 3. Batch Inference (Much faster than looping)
            # encode() handles batching internally
            vectors = self._model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
            
            # 4. Format Output
            results = []
            for i, chunk in enumerate(chunks):
                results.append({
                    "chunk_id": i,
                    "text": chunk,
                    "vector": vectors[i].tolist() # Convert numpy -> list for JSON serialization
                })
            
            return results

        except Exception as e:
            return [{"error": str(e)}]