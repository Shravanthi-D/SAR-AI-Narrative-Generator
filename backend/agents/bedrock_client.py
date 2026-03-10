import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def _build_prompt(prompt: str, system_prompt: str) -> str:
    parts = ["<|begin_of_text|>"]

    if system_prompt:
        parts.append(
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        )

    parts.append(
        f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )

    return "".join(parts)


def call_llama(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> str:
    region = os.environ["AWS_REGION"]
    model_id = os.environ["BEDROCK_MODEL_ID"]

    client = boto3.client("bedrock-runtime", region_name=region)

    body = json.dumps(
        {
            "prompt": _build_prompt(prompt, system_prompt),
            "max_gen_len": max_tokens,
            "temperature": temperature,
        }
    )

    response = client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    return result["generation"]
