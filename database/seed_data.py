import psycopg2
import random
from datetime import datetime, timezone

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="saruser",
    password="localpassword123",
    database="sardb",
)
cur = conn.cursor()

ACCOUNT_TOKEN = "ACC_001"
transactions = []

# 12 structuring CASH_DEPOSITs spread across Jan 1-14 2024
for i in range(12):
    day = (i % 14) + 1
    hour = random.choice([9, 10, 11, 14, 15, 16, 17])
    transactions.append({
        "txn_id":        f"TXN-2024-{i+1:03d}",
        "account_token": ACCOUNT_TOKEN,
        "amount":        round(random.uniform(9000, 9900), 2),
        "txn_type":      "CASH_DEPOSIT",
        "counterparty":  None,
        "txn_timestamp": datetime(2024, 1, day, hour, random.randint(0, 59), tzinfo=timezone.utc),
        "channel":       "BRANCH",
        "flagged":       True,
        "raw_data":      None,
    })

# 38 mixed TRANSFER / WITHDRAWAL transactions
other_types = ["TRANSFER", "WITHDRAWAL"]
for i in range(38):
    idx = 12 + i + 1
    month = random.randint(1, 3)
    day   = random.randint(1, 28)
    transactions.append({
        "txn_id":        f"TXN-2024-{idx:03d}",
        "account_token": ACCOUNT_TOKEN,
        "amount":        round(random.uniform(500, 50000), 2),
        "txn_type":      random.choice(other_types),
        "counterparty":  random.choice(["ACC_VENDOR_01", "ACC_VENDOR_02", "ACC_PERSONAL_05", None]),
        "txn_timestamp": datetime(2024, month, day, random.randint(8, 20), random.randint(0, 59), tzinfo=timezone.utc),
        "channel":       random.choice(["ONLINE", "ATM", "BRANCH", "MOBILE"]),
        "flagged":       False,
        "raw_data":      None,
    })

insert_sql = """
    INSERT INTO transactions
        (txn_id, account_token, amount, txn_type, counterparty, txn_timestamp, channel, flagged, raw_data)
    VALUES
        (%(txn_id)s, %(account_token)s, %(amount)s, %(txn_type)s, %(counterparty)s,
         %(txn_timestamp)s, %(channel)s, %(flagged)s, %(raw_data)s)
    ON CONFLICT (txn_id) DO NOTHING
"""

cur.executemany(insert_sql, transactions)
conn.commit()
print(f"Inserted {cur.rowcount} transactions (skipped duplicates).")

cur.close()
conn.close()
