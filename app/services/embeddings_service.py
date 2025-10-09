# app/services/embeddings_service.py
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class EmbeddingsService:
    """
    Local embedding generator using a multilingual model (optimized for French data).
    Default: intfloat/multilingual-e5-base
    """

    def __init__(self, model_name: str | None = None):
        # Use model from config or override manually
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single string."""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings for a list of strings."""
        return self.model.encode(texts, normalize_embeddings=True).tolist()

