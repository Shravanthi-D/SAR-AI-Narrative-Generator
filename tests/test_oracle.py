import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0")

from backend.agents.oracle import (
    _build_semantic_query,
    _build_user_prompt,
    _format_chunks,
    _parse_llm_json,
    run_oracle,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_INVESTIGATION = {
    "account": "ACC_001",
    "patterns_detected": ["STRUCTURING"],
    "primary_concern": "Repeated sub-threshold cash deposits indicate deliberate structuring.",
    "evidence_summary": "12 cash deposits between $9,000 and $9,900 within 14 days.",
    "total_suspicious_amount": 114000.00,
    "time_period": "2024-01-01 to 2024-01-12",
    "transaction_ids": ["TXN_000", "TXN_001", "TXN_002"],
}

SAMPLE_CHUNKS = [
    {
        "source": "FATF Recommendation 29",
        "chunk_id": "fatf_rec29_001",
        "text": "Financial institutions should report suspicious transactions to the FIU.",
        "score": 0.95,
    },
    {
        "source": "PMLA Section 12",
        "chunk_id": "pmla_s12_001",
        "text": "Every banking company shall maintain records of transactions above the prescribed threshold.",
        "score": 0.88,
    },
]

GOOD_LLM_RESPONSE = {
    "applicable_regulations": [
        {
            "source": "FATF Recommendation 29",
            "summary": "Requires reporting of suspicious transactions to the FIU.",
            "relevant_excerpt": "Financial institutions should report suspicious transactions to the FIU.",
        },
        {
            "source": "PMLA Section 12",
            "summary": "Mandates record-keeping of transactions above threshold.",
            "relevant_excerpt": "Every banking company shall maintain records of transactions above the prescribed threshold.",
        },
    ],
    "reporting_obligation": "A SAR must be filed with the FIU within 7 days of detection.",
    "regulatory_basis_summary": "FATF Rec 29 and PMLA Section 12 both require reporting of structuring activity.",
}


# ---------------------------------------------------------------------------
# _parse_llm_json
# ---------------------------------------------------------------------------

class TestParseLlmJson:
    def test_parses_clean_json(self):
        result = _parse_llm_json(json.dumps(GOOD_LLM_RESPONSE))
        assert "applicable_regulations" in result

    def test_parses_json_markdown_fence(self):
        raw = f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert result["reporting_obligation"] == GOOD_LLM_RESPONSE["reporting_obligation"]

    def test_parses_plain_markdown_fence(self):
        raw = f"```\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert "regulatory_basis_summary" in result

    def test_raises_on_garbage_response(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("Here are the regulations you need.")

    def test_raises_when_fence_contains_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("```json\nnot valid\n```")

    def test_whitespace_inside_fence_handled(self):
        raw = f"```json\n\n  {json.dumps(GOOD_LLM_RESPONSE)}  \n\n```"
        result = _parse_llm_json(raw)
        assert len(result["applicable_regulations"]) == 2


# ---------------------------------------------------------------------------
# _build_semantic_query
# ---------------------------------------------------------------------------

class TestBuildSemanticQuery:
    def test_contains_primary_concern(self):
        query = _build_semantic_query(SAMPLE_INVESTIGATION)
        assert "sub-threshold cash deposits" in query

    def test_contains_pattern_name(self):
        query = _build_semantic_query(SAMPLE_INVESTIGATION)
        assert "STRUCTURING" in query

    def test_contains_aml_keywords(self):
        query = _build_semantic_query(SAMPLE_INVESTIGATION)
        assert "AML" in query
        assert "threshold" in query

    def test_multiple_patterns_all_included(self):
        inv = {**SAMPLE_INVESTIGATION, "patterns_detected": ["STRUCTURING", "LAYERING"]}
        query = _build_semantic_query(inv)
        assert "STRUCTURING" in query
        assert "LAYERING" in query

    def test_missing_primary_concern_does_not_crash(self):
        query = _build_semantic_query({"patterns_detected": ["STRUCTURING"]})
        assert "STRUCTURING" in query

    def test_missing_patterns_does_not_crash(self):
        query = _build_semantic_query({"primary_concern": "suspicious deposits"})
        assert "suspicious deposits" in query


# ---------------------------------------------------------------------------
# _format_chunks
# ---------------------------------------------------------------------------

class TestFormatChunks:
    def test_contains_source_label(self):
        result = _format_chunks(SAMPLE_CHUNKS)
        assert "SOURCE: FATF Recommendation 29" in result

    def test_contains_text_label(self):
        result = _format_chunks(SAMPLE_CHUNKS)
        assert "TEXT: Financial institutions should report" in result

    def test_both_chunks_present(self):
        result = _format_chunks(SAMPLE_CHUNKS)
        assert "PMLA Section 12" in result
        assert "FATF Recommendation 29" in result

    def test_empty_chunks_returns_empty_string(self):
        assert _format_chunks([]) == ""

    def test_chunks_numbered(self):
        result = _format_chunks(SAMPLE_CHUNKS)
        assert "[1]" in result
        assert "[2]" in result


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_contains_account(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, "context here")
        assert "ACC_001" in prompt

    def test_contains_pattern(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, "context here")
        assert "STRUCTURING" in prompt

    def test_contains_context(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, "FATF context text")
        assert "FATF context text" in prompt

    def test_lists_required_output_keys(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, "context")
        for key in ["applicable_regulations", "reporting_obligation", "regulatory_basis_summary"]:
            assert key in prompt, f"'{key}' missing from prompt"

    def test_applicable_regulations_subkeys_described(self):
        prompt = _build_user_prompt(SAMPLE_INVESTIGATION, "context")
        for subkey in ["source", "summary", "relevant_excerpt"]:
            assert subkey in prompt, f"Sub-key '{subkey}' not described in prompt"


# ---------------------------------------------------------------------------
# run_oracle
# ---------------------------------------------------------------------------

class TestRunOracle:
    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_returns_parsed_llm_output(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        assert "applicable_regulations" in result
        assert len(result["applicable_regulations"]) == 2

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_retrieved_chunks_added_to_result(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        assert result["retrieved_chunks"] == SAMPLE_CHUNKS

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_retrieve_called_with_top_k_5(self, mock_retrieve, mock_llm):
        os_client = MagicMock()
        run_oracle(SAMPLE_INVESTIGATION, os_client)
        call_kwargs = mock_retrieve.call_args
        assert call_kwargs.kwargs.get("top_k") == 5 or call_kwargs.args[2] == 5

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_retrieve_called_with_opensearch_client(self, mock_retrieve, mock_llm):
        os_client = MagicMock()
        run_oracle(SAMPLE_INVESTIGATION, os_client)
        args = mock_retrieve.call_args.args
        assert os_client in args

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_llm_called_with_temperature_zero(self, mock_retrieve, mock_llm):
        run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        assert mock_llm.call_args.kwargs.get("temperature") == 0.0

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_llm_called_with_correct_system_prompt(self, mock_retrieve, mock_llm):
        run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        system_prompt = mock_llm.call_args.kwargs.get("system_prompt", "")
        assert "regulatory compliance expert" in system_prompt
        assert "NEVER cite a regulation not in the context" in system_prompt

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_query_contains_primary_concern(self, mock_retrieve, mock_llm):
        run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        query_used = mock_retrieve.call_args.args[0]
        assert "sub-threshold cash deposits" in query_used

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_chunk_text_appears_in_llm_prompt(self, mock_retrieve, mock_llm):
        run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        user_prompt = mock_llm.call_args.args[0]
        assert "Financial institutions should report suspicious transactions" in user_prompt

    @patch(
        "backend.agents.oracle.call_llama",
        return_value=f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```",
    )
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_handles_markdown_fence_in_response(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        assert "applicable_regulations" in result

    @patch("backend.agents.oracle.call_llama", return_value="not json at all")
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_raises_on_completely_unparseable_response(self, mock_retrieve, mock_llm):
        with pytest.raises(json.JSONDecodeError):
            run_oracle(SAMPLE_INVESTIGATION, MagicMock())

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_result_has_all_required_keys(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        for key in ["applicable_regulations", "reporting_obligation",
                    "regulatory_basis_summary", "retrieved_chunks"]:
            assert key in result, f"Key '{key}' missing from result"

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_applicable_regulations_is_list(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        assert isinstance(result["applicable_regulations"], list)

    @patch("backend.agents.oracle.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.oracle.retrieve_regulations", return_value=SAMPLE_CHUNKS)
    def test_each_regulation_has_required_subkeys(self, mock_retrieve, mock_llm):
        result = run_oracle(SAMPLE_INVESTIGATION, MagicMock())
        for reg in result["applicable_regulations"]:
            for subkey in ["source", "summary", "relevant_excerpt"]:
                assert subkey in reg, f"Sub-key '{subkey}' missing from regulation entry"
