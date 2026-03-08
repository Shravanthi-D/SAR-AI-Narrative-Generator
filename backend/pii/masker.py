import hashlib
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

FIELD_TYPE_MAP = {
    "customer_name":        "NAME",
    "account_number":       "ACCOUNT",
    "phone":                "PHONE",
    "email":                "EMAIL",
    "counterparty_name":    "NAME",
    "counterparty_account": "ACCOUNT",
}

def _get_fernet() -> Fernet:
    key = os.environ.get("PII_ENCRYPTION_KEY")
    if not key:
        raise ValueError("PII_ENCRYPTION_KEY not set in environment")
    return Fernet(key.encode() if isinstance(key, str) else key)


def make_token(field_type: str, value: str) -> str:
    """Create a stable token like NAME_A4F2C1 from field type + value."""
    hash_hex = hashlib.sha256(value.encode()).hexdigest()[:6].upper()
    return f"{field_type}_{hash_hex}"


def mask_transaction(txn: dict, db_conn) -> dict:
    """
    Replace PII fields in a transaction dict with tokens.
    Stores token->encrypted_real_value in pii_vault.
    Returns the masked dict.
    """
    fernet = _get_fernet()
    masked = txn.copy()
    cursor = db_conn.cursor()

    for field, field_type in FIELD_TYPE_MAP.items():
        raw_value = txn.get(field)
        if not raw_value:
            continue

        token = make_token(field_type, str(raw_value))
        encrypted = fernet.encrypt(str(raw_value).encode()).decode()

        cursor.execute(
            """
            INSERT INTO pii_vault (token, real_value, field_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (token) DO NOTHING
            """,
            (token, encrypted, field_type),
        )

        masked[field] = token

    db_conn.commit()
    cursor.close()
    return masked


def mask_transactions_batch(txn_list: list, db_conn) -> list:
    """Mask a list of transactions, returning all masked dicts."""
    return [mask_transaction(txn, db_conn) for txn in txn_list]


def reveal_token(token: str, db_conn) -> str:
    """Decrypt and return the real value for a token. For final report stage only."""
    fernet = _get_fernet()
    cursor = db_conn.cursor()
    cursor.execute("SELECT real_value FROM pii_vault WHERE token = %s", (token,))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        raise KeyError(f"Token not found: {token}")
    return fernet.decrypt(row[0].encode()).decode()
