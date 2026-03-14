"""
Agent 2 — Regulatory Oracle

Receives investigator findings, retrieves relevant regulations from the RAG
vector store (OpenSearch), then uses the LLM to select and excerpt the most
applicable rules.

Input:
    investigation (dict): output from Agent 1 (Investigator)
    opensearch_client: an opensearchpy.OpenSearch instance

Output dict keys:
    applicable_regulations  — list of {source, summary, relevant_excerpt}
    reporting_obligation    — plain-text statement of the filing deadline/requirement
    regulatory_basis_summary — one-paragraph summary of the regulatory basis
    retrieved_chunks        — raw chunks from OpenSearch (for lineage)
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama
from backend.rag.retriever import retrieve_regulations


_SYSTEM_PROMPT = (
    "You are a regulatory compliance expert for anti-money laundering. "
    "Given the investigator findings and retrieved regulation excerpts, "
    "identify all applicable rules and obligations. "
    "NEVER cite a regulation not in the context provided. "
    "Return ONLY valid JSON with exactly these keys: "
    "applicable_regulations (array of objects each with source, summary, relevant_excerpt), "
    "reporting_obligation, regulatory_basis_summary."
)

_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL)
_BRACE_RE = re.compile(r'\{.*\}', re.DOTALL)


def _parse_llm_json(raw: str) -> dict:
    """
    Extract and parse JSON from an LLM response that may contain preamble text.
    Raises json.JSONDecodeError if no valid JSON found.
    """
    cleaned = raw.strip()
    m = _FENCE_RE.search(cleaned)
    if m:
        return json.loads(m.group(1).strip())
    m2 = _BRACE_RE.search(cleaned)
    if m2:
        return json.loads(m2.group(0))
    return json.loads(cleaned)


def _build_semantic_query(investigation: dict) -> str:
    """Build a semantic search query from investigation findings."""
    patterns = " ".join(investigation.get("patterns_detected", []))
    concern  = investigation.get("primary_concern", "")
    return f"AML suspicious activity {patterns} threshold {concern}".strip()


def _format_chunks(chunks: list) -> str:
    """Format retrieved OpenSearch chunks into a numbered context block."""
    if not chunks:
        return ""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] SOURCE: {chunk.get('source', '')}")
        lines.append(f"TEXT: {chunk.get('text', '')}")
    return "\n".join(lines)


def _build_user_prompt(investigation: dict, context: str) -> str:
    """Build the user message sent to the LLM."""
    return (
        f"Investigation findings:\n"
        f"{json.dumps(investigation, indent=2, default=str)}\n\n"
        f"Retrieved regulation excerpts:\n{context}\n\n"
        f"Return JSON with keys: applicable_regulations "
        f"(each with source, summary, relevant_excerpt), "
        f"reporting_obligation, regulatory_basis_summary."
    )


def run_oracle(investigation: dict, opensearch_client) -> dict:
    query = _build_semantic_query(investigation)

    try:
        retrieved = retrieve_regulations(query, opensearch_client, top_k=5)
    except Exception:
        retrieved = []

    context     = _format_chunks(retrieved)
    user_prompt = _build_user_prompt(investigation, context)

    raw = call_llama(
        user_prompt,
        system_prompt=_SYSTEM_PROMPT,
        max_tokens=2048,
        temperature=0.0,
    )
    result = _parse_llm_json(raw)
    result["retrieved_chunks"] = retrieved
    return result
