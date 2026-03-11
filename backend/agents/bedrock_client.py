"""
Shared Bedrock LLM client used by all three agents.

Uses the AWS Bedrock converse API via boto3.  Model ID and region are read
from environment variables:
    BEDROCK_MODEL_ID  — defaults to "meta.llama3-1-70b-instruct-v1:0"
    AWS_REGION        — defaults to "us-east-1"
"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def invoke_llm(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
    temperature: float = 0.1,
) -> str:
    """
    Sends a system prompt and user message to Amazon Bedrock and returns
    the model's raw text response.

    Args:
        system_prompt: instructions for the model role/behaviour
        user_message:  the actual content to analyse
        max_tokens:    maximum tokens to generate (default 4096)
        temperature:   sampling temperature (default 0.1)

    Returns:
        str — the raw text from the model (expected to be valid JSON)
    """
    model_id = os.environ.get(
        "BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0"
    )
    region = os.environ.get("AWS_REGION", "us-east-1")

    client = boto3.client("bedrock-runtime", region_name=region)

    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )

    return response["output"]["message"]["content"][0]["text"]


def call_llama(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> str:
    if not system_prompt:
        system_prompt = "You are a helpful assistant."
    return invoke_llm(system_prompt, prompt, max_tokens=max_tokens, temperature=temperature)
