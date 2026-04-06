"""
Tests for the hybrid search service (Reciprocal Rank Fusion).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.hybrid_search import reciprocal_rank_fusion


def test_rrf_merges_two_lists():
    """RRF merges two ranked result lists by document ID."""
    vector_results = [
        {"id": "a", "title": "A", "content": "a", "score": 0.9, "metadata": {}},
        {"id": "b", "title": "B", "content": "b", "score": 0.7, "metadata": {}},
        {"id": "c", "title": "C", "content": "c", "score": 0.5, "metadata": {}},
    ]
    bm25_results = [
        {"id": "b", "title": "B", "content": "b", "score": 5.0, "metadata": {}},
        {"id": "d", "title": "D", "content": "d", "score": 3.0, "metadata": {}},
        {"id": "a", "title": "A", "content": "a", "score": 1.0, "metadata": {}},
    ]

    merged = reciprocal_rank_fusion(vector_results, bm25_results, limit=4)

    assert len(merged) == 4
    ids = [r["id"] for r in merged]
    assert "a" in ids[:2]
    assert "b" in ids[:2]


def test_rrf_respects_limit():
    """RRF returns at most `limit` results."""
    results_a = [{"id": str(i), "title": "", "content": "", "score": 1.0, "metadata": {}} for i in range(10)]
    results_b = [{"id": str(i), "title": "", "content": "", "score": 1.0, "metadata": {}} for i in range(10, 20)]

    merged = reciprocal_rank_fusion(results_a, results_b, limit=5)
    assert len(merged) == 5


def test_rrf_empty_inputs():
    """RRF handles empty input lists."""
    merged = reciprocal_rank_fusion([], [], limit=10)
    assert merged == []


def test_rrf_one_empty():
    """RRF works when one list is empty."""
    results = [
        {"id": "a", "title": "A", "content": "a", "score": 0.9, "metadata": {}},
    ]
    merged = reciprocal_rank_fusion(results, [], limit=10)
    assert len(merged) == 1
    assert merged[0]["id"] == "a"
