import sys
import os
import json
import psycopg2
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ensure PII_ENCRYPTION_KEY is available for tests
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.pii.masker import mask_transaction


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


def test_pii_masking(db_conn):
    txn = {
        "txn_id":          "TXN-TEST-001",
        "customer_name":   "Rajesh Kumar",
        "account_number":  "4532123456789012",
        "phone":           "9876543210",
        "email":           "rajesh@example.com",
        "amount":          9500.00,
        "txn_type":        "CASH_DEPOSIT",
    }

    masked = mask_transaction(txn, db_conn)
    masked_str = json.dumps(masked)

    # Real PII must not appear anywhere in the masked output
    assert "Rajesh" not in masked_str, "Customer name leaked into masked output"
    assert "4532" not in masked_str, "Account number leaked into masked output"

    # Token for customer_name must start with NAME_
    assert masked["customer_name"].startswith("NAME_"), (
        f"Expected NAME_ token, got: {masked['customer_name']}"
    )

    print("Masked output:", json.dumps(masked, indent=2))
