import sys
import os
import uuid

import psycopg2
import psycopg2.extras
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.lineage.mapper import build_lineage_map, save_lineage


@pytest.fixture
def db_conn():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="saruser",
        password="localpassword123",
        database="sardb",
    )
    yield conn
    conn.close()


# ─── Helper: seed a case + report row, return report_id string ────────────────

def _seed_report(db_conn) -> str:
    cur = db_conn.cursor()
    alert_id = f"TEST-{uuid.uuid4().hex[:10]}"
    cur.execute(
        """
        INSERT INTO sar_cases (alert_id, account_token, customer_token, status)
        VALUES (%s, 'ACC_TEST', 'CUST_TEST', 'DRAFT')
        RETURNING id
        """,
        (alert_id,),
    )
    case_id = cur.fetchone()[0]
    cur.execute(
        """
        INSERT INTO sar_reports (case_id, version, content, generated_by)
        VALUES (%s, 1, %s, 'AI')
        RETURNING id
        """,
        (case_id, psycopg2.extras.Json({"sections": {}, "status": "Pending Review"})),
    )
    report_id = str(cur.fetchone()[0])
    db_conn.commit()
    cur.close()
    return report_id


# ─── Test 1: build_lineage_map ────────────────────────────────────────────────

def test_build_lineage_map():
    narrative = {
        "section_1_subject": (
            "Account ACC_001 made a suspicious deposit. [TXN_REF: TXN-001] "
            "This activity triggers reporting obligations. [REG: FATF]"
        ),
    }
    investigation = {
        "transactions": [
            {
                "txn_id":   "TXN-001",
                "amount":   9500.0,
                "txn_type": "CASH_DEPOSIT",
                "date":     "2024-01-02",
            }
        ]
    }
    regulations = {
        "applicable_regulations": [
            {
                "source":           "FATF",
                "summary":          "FATF Recommendation 20",
                "relevant_excerpt": "Report suspicious transactions to the FIU.",
            }
        ]
    }

    records = build_lineage_map(narrative, investigation, regulations)

    assert len(records) >= 1, "Expected at least one lineage record"

    # Sentence indexes must be sequential starting from 0
    for i, rec in enumerate(records):
        assert rec["sentence_index"] == i, f"Expected sentence_index={i}, got {rec['sentence_index']}"

    # Sentence citing TXN-001 must resolve the transaction
    txn_sentence = next(
        (r for r in records if "TXN-001" in r["agent_meta"]["cited_txns"]), None
    )
    assert txn_sentence is not None, "No sentence with [TXN_REF: TXN-001] found"
    assert len(txn_sentence["transactions"]) == 1
    assert txn_sentence["transactions"][0]["txn_id"] == "TXN-001"

    # Sentence citing FATF must resolve the regulation
    reg_sentence = next(
        (r for r in records if "FATF" in r["agent_meta"]["cited_regs"]), None
    )
    assert reg_sentence is not None, "No sentence with [REG: FATF] found"
    assert len(reg_sentence["regulations"]) == 1
    assert reg_sentence["regulations"][0]["source"] == "FATF"


# ─── Test 2: save_lineage writes rows to the DB ───────────────────────────────

def test_save_lineage(db_conn):
    report_id = _seed_report(db_conn)

    records = [
        {
            "id":             str(uuid.uuid4()),
            "sentence_index": i,
            "sentence_text":  f"Test sentence {i}.",
            "section":        "section_1_subject",
            "transactions":   [{"txn_id": f"TXN-{i:03d}", "amount": 9000 + i * 100}],
            "regulations":    [{"source": "FATF", "summary": "Test regulation"}],
            "agent_meta":     {
                "model":       "test",
                "section":     "section_1_subject",
                "cited_txns":  [f"TXN-{i:03d}"],
                "cited_regs":  ["FATF"],
            },
        }
        for i in range(3)
    ]

    save_lineage(report_id, records, db_conn)

    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM sentence_lineage WHERE report_id = %s",
        (report_id,),
    )
    count = cur.fetchone()[0]
    cur.close()

    assert count == 3, f"Expected 3 lineage rows, got {count}"


# ─── Test 3: GET /api/sar/{report_id}/lineage returns the saved rows ──────────

def test_lineage_api(db_conn):
    from fastapi.testclient import TestClient
    from backend.api.main import app

    client = TestClient(app)

    report_id = _seed_report(db_conn)

    save_lineage(
        report_id,
        [
            {
                "id":             str(uuid.uuid4()),
                "sentence_index": 0,
                "sentence_text":  "Suspicious activity was observed in the account.",
                "section":        "section_1_subject",
                "transactions":   [{"txn_id": "TXN-API-001", "amount": 9500.0}],
                "regulations":    [{"source": "FATF", "summary": "Report suspicious transactions."}],
                "agent_meta":     {
                    "model":      "test",
                    "section":    "section_1_subject",
                    "cited_txns": ["TXN-API-001"],
                    "cited_regs": ["FATF"],
                },
            }
        ],
        db_conn,
    )

    response = client.get(f"/api/sar/{report_id}/lineage")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 1, f"Expected 1 lineage entry, got {len(data)}"
    assert data[0]["sentence_index"] == 0
    assert data[0]["sentence"] == "Suspicious activity was observed in the account."
    assert isinstance(data[0]["transactions"], list)
    assert isinstance(data[0]["regulations"], list)
