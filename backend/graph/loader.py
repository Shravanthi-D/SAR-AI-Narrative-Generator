import networkx as nx
from dateutil.parser import parse as parse_dt


def build_transaction_graph(transactions: list) -> nx.MultiDiGraph:
    """
    Build a directed multigraph from a list of masked transaction dicts.

    Nodes  — account tokens (and "CASH_SOURCE" for cash deposits)
    Edges  — money flows, with txn_id, amount, timestamp, txn_type as attributes.
    MultiDiGraph is used so multiple transactions between the same account pair
    (e.g. repeated CASH_DEPOSITs) are all preserved as distinct edges.
    """
    G = nx.MultiDiGraph()

    for txn in transactions:
        account = txn.get("account_token") or txn.get("account_token")
        txn_type = txn.get("txn_type", "")
        counterparty = txn.get("counterparty")
        txn_id = txn.get("txn_id")
        amount = float(txn.get("amount", 0))
        timestamp = txn.get("txn_timestamp")
        if isinstance(timestamp, str):
            timestamp = parse_dt(timestamp)

        edge_attrs = {
            "txn_id":    txn_id,
            "amount":    amount,
            "timestamp": timestamp,
            "txn_type":  txn_type,
        }

        if txn_type == "CASH_DEPOSIT":
            source = "CASH_SOURCE"
            target = account
        elif txn_type == "WITHDRAWAL":
            source = account
            target = counterparty if counterparty else "EXTERNAL"
        else:
            # TRANSFER and anything else: account → counterparty
            source = account
            target = counterparty if counterparty else "EXTERNAL"

        G.add_node(source)
        G.add_node(target)
        # Multiple edges between same pair — use add_edges_from with key via MultiDiGraph
        # DiGraph overwrites; use a unique key via the txn_id stored in edge data
        G.add_edge(source, target, **edge_attrs)

    return G
