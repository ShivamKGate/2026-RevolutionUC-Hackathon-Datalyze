"""
Phase 1 robust smoke suite (deterministic, no external model calls).

Validates:
  - key Phase 1 agent contracts
  - normalizer envelopes + artifact extraction
  - file_type_classifier utility routing
  - output_evaluator visualization_plan generation
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from services.agents.contracts import get_contract
from services.agents.file_type_classifier import classify_file_types
from services.agents.normalizer import normalize_agent_output, validate_envelope
from services.agents.output_evaluator import build_visualization_plan


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _validate_agent(agent_id: str, payload: dict[str, Any]) -> None:
    contract = get_contract(agent_id)
    _assert(contract is not None, f"missing contract: {agent_id}")
    ok, errs = contract.validate_output(payload)
    _assert(ok, f"{agent_id} contract errors: {errs}")
    env = normalize_agent_output(agent_id, payload)
    ev_ok, ev_errs = validate_envelope(env)
    _assert(ev_ok, f"{agent_id} envelope errors: {ev_errs}")


def main() -> int:
    # Phase 1.1 core agents
    _validate_agent(
        "trend_forecasting",
        {
            "forecasts": [
                {
                    "metric": "revenue",
                    "historical": [{"date": "2025-01", "value": 100}],
                    "predicted": [{"date": "2026-01", "value": 120, "lower": 110, "upper": 130}],
                    "confidence": 0.82,
                    "trend_direction": "upward",
                    "seasonality_detected": False,
                }
            ],
            "drivers": [{"factor": "marketing_efficiency", "impact_pct": 22}],
            "anomalies": [],
            "chart_suggestions": ["time_series_confidence_band"],
        },
    )
    _validate_agent(
        "insight_generation",
        {
            "insights": [
                {
                    "title": "Revenue acceleration",
                    "description": "Growth improved quarter-over-quarter.",
                    "impact": "high",
                    "confidence": 0.86,
                    "chart_type": "kpi_card",
                    "data": {"current": 120, "previous": 100, "change_pct": 20},
                    "provenance": ["sales_sheet_q4"],
                }
            ],
            "recommendations": [
                {
                    "action": "Expand high-performing channel",
                    "priority": "high",
                    "expected_impact": "Increase top-line growth",
                    "confidence": 0.78,
                }
            ],
            "chart_suggestions": ["kpi_card"],
        },
    )
    _validate_agent(
        "automation_strategy",
        {
            "processes": [
                {
                    "name": "Invoice processing",
                    "current_time_hours": 4.5,
                    "automated_time_hours": 0.8,
                    "cost_current": 10000,
                    "cost_automated": 2500,
                    "roi_months": 4,
                    "implementation_effort": "medium",
                    "impact_score": 0.88,
                }
            ],
            "bottlenecks": [{"stage": "Manual review", "time_pct": 42, "cost_pct": 35}],
            "sop_draft": {"steps": ["Ingest", "Validate", "Post"], "estimated_savings_annual": 54000},
            "chart_suggestions": ["process_sankey"],
        },
    )
    _validate_agent(
        "knowledge_graph_builder",
        {
            "nodes": [
                {
                    "id": "revenue_q1",
                    "label": "Q1 Revenue",
                    "type": "metric",
                    "value": 820000,
                    "context": "Pulled from aggregated sales workbook.",
                    "insights": ["Improving quarter trend"],
                },
                {
                    "id": "marketing_spend",
                    "label": "Marketing Spend",
                    "type": "metric",
                    "value": 210000,
                    "context": "Pulled from expense sheet.",
                    "insights": [],
                },
            ],
            "edges": [
                {
                    "source": "revenue_q1",
                    "target": "marketing_spend",
                    "relationship": "correlated_with",
                    "strength": 0.73,
                }
            ],
            "clusters": [{"name": "Financial Metrics", "node_ids": ["revenue_q1", "marketing_spend"]}],
            "chart_suggestions": ["knowledge_graph_network"],
        },
    )

    # Phase 1.2 file routing utility + contract
    routed = classify_file_types(
        [
            {"filename": "book.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            {"filename": "notes.txt", "mime": "text/plain"},
            {"filename": "mystery.xyz", "mime": "application/octet-stream"},
        ]
    )
    _validate_agent("file_type_classifier", routed)
    _assert(routed["file_routing_map"]["book.xlsx"] == "excel_processor", "xlsx routing")
    _assert(routed["file_routing_map"]["notes.txt"] == "plain_text_processor", "txt routing")

    # Phase 1.3 classifier schema
    _validate_agent(
        "pipeline_classifier",
        {
            "track": "predictive",
            "confidence": 0.91,
            "reasoning": "Temporal sales/finance tables indicate forecasting workload.",
            "secondary_track": "optimization",
            "file_types_detected": ["excel"],
            "data_domains_detected": ["sales", "finance"],
            "recommended_agents": ["trend_forecasting", "insight_generation"],
            "skip_agents": ["automation_strategy"],
            "priority_map": {"trend_forecasting": 10, "insight_generation": 8},
            "scraper_strategy": {
                "focus_keywords": ["revenue", "forecast"],
                "industry_vertical": "retail",
                "depth": "moderate",
            },
        },
    )

    # Phase 1.5 visualization utility + contract
    viz_plan = build_visualization_plan(
        {
            "trend_forecasting": {
                "forecasts": [
                    {
                        "metric": "revenue",
                        "historical": [],
                        "predicted": [],
                        "confidence": 0.81,
                        "trend_direction": "upward",
                        "seasonality_detected": True,
                    }
                ],
                "drivers": [],
                "anomalies": [],
                "chart_suggestions": [],
            },
            "insight_generation": {
                "insights": [
                    {
                        "title": "Revenue acceleration",
                        "description": "d",
                        "impact": "high",
                        "confidence": 0.84,
                        "chart_type": "kpi_card",
                        "data": {"current": 120, "previous": 100, "change_pct": 20},
                    }
                ],
                "recommendations": [
                    {"action": "Scale channel A", "priority": "high", "expected_impact": "growth", "confidence": 0.75}
                ],
                "chart_suggestions": [],
            },
            "knowledge_graph_builder": {
                "nodes": [{"id": "n1", "label": "N1", "type": "metric", "context": "ctx", "insights": []}],
                "edges": [],
                "clusters": [],
                "chart_suggestions": [],
            },
        }
    )
    _validate_agent("output_evaluator", viz_plan)
    _assert(viz_plan["knowledge_graph"]["available"] is True, "viz knowledge graph availability")

    print("validate_phase1_suite: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
