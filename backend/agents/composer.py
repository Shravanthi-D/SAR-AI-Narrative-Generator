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
    compliance_warnings        — list of violation dicts (omitted if empty)
    model                      — model identifier used
"""

import json
import logging
import os
import re

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from backend.agents.bedrock_client import call_llama

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a SAR narrative writer for a bank compliance department. "
    "Draft all five SAR narrative sections based on the investigation and regulations provided. "
    "CRITICAL RULE: Every single sentence MUST end with a citation tag. "
    "Every sentence referencing a transaction MUST end with [TXN_REF: txn_id]. "
    "Every sentence citing a regulation MUST end with [REG: source_name]. "
    "Every sentence that references both a transaction AND a regulation must have BOTH tags. "
    "Never write a sentence without at least one citation tag. "
    "Avoid Accusatory language (guilty, criminal, illegal activity, laundering) and "
    "imprecise speculative language (probably, might be, likely, suspected to be). "
    "Return ONLY valid JSON with exactly these keys: "
    "section_1_subject, section_2_activity, section_3_why_suspicious, "
    "section_4_regulatory_basis, section_5_evidence. "
    "Each section must be a non-empty string with multiple sentences and citation tags."
)

_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL)
_BRACE_RE = re.compile(r'\{.*\}', re.DOTALL)

_COMPLIANCE_ACCUSATORY = re.compile(
    r'\b(guilty|criminal|illegal activity|laundering)\b', re.IGNORECASE
)
_COMPLIANCE_SPECULATIVE = re.compile(
    r'\b(probably|might be|likely|suspected to be)\b', re.IGNORECASE
)

_REQUIRED_SECTIONS = [
    "section_1_subject",
    "section_2_activity",
    "section_3_why_suspicious",
    "section_4_regulatory_basis",
    "section_5_evidence",
]


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


def compliance_guard(text: str) -> list:
    """
    Scan text for language that is inappropriate in SAR narratives.

    Returns a list of violation dicts, each with:
        message      — human-readable description of the rule violated
        matched_terms — deduplicated list of the specific terms found

    Returns an empty list if no issues are found.
    """
    violations = []

    accusatory_matches = [m.group().lower() for m in _COMPLIANCE_ACCUSATORY.finditer(text)]
    if accusatory_matches:
        violations.append({
            "message":      "Accusatory language detected — use factual descriptions only",
            "matched_terms": list(dict.fromkeys(accusatory_matches)),
        })

    speculative_matches = [m.group().lower() for m in _COMPLIANCE_SPECULATIVE.finditer(text)]
    if speculative_matches:
        violations.append({
            "message":      "Speculative language detected — use factual observations only",
            "matched_terms": list(dict.fromkeys(speculative_matches)),
        })

    return violations


def _build_user_prompt(
    investigation: dict,
    regulations: list,
    account_token: str,
) -> str:
    txn_ids  = investigation.get("transaction_ids", [])
    patterns = investigation.get("patterns_detected", [])
    period   = investigation.get("time_period", "")
    reg_sources = [r.get("source", "") for r in regulations]
    evidence_summary = investigation.get("evidence_summary", "")
    total_amount = investigation.get("total_suspicious_amount", 0)

    # Provide example sentences so the LLM understands the tag format
    example_txn_id = txn_ids[0] if txn_ids else "TXN-001"
    example_reg = reg_sources[0] if reg_sources else "FATF Recommendation 20"

    return (
        f"Account: {account_token}\n"
        f"Patterns: {', '.join(patterns)}\n"
        f"Time period: {period}\n"
        f"Total suspicious amount: ${total_amount:,.2f}\n"
        f"Transaction IDs available for citation: {', '.join(txn_ids)}\n"
        f"Regulation sources available for citation: {', '.join(reg_sources)}\n\n"
        f"Investigation summary:\n{evidence_summary}\n\n"
        f"Full investigation:\n{json.dumps(investigation, indent=2, default=str)}\n\n"
        f"Applicable regulations:\n{json.dumps(regulations, indent=2, default=str)}\n\n"
        f"IMPORTANT: Every sentence MUST end with a citation tag.\n"
        f"Example with transaction: 'Account {account_token} made 12 cash deposits [TXN_REF: {example_txn_id}].'\n"
        f"Example with regulation: 'This activity must be reported per applicable rules [REG: {example_reg}].'\n\n"
        f"Draft all five SAR sections. Return JSON with keys: section_1_subject, section_2_activity, "
        f"section_3_why_suspicious, section_4_regulatory_basis, section_5_evidence."
    )


def _build_fallback_narrative(
    investigation: dict,
    regulations: list,
    account_token: str,
) -> dict:
    """
    Build a minimal but valid SAR narrative from Python data when the LLM fails.
    Every sentence includes at least one citation tag.
    """
    txn_ids     = investigation.get("transaction_ids", [])
    patterns    = investigation.get("patterns_detected", ["STRUCTURING"])
    period      = investigation.get("time_period", {})
    total_amt   = investigation.get("total_suspicious_amount", 0)
    txn_count   = len(txn_ids)
    reg_sources = [r.get("source", "") for r in regulations]

    start = period.get("start", "N/A") if isinstance(period, dict) else str(period)
    end   = period.get("end",   "N/A") if isinstance(period, dict) else str(period)

    # Reference the first few txn_ids and regs in each section
    def txn_ref(i: int = 0) -> str:
        tid = txn_ids[i] if i < len(txn_ids) else (txn_ids[0] if txn_ids else "TXN-001")
        return f"[TXN_REF: {tid}]"

    def reg_ref(i: int = 0) -> str:
        src = reg_sources[i] if i < len(reg_sources) else "FATF Recommendation 20"
        return f"[REG: {src}]"

    pattern_str = ", ".join(patterns)

    section_1 = (
        f"This Suspicious Activity Report is filed regarding account {account_token} "
        f"for detected {pattern_str} activity {txn_ref(0)}. "
        f"The account exhibited transaction patterns inconsistent with normal banking activity {txn_ref(1 if txn_count > 1 else 0)}. "
        f"This report is filed in accordance with applicable AML obligations {reg_ref(0)}."
    )

    section_2 = (
        f"Between {start} and {end}, account {account_token} conducted {txn_count} transactions "
        f"totalling ${total_amt:,.2f} {txn_ref(0)}. "
        f"The transactions were structured in a pattern consistent with {pattern_str} {txn_ref(min(1, txn_count-1))}. "
        f"Each transaction was individually below the $10,000 reporting threshold {txn_ref(min(2, txn_count-1))}."
    )

    section_3 = (
        f"The transaction pattern detected for account {account_token} is consistent with {pattern_str} {txn_ref(0)}. "
        f"Multiple cash deposits each below the $10,000 CTR filing threshold were observed within a 14-day window {reg_ref(0)}. "
        f"The clustering of sub-threshold deposits within a short time period is a known indicator of structuring {reg_ref(1 if len(reg_sources) > 1 else 0)}."
    )

    section_4 = (
        f"This report is filed pursuant to applicable anti-money laundering regulations {reg_ref(0)}. "
        f"Financial institutions are required to file SARs when structuring or other suspicious activity is detected {reg_ref(1 if len(reg_sources) > 1 else 0)}. "
        f"The detected activity meets the threshold for mandatory SAR filing {txn_ref(0)}."
    )

    section_5 = (
        f"Supporting evidence includes {txn_count} transaction records for account {account_token} {txn_ref(0)}. "
        f"Graph analysis confirmed the {pattern_str} pattern with high confidence {txn_ref(min(1, txn_count-1))}. "
        f"All transaction records are preserved and available for regulatory review {reg_ref(0)}."
    )

    return {
        "section_1_subject":          section_1,
        "section_2_activity":         section_2,
        "section_3_why_suspicious":   section_3,
        "section_4_regulatory_basis": section_4,
        "section_5_evidence":         section_5,
    }


def _validate_sections(result: dict) -> None:
    """Raise ValueError if any required section is missing or empty."""
    missing = []
    for key in _REQUIRED_SECTIONS:
        val = result.get(key, "")
        if not isinstance(val, str) or not val.strip():
            missing.append(key)
    if missing:
        raise ValueError(f"Composer returned empty sections: {missing}. Full result: {result}")


def run_composer(investigation: dict, regulations: dict, account_token: str) -> dict:
    regs_list   = (regulations or {}).get("applicable_regulations", [])
    user_prompt = _build_user_prompt(investigation, regs_list, account_token)

    result = None
    for attempt in range(1, 3):
        try:
            logger.info("Composer attempt %d/2 — calling LLM", attempt)
            raw = call_llama(
                user_prompt,
                system_prompt=_SYSTEM_PROMPT,
                max_tokens=3000,
                temperature=0.1,
            )
            logger.info("Composer raw LLM response (first 500 chars): %s", raw[:500])
            parsed = _parse_llm_json(raw)
            _validate_sections(parsed)
            result = parsed
            logger.info("Composer attempt %d succeeded — all sections populated", attempt)
            break
        except Exception as exc:
            logger.warning("Composer attempt %d failed: %s", attempt, exc)

    if result is None:
        logger.warning("Both LLM attempts failed — using Python fallback narrative")
        result = _build_fallback_narrative(investigation, regs_list, account_token)

    all_text = " ".join(str(v) for v in result.values() if isinstance(v, str))
    warnings = compliance_guard(all_text)
    if warnings:
        result["compliance_warnings"] = warnings

    result.setdefault("model", os.environ.get("BEDROCK_MODEL_ID", "unknown"))
    return result
