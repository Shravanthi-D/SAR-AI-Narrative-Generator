import re
import uuid


def build_lineage_map(narrative: dict, investigation: dict, regulations: dict) -> list:
    """
    Walk every string value in the narrative dict, split into sentences,
    extract [TXN_REF: txn_id] and [REG: source_name] tags, resolve them
    against investigation transactions and regulations, and return a list
    of lineage records.

    Args:
        narrative: dict output from Agent 3 (Narrative Composer), containing
                   SAR sections where each value is a string of sentences.
        investigation: dict output from Agent 1 (Investigator), must contain
                       a "transactions" key with a list of transaction dicts.
        regulations: dict output from Agent 2 (Regulatory Oracle), must contain
                     an "applicable_regulations" key with a list of regulation dicts.

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

    txn_ref_pattern = re.compile(r'\[TXN_REF:\s*([^\]]+)\]')
    reg_ref_pattern = re.compile(r'\[REG:\s*([^\]]+)\]')
    sentence_split_pattern = re.compile(r'(?<=[.!?])\s+')

    lineage_records = []
    global_sentence_index = 0

    for section_key, section_value in (narrative or {}).items():
        if not isinstance(section_value, str):
            continue

        sentences = sentence_split_pattern.split(section_value.strip())

        for sentence_text in sentences:
            sentence_text = sentence_text.strip()
            if not sentence_text:
                continue

            cited_txn_ids = txn_ref_pattern.findall(sentence_text)
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
                "id": str(uuid.uuid4()),
                "sentence_index": global_sentence_index,
                "sentence_text": sentence_text,
                "section": section_key,
                "transactions": resolved_txns,
                "regulations": resolved_regs,
                "agent_meta": {
                    "model": (narrative or {}).get("model", "unknown"),
                    "section": section_key,
                    "cited_txns": cited_txn_ids,
                    "cited_regs": cited_reg_sources,
                },
            }
            lineage_records.append(record)
            global_sentence_index += 1

    return lineage_records
