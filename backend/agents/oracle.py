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

import os
import re
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama
from backend.rag.retriever import retrieve_regulations


_SYSTEM_PROMPT = (
    "You are a regulatory compliance expert for anti-money laundering. "
    "Given the investigator findings and retrieved regulation excerpts, "
    "identify all applicable rules and obligations. "
    "Return ONLY valid JSON with exactly these keys: "
    "applicable_regulations (array of objects each with source, summary, relevant_excerpt), "
    "reporting_obligation, regulatory_basis_summary."
)


def _strip_markdown_fences(text: str) -> str:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def run_oracle(investigation: dict, opensearch_client) -> dict:
    concern = (investigation or {}).get("primary_concern", "SUSPICIOUS_ACTIVITY")

    try:
        retrieved = retrieve_regulations(concern, opensearch_client)
    except Exception:
        retrieved = []

    user_message = (
        f"Investigation findings:\n{json.dumps(investigation, indent=2, default=str)}\n\n"
        f"Retrieved regulation excerpts:\n{json.dumps(retrieved, indent=2)}"
    )

    try:
        raw = call_llama(user_message, _SYSTEM_PROMPT, max_tokens=2048)
        result = json.loads(_strip_markdown_fences(raw))
    except json.JSONDecodeError:
        result = {
            "applicable_regulations": [
                {
                    "source": r.get("source", ""),
                    "summary": r.get("text", "")[:200],
                    "relevant_excerpt": r.get("text", ""),
                }
                for r in retrieved
                if r.get("source")
            ],
            "reporting_obligation": "File SAR within 30 days of detection per applicable law.",
            "regulatory_basis_summary": (
                f"Activity flagged as {concern} triggers mandatory SAR filing obligations."
            ),
        }

    result["retrieved_chunks"] = retrieved
    return result
