import sys
import os
import json
import psycopg2
import psycopg2.extras
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.graph.loader import build_transaction_graph
from backend.graph.patterns import detect_structuring


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


def test_structuring_detected(db_conn):
    # Fetch all transactions for ACC_001
    cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM transactions WHERE account_token = %s ORDER BY txn_timestamp",
        ("ACC_001",),
    )
    transactions = [dict(row) for row in cur.fetchall()]
    cur.close()

    assert len(transactions) == 50, f"Expected 50 transactions, got {len(transactions)}"

    # Build graph
    G = build_transaction_graph(transactions)

    # Detect structuring
    finding = detect_structuring(G, "ACC_001")

    print("\n--- Structuring Finding ---")
    print(json.dumps(finding, indent=2, default=str))
    print("---------------------------\n")

    assert finding is not None, "Structuring was NOT detected — expected it to be found"
    assert finding["confidence"] > 0.7, (
        f"Expected confidence > 0.7, got {finding['confidence']}"
    )
    assert finding["pattern"] == "STRUCTURING"
    assert finding["transaction_count"] >= 3
