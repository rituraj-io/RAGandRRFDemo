"""
Tests for the embedding service.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.embedding import EmbeddingService


def test_embed_single_text():
    """Embedding a single text returns a list of floats."""
    svc = EmbeddingService(model_name="all-MiniLM-L6-v2")
    result = svc.embed("hello world")

    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(x, float) for x in result)


def test_embed_batch():
    """Embedding multiple texts returns a list of embeddings."""
    svc = EmbeddingService(model_name="all-MiniLM-L6-v2")
    results = svc.embed_batch(["hello", "world"])

    assert len(results) == 2
    assert len(results[0]) == 384
    assert len(results[1]) == 384
