"""
Hybrid search service — Reciprocal Rank Fusion.

Merges ranked results from vector search and BM25 search
into a single ranked list using the RRF algorithm.
"""


def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    limit: int = 10,
    k: int = 60,
) -> list[dict]:
    """
    Merge two ranked result lists using Reciprocal Rank Fusion.

    Each document gets a score of 1/(k + rank) from each list.
    Documents appearing in both lists get summed scores.

    Args:
        vector_results: Ranked results from vector search.
        bm25_results: Ranked results from BM25 search.
        limit: Max number of results to return.
        k: RRF constant (default 60, standard value).

    Returns:
        Merged and re-ranked list of results.
    """

    scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}


    # Score vector results
    for rank, doc in enumerate(vector_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc


    # Score BM25 results
    for rank, doc in enumerate(bm25_results):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        if doc_id not in doc_map:
            doc_map[doc_id] = doc


    # Sort by fused score descending
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids[:limit]:
        result = {**doc_map[doc_id], "score": scores[doc_id]}
        results.append(result)

    return results
