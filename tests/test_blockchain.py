import sys
import os
import uuid

import psycopg2
import psycopg2.extras
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.blockchain.anchor import compute_hash, verify_integrity, anchor_mock


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


def _seed_report(db_conn) -> str:
    """Insert a minimal sar_case + sar_report; return report_id str."""
    alert_id = "ALERT_BC_" + uuid.uuid4().hex[:6].upper()
    cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "INSERT INTO sar_cases (alert_id, account_token, customer_token, status) "
        "VALUES (%s, %s, %s, 'DRAFT') RETURNING id",
        (alert_id, "ACC_TEST", "ACC_TEST"),
    )
    case_id = str(cur.fetchone()["id"])

    content = {
        "sections": {
            "section_1_subject": "Test subject.",
            "section_2_activity": "Test activity.",
        },
        "status": "Pending Review",
    }
    cur.execute(
        "INSERT INTO sar_reports (case_id, version, content, generated_by) "
        "VALUES (%s, 1, %s, 'AI') RETURNING id",
        (case_id, psycopg2.extras.Json(content)),
    )
    report_id = str(cur.fetchone()["id"])
    db_conn.commit()
    cur.close()
    return report_id, content


# ─── Test 1: compute_hash is deterministic ────────────────────────────────────

def test_compute_hash_deterministic():
    content = {"a": 1, "b": "hello", "nested": {"x": True}}
    h1 = compute_hash(content)
    h2 = compute_hash(content)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


# ─── Test 2: compute_hash is sensitive to content changes ─────────────────────

def test_compute_hash_sensitive():
    original = {"section_1_subject": "Account holder identified."}
    tampered = {"section_1_subject": "Account holder identified. [TAMPERED]"}
    assert compute_hash(original) != compute_hash(tampered)


# ─── Test 3: anchor_mock writes hash + txn to DB and logs to audit_log ────────

def test_anchor_mock(db_conn):
    report_id, content = _seed_report(db_conn)
    doc_hash = compute_hash(content)

    result = anchor_mock(report_id, doc_hash, "analyst_001", db_conn)

    assert result["hash"] == doc_hash
    assert result["txn_id"].startswith("MOCK_BC_")
    assert result["mode"] == "MOCK"

    cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Hash and txn written to sar_reports
    cur.execute(
        "SELECT blockchain_hash, blockchain_txn FROM sar_reports WHERE id = %s",
        (report_id,),
    )
    row = cur.fetchone()
    assert row["blockchain_hash"] == doc_hash
    assert row["blockchain_txn"] == result["txn_id"]

    # Audit log entry created
    cur.execute(
        "SELECT action, details FROM audit_log WHERE entity_id = %s AND action = 'BLOCKCHAIN_ANCHOR'",
        (report_id,),
    )
    log = cur.fetchone()
    assert log is not None
    assert log["details"]["hash"] == doc_hash

    cur.close()


# ─── Test 4: verify_integrity returns True / False correctly ──────────────────

def test_verify_integrity():
    content = {"section_1_subject": "The account holder made repeated deposits."}
    stored_hash = compute_hash(content)

    assert verify_integrity(content, stored_hash) is True

    tampered_content = dict(content)
    tampered_content["section_1_subject"] += " [TAMPERED]"
    assert verify_integrity(tampered_content, stored_hash) is False
