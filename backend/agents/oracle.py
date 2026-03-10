import json
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama
from backend.rag.retriever import retrieve_regulations

SYSTEM_PROMPT = (
    "You are a regulatory compliance expert. "
    "Only cite regulations present in the provided context. "
    "NEVER cite a regulation not in the context. "
    "Return JSON only."
)

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")


def _parse_llm_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = _FENCE_RE.search(raw)
    if match:
        return json.loads(match.group(1))

    raise json.JSONDecodeError("No valid JSON found in LLM response", raw, 0)


def _build_semantic_query(investigation: dict) -> str:
    primary_concern = investigation.get("primary_concern", "")
    patterns = investigation.get("patterns_detected", [])
    patterns_str = " ".join(patterns) if patterns else ""
    return (
        f"{primary_concern} {patterns_str} "
        "AML reporting cash deposits threshold"
    ).strip()


def _format_chunks(chunks: list) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] SOURCE: {chunk['source']}\nTEXT: {chunk['text']}")
    return "\n\n".join(parts)


def _build_user_prompt(investigation: dict, formatted_context: str) -> str:
    account = investigation.get("account", "unknown")
    patterns = investigation.get("patterns_detected", [])
    primary_concern = investigation.get("primary_concern", "")
    evidence_summary = investigation.get("evidence_summary", "")

    return (
        f"Account under review: {account}\n"
        f"Detected patterns: {', '.join(patterns)}\n"
        f"Primary concern: {primary_concern}\n"
        f"Evidence summary: {evidence_summary}\n\n"
        f"Relevant regulatory context:\n{formatted_context}\n\n"
        "Based only on the regulatory context above, produce a JSON object with exactly these keys:\n"
        "  applicable_regulations  — array of objects, each with keys:\n"
        "                              source          (string — regulation name/ID from context)\n"
        "                              summary         (string — one sentence summary)\n"
        "                              relevant_excerpt (string — verbatim or close excerpt from context)\n"
        "  reporting_obligation    — string describing what must be filed and when\n"
        "  regulatory_basis_summary — string summarising the overall regulatory basis for filing\n\n"
        "Respond with the JSON object only. No commentary, no markdown."
    )


def run_oracle(investigation: dict, opensearch_client) -> dict:
    query = _build_semantic_query(investigation)
    chunks = retrieve_regulations(query, opensearch_client, top_k=5)

    formatted_context = _format_chunks(chunks)
    user_prompt = _build_user_prompt(investigation, formatted_context)

    raw = call_llama(user_prompt, system_prompt=SYSTEM_PROMPT, temperature=0.0)
    result = _parse_llm_json(raw)
    result["retrieved_chunks"] = chunks
    return result
