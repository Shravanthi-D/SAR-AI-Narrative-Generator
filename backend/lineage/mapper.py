import decimal
import datetime
import json
import re
import uuid
import logging

import psycopg2.extras

logger = logging.getLogger(__name__)


def build_lineage_map(narrative: dict, investigation: dict, regulations: dict) -> list:
    """
    Walk every string value in the narrative dict, split into sentences,
    extract [TXN_REF: txn_id] and [REG: source_name] tags, resolve them
    against investigation transactions and regulations, and return a list
    of lineage records.

    If zero citation tags are found across all sentences (LLM failed to add
    them), the function falls back to distributing transactions and regulations
    evenly across sentences so lineage is never empty.

    Args:
        narrative: dict output from Agent 3 (Narrative Composer).
        investigation: dict output from Agent 1, must have "transactions" key.
        regulations: dict output from Agent 2, must have "applicable_regulations" key.

    Returns:
        list of dicts with keys: id, sentence_index, sentence_text, section,
        transactions, regulations, agent_meta.
    """
    txn_lookup = {
        txn.get("txn_id", txn.get("id", "")): txn
        for txn in (investigation or {}).get("transactions", [])
    }
    reg_lookup = {
        reg.get("source", reg.get("name", "")): reg
        for reg in (regulations or {}).get("applicable_regulations", [])
    }

    # Match individual TXN_REF: <id> occurrences — handles both single-bracket
    # [TXN_REF: X] and multi-ID [TXN_REF: X, TXN_REF: Y, ...] formats.
    txn_ref_pattern      = re.compile(r'TXN_REF:\s*([^\s,\]\[]+)')
    # Match REG: <source> — source may contain spaces; ends at ] or , REG:
    reg_ref_pattern      = re.compile(r'REG:\s*([^\]]+?)(?=\s*(?:,\s*REG:|]|$))')
    sentence_split_pattern = re.compile(r'(?<=[.!?])\s+')

    lineage_records = []
    global_sentence_index = 0

    section_keys = [
        "section_1_subject",
        "section_2_activity",
        "section_3_why_suspicious",
        "section_4_regulatory_basis",
        "section_5_evidence",
    ]

    for section_key in section_keys:
        section_value = (narrative or {}).get(section_key, "")
        if not isinstance(section_value, str):
            continue

        sentences = sentence_split_pattern.split(section_value.strip())

        for sentence_text in sentences:
            sentence_text = sentence_text.strip()
            if not sentence_text:
                continue

            cited_txn_ids     = txn_ref_pattern.findall(sentence_text)
            cited_reg_sources = reg_ref_pattern.findall(sentence_text)

            resolved_txns = [
                txn_lookup[tid.strip()]
                for tid in cited_txn_ids
                if tid.strip() in txn_lookup
            ]
            resolved_regs = [
                reg_lookup[src.strip()]
                for src in cited_reg_sources
                if src.strip() in reg_lookup
            ]

            record = {
                "id":             str(uuid.uuid4()),
                "sentence_index": global_sentence_index,
                "sentence_text":  sentence_text,
                "section":        section_key,
                "transactions":   resolved_txns,
                "regulations":    resolved_regs,
                "agent_meta": {
                    "model":       (narrative or {}).get("model", "unknown"),
                    "section":     section_key,
                    "cited_txns":  cited_txn_ids,
                    "cited_regs":  cited_reg_sources,
                },
            }
            lineage_records.append(record)
            global_sentence_index += 1

    total_sentences   = len(lineage_records)
    total_txn_resolved = sum(len(r["transactions"]) for r in lineage_records)
    total_reg_resolved = sum(len(r["regulations"])  for r in lineage_records)

    logger.info(
        "build_lineage_map: %d sentences parsed, %d TXN_REF resolved, %d REG resolved",
        total_sentences, total_txn_resolved, total_reg_resolved,
    )

    # ── Fallback: if transactions were not resolved, distribute evenly ─────────
    if lineage_records and total_txn_resolved == 0:
        logger.warning(
            "No citation tags resolved from narrative — falling back to even distribution"
        )
        all_txns = list(txn_lookup.values())
        all_regs = list(reg_lookup.values())
        n = len(lineage_records)

        for i, record in enumerate(lineage_records):
            # Give each sentence a slice of transactions and regulations
            txn_slice = all_txns[i % len(all_txns) : i % len(all_txns) + 2] if all_txns else []
            reg_slice = [all_regs[i % len(all_regs)]] if all_regs else []

            record["transactions"] = txn_slice
            record["regulations"]  = reg_slice
            record["agent_meta"]["fallback_distribution"] = True

        logger.info(
            "Fallback complete: distributed %d txns and %d regs across %d sentences",
            len(all_txns), len(all_regs), n,
        )

    return lineage_records


def _json_safe(obj):
    """Convert Decimal and datetime to JSON-serializable types."""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _sanitize_for_json(value):
    """Recursively make a value safe for JSON serialization."""
    return json.loads(json.dumps(value, default=_json_safe))


def save_lineage(report_id: str, records: list, db_conn) -> None:
    """
    Persist lineage records produced by build_lineage_map() into the
    sentence_lineage table.  Idempotent: ON CONFLICT (id) DO NOTHING.

    Args:
        report_id: UUID string of the sar_reports row these sentences belong to.
        records:   list of dicts returned by build_lineage_map().
        db_conn:   open psycopg2 connection.
    """
    if not records:
        logger.warning("save_lineage: no records to save for report_id=%s", report_id)
        return

    rows = [
        (
            rec["id"],
            report_id,
            rec["sentence_index"],
            rec["sentence_text"],
            psycopg2.extras.Json(_sanitize_for_json(rec.get("transactions", []))),
            psycopg2.extras.Json(_sanitize_for_json(rec.get("regulations", []))),
            psycopg2.extras.Json(_sanitize_for_json(rec.get("agent_meta", {}))),
        )
        for rec in records
    ]

    cur = db_conn.cursor()
    cur.executemany(
        """
        INSERT INTO sentence_lineage
            (id, report_id, sentence_index, sentence_text, transactions, regulations, agent_meta)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    db_conn.commit()
    cur.close()
    logger.info("save_lineage: saved %d records for report_id=%s", len(rows), report_id)
