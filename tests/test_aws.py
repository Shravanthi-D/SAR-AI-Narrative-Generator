import sys
import os
import json
import boto3
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

AWS_REGION       = os.environ["AWS_REGION"]
AWS_ACCESS_KEY   = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY   = os.environ["AWS_SECRET_ACCESS_KEY"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]


def make_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


def test_bedrock_llama_hello():
    """Send a simple prompt to Llama 3.1 and assert a non-empty response."""
    client = make_bedrock_client()

    # Llama 3.1 prompt format
    prompt = (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n"
        "You are a helpful assistant."
        "<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n"
        "Say hello in one word."
        "<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n"
    )

    body = json.dumps({
        "prompt":      prompt,
        "max_gen_len": 32,
        "temperature": 0.1,
    })

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    text = result.get("generation", "").strip()

    print(f"\n--- Llama 3.1 Response ---")
    print(f"Raw result: {json.dumps(result, indent=2)}")
    print(f"Text: {text!r}")
    print(f"--------------------------\n")

    assert text, "Bedrock returned an empty response"


def test_bedrock_titan_embeddings():
    """Embed a short string with Titan Embed v2 and assert a non-empty vector."""
    client = make_bedrock_client()

    body = json.dumps({"inputText": "test embedding"})

    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    embedding = result.get("embedding", [])

    print(f"\n--- Titan Embedding ---")
    print(f"Vector length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"----------------------\n")

    assert len(embedding) > 0, "Titan returned an empty embedding vector"
