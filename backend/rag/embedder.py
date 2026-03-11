import json
import os
import time
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import ConnectionError as OSConnectionError
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

RAG_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "rag_docs")
INDEX_NAME = "regulations"


def get_opensearch_client() -> OpenSearch:
    """Create and return an OpenSearch client for localhost:9200 (HTTP, no SSL)."""
    return OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=(os.environ.get("OPENSEARCH_USER", "admin"), os.environ.get("OPENSEARCH_PASS", "admin")),
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_assert_fingerprint=False,
        http_compress=True,
        connection_class=RequestsHttpConnection,
        timeout=60,
        max_retries=3,
        retry_on_timeout=True,
    )


def wait_for_opensearch(client: OpenSearch, timeout: int = 30) -> None:
    """Retry pinging OpenSearch every second until ready or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if client.ping():
                print("OpenSearch is ready.")
                return
        except (OSConnectionError, Exception):
            pass
        print("Waiting for OpenSearch...")
        time.sleep(1)
    raise TimeoutError(
        f"OpenSearch did not become ready within {timeout} seconds. "
        "Check that the Docker container is running on localhost:9200."
    )


def embed_text(text: str) -> list:
    """Embed text using Amazon Titan Embed Text v2 via Bedrock."""
    client = boto3.client(
        "bedrock-runtime",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    body = json.dumps({"inputText": text})
    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    return json.loads(response["body"].read())["embedding"]


def setup_opensearch_index(client: OpenSearch):
    """
    Create the 'regulations' index with knn enabled.
    Embeds a test string first to determine the vector dimension.
    Skips creation if the index already exists.
    """
    if client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists — skipping creation.")
        return

    sample = embed_text("test")
    dim = len(sample)
    print(f"Detected embedding dimension: {dim}")

    mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100,
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type":      "knn_vector",
                    "dimension": dim,
                    "method": {
                        "name":       "hnsw",
                        "space_type": "cosinesimil",
                        "engine":     "nmslib",
                    },
                },
                "chunk_id":   {"type": "keyword"},
                "source":     {"type": "keyword"},
                "text":       {"type": "text"},
                "word_count": {"type": "integer"},
            }
        },
    }

    client.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Index '{INDEX_NAME}' created with dimension {dim}.")


def index_all_chunks(chunks_json_path: str, client: OpenSearch):
    """Read chunks.json, embed each chunk, and index into OpenSearch."""
    with open(chunks_json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Indexing {len(chunks)} chunks into '{INDEX_NAME}'...")
    indexed = 0

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk["text"])
        doc = {
            "chunk_id":   chunk["chunk_id"],
            "source":     chunk["source"],
            "text":       chunk["text"],
            "word_count": chunk["word_count"],
            "embedding":  embedding,
        }
        client.index(index=INDEX_NAME, id=chunk["chunk_id"], body=doc)
        indexed += 1

        if indexed % 50 == 0:
            print(f"  Progress: {indexed}/{len(chunks)} chunks indexed")

    print(f"Done. {indexed} chunks indexed into OpenSearch.")


if __name__ == "__main__":
    os_client = get_opensearch_client()
    wait_for_opensearch(os_client)
    setup_opensearch_index(os_client)
    index_all_chunks(
        os.path.join(RAG_DOCS_DIR, "chunks.json"),
        os_client,
    )
