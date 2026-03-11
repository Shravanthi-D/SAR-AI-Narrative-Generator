import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

FAKE_ACCOUNT_TOKEN = "ACC_TEST_001"
FAKE_TRANSACTIONS = [
    {"txn_id": "TXN-001", "amount": 9500.00, "txn_type": "CASH_DEPOSIT"},
    {"txn_id": "TXN-002", "amount": 9800.00, "txn_type": "CASH_DEPOSIT"},
]

FAKE_INVESTIGATION = {
    "status": "SUSPICIOUS",
    "primary_concern": "STRUCTURING",
    "evidence_summary": "Multiple cash deposits just below $10,000 threshold.",
    "transaction_ids": ["TXN-001", "TXN-002"],
    "transactions": [
        {"txn_id": "TXN-001", "amount": 9500.00, "txn_type": "CASH_DEPOSIT"},
        {"txn_id": "TXN-002", "amount": 9800.00, "txn_type": "CASH_DEPOSIT"},
    ],
}

FAKE_REGULATIONS = {
    "applicable_regulations": [
        {
            "source": "FATF Recommendation 29",
            "relevant_excerpt": "Financial institutions should report suspicious transactions.",
        },
        {
            "source": "PMLA Section 12",
            "relevant_excerpt": "Reporting entities shall maintain records of all transactions.",
        },
    ]
}

FAKE_NARRATIVE = {
    "model": "llama3-test",
    "section_1_subject": (
        "The subject account ACC_TEST_001 made two cash deposits of $9,500 and $9,800. "
        "[TXN_REF: TXN-001] This pattern is consistent with structuring. [TXN_REF: TXN-002]"
    ),
    "section_2_suspicious_activity": (
        "The activity violates FATF guidelines. [REG: FATF Recommendation 29] "
        "Domestic reporting obligations also apply. [REG: PMLA Section 12]"
    ),
    "section_3_law_enforcement": "No prior law enforcement contact on file.",
    "section_4_contact": "SAR filed by compliance officer.",
    "section_5_narrative": "Transactions flagged by automated monitoring system.",
}

FAKE_LINEAGE = [
    {
        "id": "mock-uuid",
        "sentence_index": 0,
        "sentence_text": "The subject account made deposits.",
        "section": "section_1_subject",
        "transactions": [],
        "regulations": [],
        "agent_meta": {"model": "llama3-test", "section": "section_1_subject",
                       "cited_txns": [], "cited_regs": []},
    }
]


@patch("backend.orchestrator.OpenSearch")
@patch("backend.orchestrator.build_lineage_map", return_value=FAKE_LINEAGE)
@patch("backend.orchestrator.run_composer", return_value=FAKE_NARRATIVE)
@patch("backend.orchestrator.run_oracle", return_value=FAKE_REGULATIONS)
@patch("backend.orchestrator.run_investigator", return_value=FAKE_INVESTIGATION)
def test_full_pipeline_happy_path(
    mock_investigator, mock_oracle, mock_composer, mock_lineage, mock_opensearch
):
    from backend.orchestrator import run_sar_pipeline

    result = run_sar_pipeline("CASE-001", FAKE_ACCOUNT_TOKEN, FAKE_TRANSACTIONS)

    assert result["status"] == "LINEAGE_COMPLETE", (
        f"Expected LINEAGE_COMPLETE, got {result['status']}. error={result.get('error')}"
    )
    assert result["narrative"] is not None, "narrative should not be None"
    assert result["narrative"] == FAKE_NARRATIVE
    assert result["lineage"] == FAKE_LINEAGE

    mock_investigator.assert_called_once_with(FAKE_ACCOUNT_TOKEN, FAKE_TRANSACTIONS)
    mock_oracle.assert_called_once()
    mock_composer.assert_called_once()
    mock_lineage.assert_called_once()


@patch("backend.orchestrator.OpenSearch")
@patch("backend.orchestrator.build_lineage_map")
@patch("backend.orchestrator.run_composer")
@patch("backend.orchestrator.run_oracle")
@patch(
    "backend.orchestrator.run_investigator",
    return_value={"status": "NO_SUSPICIOUS_ACTIVITY", "findings": []},
)
def test_pipeline_exits_early_on_no_suspicious_activity(
    mock_investigator, mock_oracle, mock_composer, mock_lineage, mock_opensearch
):
    from backend.orchestrator import run_sar_pipeline

    result = run_sar_pipeline("CASE-002", FAKE_ACCOUNT_TOKEN, FAKE_TRANSACTIONS)

    assert result["status"] == "NO_SUSPICIOUS_ACTIVITY", (
        f"Expected NO_SUSPICIOUS_ACTIVITY for early exit, got {result['status']}"
    )
    assert result["narrative"] is None, "narrative should be None for clean exit"
    assert result["regulations"] is None, "regulations should be None for clean exit"

    mock_oracle.assert_not_called()
    mock_composer.assert_not_called()
    mock_lineage.assert_not_called()
