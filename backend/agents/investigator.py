import json
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama
from backend.graph.loader import build_transaction_graph
from backend.graph.patterns import run_all_detections

SYSTEM_PROMPT = (
    "You are a financial crime investigator AI. "
    "Be factual and precise. Never speculate. Respond with valid JSON only."
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


def _build_user_prompt(account_token: str, findings: list, transactions: list) -> str:
    all_suspicious_ids = []
    for f in findings:
        all_suspicious_ids.extend(f.get("transactions", []))
    suspicious_txns = [t for t in transactions if t.get("txn_id") in all_suspicious_ids]

    timestamps = [
        t["txn_timestamp"]
        for t in suspicious_txns
        if t.get("txn_timestamp") is not None
    ]
    if timestamps:
        start = min(str(ts)[:10] for ts in timestamps)
        end = max(str(ts)[:10] for ts in timestamps)
        time_period = f"{start} to {end}"
    else:
        time_period = "unknown"

    prompt = (
        f"Account under review: {account_token}\n\n"
        f"Detected patterns:\n{json.dumps(findings, indent=2, default=str)}\n\n"
        f"Time period of suspicious activity: {time_period}\n\n"
        "Produce a JSON object with exactly these keys:\n"
        "  account             — the account token string\n"
        "  patterns_detected   — list of pattern name strings (e.g. [\"STRUCTURING\"])\n"
        "  primary_concern     — one sentence describing the main concern\n"
        "  evidence_summary    — 2-4 sentences summarising the evidence\n"
        "  total_suspicious_amount — total USD amount across all suspicious transactions (number)\n"
        f"  time_period         — use exactly \"{time_period}\"\n"
        "  transaction_ids     — list of all suspicious transaction ID strings\n\n"
        "Respond with the JSON object only. No commentary, no markdown."
    )
    return prompt


def run_investigator(account_token: str, transactions: list) -> dict:
    G = build_transaction_graph(transactions)
    findings = run_all_detections(G, account_token)

    if not findings:
        return {"status": "NO_SUSPICIOUS_ACTIVITY", "findings": []}

    user_prompt = _build_user_prompt(account_token, findings, transactions)
    raw = call_llama(user_prompt, system_prompt=SYSTEM_PROMPT, temperature=0.0)
    return _parse_llm_json(raw)
