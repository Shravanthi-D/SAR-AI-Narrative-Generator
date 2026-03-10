import json
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama

SYSTEM_PROMPT = (
    "You are a SAR (Suspicious Activity Report) narrative writer for a bank compliance team. "
    "Rules you must follow without exception:\n"
    "1. Never use speculative language — do not write 'probably', 'might be', 'likely', or 'suspected to be'.\n"
    "2. Never use accusatory language — do not write 'guilty', 'criminal', 'illegal activity', or 'laundering'.\n"
    "3. Every factual claim about a transaction must end with a citation tag [TXN_REF: txn_id].\n"
    "4. Every regulatory reference must end with a citation tag [REG: source_name].\n"
    "5. Describe only observed facts — what happened, when, and how much.\n"
    "6. Return JSON only — no commentary, no markdown fences."
)

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")

_COMPLIANCE_RULES = [
    (
        re.compile(r"\b(guilty|criminal|illegal activity|laundering)\b", re.IGNORECASE),
        "Accusatory language — use 'activity consistent with...' instead",
    ),
    (
        re.compile(r"\b(probably|might be|likely|suspected to be)\b", re.IGNORECASE),
        "Speculative language — describe only observed facts",
    ),
]


def compliance_guard(text: str) -> list:
    violations = []
    for pattern, message in _COMPLIANCE_RULES:
        matches = pattern.findall(text)
        if matches:
            violations.append({"message": message, "matched_terms": list(set(m.lower() for m in matches))})
    return violations


def _parse_llm_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = _FENCE_RE.search(raw)
    if match:
        return json.loads(match.group(1))

    raise json.JSONDecodeError("No valid JSON found in LLM response", raw, 0)


def _build_user_prompt(
    investigation: dict,
    applicable_regulations: list,
    account_token: str,
) -> str:
    patterns = investigation.get("patterns_detected", [])
    primary_concern = investigation.get("primary_concern", "")
    evidence_summary = investigation.get("evidence_summary", "")
    total_amount = investigation.get("total_suspicious_amount", 0)
    time_period = investigation.get("time_period", "unknown")
    transaction_ids = investigation.get("transaction_ids", [])

    reg_lines = []
    for reg in applicable_regulations:
        reg_lines.append(
            f"  - {reg.get('source','')}: {reg.get('summary','')}"
        )
    regs_text = "\n".join(reg_lines) if reg_lines else "  (none provided)"

    txn_ids_text = ", ".join(transaction_ids) if transaction_ids else "(none)"

    return (
        f"Account token: {account_token}\n"
        f"Detected patterns: {', '.join(patterns)}\n"
        f"Primary concern: {primary_concern}\n"
        f"Evidence summary: {evidence_summary}\n"
        f"Total suspicious amount: ${total_amount:,.2f}\n"
        f"Time period: {time_period}\n"
        f"Transaction IDs: {txn_ids_text}\n\n"
        f"Applicable regulations:\n{regs_text}\n\n"
        "Write a SAR narrative as a JSON object with exactly these five keys. "
        "Every sentence that states a fact about a transaction must end with [TXN_REF: txn_id]. "
        "Every sentence that references a regulation must end with [REG: source_name].\n\n"
        "  section_1_subject        — 1-2 sentences identifying the account and reporting period\n"
        "  section_2_activity       — 3-5 sentences describing the observed transactions factually\n"
        "  section_3_why_suspicious — 2-3 sentences explaining why the activity is consistent with "
        "a reportable pattern, citing transactions\n"
        "  section_4_regulatory_basis — 1-2 sentences citing the regulations that require this filing\n"
        "  section_5_evidence       — bullet-point style string listing each key transaction ID and amount\n\n"
        "Respond with the JSON object only."
    )


def run_composer(investigation: dict, regulations: dict, account_token: str) -> dict:
    applicable_regulations = regulations.get("applicable_regulations", [])
    user_prompt = _build_user_prompt(investigation, applicable_regulations, account_token)

    raw = call_llama(
        user_prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=3000,
        temperature=0.1,
    )
    result = _parse_llm_json(raw)

    all_text = " ".join(
        str(result.get(key, ""))
        for key in [
            "section_1_subject",
            "section_2_activity",
            "section_3_why_suspicious",
            "section_4_regulatory_basis",
            "section_5_evidence",
        ]
    )
    warnings = compliance_guard(all_text)
    if warnings:
        result["compliance_warnings"] = warnings

    return result
