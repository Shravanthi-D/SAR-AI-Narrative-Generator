# SAR Narrative Generator — Project Context for Claude

## What This Project Is
A system that automatically generates Suspicious Activity Reports (SARs) for banks.
Banks are legally required to file SARs when they detect suspicious financial activity
like money laundering. Currently this takes analysts 5-6 hours per report. This system
reduces it to 30 minutes using AI.

## Current Status
- [x] Project structure created
- [x] PostgreSQL database schema created and running in Docker
- [x] Seed data inserted (50 transactions for ACC_001 with structuring pattern)
- [x] PII Masking service built and tested
- [ ] RAG pipeline (next)
- [ ] Graph analysis
- [ ] AI agents
- [ ] LangGraph orchestration
- [ ] Lineage mapping
- [ ] Blockchain anchoring
- [ ] FastAPI backend
- [ ] Streamlit frontend

## How the System Works (Read Before Writing Any Code)
Raw transaction data comes in → PII is masked → 3 AI agents process it →
SAR narrative is generated → human analyst reviews → blockchain anchors the final report.

## Tech Stack
- Language: Python
- Database: PostgreSQL 15 (running in Docker on localhost:5432)
- Vector Database: Amazon OpenSearch (running in Docker on localhost:9200)
- Graph Database: NetworkX locally (Amazon Neptune in production)
- LLM: Llama 3.1 via Amazon Bedrock
- Agent Framework: LangGraph
- API: FastAPI
- Frontend: Streamlit
- Blockchain: Mock mode locally (Hyperledger Fabric in production)

## Database
- Host: localhost
- Port: 5432
- User: saruser
- Password: localpassword123
- Database: sardb
- Tables: sar_cases, sar_reports, pii_vault, sentence_lineage, transactions, audit_log

## Environment Variables
All secrets are in .env — never hardcode credentials.
Always load using: from dotenv import load_dotenv

## Project Structure
backend/api/main.py          — FastAPI routes
backend/pii/masker.py        — PII masking (BUILT)
backend/agents/              — 3 AI agents (NOT BUILT YET)
backend/rag/                 — RAG pipeline (NOT BUILT YET)
backend/graph/               — Pattern detection (NOT BUILT YET)
backend/lineage/mapper.py    — Lineage mapping (NOT BUILT YET)
backend/blockchain/anchor.py — Blockchain anchoring (NOT BUILT YET)
backend/orchestrator.py      — LangGraph workflow (NOT BUILT YET)
frontend/app.py              — Streamlit UI (NOT BUILT YET)
database/schema.sql          — All table definitions (BUILT)
database/seed_data.py        — Test data with structuring pattern (BUILT)

## What is Already Built

### 1. Database Schema (database/schema.sql)
Six tables:
- sar_cases: one row per alert from the bank's transaction monitoring system
- sar_reports: stores SAR drafts and versions, each with full JSON content
- pii_vault: encrypted mapping of tokens to real customer data (e.g. Customer_A -> Rajesh Kumar)
- sentence_lineage: links every sentence in a SAR to the transactions that support it
- transactions: the actual financial transaction records (masked)
- audit_log: records every action taken in the system for compliance

### 2. Seed Data (database/seed_data.py)
50 fake transactions for account ACC_001.
12 of them are cash deposits between $9,000-$9,900 within a 14-day window in January 2024.
This simulates a STRUCTURING pattern — someone breaking large amounts into
sub-$10,000 deposits to avoid automatic reporting thresholds.
This is the test data the AI agents will analyse.

### 3. PII Masking Service (backend/pii/masker.py)
Sits at the entry point of the system.
Before any data reaches the AI, it strips all personal information and replaces it with tokens.
Example: "Rajesh Kumar" becomes "NAME_A4F2C1", account "4532123456789012" becomes "ACC_3B9F12"
The real values are encrypted using Fernet (AES-128) and stored in the pii_vault table.
Functions available:
- mask_transaction(txn, db_conn) — masks one transaction dict
- mask_transactions_batch(txn_list, db_conn) — masks a list of transactions
- reveal_token(token, db_conn) — decrypts back to real value (used only for final report)

## Critical Rules (ALWAYS Follow These)
1. Never put real customer data through the AI — always mask first
2. Always load env vars from .env using python-dotenv — never hardcode
3. All AI agent outputs must be JSON — always parse and validate
4. Every function that touches the database must accept db_conn as a parameter
5. Never commit .env or .claude/ to git

## What Each Module Receives and Returns

### PII Masker
- Input: raw transaction dict with real customer data
- Output: same dict with all PII replaced by tokens
- Side effect: stores token->real mapping in pii_vault table

### Graph Patterns (to be built)
- Input: list of masked transaction dicts
- Output: list of findings like {pattern: "STRUCTURING", transactions: [...], confidence: 0.85}

### Agent 1 - Investigator (to be built)
- Input: account_token + findings from graph patterns
- Output: JSON with primary_concern, evidence_summary, transaction_ids

### Agent 2 - Regulatory Oracle (to be built)
- Input: investigator output
- Output: JSON with applicable_regulations, each with source and relevant_excerpt

### Agent 3 - Narrative Composer (to be built)
- Input: investigator output + oracle output
- Output: JSON with 5 SAR sections, each sentence ending with [TXN_REF:] or [REG:] tags

### Lineage Mapper (to be built)
- Input: narrative JSON from Agent 3
- Output: list of records linking each sentence to its source transactions and regulations

### Blockchain Anchor (to be built)
- Input: final approved SAR content dict
- Output: SHA-256 hash stored in pii_vault + blockchain transaction ID

## Money Laundering Patterns the System Detects
- STRUCTURING: multiple cash deposits each just below $10,000 reporting threshold
- LAYERING: money moved through 3+ accounts in a chain to hide origin
- ROUND_TRIPPING: money leaves an account and returns via different route

## Test Data
Account: ACC_001
Pattern: STRUCTURING
Evidence: 12 cash deposits of $9,000-$9,900 in January 1-14 2024
Expected agent output: SAR citing FATF Recommendation 29 and PMLA Section 12
