"""
Phase 1.4 validation: knowledge_graph_builder schema + normalizer knowledge_graph artifact.

Run: apps/api with PYTHONPATH=src and venv:
  .\\.venv\\Scripts\\python.exe scripts/validate_knowledge_graph_builder.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from services.agents.contracts import get_contract
from services.agents.normalizer import normalize_agent_output, validate_envelope


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    contract = get_contract("knowledge_graph_builder")
    _assert(contract is not None, "contract missing")

    sample = {
        "nodes": [
            {
                "id": "revenue_q1",
                "label": "Q1 Revenue",
                "type": "metric",
                "value": 820000,
                "context": "Aggregator cited Q1 revenue from sales workbook.",
                "insights": ["Up YoY", "Seasonal peak"],
            },
            {
                "id": "marketing_spend",
                "label": "Marketing spend",
                "type": "metric",
                "value": 120000,
                "context": "Expense line from P&L excerpt.",
                "insights": [],
            },
        ],
        "edges": [
            {
                "source": "revenue_q1",
                "target": "marketing_spend",
                "relationship": "correlated_with",
                "strength": 0.78,
            }
        ],
        "clusters": [{"name": "Financial Metrics", "node_ids": ["revenue_q1", "marketing_spend"]}],
        "chart_suggestions": ["knowledge_graph_network", "cluster_map"],
    }

    ok, errs = contract.validate_output(sample)
    _assert(ok, f"contract: {errs}")

    env = normalize_agent_output("knowledge_graph_builder", sample)
    ev_ok, ev_errs = validate_envelope(env)
    _assert(ev_ok, f"envelope: {ev_errs}")
    _assert("nodes and" in env["summary"] and "edges" in env["summary"], "summary should mention nodes and edges")

    kinds = [a.get("kind") for a in env["artifacts"] if isinstance(a, dict)]
    _assert("knowledge_graph" in kinds, f"expected knowledge_graph artifact, got {kinds}")
    kg = next(a for a in env["artifacts"] if isinstance(a, dict) and a.get("kind") == "knowledge_graph")
    _assert(len(kg.get("nodes", [])) == 2, "artifact nodes")
    _assert(len(kg.get("edges", [])) == 1, "artifact edges")

    print("validate_knowledge_graph_builder: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
