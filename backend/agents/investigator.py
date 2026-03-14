"""
Agent 1 — Investigator

Analyses masked transactions for a given account using graph pattern detection
and an LLM to produce a structured investigation finding.

Input:
    account_token (str): masked account identifier, e.g. "ACC_001"
    transactions (list): list of masked transaction dicts

Output dict keys:
    status                  — "SUSPICIOUS" | "NO_SUSPICIOUS_ACTIVITY"
    account                 — account_token
    patterns_detected       — list of pattern names, e.g. ["STRUCTURING"]
    primary_concern         — first and most significant pattern
    evidence_summary        — narrative paragraph describing the suspicious activity
    total_suspicious_amount — sum of amounts in flagged transactions
    time_period             — {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    transaction_ids         — list of txn_id strings that are evidence
    transactions            — full dicts for the evidence transactions
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama
from backend.graph.loader import build_transaction_graph
from backend.graph.patterns import run_all_detections


_SYSTEM_PROMPT = (
    "You are a financial crime investigator writing structured SAR reports. "
    "Given graph-detected suspicious pattern findings for an account, produce "
    "a concise investigation summary as valid JSON. Return ONLY valid JSON with "
    "exactly these keys: account, patterns_detected, primary_concern, "
    "evidence_summary, total_suspicious_amount, "
    "time_period (object with start and end as ISO date strings), "
    "transaction_ids, status."
)

_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL)
_BRACE_RE = re.compile(r'\{.*\}', re.DOTALL)


def _parse_llm_json(raw: str) -> dict:
    """
    Extract and parse JSON from an LLM response that may contain preamble text.
    Tries in order:
      1. Markdown code fence (anywhere in the response)
      2. Raw JSON object (first { ... } block)
    Raises json.JSONDecodeError if no valid JSON found.
    """
    cleaned = raw.strip()
    # Try code fence anywhere in response
    m = _FENCE_RE.search(cleaned)
    if m:
        return json.loads(m.group(1).strip())
    # Try extracting first { ... } block
    m2 = _BRACE_RE.search(cleaned)
    if m2:
        return json.loads(m2.group(0))
    return json.loads(cleaned)  # will raise JSONDecodeError if still not valid


def _build_user_prompt(account_token: str, findings: list, transactions: list) -> str:
    """Build the user message sent to the LLM."""
    all_txn_ids: set = set()
    for f in findings:
        all_txn_ids.update(f.get("transactions", []))

    matching = [t for t in transactions if t.get("txn_id") in all_txn_ids]
    timestamps = sorted(
        str(t.get("txn_timestamp", ""))
        for t in matching
        if t.get("txn_timestamp")
    )

    if timestamps:
        date_range = f"{timestamps[0][:10]} to {timestamps[-1][:10]}"
    else:
        date_range = "unknown"

    return (
        f"Account: {account_token}\n\n"
        f"Time period: {date_range}\n\n"
        f"Pattern findings from graph analysis:\n"
        f"{json.dumps(findings, indent=2, default=str)}\n\n"
        f"All transactions (masked):\n"
        f"{json.dumps(transactions, indent=2, default=str)}\n\n"
        f"Return JSON with keys: account, patterns_detected, primary_concern, "
        f"evidence_summary, total_suspicious_amount, time_period, transaction_ids, status."
    )


def run_investigator(account_token: str, transactions: list) -> dict:
    G = build_transaction_graph(transactions)
    findings = run_all_detections(G, account_token)

    if not findings:
        return {"status": "NO_SUSPICIOUS_ACTIVITY", "findings": []}

    user_message = _build_user_prompt(account_token, findings, transactions)

    raw = call_llama(
        user_message,
        system_prompt=_SYSTEM_PROMPT,
        max_tokens=2048,
        temperature=0.0,
    )
    result = _parse_llm_json(raw)
    result.setdefault("status", "SUSPICIOUS")

    txn_id_set = set(result.get("transaction_ids", []))
    result.setdefault(
        "transactions",
        [t for t in transactions if t.get("txn_id") in txn_id_set],
    )
    return result
