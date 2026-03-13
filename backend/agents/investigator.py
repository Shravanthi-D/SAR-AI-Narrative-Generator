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

import os
import re
import json
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


def _strip_markdown_fences(text: str) -> str:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def _build_fallback(account_token: str, findings: list, transactions: list) -> dict:
    all_txn_ids = []
    total_amount = 0.0
    patterns = []

    for f in findings:
        patterns.append(f["pattern"])
        all_txn_ids.extend(f.get("transactions", []))
        total_amount += f.get("total_amount", 0.0)

    txn_id_set = set(all_txn_ids)
    evidence_txns = [t for t in transactions if t.get("txn_id") in txn_id_set]

    timestamps = sorted(
        str(t.get("txn_timestamp", ""))
        for t in evidence_txns
        if t.get("txn_timestamp")
    )

    time_period = {
        "start": timestamps[0] if timestamps else "unknown",
        "end": timestamps[-1] if timestamps else "unknown",
    }

    descriptions = " ".join(f.get("description", "") for f in findings)

    return {
        "status": "SUSPICIOUS",
        "account": account_token,
        "patterns_detected": patterns,
        "primary_concern": patterns[0] if patterns else "UNKNOWN",
        "evidence_summary": descriptions,
        "total_suspicious_amount": round(total_amount, 2),
        "time_period": time_period,
        "transaction_ids": list(dict.fromkeys(all_txn_ids)),
        "transactions": evidence_txns,
    }


def run_investigator(account_token: str, transactions: list) -> dict:
    G = build_transaction_graph(transactions)
    findings = run_all_detections(G, account_token)

    if not findings:
        return {"status": "NO_SUSPICIOUS_ACTIVITY", "findings": []}

    user_message = (
        f"Account: {account_token}\n\n"
        f"Pattern findings from graph analysis:\n"
        f"{json.dumps(findings, indent=2, default=str)}\n\n"
        f"All transactions (masked):\n"
        f"{json.dumps(transactions, indent=2, default=str)}"
    )

    try:
        raw = call_llama(user_message, _SYSTEM_PROMPT, max_tokens=2048)
        result = json.loads(_strip_markdown_fences(raw))
        result.setdefault("status", "SUSPICIOUS")
        txn_id_set = set(result.get("transaction_ids", []))
        result.setdefault(
            "transactions",
            [t for t in transactions if t.get("txn_id") in txn_id_set],
        )
        return result
    except json.JSONDecodeError:
        return _build_fallback(account_token, findings, transactions)
