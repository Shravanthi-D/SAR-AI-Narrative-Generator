"""
Shared Bedrock LLM client used by all three agents.

Uses the invoke_model API with Llama 3 instruct prompt format.
Model ID and region are read from environment variables:
    BEDROCK_MODEL_ID  — defaults to "meta.llama3-1-70b-instruct-v1:0"
    AWS_REGION        — defaults to "us-east-1"
"""
import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def _build_prompt(user_message: str, system_prompt: str) -> str:
    """
    Build a Llama 3 instruct-format prompt string.

    When system_prompt is non-empty the system block is prepended:
        <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>\\n\\n{system_prompt}<|eot_id|>
        <|start_header_id|>user<|end_header_id|>\\n\\n{user_message}<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>\\n\\n

    When system_prompt is empty the system block is omitted entirely.
    """
    parts = ["<|begin_of_text|>"]
    if system_prompt:
        parts.append(
            f"<|start_header_id|>system<|end_header_id|>\n\n"
            f"{system_prompt}<|eot_id|>"
        )
    parts.append(
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_message}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    return "".join(parts)


def call_llama(
    user_message: str,
    *,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> str:
    """
    Call the Llama 3 model on Amazon Bedrock via invoke_model.

    Args:
        user_message:  The content to analyse.
        system_prompt: Role/behaviour instructions for the model.
        max_tokens:    Maximum tokens to generate (default 2048).
        temperature:   Sampling temperature (default 0.1).

    Returns:
        str — raw text response from the model.
    """
    model_id = os.environ.get("BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0")
    region = os.environ.get("AWS_REGION", "us-east-1")

    prompt = _build_prompt(user_message, system_prompt)
    body = json.dumps({
        "prompt":      prompt,
        "temperature": temperature,
        "max_gen_len": max_tokens,
    })

    client = boto3.client("bedrock-runtime", region_name=region)
    response = client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["generation"]
