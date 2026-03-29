"""
Phase 1.3 validation: pipeline_classifier contract + normalizer artifacts.

Run from apps/api with PYTHONPATH=src and project venv:
  .\\.venv\\Scripts\\python.exe scripts/validate_pipeline_classifier.py
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


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    contract = get_contract("pipeline_classifier")
    _assert(contract is not None, "missing contract")

    sample = {
        "track": "predictive",
        "confidence": 0.92,
        "reasoning": "Sales and revenue data with temporal columns suggest forecasting.",
        "secondary_track": "optimization",
        "file_types_detected": ["excel"],
        "data_domains_detected": ["sales", "finance"],
        "recommended_agents": ["trend_forecasting", "insight_generation", "sentiment_analysis"],
        "skip_agents": ["automation_strategy"],
        "priority_map": {"trend_forecasting": 10, "insight_generation": 8},
        "scraper_strategy": {
            "focus_keywords": ["revenue", "quarterly"],
            "industry_vertical": "retail",
            "depth": "moderate",
        },
    }

    ok, errs = contract.validate_output(sample)
    _assert(ok, f"contract: {errs}")

    env = normalize_agent_output("pipeline_classifier", sample)
    ev_ok, ev_errs = validate_envelope(env)
    _assert(ev_ok, f"envelope: {ev_errs}")
    _assert(env["status"] == "ok", "status")
    _assert("Track: predictive" in env["summary"], "summary should mention track")
    kinds = [a.get("kind") for a in env["artifacts"] if isinstance(a, dict)]
    _assert("pipeline_classification" in kinds, f"expected pipeline_classification artifact, got {kinds}")

    # Determinism (same as verify_all_agents Phase C for this agent)
    runs = [json.dumps(normalize_agent_output("pipeline_classifier", sample), sort_keys=True) for _ in range(3)]
    _assert(len(set(runs)) == 1, "normalizer should be deterministic for fixed input")

    print("validate_pipeline_classifier: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
