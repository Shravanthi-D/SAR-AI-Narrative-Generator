import os
import json
import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestError

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

_TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"


def embed_text(text: str) -> list:
    body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
    response = _bedrock.invoke_model(
        modelId=_TITAN_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def setup_index(client: OpenSearch, index: str = "regulations") -> None:
    index_body = {
        "settings": {
            "index": {
                "knn": True,
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "text": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1024,
                },
            }
        },
    }
    try:
        client.indices.create(index=index, body=index_body)
    except RequestError as e:
        if e.status_code != 400:
            raise


def index_all_chunks(chunks_json_path: str, client: OpenSearch, index: str = "regulations") -> None:
    with open(chunks_json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk["text"])
        doc = {
            "chunk_id": chunk.get("chunk_id", str(i)),
            "source": chunk.get("source", ""),
            "text": chunk["text"],
            "embedding": embedding,
        }
        client.index(index=index, body=doc)

        if (i + 1) % 10 == 0:
            print(f"Indexed {i + 1}/{len(chunks)} chunks")


if __name__ == "__main__":
    os_client = OpenSearch(
        hosts=[os.environ.get("OPENSEARCH_URL", "http://localhost:9200")],
        http_auth=(
            os.environ.get("OPENSEARCH_USER", "admin"),
            os.environ.get("OPENSEARCH_PASS", "admin"),
        ),
        verify_certs=False,
        ssl_show_warn=False,
    )

    setup_index(os_client)
    index_all_chunks("rag_docs/chunks.json", os_client)
    print("Indexing complete")
