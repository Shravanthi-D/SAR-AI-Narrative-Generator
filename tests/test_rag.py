import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.rag.embedder import get_opensearch_client
from backend.rag.retriever import retrieve_regulations


def test_retrieve_structuring_regulations():
    query = "multiple cash deposits just below 10000 reporting threshold structuring"

    client = get_opensearch_client()
    results = retrieve_regulations(query, client, top_k=5)

    print(f"\n--- RAG Retrieval Results for query ---")
    print(f"Query: {query!r}\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] source:   {r['source']}")
        print(f"    chunk_id: {r['chunk_id']}")
        print(f"    score:    {r['score']:.4f}")
        print(f"    text:     {r['text'][:150]}...")
        print()
    print("---------------------------------------\n")

    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    assert any(r["score"] > 0.5 for r in results), (
        f"Expected at least one result with score > 0.5, got scores: {[r['score'] for r in results]}"
    )
