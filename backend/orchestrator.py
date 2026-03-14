import logging
import os
import traceback
from typing import Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from opensearchpy import OpenSearch

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.agents.investigator import run_investigator
from backend.agents.oracle import run_oracle
from backend.agents.composer import run_composer
from backend.lineage.mapper import build_lineage_map

logger = logging.getLogger(__name__)


class SARState(TypedDict):
    case_id: str
    account_token: str
    transactions: list
    investigation: Optional[dict]
    regulations: Optional[dict]
    narrative: Optional[dict]
    lineage: Optional[list]
    status: str
    error: Optional[str]


def node_investigate(state: SARState) -> dict:
    logger.info("Starting investigate node for account=%s, %d transactions",
                state["account_token"], len(state.get("transactions", [])))
    try:
        result = run_investigator(state["account_token"], state["transactions"])
        status = (result or {}).get("status", "SUSPICIOUS")
        logger.info("Investigate complete: status=%s, patterns=%s",
                    status, (result or {}).get("patterns_detected", []))
        if status == "NO_SUSPICIOUS_ACTIVITY":
            return {"investigation": result, "status": "NO_SUSPICIOUS_ACTIVITY"}
        return {"investigation": result, "status": "INVESTIGATED"}
    except Exception as e:
        logger.error("Investigate node FAILED: %s\n%s", e, traceback.format_exc())
        return {"status": "ERROR", "error": str(e)}


def node_retrieve_regs(state: SARState) -> dict:
    logger.info("Starting oracle node — building OpenSearch client")
    try:
        opensearch_client = OpenSearch(
            hosts=[os.environ.get("OPENSEARCH_URL", "http://localhost:9200")],
            http_auth=(
                os.environ.get("OPENSEARCH_USER", "admin"),
                os.environ.get("OPENSEARCH_PASS", "admin"),
            ),
            verify_certs=False,
            ssl_show_warn=False,
        )
        result = run_oracle(state["investigation"], opensearch_client)
        reg_count = len((result or {}).get("applicable_regulations", []))
        logger.info("Oracle complete: %d regulations retrieved", reg_count)
        return {"regulations": result, "status": "REGS_RETRIEVED"}
    except Exception as e:
        logger.error("Oracle node FAILED: %s\n%s", e, traceback.format_exc())
        return {"status": "ERROR", "error": str(e)}


def node_compose(state: SARState) -> dict:
    logger.info("Starting composer node")
    try:
        result = run_composer(
            state["investigation"], state["regulations"], state["account_token"]
        )
        sections = {k: bool(result.get(k)) for k in [
            "section_1_subject", "section_2_activity",
            "section_3_why_suspicious", "section_4_regulatory_basis", "section_5_evidence"
        ]}
        logger.info("Composer complete: section fill status=%s", sections)
        return {"narrative": result, "status": "DRAFT_COMPLETE"}
    except Exception as e:
        logger.error("Composer node FAILED: %s\n%s", e, traceback.format_exc())
        return {"status": "ERROR", "error": str(e)}


def node_lineage(state: SARState) -> dict:
    logger.info("Starting lineage node")
    try:
        result = build_lineage_map(
            state["narrative"], state["investigation"], state["regulations"]
        )
        logger.info("Lineage complete: %d lineage records built", len(result))
        return {"lineage": result, "status": "LINEAGE_COMPLETE"}
    except Exception as e:
        logger.error("Lineage node FAILED: %s\n%s", e, traceback.format_exc())
        return {"status": "ERROR", "error": str(e)}


def after_investigate(state: SARState) -> str:
    if state["status"] in ("ERROR", "NO_SUSPICIOUS_ACTIVITY"):
        return "end"
    return "continue"


def build_sar_graph():
    g = StateGraph(SARState)

    g.add_node("investigate", node_investigate)
    g.add_node("retrieve_regs", node_retrieve_regs)
    g.add_node("compose", node_compose)
    g.add_node("lineage", node_lineage)

    g.set_entry_point("investigate")

    g.add_conditional_edges(
        "investigate",
        after_investigate,
        {"continue": "retrieve_regs", "end": END},
    )
    g.add_edge("retrieve_regs", "compose")
    g.add_edge("compose", "lineage")
    g.add_edge("lineage", END)

    return g.compile()


_graph = build_sar_graph()


def run_sar_pipeline(case_id: str, account_token: str, transactions: list) -> dict:
    logger.info(
        "run_sar_pipeline: case_id=%s account=%s txn_count=%d",
        case_id, account_token, len(transactions),
    )
    initial_state: SARState = {
        "case_id": case_id,
        "account_token": account_token,
        "transactions": transactions,
        "investigation": None,
        "regulations": None,
        "narrative": None,
        "lineage": None,
        "status": "STARTED",
        "error": None,
    }
    final_state = _graph.invoke(initial_state)
    logger.info(
        "run_sar_pipeline complete: status=%s lineage_records=%d",
        final_state.get("status"),
        len(final_state.get("lineage") or []),
    )
    return final_state
