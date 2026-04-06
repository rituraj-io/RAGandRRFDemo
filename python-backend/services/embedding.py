"""
Embedding service — wraps sentence-transformers model.

Loads the model once and provides methods to embed
single texts or batches.
"""

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wrapper around a sentence-transformers embedding model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)


    def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns a list of floats."""
        embedding = self._model.encode(text)
        return embedding.tolist()


    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. Returns a list of embeddings."""
        embeddings = self._model.encode(texts)
        return [e.tolist() for e in embeddings]
