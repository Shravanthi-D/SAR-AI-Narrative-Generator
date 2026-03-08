from datetime import timedelta
from typing import Optional
import networkx as nx

REPORTING_THRESHOLD = 10_000.00
STRUCTURING_LOW  = REPORTING_THRESHOLD * 0.80   # 8,000
STRUCTURING_HIGH = REPORTING_THRESHOLD * 0.999  # 9,990


def detect_structuring(
    G: nx.MultiDiGraph,
    account_token: str,
    window_days: int = 14,
) -> Optional[dict]:
    """
    Detect structuring: 3+ cash deposits each between 80%-99.9% of $10,000,
    clustered within any rolling window_days-day period.
    """
    # Collect all CASH_DEPOSIT edges into the target account
    deposits = []
    if "CASH_SOURCE" not in G or account_token not in G:
        return None

    # Use edges() to iterate safely over a MultiDiGraph
    for u, v, attrs in G.edges(data=True):
        if (
            v == account_token
            and u == "CASH_SOURCE"
            and attrs.get("txn_type") == "CASH_DEPOSIT"
            and STRUCTURING_LOW <= attrs.get("amount", 0) <= STRUCTURING_HIGH
        ):
            deposits.append(attrs)

    if len(deposits) < 3:
        return None

    # Sort by timestamp
    deposits.sort(key=lambda x: x["timestamp"])

    # Sliding window — find the largest cluster within window_days
    best_cluster = []
    window = timedelta(days=window_days)

    for i, anchor in enumerate(deposits):
        cluster = [
            d for d in deposits
            if abs(d["timestamp"] - anchor["timestamp"]) <= window
        ]
        if len(cluster) > len(best_cluster):
            best_cluster = cluster

    if len(best_cluster) < 3:
        return None

    total = sum(d["amount"] for d in best_cluster)
    txn_ids = [d["txn_id"] for d in best_cluster]

    # Confidence: scales with count and how tightly below the threshold each deposit is
    count_score = min(len(best_cluster) / 12, 1.0)          # saturates at 12 deposits
    proximity_score = sum(
        (REPORTING_THRESHOLD - d["amount"]) / (REPORTING_THRESHOLD * 0.20)
        for d in best_cluster
    ) / len(best_cluster)
    proximity_score = 1.0 - min(proximity_score, 1.0)        # closer to threshold = higher score
    confidence = round(0.6 * count_score + 0.4 * proximity_score, 4)

    return {
        "pattern":           "STRUCTURING",
        "confidence":        confidence,
        "account":           account_token,
        "transaction_count": len(best_cluster),
        "total_amount":      round(total, 2),
        "transactions":      txn_ids,
        "description": (
            f"Account {account_token} made {len(best_cluster)} cash deposits "
            f"totalling ${total:,.2f}, each between "
            f"${STRUCTURING_LOW:,.0f} and ${STRUCTURING_HIGH:,.0f} "
            f"(80%-99.9% of the $10,000 reporting threshold), "
            f"within a {window_days}-day window. "
            f"This pattern is consistent with deliberate structuring to evade CTR filing."
        ),
    }


def detect_layering(
    G: nx.MultiDiGraph,
    account_token: str,
    min_hops: int = 3,
    max_hops: int = 6,
) -> Optional[dict]:
    """
    Detect layering: money moving through 3+ accounts in sequence.
    Looks for simple paths of length min_hops..max_hops starting from account_token.
    """
    if account_token not in G:
        return None

    longest_chain = []

    try:
        for target in G.nodes():
            if target == account_token:
                continue
            for path in nx.all_simple_paths(G, account_token, target, cutoff=max_hops):
                if min_hops <= len(path) - 1 <= max_hops:
                    if len(path) > len(longest_chain):
                        longest_chain = path
    except (nx.NetworkXError, nx.NodeNotFound):
        return None

    if len(longest_chain) - 1 < min_hops:
        return None

    hops = len(longest_chain) - 1
    confidence = round(min(0.5 + (hops - min_hops) * 0.1, 0.95), 4)

    return {
        "pattern":      "LAYERING",
        "confidence":   confidence,
        "account":      account_token,
        "chain_length": hops,
        "chain":        longest_chain,
        "description": (
            f"Funds from account {account_token} moved through "
            f"{hops} intermediate accounts in sequence: "
            f"{' → '.join(longest_chain)}. "
            f"Multi-hop transfers with no clear business purpose are "
            f"consistent with layering to obscure the origin of funds."
        ),
    }


def run_all_detections(G: nx.MultiDiGraph, account_token: str) -> list:
    """Run all pattern detectors and return a list of non-None findings."""
    detectors = [
        detect_structuring(G, account_token),
        detect_layering(G, account_token),
    ]
    return [finding for finding in detectors if finding is not None]
