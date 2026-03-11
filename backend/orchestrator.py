import os
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
    try:
        result = run_investigator(state["account_token"], state["transactions"])
        if (result or {}).get("status") == "NO_SUSPICIOUS_ACTIVITY":
            return {"investigation": result, "status": "NO_SUSPICIOUS_ACTIVITY"}
        return {"investigation": result, "status": "INVESTIGATED"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def node_retrieve_regs(state: SARState) -> dict:
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
        return {"regulations": result, "status": "REGS_RETRIEVED"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def node_compose(state: SARState) -> dict:
    try:
        result = run_composer(
            state["investigation"], state["regulations"], state["account_token"]
        )
        return {"narrative": result, "status": "DRAFT_COMPLETE"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def node_lineage(state: SARState) -> dict:
    try:
        result = build_lineage_map(
            state["narrative"], state["investigation"], state["regulations"]
        )
        return {"lineage": result, "status": "LINEAGE_COMPLETE"}
    except Exception as e:
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
    return _graph.invoke(initial_state)
