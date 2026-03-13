"""
Agent 3 — Narrative Composer

Receives investigator findings and regulatory citations, then drafts the five
sections of the SAR narrative.  Every sentence that references a transaction
must end with [TXN_REF: txn_id] and every sentence citing a regulation must
end with [REG: source_name].

Input:
    investigation (dict): output from Agent 1
    regulations   (dict): output from Agent 2
    account_token (str):  masked account identifier

Output dict keys:
    section_1_subject          — subject identification paragraph
    section_2_activity         — description of the activity observed
    section_3_why_suspicious   — explanation of why the activity is suspicious
    section_4_regulatory_basis — applicable regulations and reporting obligations
    section_5_evidence         — supporting evidence and transaction references
    compliance_warnings        — list of flagged language issues (omitted if empty)
    model                      — model identifier used
"""

import os
import re
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama


_COMPLIANCE_DEFINITIVE = re.compile(
    r'\b(guilty|criminal|illegal activity|laundering)\b', re.IGNORECASE
)
_COMPLIANCE_HEDGE = re.compile(
    r'\b(probably|might be|likely|suspected to be)\b', re.IGNORECASE
)

_SYSTEM_PROMPT = (
    "You are a SAR narrative writer for a bank compliance department. "
    "Draft all five SAR narrative sections based on the investigation and regulations provided. "
    "Tag each sentence referencing a transaction with [TXN_REF: txn_id] and each sentence "
    "citing a regulation with [REG: source_name]. "
    "Return ONLY valid JSON with exactly these keys: "
    "section_1_subject, section_2_activity, section_3_why_suspicious, "
    "section_4_regulatory_basis, section_5_evidence."
)


def compliance_guard(text: str) -> list:
    """
    Scans text for language that is inappropriate in SAR narratives.

    Flags:
        - Definitive guilt language: guilty, criminal, illegal activity, laundering
        - Imprecise hedging: probably, might be, likely, suspected to be

    Returns:
        list of warning strings, empty if no issues found.
    """
    warnings = []
    for match in _COMPLIANCE_DEFINITIVE.finditer(text):
        warnings.append(
            f"Definitive guilt language: '{match.group()}' at char {match.start()}"
        )
    for match in _COMPLIANCE_HEDGE.finditer(text):
        warnings.append(
            f"Imprecise hedging language: '{match.group()}' at char {match.start()}"
        )
    return warnings


def _strip_markdown_fences(text: str) -> str:
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def run_composer(investigation: dict, regulations: dict, account_token: str) -> dict:
    user_message = (
        f"Account: {account_token}\n\n"
        f"Investigation:\n{json.dumps(investigation, indent=2, default=str)}\n\n"
        f"Regulations:\n{json.dumps(regulations, indent=2, default=str)}"
    )

    try:
        raw = call_llama(user_message, _SYSTEM_PROMPT, max_tokens=2048)
        result = json.loads(_strip_markdown_fences(raw))
    except json.JSONDecodeError:
        concern = (investigation or {}).get("primary_concern", "suspicious activity")
        summary = (investigation or {}).get("evidence_summary", "")
        txn_ids = (investigation or {}).get("transaction_ids", [])
        regs = [
            r.get("source", "")
            for r in (regulations or {}).get("applicable_regulations", [])
        ]
        result = {
            "section_1_subject": (
                f"The subject account {account_token} is reported for {concern}."
            ),
            "section_2_activity": summary,
            "section_3_why_suspicious": (
                f"The transaction pattern matches known {concern} typologies. "
                + " ".join(f"[TXN_REF: {tid}]" for tid in txn_ids)
            ),
            "section_4_regulatory_basis": " ".join(
                f"This activity falls under [REG: {r}]." for r in regs
            ),
            "section_5_evidence": (
                f"Graph analysis detected {len(txn_ids)} suspicious transactions."
            ),
        }

    all_text = " ".join(str(v) for v in result.values() if isinstance(v, str))
    warnings = compliance_guard(all_text)
    if warnings:
        result["compliance_warnings"] = warnings

    result.setdefault("model", os.environ.get("BEDROCK_MODEL_ID", "unknown"))
    return result
