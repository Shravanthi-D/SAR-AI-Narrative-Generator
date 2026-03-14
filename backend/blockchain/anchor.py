"""
Blockchain anchoring module for the SAR system.

In mock mode (BLOCKCHAIN_MOCK=true, the default) a transaction ID is generated
locally and the hash + txn are stored in sar_reports / audit_log.

In real mode (BLOCKCHAIN_MOCK=false) the hash is submitted to a Hyperledger
Fabric REST gateway at FABRIC_GATEWAY_URL.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone

import psycopg2.extras
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


# ─── Hashing ──────────────────────────────────────────────────────────────────

def compute_hash(sar_content: dict) -> str:
    """
    Compute a deterministic SHA-256 hash of a SAR content dict.

    Uses json.dumps with sort_keys=True and default=str so the output is
    canonical regardless of key insertion order or non-serialisable values.

    Returns:
        64-character lowercase hex digest string.
    """
    canonical = json.dumps(sar_content, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_integrity(sar_content: dict, stored_hash: str) -> bool:
    """
    Recompute the hash of sar_content and compare it to stored_hash.

    Returns:
        True  — content matches the stored hash (untampered).
        False — mismatch detected (content has been altered).
    """
    return compute_hash(sar_content) == stored_hash


# ─── Mock mode ────────────────────────────────────────────────────────────────

def anchor_mock(report_id: str, doc_hash: str, analyst_id: str, db_conn) -> dict:
    """
    Mock blockchain anchor for demo / hackathon use.

    Generates a deterministic-looking transaction ID, writes the hash and
    txn to sar_reports, and logs the event in audit_log.

    Returns:
        {"txn_id": str, "hash": str, "mode": "MOCK"}
    """
    txn_id = "MOCK_BC_" + uuid.uuid4().hex[:8].upper()
    anchored_at = datetime.now(timezone.utc).isoformat()

    cur = db_conn.cursor()

    cur.execute(
        """
        UPDATE sar_reports
        SET blockchain_hash = %s,
            blockchain_txn  = %s
        WHERE id = %s
        """,
        (doc_hash, txn_id, report_id),
    )

    cur.execute(
        """
        INSERT INTO audit_log (user_id, action, entity_type, entity_id, details)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            analyst_id,
            "BLOCKCHAIN_ANCHOR",
            "SAR_REPORT",
            report_id,
            psycopg2.extras.Json({
                "hash":        doc_hash,
                "txn_id":      txn_id,
                "anchored_at": anchored_at,
                "mode":        "MOCK",
            }),
        ),
    )

    db_conn.commit()
    cur.close()

    return {"txn_id": txn_id, "hash": doc_hash, "mode": "MOCK"}


# ─── Real Hyperledger Fabric mode ─────────────────────────────────────────────

def anchor_hyperledger(report_id: str, doc_hash: str, analyst_id: str) -> dict:
    """
    Submit a SAR hash to a Hyperledger Fabric REST gateway.

    Reads FABRIC_GATEWAY_URL from the environment.  Raises if not set.

    Returns:
        Response JSON from the gateway: {txn_id, block_number, timestamp}
    """
    gateway_url = os.environ.get("FABRIC_GATEWAY_URL")
    if not gateway_url:
        raise EnvironmentError(
            "FABRIC_GATEWAY_URL is not set. "
            "Set it in .env or use BLOCKCHAIN_MOCK=true for demo mode."
        )

    payload = {
        "reportId":  report_id,
        "docHash":   doc_hash,
        "analystId": analyst_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    response = requests.post(
        gateway_url.rstrip("/") + "/api/sar/anchor",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# ─── Main entry point ─────────────────────────────────────────────────────────

def anchor_report(
    report_id: str,
    sar_content: dict,
    analyst_id: str,
    db_conn,
) -> dict:
    """
    Anchor a SAR report to the blockchain after analyst approval.

    Reads BLOCKCHAIN_MOCK env var (default "true").
    - "true"  → anchor_mock (local, no external dependency)
    - "false" → anchor_hyperledger (real Fabric gateway)

    Always computes the hash first with compute_hash().

    Returns:
        dict with at minimum: hash, txn_id, mode
    """
    doc_hash   = compute_hash(sar_content)
    use_mock   = os.environ.get("BLOCKCHAIN_MOCK", "true").lower() != "false"

    if use_mock:
        return anchor_mock(report_id, doc_hash, analyst_id, db_conn)
    else:
        result = anchor_hyperledger(report_id, doc_hash, analyst_id)
        result["hash"] = doc_hash
        return result


# ─── Tamper demo (jury demonstration only) ────────────────────────────────────

def tamper_demo(report_id: str, db_conn) -> dict:
    """
    Demonstrate tamper detection for the jury.

    Appends " [TAMPERED]" to section_1_subject in the stored content
    WITHOUT updating blockchain_hash, so verify_integrity() will return False.

    Returns:
        {"tampered": True, "report_id": report_id}
    """
    cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "SELECT content FROM sar_reports WHERE id = %s",
        (report_id,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        raise ValueError(f"Report {report_id} not found")

    content = dict(row["content"] or {})
    sections = dict(content.get("sections", {}))
    sections["section_1_subject"] = sections.get("section_1_subject", "") + " [TAMPERED]"
    content["sections"] = sections

    cur.execute(
        "UPDATE sar_reports SET content = %s WHERE id = %s",
        (psycopg2.extras.Json(content), report_id),
    )
    db_conn.commit()
    cur.close()

    return {"tampered": True, "report_id": report_id}
