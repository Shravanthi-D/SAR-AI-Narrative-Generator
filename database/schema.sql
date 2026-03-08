CREATE TABLE sar_cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id        TEXT NOT NULL UNIQUE,
    customer_token  TEXT NOT NULL,
    account_token   TEXT NOT NULL,
    status          TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING','DRAFT','REVIEW','APPROVED','FILED')),
    risk_score      FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sar_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID REFERENCES sar_cases(id),
    version         INTEGER NOT NULL DEFAULT 1,
    content         JSONB NOT NULL,
    generated_by    TEXT DEFAULT 'AI',
    is_final        BOOLEAN DEFAULT FALSE,
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ,
    blockchain_hash TEXT,
    blockchain_txn  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pii_vault (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token       TEXT NOT NULL UNIQUE,
    real_value  TEXT NOT NULL,
    field_type  TEXT NOT NULL CHECK (field_type IN ('NAME','ACCOUNT','PHONE','EMAIL','ID','ADDRESS')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sentence_lineage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID REFERENCES sar_reports(id),
    sentence_index  INTEGER NOT NULL,
    sentence_text   TEXT NOT NULL,
    transactions    JSONB NOT NULL,
    regulations     JSONB NOT NULL,
    agent_meta      JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    txn_id          TEXT PRIMARY KEY,
    account_token   TEXT NOT NULL,
    amount          DECIMAL(15,2) NOT NULL,
    txn_type        TEXT NOT NULL,
    counterparty    TEXT,
    txn_timestamp   TIMESTAMPTZ NOT NULL,
    channel         TEXT,
    flagged         BOOLEAN DEFAULT FALSE,
    raw_data        JSONB
);

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT,
    action      TEXT NOT NULL,
    entity_type TEXT,
    entity_id   TEXT,
    details     JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_txns_account ON transactions(account_token);
CREATE INDEX idx_txns_timestamp ON transactions(txn_timestamp);
CREATE INDEX idx_lineage_report ON sentence_lineage(report_id);
CREATE INDEX idx_reports_case ON sar_reports(case_id);
