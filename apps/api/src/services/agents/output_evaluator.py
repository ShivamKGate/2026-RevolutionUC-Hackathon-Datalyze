"""
Output quality evaluation — deterministic visualization_plan from agent JSON outputs.

Intended to run after analysis agents complete and before executive_summary
(or as input to it). Orchestrator calls ``build_visualization_plan(...)`` with
``agent_id -> parsed_output`` mappings.
"""

from __future__ import annotations

import re
from typing import Any

AGENT_ID = "output_evaluator"
AGENT_NAME = "Output Evaluator"

OUTPUT_SCHEMA: dict[str, Any] = {
    "required": [
        "kpi_cards",
        "charts",
        "recommendations",
        "knowledge_graph",
        "overall_confidence",
        "confidence_breakdown",
    ],
    "optional": ["chart_priority"],
}


def _as_dict(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        inner = data.get("result")
        if isinstance(inner, dict):
            return inner
        return data
    return {}


def _slug(s: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")
    return (t[:48] or "x").rstrip("_")


def _build_chart_priority(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Higher score = earlier in UI (descending sort)."""
    sorted_charts = sorted(charts, key=lambda c: int(c.get("priority") or 999))
    n = len(sorted_charts)
    out: list[dict[str, Any]] = []
    for i, c in enumerate(sorted_charts):
        cid = str(c.get("chart_id") or c.get("type") or f"chart_{i}")
        score = round(1.0 - (i / max(n, 1)), 4)
        out.append(
            {
                "chart_id": cid,
                "score": score,
                "reason": str(c.get("title", ""))[:200],
            }
        )
    return out


def build_visualization_plan(outputs_by_agent_id: dict[str, Any]) -> dict[str, Any]:
    """Build a UI-oriented visualization_plan from per-agent structured outputs.

    ``outputs_by_agent_id`` maps agent_id strings to either:
      - parsed JSON dicts from each agent, or
      - envelopes / wrappers containing a ``result`` dict.

    Returns a single JSON-serializable dict matching OUTPUT_SCHEMA.
    """
    kpi_cards: list[dict[str, Any]] = []
    charts: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    priority_seq = 1

    def add_chart(
        ctype: str,
        title: str,
        source_agent: str,
        *,
        chart_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        nonlocal priority_seq
        row: dict[str, Any] = {
            "type": ctype,
            "title": title,
            "data_source_agent": source_agent,
            "priority": priority_seq,
        }
        priority_seq += 1
        if extra:
            row.update(extra)
        row["chart_id"] = chart_id or row.get("chart_id") or _slug(f"{ctype}_{title}")
        charts.append(row)

    # --- trend_forecasting ---
    tf = _as_dict(outputs_by_agent_id.get("trend_forecasting"))
    fc_list = [x for x in (tf.get("forecasts") or []) if isinstance(x, dict)]
    if fc_list:
        primary = str(fc_list[0].get("metric", "metrics"))
        title = (
            f"{primary} (+{len(fc_list) - 1} more) — forecast"
            if len(fc_list) > 1
            else f"{primary} — forecast"
        )
        add_chart(
            "time_series",
            title,
            "trend_forecasting",
            chart_id="forecast_panel",
            extra={"metric": primary},
        )
    drivers = tf.get("drivers") or []
    if isinstance(drivers, list) and drivers:
        add_chart(
            "waterfall",
            "Driver sensitivity",
            "trend_forecasting",
            chart_id="driver_waterfall",
        )
    anoms = tf.get("anomalies") or []
    if isinstance(anoms, list) and anoms:
        add_chart(
            "timeline",
            "Anomaly timeline",
            "trend_forecasting",
            chart_id="anomaly_timeline",
        )
    if len(fc_list) > 1:
        add_chart(
            "time_series",
            "Segment forecasts",
            "trend_forecasting",
            chart_id="segment_forecasts",
            extra={"metric": "segments"},
        )

    # --- insight_generation ---
    ig = _as_dict(outputs_by_agent_id.get("insight_generation"))
    for ins in ig.get("insights") or []:
        if not isinstance(ins, dict):
            continue
        title = str(ins.get("title", "Insight"))
        data = ins.get("data") if isinstance(ins.get("data"), dict) else {}
        cur = data.get("current")
        prev = data.get("previous")
        chg = data.get("change_pct")
        kpi_cards.append(
            {
                "metric": title,
                "value": "" if cur is None else str(cur),
                "change": "" if chg is None else str(chg),
                "source_agent": "insight_generation",
            }
        )
    insights_list = [x for x in (ig.get("insights") or []) if isinstance(x, dict)]
    if insights_list:
        add_chart(
            "radar",
            "Current vs predicted (insights)",
            "insight_generation",
            chart_id="insight_radar",
        )
        add_chart(
            "heatmap",
            "Cohort / metric heatmap",
            "insight_generation",
            chart_id="cohort_heatmap",
        )
    for rec in ig.get("recommendations") or []:
        if not isinstance(rec, dict):
            continue
        conf = rec.get("confidence")
        try:
            cfn = float(conf) if conf is not None else 0.0
        except (TypeError, ValueError):
            cfn = 0.0
        if cfn >= 0.6:
            recommendations.append(
                {
                    "text": str(rec.get("action", "")),
                    "confidence": cfn,
                    "source_agent": "insight_generation",
                }
            )

    # --- automation_strategy ---
    au = _as_dict(outputs_by_agent_id.get("automation_strategy"))
    procs = au.get("processes") or []
    if isinstance(procs, list) and procs:
        add_chart(
            "process_sankey",
            "Process automation opportunities",
            "automation_strategy",
            chart_id="bottleneck_sankey",
        )
        add_chart(
            "automation_matrix",
            "Impact vs effort (processes)",
            "automation_strategy",
            chart_id="opportunity_matrix",
        )
        add_chart(
            "roi_scatter",
            "ROI analysis",
            "automation_strategy",
            chart_id="roi_bubbles",
        )
        add_chart(
            "capacity_projection",
            "Capacity projection",
            "automation_strategy",
            chart_id="capacity_projection",
        )

    # --- sentiment_analysis ---
    sa = _as_dict(outputs_by_agent_id.get("sentiment_analysis"))
    if sa.get("sentiment_distribution") or sa.get("trend_summary"):
        add_chart(
            "sentiment_distribution",
            "Sentiment distribution",
            "sentiment_analysis",
            chart_id="sentiment_distribution",
        )

    # --- swot_analysis ---
    sw = _as_dict(outputs_by_agent_id.get("swot_analysis"))
    if any(sw.get(k) for k in ("strengths", "weaknesses", "opportunities", "threats")):
        add_chart(
            "swot_quadrant",
            "SWOT overview",
            "swot_analysis",
            chart_id="swot_quadrant",
        )

    # --- conflict_detection ---
    cd = _as_dict(outputs_by_agent_id.get("conflict_detection"))
    contradictions = cd.get("contradictions") or []
    if isinstance(contradictions, list) and contradictions:
        add_chart(
            "conflict_table",
            "Detected conflicts",
            "conflict_detection",
            chart_id="conflict_table",
        )
        for c in contradictions:
            if not isinstance(c, dict):
                continue
            res = c.get("resolution_suggestion")
            conf = c.get("confidence")
            try:
                cfn = float(conf) if conf is not None else 0.0
            except (TypeError, ValueError):
                cfn = 0.0
            if res and cfn >= 0.6:
                recommendations.append(
                    {
                        "text": str(res),
                        "confidence": cfn,
                        "source_agent": "conflict_detection",
                    }
                )

    # --- knowledge_graph_builder ---
    kg = _as_dict(outputs_by_agent_id.get("knowledge_graph_builder"))
    nodes = kg.get("nodes") or []
    node_count = len(nodes) if isinstance(nodes, list) else 0
    knowledge_graph: dict[str, Any] = {
        "available": node_count > 0,
        "node_count": node_count,
    }
    edges = kg.get("edges") or []
    if isinstance(edges, list):
        knowledge_graph["edge_count"] = len(edges)
    if node_count:
        add_chart(
            "knowledge_graph_network",
            "Knowledge graph",
            "knowledge_graph_builder",
            chart_id="knowledge_graph_network",
        )

    # Ensure every chart has chart_id (extras may overwrite)
    for i, c in enumerate(charts):
        if not c.get("chart_id"):
            c["chart_id"] = f"{c.get('type', 'chart')}_{i}"

    chart_priority = _build_chart_priority(charts)

    # --- confidence_breakdown (heuristic) ---
    processor_ids = (
        "pdf_processor",
        "csv_processor",
        "excel_processor",
        "json_processor",
        "plain_text_processor",
    )
    proc_hits = sum(1 for pid in processor_ids if _as_dict(outputs_by_agent_id.get(pid)))
    data_quality = min(1.0, 0.45 + 0.12 * proc_hits + (0.1 if _as_dict(outputs_by_agent_id.get("aggregator")) else 0))

    analysis_agents = (
        "trend_forecasting",
        "insight_generation",
        "knowledge_graph_builder",
        "sentiment_analysis",
        "swot_analysis",
        "automation_strategy",
        "conflict_detection",
    )
    nonempty = sum(
        1
        for aid in analysis_agents
        if _has_substance(_as_dict(outputs_by_agent_id.get(aid)))
    )
    analysis_depth = min(1.0, 0.35 + 0.09 * nonempty)

    actionability = min(
        1.0,
        0.4 + 0.12 * len(recommendations) + 0.04 * len(kpi_cards),
    )

    confidence_breakdown = {
        "data_quality": round(data_quality, 2),
        "analysis_depth": round(analysis_depth, 2),
        "actionability": round(actionability, 2),
    }
    overall_confidence = round(
        (
            confidence_breakdown["data_quality"]
            + confidence_breakdown["analysis_depth"]
            + confidence_breakdown["actionability"]
        )
        / 3.0,
        2,
    )

    return {
        "kpi_cards": kpi_cards,
        "charts": charts,
        "recommendations": recommendations,
        "knowledge_graph": knowledge_graph,
        "overall_confidence": overall_confidence,
        "confidence_breakdown": confidence_breakdown,
        "chart_priority": chart_priority,
    }


def _has_substance(d: dict[str, Any]) -> bool:
    if not d:
        return False
    for k, v in d.items():
        if k == "errors":
            continue
        if isinstance(v, list) and len(v) > 0:
            return True
        if isinstance(v, dict) and v:
            return True
        if v not in (None, "", 0, 0.0, False):
            return True
    return False
