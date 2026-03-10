import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0")

from backend.agents.composer import (
    _build_user_prompt,
    _parse_llm_json,
    compliance_guard,
    run_composer,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_INVESTIGATION = {
    "account": "ACC_001",
    "patterns_detected": ["STRUCTURING"],
    "primary_concern": "Repeated sub-threshold cash deposits indicate activity consistent with structuring.",
    "evidence_summary": "12 cash deposits between $9,000 and $9,900 were recorded within a 14-day window.",
    "total_suspicious_amount": 114000.00,
    "time_period": "2024-01-01 to 2024-01-12",
    "transaction_ids": ["TXN_000", "TXN_001", "TXN_002"],
}

SAMPLE_REGULATIONS = {
    "applicable_regulations": [
        {
            "source": "FATF Recommendation 29",
            "summary": "Requires filing of suspicious transaction reports with the FIU.",
            "relevant_excerpt": "Financial institutions should report suspicious transactions.",
        },
        {
            "source": "PMLA Section 12",
            "summary": "Mandates record-keeping of transactions above prescribed threshold.",
            "relevant_excerpt": "Every banking company shall maintain records.",
        },
    ],
    "reporting_obligation": "File SAR within 7 days.",
    "regulatory_basis_summary": "Both FATF and PMLA require this filing.",
}

GOOD_LLM_RESPONSE = {
    "section_1_subject": (
        "Account ACC_001 is the subject of this report for the period 2024-01-01 to 2024-01-12."
    ),
    "section_2_activity": (
        "The account received 12 cash deposits each below $10,000 [TXN_REF: TXN_000]. "
        "Deposit amounts ranged from $9,000 to $9,900 [TXN_REF: TXN_001]. "
        "All deposits occurred within a 14-day window [TXN_REF: TXN_002]."
    ),
    "section_3_why_suspicious": (
        "The pattern of deposits is consistent with structuring activity [TXN_REF: TXN_000]. "
        "The amounts are clustered just below the $10,000 CTR threshold."
    ),
    "section_4_regulatory_basis": (
        "This report is filed pursuant to FATF Recommendation 29 [REG: FATF Recommendation 29] "
        "and PMLA Section 12 [REG: PMLA Section 12]."
    ),
    "section_5_evidence": (
        "- TXN_000: $9,500 cash deposit on 2024-01-01\n"
        "- TXN_001: $9,800 cash deposit on 2024-01-02\n"
        "- TXN_002: $9,200 cash deposit on 2024-01-03"
    ),
}


# ---------------------------------------------------------------------------
# compliance_guard
# ---------------------------------------------------------------------------

class TestComplianceGuard:
    def test_clean_text_returns_no_violations(self):
        text = (
            "The account received multiple cash deposits consistent with structuring activity. "
            "Each deposit was below the $10,000 reporting threshold."
        )
        assert compliance_guard(text) == []

    def test_flags_guilty(self):
        violations = compliance_guard("The account holder is guilty of fraud.")
        assert len(violations) > 0
        messages = [v["message"] for v in violations]
        assert any("Accusatory" in m for m in messages)

    def test_flags_criminal(self):
        violations = compliance_guard("This is criminal behaviour.")
        assert len(violations) > 0

    def test_flags_illegal_activity(self):
        violations = compliance_guard("The transactions show illegal activity.")
        assert len(violations) > 0

    def test_flags_laundering(self):
        violations = compliance_guard("This appears to be laundering.")
        assert len(violations) > 0

    def test_flags_probably(self):
        violations = compliance_guard("The customer probably moved funds offshore.")
        assert len(violations) > 0
        messages = [v["message"] for v in violations]
        assert any("Speculative" in m for m in messages)

    def test_flags_might_be(self):
        violations = compliance_guard("This might be an attempt to evade reporting.")
        assert len(violations) > 0

    def test_flags_likely(self):
        violations = compliance_guard("The deposits are likely structured to avoid CTR.")
        assert len(violations) > 0

    def test_flags_suspected_to_be(self):
        violations = compliance_guard("The account is suspected to be involved.")
        assert len(violations) > 0

    def test_case_insensitive_accusatory(self):
        violations = compliance_guard("The customer is GUILTY of this offense.")
        assert len(violations) > 0

    def test_case_insensitive_speculative(self):
        violations = compliance_guard("This is LIKELY a violation.")
        assert len(violations) > 0

    def test_both_rule_types_flagged_simultaneously(self):
        violations = compliance_guard("The customer is guilty and probably laundering funds.")
        messages = [v["message"] for v in violations]
        assert any("Accusatory" in m for m in messages)
        assert any("Speculative" in m for m in messages)

    def test_violation_contains_matched_terms(self):
        violations = compliance_guard("The customer is guilty.")
        assert len(violations) == 1
        assert "guilty" in violations[0]["matched_terms"]

    def test_duplicate_terms_deduplicated_in_matched_terms(self):
        violations = compliance_guard("guilty guilty guilty")
        assert violations[0]["matched_terms"].count("guilty") == 1

    def test_injected_guilty_returns_non_empty_list(self):
        text = "The account holder is guilty of structuring deposits."
        result = compliance_guard(text)
        assert result != [], "Expected compliance_guard to return violations for 'guilty'"


# ---------------------------------------------------------------------------
# _parse_llm_json
# ---------------------------------------------------------------------------

class TestParseLlmJson:
    def test_parses_clean_json(self):
        result = _parse_llm_json(json.dumps(GOOD_LLM_RESPONSE))
        assert "section_1_subject" in result

    def test_parses_json_markdown_fence(self):
        raw = f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert "section_2_activity" in result

    def test_parses_plain_markdown_fence(self):
        raw = f"```\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert "section_5_evidence" in result

    def test_raises_on_garbage_response(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("Here is your SAR narrative in plain English.")

    def test_raises_when_fence_content_invalid(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("```json\nnot valid json\n```")


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_contains_account_token(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "ACC_001" in prompt

    def test_contains_pattern(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "STRUCTURING" in prompt

    def test_contains_regulation_source(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "FATF Recommendation 29" in prompt

    def test_contains_transaction_ids(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "TXN_000" in prompt

    def test_contains_time_period(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "2024-01-01 to 2024-01-12" in prompt

    def test_lists_all_five_section_keys(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        for key in ["section_1_subject", "section_2_activity", "section_3_why_suspicious",
                    "section_4_regulatory_basis", "section_5_evidence"]:
            assert key in prompt, f"Section key '{key}' missing from prompt"

    def test_mentions_txn_ref_citation_format(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "TXN_REF" in prompt

    def test_mentions_reg_citation_format(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS["applicable_regulations"], "ACC_001")
        assert "[REG:" in prompt

    def test_empty_regulations_does_not_crash(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, [], "ACC_001")
        assert "ACC_001" in prompt


# ---------------------------------------------------------------------------
# run_composer
# ---------------------------------------------------------------------------

class TestRunComposer:
    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_returns_all_five_sections(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        for key in ["section_1_subject", "section_2_activity", "section_3_why_suspicious",
                    "section_4_regulatory_basis", "section_5_evidence"]:
            assert key in result, f"Section '{key}' missing from result"

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_no_compliance_warnings_on_clean_output(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert "compliance_warnings" not in result

    @patch(
        "backend.agents.composer.call_llama",
        return_value=json.dumps({
            **GOOD_LLM_RESPONSE,
            "section_3_why_suspicious": "The account holder is guilty of structuring deposits.",
        }),
    )
    def test_compliance_warnings_added_when_guilty_present(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert "compliance_warnings" in result
        assert len(result["compliance_warnings"]) > 0

    @patch(
        "backend.agents.composer.call_llama",
        return_value=json.dumps({
            **GOOD_LLM_RESPONSE,
            "section_2_activity": "The customer probably moved funds to avoid reporting.",
        }),
    )
    def test_compliance_warnings_added_for_speculative_language(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert "compliance_warnings" in result
        messages = [v["message"] for v in result["compliance_warnings"]]
        assert any("Speculative" in m for m in messages)

    @patch(
        "backend.agents.composer.call_llama",
        return_value=json.dumps({
            **GOOD_LLM_RESPONSE,
            "section_3_why_suspicious": "This is clearly criminal and illegal activity.",
        }),
    )
    def test_compliance_warnings_added_for_multiple_accusatory_terms(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert "compliance_warnings" in result
        violation = result["compliance_warnings"][0]
        assert len(violation["matched_terms"]) >= 1

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_llm_called_with_max_tokens_3000(self, mock_llm):
        run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert mock_llm.call_args.kwargs.get("max_tokens") == 3000

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_llm_called_with_temperature_0_1(self, mock_llm):
        run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert mock_llm.call_args.kwargs.get("temperature") == 0.1

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_llm_called_with_system_prompt(self, mock_llm):
        run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        system_prompt = mock_llm.call_args.kwargs.get("system_prompt", "")
        assert "SAR" in system_prompt
        assert "accusatory" in system_prompt.lower() or "Accusatory" in system_prompt

    @patch(
        "backend.agents.composer.call_llama",
        return_value=f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```",
    )
    def test_handles_markdown_fence_in_response(self, mock_llm):
        result = run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        assert "section_1_subject" in result

    @patch("backend.agents.composer.call_llama", return_value="not json at all")
    def test_raises_on_unparseable_response(self, mock_llm):
        with pytest.raises(json.JSONDecodeError):
            run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_regulations_passed_to_prompt(self, mock_llm):
        run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        user_prompt = mock_llm.call_args.args[0]
        assert "FATF Recommendation 29" in user_prompt

    @patch("backend.agents.composer.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    def test_account_token_passed_to_prompt(self, mock_llm):
        run_composer(SAMPLE_INVESTIGATION, SAMPLE_REGULATIONS, "ACC_001")
        user_prompt = mock_llm.call_args.args[0]
        assert "ACC_001" in user_prompt
