import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0")

from backend.agents.investigator import _build_user_prompt, _parse_llm_json, run_investigator

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_structuring_transactions(account_token: str = "ACC_001", count: int = 12):
    base = datetime(2024, 1, 1)
    txns = []
    for i in range(count):
        txns.append({
            "txn_id": f"TXN_{i:03d}",
            "account_token": account_token,
            "txn_type": "CASH_DEPOSIT",
            "amount": 9500.00,
            "txn_timestamp": base + timedelta(days=i),
            "counterparty": None,
        })
    return txns


GOOD_LLM_RESPONSE = {
    "account": "ACC_001",
    "patterns_detected": ["STRUCTURING"],
    "primary_concern": "Repeated sub-threshold cash deposits indicate deliberate structuring.",
    "evidence_summary": "12 cash deposits between $9,000 and $9,900 were made within 14 days.",
    "total_suspicious_amount": 114000.00,
    "time_period": "2024-01-01 to 2024-01-12",
    "transaction_ids": [f"TXN_{i:03d}" for i in range(12)],
}


# ---------------------------------------------------------------------------
# _parse_llm_json
# ---------------------------------------------------------------------------

class TestParseLlmJson:
    def test_parses_clean_json(self):
        raw = json.dumps(GOOD_LLM_RESPONSE)
        result = _parse_llm_json(raw)
        assert result["account"] == "ACC_001"

    def test_parses_json_markdown_fence(self):
        raw = f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert result["patterns_detected"] == ["STRUCTURING"]

    def test_parses_plain_markdown_fence(self):
        raw = f"```\n{json.dumps(GOOD_LLM_RESPONSE)}\n```"
        result = _parse_llm_json(raw)
        assert result["total_suspicious_amount"] == 114000.00

    def test_raises_on_unparseable_response(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("This is not JSON at all.")

    def test_raises_when_fence_content_is_invalid(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("```json\nnot valid json\n```")

    def test_parses_json_with_leading_whitespace_in_fence(self):
        raw = f"```json\n\n  {json.dumps(GOOD_LLM_RESPONSE)}  \n```"
        result = _parse_llm_json(raw)
        assert "transaction_ids" in result


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_contains_account_token(self):
        txns = _make_structuring_transactions()
        findings = [{"pattern": "STRUCTURING", "transactions": ["TXN_000"], "total_amount": 9500}]
        prompt = _build_user_prompt("ACC_001", findings, txns)
        assert "ACC_001" in prompt

    def test_contains_findings_json(self):
        txns = _make_structuring_transactions()
        findings = [{"pattern": "STRUCTURING", "transactions": ["TXN_000"], "total_amount": 9500}]
        prompt = _build_user_prompt("ACC_001", findings, txns)
        assert "STRUCTURING" in prompt

    def test_contains_time_period(self):
        txns = _make_structuring_transactions()
        findings = [{"pattern": "STRUCTURING", "transactions": ["TXN_000", "TXN_011"], "total_amount": 9500}]
        prompt = _build_user_prompt("ACC_001", findings, txns)
        assert "2024-01-01" in prompt

    def test_time_period_unknown_when_no_matching_txns(self):
        findings = [{"pattern": "STRUCTURING", "transactions": ["TXN_999"], "total_amount": 9500}]
        prompt = _build_user_prompt("ACC_001", findings, [])
        assert "unknown" in prompt

    def test_lists_all_required_output_keys(self):
        txns = _make_structuring_transactions()
        findings = [{"pattern": "STRUCTURING", "transactions": ["TXN_000"], "total_amount": 9500}]
        prompt = _build_user_prompt("ACC_001", findings, txns)
        for key in ["account", "patterns_detected", "primary_concern",
                    "evidence_summary", "total_suspicious_amount",
                    "time_period", "transaction_ids"]:
            assert key in prompt, f"Key '{key}' missing from prompt"


# ---------------------------------------------------------------------------
# run_investigator — no suspicious activity
# ---------------------------------------------------------------------------

class TestRunInvestigatorNoFindings:
    @patch("backend.agents.investigator.run_all_detections", return_value=[])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_returns_no_suspicious_activity(self, mock_graph, mock_detections):
        result = run_investigator("ACC_CLEAN", [])
        assert result == {"status": "NO_SUSPICIOUS_ACTIVITY", "findings": []}

    @patch("backend.agents.investigator.run_all_detections", return_value=[])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_llm_not_called_when_no_findings(self, mock_graph, mock_detections):
        with patch("backend.agents.investigator.call_llama") as mock_llm:
            run_investigator("ACC_CLEAN", [])
            mock_llm.assert_not_called()

    @patch("backend.agents.investigator.run_all_detections", return_value=[])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_graph_is_built(self, mock_graph, mock_detections):
        txns = _make_structuring_transactions()
        run_investigator("ACC_001", txns)
        mock_graph.assert_called_once_with(txns)


# ---------------------------------------------------------------------------
# run_investigator — with suspicious findings
# ---------------------------------------------------------------------------

STRUCTURING_FINDING = {
    "pattern": "STRUCTURING",
    "confidence": 0.85,
    "account": "ACC_001",
    "transaction_count": 12,
    "total_amount": 114000.00,
    "transactions": [f"TXN_{i:03d}" for i in range(12)],
    "description": "12 deposits just below $10,000 within 14 days.",
}


class TestRunInvestigatorWithFindings:
    @patch("backend.agents.investigator.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_returns_parsed_llm_output(self, mock_graph, mock_detections, mock_llm):
        result = run_investigator("ACC_001", _make_structuring_transactions())
        assert result["account"] == "ACC_001"
        assert result["patterns_detected"] == ["STRUCTURING"]

    @patch("backend.agents.investigator.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_llm_called_with_temperature_zero(self, mock_graph, mock_detections, mock_llm):
        run_investigator("ACC_001", _make_structuring_transactions())
        call_kwargs = mock_llm.call_args.kwargs
        assert call_kwargs.get("temperature") == 0.0

    @patch("backend.agents.investigator.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_llm_called_with_system_prompt(self, mock_graph, mock_detections, mock_llm):
        run_investigator("ACC_001", _make_structuring_transactions())
        call_kwargs = mock_llm.call_args.kwargs
        assert "financial crime investigator" in call_kwargs.get("system_prompt", "")

    @patch("backend.agents.investigator.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_detections_called_with_graph_and_account(self, mock_graph, mock_detections, mock_llm):
        fake_graph = MagicMock()
        mock_graph.return_value = fake_graph
        run_investigator("ACC_001", _make_structuring_transactions())
        mock_detections.assert_called_once_with(fake_graph, "ACC_001")

    @patch(
        "backend.agents.investigator.call_llama",
        return_value=f"```json\n{json.dumps(GOOD_LLM_RESPONSE)}\n```",
    )
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_handles_markdown_fence_in_llm_response(self, mock_graph, mock_detections, mock_llm):
        result = run_investigator("ACC_001", _make_structuring_transactions())
        assert result["account"] == "ACC_001"

    @patch("backend.agents.investigator.call_llama", return_value="not json at all")
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_raises_on_completely_unparseable_llm_response(
        self, mock_graph, mock_detections, mock_llm
    ):
        with pytest.raises(json.JSONDecodeError):
            run_investigator("ACC_001", _make_structuring_transactions())

    @patch("backend.agents.investigator.call_llama", return_value=json.dumps(GOOD_LLM_RESPONSE))
    @patch("backend.agents.investigator.run_all_detections", return_value=[STRUCTURING_FINDING])
    @patch("backend.agents.investigator.build_transaction_graph")
    def test_result_contains_all_required_keys(self, mock_graph, mock_detections, mock_llm):
        result = run_investigator("ACC_001", _make_structuring_transactions())
        for key in ["account", "patterns_detected", "primary_concern",
                    "evidence_summary", "total_suspicious_amount",
                    "time_period", "transaction_ids"]:
            assert key in result, f"Key '{key}' missing from result"
