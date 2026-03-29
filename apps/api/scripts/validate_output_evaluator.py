"""
Phase 1.5 validation: output_evaluator.build_visualization_plan + contract + normalizer.

Run from apps/api with PYTHONPATH=src and venv:
  .\\.venv\\Scripts\\python.exe scripts/validate_output_evaluator.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from services.agents.contracts import get_contract
from services.agents.normalizer import normalize_agent_output, validate_envelope
from services.agents.output_evaluator import build_visualization_plan


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    contract = get_contract("output_evaluator")
    _assert(contract is not None, "contract missing")

    sample_inputs = {
        "csv_processor": {"rows_summary": {"total_rows": 10}, "chart_suggestions": []},
        "aggregator": {"corpus": [{"item_id": "1"}], "storyline_hypotheses": ["h1"]},
        "trend_forecasting": {
            "forecasts": [
                {
                    "metric": "revenue",
                    "historical": [],
                    "predicted": [],
                    "confidence": 0.8,
                    "trend_direction": "upward",
                    "seasonality_detected": False,
                }
            ],
            "drivers": [],
            "anomalies": [],
            "chart_suggestions": [],
        },
        "insight_generation": {
            "insights": [
                {
                    "title": "Revenue up",
                    "description": "d",
                    "impact": "high",
                    "confidence": 0.85,
                    "chart_type": "kpi_card",
                    "data": {"current": 100, "previous": 90, "change_pct": 11.1},
                }
            ],
            "recommendations": [
                {
                    "action": "Invest in channel X",
                    "priority": "high",
                    "expected_impact": "medium",
                    "confidence": 0.78,
                }
            ],
            "chart_suggestions": [],
        },
        "knowledge_graph_builder": {
            "nodes": [{"id": "n1", "label": "N", "type": "metric", "context": "c", "insights": []}],
            "edges": [],
            "clusters": [],
            "chart_suggestions": [],
        },
    }

    plan = build_visualization_plan(sample_inputs)
    ok, errs = contract.validate_output(plan)
    _assert(ok, f"contract: {errs}")
    _assert(isinstance(plan["knowledge_graph"]["node_count"], int), "node_count")
    _assert(plan["knowledge_graph"]["available"] is True, "kg available")
    _assert("overall_confidence" in plan and "confidence_breakdown" in plan, "scores")

    env = normalize_agent_output("output_evaluator", plan)
    ev_ok, ev_errs = validate_envelope(env)
    _assert(ev_ok, f"envelope: {ev_errs}")
    _assert(abs(env["confidence"] - float(plan["overall_confidence"])) < 1e-6, "envelope confidence")

    kinds = [a.get("kind") for a in env["artifacts"] if isinstance(a, dict)]
    _assert("visualization_plan" in kinds, f"artifact kinds {kinds}")

    # Determinism
    runs = [json.dumps(build_visualization_plan(sample_inputs), sort_keys=True) for _ in range(3)]
    _assert(len(set(runs)) == 1, "deterministic")

    # Empty-ish run still validates
    empty_plan = build_visualization_plan({})
    ok2, _ = contract.validate_output(empty_plan)
    _assert(ok2, "empty inputs should still produce valid schema")

    print("validate_output_evaluator: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
