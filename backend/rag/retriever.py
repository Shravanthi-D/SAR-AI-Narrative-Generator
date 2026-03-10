import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

INDEX_NAME = "regulations"


def retrieve_regulations(query: str, client: OpenSearch, top_k: int = 5) -> list:
    """
    Embed the query and search OpenSearch with knn to find the top_k most
    relevant regulation chunks.

    Returns a list of dicts with keys: source, chunk_id, text, score.
    """
    from backend.rag.embedder import embed_text

    query_vector = embed_text(query)

    search_body = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k":      top_k,
                }
            }
        },
        "_source": ["chunk_id", "source", "text"],
    }

    response = client.search(index=INDEX_NAME, body=search_body)

    results = []
    for hit in response["hits"]["hits"]:
        results.append({
            "source":   hit["_source"]["source"],
            "chunk_id": hit["_source"]["chunk_id"],
            "text":     hit["_source"]["text"],
            "score":    hit["_score"],
        })

    return results
