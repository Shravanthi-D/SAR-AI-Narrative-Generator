"""
RAG retriever — queries OpenSearch for regulation documents relevant to a
given suspicious activity pattern.

Input:
    concern (str): e.g. "STRUCTURING", "LAYERING"
    opensearch_client: opensearchpy.OpenSearch instance

Output:
    list of dicts with keys: source, text, score
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "sar-regulations")
_TOP_K = 5


def retrieve_regulations(concern: str, opensearch_client, top_k: int = _TOP_K) -> list:
    """
    Performs a keyword search against the regulations index in OpenSearch
    and returns the top-K matching documents.

    Args:
        concern:           the suspicious activity pattern or semantic query
        opensearch_client: an initialised opensearchpy.OpenSearch instance
        top_k:             number of results to return (default 5)

    Returns:
        list of dicts: [{chunk_id, source, text, score}, ...]
    """
    query = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": concern,
                "fields": ["source", "text", "pattern_tags"],
            }
        },
    }

    response = opensearch_client.search(index=_INDEX_NAME, body=query)
    hits = response.get("hits", {}).get("hits", [])

    return [
        {
            "chunk_id": hit["_source"].get("chunk_id", hit.get("_id", "")),
            "source":   hit["_source"].get("source", ""),
            "text":     hit["_source"].get("text", ""),
            "score":    hit.get("_score", 0.0),
        }
        for hit in hits
    ]
