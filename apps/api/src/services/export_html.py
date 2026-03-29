"""Full HTML report export: same data as the analysis UI (replay + charts via Plotly)."""

from __future__ import annotations

import html
import json
import logging
import math
from typing import Any
from uuid import uuid4

import plotly.graph_objects as go
import plotly.io as pio

from services.export_common import (
    chart_export_allowed,
    extract_parsed_output,
    merge_agent_results,
    merge_replay_agent_results,
    parse_loose_json,
    read_agent_outputs,
)

logger = logging.getLogger("export_html")

# Backwards-compatible aliases used throughout this module
_parse_loose_json = parse_loose_json
_merge_agent_results = merge_agent_results
_read_agent_outputs = read_agent_outputs
_extract_parsed_output = extract_parsed_output


def _safe_float(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _opt_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
CHART_COLORS = {
    "accent": "#3b82f6",
    "positive": "#22c55e",
    "negative": "#ef4444",
    "neutral": "#64748b",
    "grid": "rgba(51, 65, 85, 0.6)",
}


def _layout(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "paper_bgcolor": "#1e293b",
        "plot_bgcolor": "#0f172a",
        "font": {
            "family": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
            "color": "#e8ecf1",
            "size": 12,
        },
        "margin": {"l": 56, "r": 24, "t": 48, "b": 56},
        "showlegend": True,
        "legend": {
            "font": {"color": "#94a3b8"},
            "bgcolor": "rgba(15, 23, 42, 0.5)",
            "bordercolor": CHART_COLORS["grid"],
            "borderwidth": 1,
        },
        "xaxis": {
            "gridcolor": CHART_COLORS["grid"],
            "zerolinecolor": CHART_COLORS["grid"],
            "tickfont": {"color": "#94a3b8"},
        },
        "yaxis": {
            "gridcolor": CHART_COLORS["grid"],
            "zerolinecolor": CHART_COLORS["grid"],
            "tickfont": {"color": "#94a3b8"},
        },
    }
    base.update(extra)
    return base


def _fig_div(fig: go.Figure) -> str:
    did = f"p_{uuid4().hex[:12]}"
    return pio.to_html(
        fig,
        include_plotlyjs=False,
        full_html=False,
        div_id=did,
        config={"responsive": True, "displayModeBar": True},
    )


def _viz_plan(replay: dict[str, Any] | None, ar: dict[str, Any]) -> dict[str, Any]:
    if replay and isinstance(replay.get("visualization_plan"), dict):
        return replay["visualization_plan"]
    oe = ar.get("output_evaluator")
    if isinstance(oe, dict):
        return oe
    return {}


def _esc(x: Any) -> str:
    return html.escape(str(x), quote=True)


def _insight_cards_html(insights: list[Any]) -> str:
    if not insights:
        return ""
    parts = ['<section class="block"><h2>Insights</h2><div class="insight-grid">']
    for ins in insights:
        if not isinstance(ins, dict):
            parts.append(f'<article class="card"><p>{_esc(ins)}</p></article>')
            continue
        title = ins.get("title") or ins.get("insight") or "Insight"
        desc = ins.get("description") or ""
        impact = ins.get("impact") or ""
        conf = ins.get("confidence")
        prov = ins.get("provenance") or []
        data = ins.get("data") or {}
        parts.append('<article class="card insight-card">')
        parts.append(f"<h3>{_esc(title)}</h3>")
        if desc:
            parts.append(f'<p class="insight-desc">{_esc(desc)}</p>')
        meta: list[str] = []
        if impact:
            meta.append(f'<span class="pill impact-{_esc(impact)}">Impact: {_esc(impact)}</span>')
        if conf is not None:
            try:
                meta.append(f"<span>Confidence: {float(conf):.0%}</span>")
            except (TypeError, ValueError):
                meta.append(f"<span>Confidence: {_esc(conf)}</span>")
        if isinstance(prov, list) and prov:
            meta.append(f"<span>Sources: {_esc(', '.join(str(p) for p in prov))}</span>")
        if meta:
            parts.append(f'<p class="meta">{" · ".join(meta)}</p>')
        if isinstance(data, dict) and data:
            parts.append(
                "<table class='mini'><tr>"
                + "".join(f"<th>{_esc(k)}</th>" for k in data.keys())
                + "</tr><tr>"
                + "".join(f"<td>{_esc(v)}</td>" for v in data.values())
                + "</tr></table>"
            )
        parts.append("</article>")
    parts.append("</div></section>")
    return "\n".join(parts)


def _exec_summary_html(ex: Any) -> str:
    if isinstance(ex, str):
        ex = _parse_loose_json(ex)
    if not isinstance(ex, dict):
        return ""
    headline = ex.get("headline") or ""
    overview = ex.get("situation_overview") or ""
    parts = ['<section class="block executive"><h2>Executive summary</h2>']
    if headline:
        parts.append(f"<h1>{_esc(headline)}</h1>")
    if overview:
        parts.append(f'<p class="overview">{_esc(overview)}</p>')
    for label, key in [
        ("Key findings", "key_findings"),
        ("Risk highlights", "risk_highlights"),
        ("Next actions", "next_actions"),
    ]:
        items = ex.get(key) or []
        if isinstance(items, list) and items:
            parts.append(f"<h3>{label}</h3><ul>")
            for it in items:
                parts.append(f"<li>{_esc(it)}</li>")
            parts.append("</ul>")
    cs = ex.get("confidence_statement")
    if cs is not None:
        if isinstance(cs, dict):
            parts.append(f"<p class='conf'>{_esc(json.dumps(cs, indent=2))}</p>")
        else:
            parts.append(f"<p class='conf'>{_esc(cs)}</p>")
    parts.append("</section>")
    return "\n".join(parts)


def _kpi_row_html(kpis: list[dict[str, Any]]) -> str:
    if not kpis:
        return ""
    parts = ['<section class="block"><h2>KPI snapshot</h2><div class="kpi-row">']
    for k in kpis:
        parts.append('<div class="kpi">')
        parts.append(f'<div class="kpi-title">{_esc(k.get("metric", "—"))}</div>')
        parts.append(f'<div class="kpi-value">{_esc(k.get("value", "—"))}</div>')
        ch = k.get("change")
        if ch is not None and str(ch) != "":
            parts.append(f'<div class="kpi-change">{_esc(ch)}</div>')
        src = k.get("source_agent")
        if src:
            parts.append(f'<div class="kpi-src">{_esc(src)}</div>')
        parts.append("</div>")
    parts.append("</div></section>")
    return "\n".join(parts)


def _recs_html(recs: list[dict[str, Any]], title: str = "Recommendations") -> str:
    if not recs:
        return ""
    parts = [f'<section class="block"><h2>{_esc(title)}</h2><table class="data-table">']
    parts.append("<thead><tr><th>Action</th><th>Priority</th><th>Confidence</th></tr></thead><tbody>")
    for r in recs:
        action = r.get("action") or r.get("text") or r.get("recommendation") or "—"
        pri = r.get("priority") or "—"
        conf = r.get("confidence")
        cstr = f"{float(conf):.0%}" if conf is not None else "—"
        parts.append(
            f"<tr><td>{_esc(action)}</td><td>{_esc(pri)}</td><td>{_esc(cstr)}</td></tr>"
        )
    parts.append("</tbody></table></section>")
    return "\n".join(parts)


def _swot_html(swot: dict[str, Any]) -> str:
    if not any(swot.get(q) for q in ("strengths", "weaknesses", "opportunities", "threats")):
        return ""
    parts = ['<section class="block"><h2>SWOT analysis</h2><div class="swot-grid">']
    for key, label in [
        ("strengths", "Strengths"),
        ("weaknesses", "Weaknesses"),
        ("opportunities", "Opportunities"),
        ("threats", "Threats"),
    ]:
        items = swot.get(key) or []
        if not items:
            continue
        parts.append(f'<div class="swot-col"><h3>{_esc(label)}</h3><ul>')
        for it in items:
            if isinstance(it, dict):
                txt = it.get("item") or it.get("description") or json.dumps(it)
                ev = it.get("evidence") or ""
                line = _esc(txt)
                if ev:
                    line += f'<br/><span class="ev">{_esc(ev)}</span>'
            else:
                line = _esc(it)
            parts.append(f"<li>{line}</li>")
        parts.append("</ul></div>")
    parts.append("</div></section>")
    return "\n".join(parts)


def _confidence_html(viz: dict[str, Any]) -> str:
    oc = viz.get("overall_confidence")
    cb = viz.get("confidence_breakdown") or {}
    if oc is None and not cb:
        return ""
    parts = ['<section class="block"><h2>Confidence</h2>']
    if oc is not None:
        try:
            parts.append(f"<p><strong>Overall:</strong> {float(oc):.0%}</p>")
        except (TypeError, ValueError):
            parts.append(f"<p><strong>Overall:</strong> {_esc(oc)}</p>")
    if isinstance(cb, dict) and cb:
        parts.append("<ul>")
        for k, v in cb.items():
            try:
                parts.append(f"<li>{_esc(k)}: {float(v):.0%}</li>")
            except (TypeError, ValueError):
                parts.append(f"<li>{_esc(k)}: {_esc(v)}</li>")
        parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _single_forecast_figure(f: dict) -> go.Figure | None:
    """Build one time-series figure; returns None if data is unusable."""
    try:
        metric = f.get("metric") or f.get("name") or "Forecast"
        hist = f.get("historical") or []
        pred = f.get("predicted") or []
        dates: list[str] = []
        vals: list[float] = []
        lower: list[float | None] = []
        upper: list[float | None] = []
        for p in hist:
            if isinstance(p, dict):
                dates.append(str(p.get("date", "")))
                vals.append(_safe_float(p.get("value"), 0.0))
                lower.append(None)
                upper.append(None)
        for p in pred:
            if isinstance(p, dict):
                dates.append(str(p.get("date", "")))
                vals.append(_safe_float(p.get("value"), 0.0))
                lo = p.get("lower")
                hi = p.get("upper")
                lower.append(_opt_float(lo))
                upper.append(_opt_float(hi))
        if not dates or len(dates) != len(vals):
            return None
        fig = go.Figure()
        if any(x is not None for x in lower) and any(x is not None for x in upper):
            u = [x if x is not None else v for x, v in zip(upper, vals)]
            lo = [x if x is not None else v for x, v in zip(lower, vals)]
            fig.add_trace(
                go.Scatter(x=dates, y=u, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
            )
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=lo,
                    mode="lines",
                    line=dict(width=0),
                    fillcolor="rgba(59, 130, 246, 0.22)",
                    fill="tonexty",
                    name="Confidence",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=vals,
                mode="lines",
                name="Series",
                line=dict(color=CHART_COLORS["accent"], width=2),
            )
        )
        td = f.get("trend_direction") or ""
        fig.update_layout(
            **_layout(title=dict(text=f"{metric} ({td})" if td else str(metric), font=dict(color="#e8ecf1"))),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Value"),
        )
        return fig
    except Exception as e:
        logger.warning("forecast chart skipped: %s", e)
        return None


def chart_forecasts(forecasts: list[Any]) -> str:
    if not forecasts:
        return ""
    out: list[str] = []
    for f in forecasts:
        if not isinstance(f, dict):
            continue
        fig = _single_forecast_figure(f)
        if fig is None:
            continue
        metric = str(f.get("metric") or f.get("name") or "Forecast")
        out.append(f'<div class="chart-wrap"><h3>{_esc(metric)}</h3>{_fig_div(fig)}</div>')
    return "\n".join(out)


def _radar_figure(insights: list[dict[str, Any]]) -> go.Figure | None:
    if len(insights) < 1:
        return None
    try:
        dims = insights[:8]
        # Match UI RadarChart: single-insight runs still render (closed shape needs ≥2 vertices)
        if len(dims) == 1:
            dims = [dims[0], dims[0]]
        labels = [str(d.get("title") or "?")[:40] for d in dims]
        current = [_safe_float((d.get("data") or {}).get("current"), 0.0) for d in dims]
        predicted = []
        for d in dims:
            data = d.get("data") or {}
            cur = _safe_float(data.get("current"), 0.0)
            pct = _safe_float(data.get("change_pct"), 0.0)
            predicted.append(cur * (1 + pct / 100.0))
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(r=current + [current[0]], theta=labels + [labels[0]], name="Current", fill="toself")
        )
        fig.add_trace(
            go.Scatterpolar(
                r=predicted + [predicted[0]], theta=labels + [labels[0]], name="Predicted", fill="toself"
            )
        )
        fig.update_layout(
            **_layout(),
            polar=dict(bgcolor="#0f172a", radialaxis=dict(visible=True, gridcolor=CHART_COLORS["grid"])),
            showlegend=True,
            title=dict(text="Insight dimensions (current vs implied predicted)", font=dict(color="#e8ecf1")),
        )
        return fig
    except Exception as e:
        logger.warning("radar chart skipped: %s", e)
        return None


def chart_radar(insights: list[dict[str, Any]]) -> str | None:
    fig = _radar_figure(insights)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _waterfall_figure(drivers: list[dict[str, Any]]) -> go.Figure | None:
    if not drivers:
        return None
    try:
        labels = [str(d.get("factor", "?")) for d in drivers]
        vals = [_safe_float(d.get("impact_pct"), 0.0) for d in drivers]
        measure: list[str] = ["relative"] * len(drivers)
        net = sum(vals)
        labels = labels + ["Net impact"]
        vals = vals + [net]
        measure = measure + ["total"]
        fig = go.Figure(
            go.Waterfall(
                name="Drivers",
                orientation="v",
                measure=measure,
                x=labels,
                textposition="outside",
                y=vals,
                connector=dict(line=dict(color="#64748b", width=1)),
            )
        )
        fig.update_layout(**_layout(title=dict(text="Impact drivers", font=dict(color="#e8ecf1"))))
        return fig
    except Exception as e:
        logger.warning("waterfall chart skipped: %s", e)
        return None


def chart_waterfall(drivers: list[dict[str, Any]]) -> str | None:
    fig = _waterfall_figure(drivers)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _anomaly_figure(anomalies: list[dict[str, Any]]) -> go.Figure | None:
    if not anomalies:
        return None
    try:
        dates = [str(a.get("date", "")) for a in anomalies]
        actual = [_safe_float(a.get("actual"), 0.0) for a in anomalies]
        expected = [_safe_float(a.get("expected"), 0.0) for a in anomalies]
        hover = [
            f"{a.get('metric','')}<br>Cause: {a.get('root_cause','')}" for a in anomalies
        ]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=actual,
                mode="markers+text",
                name="Actual",
                text=[str(a.get("metric", ""))[:20] for a in anomalies],
                textposition="top center",
                marker=dict(size=12, color=CHART_COLORS["negative"], symbol="diamond"),
                customdata=hover,
                hovertemplate="%{customdata}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=expected,
                mode="markers",
                name="Expected",
                marker=dict(size=8, color=CHART_COLORS["neutral"], symbol="circle-open"),
            )
        )
        fig.update_layout(**_layout(title=dict(text="Anomaly timeline", font=dict(color="#e8ecf1"))))
        return fig
    except Exception as e:
        logger.warning("anomaly chart skipped: %s", e)
        return None


def chart_anomalies(anomalies: list[dict[str, Any]]) -> str | None:
    fig = _anomaly_figure(anomalies)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _sentiment_figure(sent: dict[str, Any]) -> go.Figure | None:
    dist = sent.get("sentiment_distribution")
    if not isinstance(dist, list) or not dist:
        return None
    try:
        labels = [str(x.get("label", "")) for x in dist]
        values = [_safe_float(x.get("pct", x.get("count")), 0.0) for x in dist]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.35)])
        fig.update_layout(**_layout(title=dict(text="Sentiment distribution", font=dict(color="#e8ecf1"))))
        return fig
    except Exception as e:
        logger.warning("sentiment chart skipped: %s", e)
        return None


def chart_sentiment(sent: dict[str, Any]) -> str | None:
    fig = _sentiment_figure(sent)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _sankey_figure(bottlenecks: list[dict[str, Any]]) -> go.Figure | None:
    if not bottlenecks:
        return None
    try:
        node_labels = ["Pipeline input"]
        node_labels += [str(b.get("stage", "?")) for b in bottlenecks]
        node_labels.append("Output")
        n = len(node_labels)
        src: list[int] = []
        tgt: list[int] = []
        val: list[float] = []
        source_id = 0
        for i, b in enumerate(bottlenecks):
            stage_idx = 1 + i
            src.append(source_id)
            tgt.append(stage_idx)
            val.append(max(_safe_float(b.get("time_pct"), 1.0), 0.01))
        sink = n - 1
        for i, b in enumerate(bottlenecks):
            stage_idx = 1 + i
            src.append(stage_idx)
            tgt.append(sink)
            val.append(max(_safe_float(b.get("cost_pct"), 1.0), 0.01))
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(label=node_labels, pad=12, thickness=14),
                    link=dict(source=src, target=tgt, value=val),
                )
            ]
        )
        fig.update_layout(**_layout(title=dict(text="Process bottlenecks", font=dict(color="#e8ecf1"))))
        return fig
    except Exception as e:
        logger.warning("sankey chart skipped: %s", e)
        return None


def chart_sankey_bottlenecks(bottlenecks: list[dict[str, Any]]) -> str | None:
    fig = _sankey_figure(bottlenecks)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _bubble_roi_figure(processes: list[dict[str, Any]]) -> go.Figure | None:
    if not processes:
        return None
    try:
        effort_map = {"low": 1, "medium": 2, "high": 3, "very_high": 4}

        def eff(e: str) -> float:
            return float(effort_map.get(str(e).lower(), 2))

        xs = [eff(p.get("implementation_effort", "medium")) for p in processes]
        ys = [_safe_float(p.get("impact_score"), 0.0) for p in processes]
        roi = [_safe_float(p.get("roi_months"), 1.0) or 1.0 for p in processes]
        max_roi = max(roi) if roi else 1
        sizes = [max(8, min(60, 400 * max_roi / max(r, 0.1))) for r in roi]
        labels = [str(p.get("name", "")) for p in processes]
        fig = go.Figure(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=labels,
                textposition="top center",
                marker=dict(size=sizes, color=CHART_COLORS["accent"], opacity=0.85, line=dict(width=1, color="#fff")),
            )
        )
        fig.update_layout(
            **_layout(
                title=dict(text="Automation opportunity matrix (effort vs impact, size ∝ ROI)", font=dict(color="#e8ecf1")),
                xaxis=dict(title="Implementation effort (1=low → 4=very high)"),
                yaxis=dict(title="Impact score"),
            )
        )
        return fig
    except Exception as e:
        logger.warning("bubble chart skipped: %s", e)
        return None


def chart_bubble_roi(processes: list[dict[str, Any]]) -> str | None:
    fig = _bubble_roi_figure(processes)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _roi_saved_figure(processes: list[dict[str, Any]]) -> go.Figure | None:
    """Matches ROIBubbles.tsx — hours saved vs cost saved, marker size ∝ ROI months."""
    if not processes:
        return None
    try:
        xs = [
            _safe_float(p.get("current_time_hours"), 0.0) - _safe_float(p.get("automated_time_hours"), 0.0)
            for p in processes
        ]
        ys = [
            _safe_float(p.get("cost_current"), 0.0) - _safe_float(p.get("cost_automated"), 0.0)
            for p in processes
        ]
        roi = [_safe_float(p.get("roi_months"), 1.0) or 1.0 for p in processes]
        labels = [str(p.get("name", "")) for p in processes]
        sizes = [max(10, min(52, 4 * r)) for r in roi]
        fig = go.Figure(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=labels,
                textposition="top center",
                marker=dict(
                    size=sizes,
                    color=CHART_COLORS["positive"],
                    opacity=0.88,
                    line=dict(width=1, color="#fff"),
                ),
            )
        )
        fig.update_layout(
            **_layout(
                title=dict(text="ROI analysis (hours saved vs cost saved)", font=dict(color="#e8ecf1")),
                xaxis=dict(title="Hours saved"),
                yaxis=dict(title="Cost saved ($)"),
            )
        )
        return fig
    except Exception as e:
        logger.warning("roi saved chart skipped: %s", e)
        return None


def chart_roi_saved(processes: list[dict[str, Any]]) -> str | None:
    fig = _roi_saved_figure(processes)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _kg_figure(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> go.Figure | None:
    if not nodes:
        return None
    try:
        ids = [str(n.get("id", i)) for i, n in enumerate(nodes)]
        pos: dict[str, tuple[float, float]] = {}
        for i, nid in enumerate(ids):
            ang = 2 * math.pi * i / max(len(ids), 1)
            pos[nid] = (math.cos(ang), math.sin(ang))
        xe: list[float] = []
        ye: list[float] = []
        for e in edges:
            s = str(e.get("source", ""))
            t = str(e.get("target", ""))
            if s in pos and t in pos:
                xe += [pos[s][0], pos[t][0], None]
                ye += [pos[s][1], pos[t][1], None]
        fig = go.Figure()
        if xe:
            fig.add_trace(go.Scatter(x=xe, y=ye, mode="lines", line=dict(color="#475569", width=1), hoverinfo="skip"))
        fig.add_trace(
            go.Scatter(
                x=[pos.get(i, (0, 0))[0] for i in ids],
                y=[pos.get(i, (0, 0))[1] for i in ids],
                mode="markers+text",
                text=[str(n.get("label", ""))[:24] for n in nodes],
                textposition="bottom center",
                marker=dict(size=18, color=CHART_COLORS["positive"]),
                customdata=[
                    "<br>".join(
                        [
                            str(n.get("context", ""))[:200],
                            " · ".join(str(x) for x in (n.get("insights") or [])[:3]),
                        ]
                    )
                    for n in nodes
                ],
                hovertemplate="%{customdata}<extra></extra>",
            )
        )
        fig.update_layout(
            **_layout(
                title=dict(text="Knowledge graph (overview)", font=dict(color="#e8ecf1")),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )
        )
        return fig
    except Exception as e:
        logger.warning("kg chart skipped: %s", e)
        return None


def chart_kg(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str | None:
    fig = _kg_figure(nodes, edges)
    if fig is None:
        return None
    return f'<div class="chart-wrap">{_fig_div(fig)}</div>'


def _conflicts_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    parts = ['<section class="block"><h2>Detected conflicts</h2><table class="data-table">']
    parts.append(
        "<thead><tr><th>Description</th><th>Severity</th><th>Resolution</th></tr></thead><tbody>"
    )
    for r in rows:
        parts.append(
            f"<tr><td>{_esc(r.get('description',''))}</td>"
            f"<td>{_esc(r.get('severity',''))}</td>"
            f"<td>{_esc(r.get('resolution_suggestion',''))}</td></tr>"
        )
    parts.append("</tbody></table></section>")
    return "\n".join(parts)


def _render_track_charts(track: str, ar: dict[str, Any]) -> str:
    """Plotly sections aligned with TrackRenderer + knowledge graph tab."""
    chunks: list[str] = []
    tf = ar.get("trend_forecasting")
    if isinstance(tf, str):
        tf = _parse_loose_json(tf)
    if isinstance(tf, dict):
        fc = tf.get("forecasts") or []
        if isinstance(fc, list) and fc and chart_export_allowed(track, "forecasts"):
            chunks.append('<section class="block"><h2>Forecasts</h2>')
            chunks.append(chart_forecasts(fc))
            chunks.append("</section>")
        dr = tf.get("drivers") or []
        if isinstance(dr, list) and dr and chart_export_allowed(track, "drivers"):
            wf = chart_waterfall(dr)
            if wf:
                chunks.append('<section class="block"><h2>Drivers</h2>' + wf + "</section>")
        an = tf.get("anomalies") or []
        if isinstance(an, list) and an and chart_export_allowed(track, "anomalies"):
            af = chart_anomalies(an)
            if af:
                chunks.append('<section class="block"><h2>Anomalies</h2>' + af + "</section>")

    ig = ar.get("insight_generation")
    if isinstance(ig, str):
        ig = _parse_loose_json(ig)
    insights: list[Any] = []
    if isinstance(ig, dict):
        insights = list(ig.get("insights") or [])

    if track == "predictive" and insights and chart_export_allowed(track, "radar"):
        rf = chart_radar([i for i in insights if isinstance(i, dict)])
        if rf:
            chunks.append('<section class="block"><h2>Current vs predicted</h2>' + rf + "</section>")

    sent = ar.get("sentiment_analysis")
    if isinstance(sent, dict) and chart_export_allowed(track, "sentiment"):
        sf = chart_sentiment(sent)
        if sf:
            chunks.append('<section class="block"><h2>Sentiment</h2>' + sf + "</section>")

    if track == "automation":
        astr = ar.get("automation_strategy")
        if isinstance(astr, dict):
            b = astr.get("bottlenecks") or []
            if isinstance(b, list) and b and chart_export_allowed(track, "sankey"):
                sf = chart_sankey_bottlenecks(b)
                if sf:
                    chunks.append(
                        '<section class="block"><h2>Process bottlenecks</h2>' + sf + "</section>"
                    )
            procs = astr.get("processes") or []
            if isinstance(procs, list) and procs:
                if chart_export_allowed(track, "opportunity_matrix"):
                    bf = chart_bubble_roi(procs)
                    if bf:
                        chunks.append(
                            '<section class="block"><h2>Opportunity matrix</h2>' + bf + "</section>"
                        )
                if chart_export_allowed(track, "roi_bubbles"):
                    rs = chart_roi_saved(procs)
                    if rs:
                        chunks.append(
                            '<section class="block"><h2>ROI analysis</h2>' + rs + "</section>"
                        )

    kg = ar.get("knowledge_graph_builder")
    if isinstance(kg, dict) and chart_export_allowed(track, "knowledge_graph"):
        nodes = kg.get("nodes") or []
        edges = kg.get("edges") or []
        if isinstance(nodes, list) and nodes:
            kf = chart_kg(nodes, edges if isinstance(edges, list) else [])
            if kf:
                chunks.append(
                    '<section class="block"><h2>Knowledge graph</h2><p class="hint">'
                    "Same graph as the &quot;Knowledge graph&quot; tab. "
                    "Interactive plot; use Print → PDF to save.</p>"
                    + kf
                    + "</section>"
                )

    cd = ar.get("conflict_detection")
    if isinstance(cd, dict):
        con = cd.get("contradictions") or []
        if isinstance(con, list) and con:
            chunks.append(_conflicts_table([x for x in con if isinstance(x, dict)]))

    return "\n".join(chunks)


def collect_figures_for_pdf(track: str, ar: dict[str, Any]) -> list[tuple[str, go.Figure]]:
    """Plotly figures for PDF — same allowlist as the analysis UI (+ Knowledge graph tab)."""
    figures: list[tuple[str, go.Figure]] = []
    tf = ar.get("trend_forecasting")
    if isinstance(tf, str):
        tf = _parse_loose_json(tf)
    if isinstance(tf, dict):
        if chart_export_allowed(track, "forecasts"):
            for f in tf.get("forecasts") or []:
                if isinstance(f, dict):
                    fig = _single_forecast_figure(f)
                    if fig is not None:
                        figures.append((str(f.get("metric") or f.get("name") or "Forecast"), fig))
        dr = tf.get("drivers") or []
        if isinstance(dr, list) and dr and chart_export_allowed(track, "drivers"):
            wf = _waterfall_figure(dr)
            if wf is not None:
                figures.append(("Impact drivers", wf))
        an = tf.get("anomalies") or []
        if isinstance(an, list) and an and chart_export_allowed(track, "anomalies"):
            af = _anomaly_figure(an)
            if af is not None:
                figures.append(("Anomaly timeline", af))

    ig = ar.get("insight_generation")
    if isinstance(ig, str):
        ig = _parse_loose_json(ig)
    insights: list[Any] = []
    if isinstance(ig, dict):
        insights = [i for i in (ig.get("insights") or []) if isinstance(i, dict)]

    if track == "predictive" and insights and chart_export_allowed(track, "radar"):
        rf = _radar_figure(insights)
        if rf is not None:
            figures.append(("Insight dimensions (radar)", rf))

    sent = ar.get("sentiment_analysis")
    if isinstance(sent, dict) and chart_export_allowed(track, "sentiment"):
        sf = _sentiment_figure(sent)
        if sf is not None:
            figures.append(("Sentiment distribution", sf))

    if track == "automation":
        astr = ar.get("automation_strategy")
        if isinstance(astr, dict):
            b = astr.get("bottlenecks") or []
            if isinstance(b, list) and b and chart_export_allowed(track, "sankey"):
                sf = _sankey_figure(b)
                if sf is not None:
                    figures.append(("Process bottlenecks (Sankey)", sf))
            procs = astr.get("processes") or []
            if isinstance(procs, list) and procs:
                if chart_export_allowed(track, "opportunity_matrix"):
                    bf = _bubble_roi_figure(procs)
                    if bf is not None:
                        figures.append(("Opportunity matrix", bf))
                if chart_export_allowed(track, "roi_bubbles"):
                    rs = _roi_saved_figure(procs)
                    if rs is not None:
                        figures.append(("ROI analysis (hours vs cost saved)", rs))

    kg = ar.get("knowledge_graph_builder")
    if isinstance(kg, dict) and chart_export_allowed(track, "knowledge_graph"):
        nodes = kg.get("nodes") or []
        edges = kg.get("edges") or []
        if isinstance(nodes, list) and nodes:
            kf = _kg_figure(nodes, edges if isinstance(edges, list) else [])
            if kf is not None:
                figures.append(("Knowledge graph", kf))

    return figures


def knowledge_graph_node_rows(nodes: list[dict[str, Any]], max_nodes: int = 40) -> list[list[str]]:
    """Table rows for PDF: one row per node with fields shown in the UI detail panel."""
    rows: list[list[str]] = []
    for n in nodes[:max_nodes]:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id", ""))
        label = str(n.get("label", ""))
        ntype = str(n.get("type", ""))
        val = n.get("value")
        val_s = "" if val is None else str(val)
        ctx = str(n.get("context", ""))[:500]
        ins_list = n.get("insights") or []
        ins_s = ""
        if isinstance(ins_list, list):
            ins_s = " · ".join(str(x) for x in ins_list[:8])[:800]
        rows.append([nid, label, ntype, val_s, ctx, ins_s])
    return rows


def _document_css() -> str:
    return """
    :root { --bg:#0f172a; --card:#1e293b; --text:#e8ecf1; --muted:#94a3b8; --accent:#38bdf8; --border:#334155; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Segoe UI, system-ui, sans-serif; background: var(--bg); color: var(--text); line-height:1.5; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; }
    header.doc-head { border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
    header.doc-head h1 { margin: 0 0 8px; font-size: 1.75rem; }
    header.doc-head .meta { color: var(--muted); font-size: 0.9rem; }
    .block { margin-bottom: 2rem; }
    .block h2 { color: var(--accent); font-size: 1.15rem; margin: 0 0 12px; }
    .executive h1 { font-size: 1.35rem; color: var(--text); }
    .overview { color: var(--muted); font-size: 1rem; }
    .kpi-row { display: flex; flex-wrap: wrap; gap: 12px; }
    .kpi { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; min-width: 140px; flex: 1; }
    .kpi-title { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }
    .kpi-value { font-size: 1.25rem; font-weight: 600; }
    .kpi-change { font-size: 0.85rem; color: #4ade80; }
    .kpi-src { font-size: 0.75rem; color: var(--muted); }
    .insight-grid { display: grid; gap: 16px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
    .insight-card h3 { margin: 0 0 8px; font-size: 1.05rem; }
    .insight-desc { color: var(--text); margin: 0 0 8px; }
    .meta { font-size: 0.85rem; color: var(--muted); margin: 0; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 6px; background: #334155; margin-right: 8px; font-size: 0.8rem; }
    .impact-high { background: rgba(248,113,113,0.2); color: #fecaca; }
    .impact-medium { background: rgba(251,191,36,0.2); color: #fde68a; }
    .impact-low { background: rgba(74,222,128,0.15); color: #bbf7d0; }
    table.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    table.data-table th, table.data-table td { border: 1px solid var(--border); padding: 8px 10px; text-align: left; }
    table.data-table thead { background: #0b1220; }
    table.mini { font-size: 0.8rem; margin-top: 8px; border-collapse: collapse; }
    table.mini th, table.mini td { border: 1px solid var(--border); padding: 4px 8px; }
    .swot-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
    .swot-col { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
    .swot-col ul { margin: 0; padding-left: 1.1rem; }
    .ev { color: var(--muted); font-size: 0.85rem; }
    .chart-wrap { margin-bottom: 24px; background: #111827; border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
    .chart-wrap h3 { margin: 0 0 8px; font-size: 1rem; color: var(--muted); }
    .plotly-chart-host { min-height: 380px; }
    .hint { color: var(--muted); font-size: 0.9rem; }
    @media print {
      body { background: #fff; color: #111; }
      .chart-wrap { break-inside: avoid; }
    }
    """


def generate_html_report(
    run_slug: str,
    run_dir: str,
    run_data: dict[str, Any],
    replay_payload: dict[str, Any] | None,
) -> str:
    ar = merge_replay_agent_results(replay_payload)
    if not ar:
        ar = _merge_agent_results(replay_payload, run_dir)
    viz = _viz_plan(replay_payload, ar)
    track = str(run_data.get("track") or "")
    if not track and replay_payload:
        fr = replay_payload.get("final_report")
        if isinstance(fr, dict) and fr.get("track"):
            track = str(fr.get("track") or "")

    ig = ar.get("insight_generation")
    if isinstance(ig, str):
        ig = _parse_loose_json(ig)
    insights_list: list[Any] = []
    recs_ig: list[dict[str, Any]] = []
    if isinstance(ig, dict):
        insights_list = list(ig.get("insights") or [])
        recs_ig = [x for x in (ig.get("recommendations") or []) if isinstance(x, dict)]

    ex = ar.get("executive_summary")
    swot = ar.get("swot_analysis")
    if isinstance(swot, str):
        swot = _parse_loose_json(swot)
    if not isinstance(swot, dict):
        swot = {}

    kpi_cards = viz.get("kpi_cards") or []
    if not kpi_cards and isinstance(ar.get("output_evaluator"), dict):
        kpi_cards = (ar.get("output_evaluator") or {}).get("kpi_cards") or []

    recs_ev = [x for x in (viz.get("recommendations") or []) if isinstance(x, dict)]
    recs = recs_ev if recs_ev else recs_ig

    parts: list[str] = []
    parts.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'/>")
    parts.append(f"<title>Datalyze — {_esc(run_slug)}</title>")
    parts.append(f"<script src='{PLOTLY_CDN}' charset='utf-8'></script>")
    parts.append(f"<style>{_document_css()}</style></head><body>")
    parts.append('<div class="wrap">')
    parts.append("<header class='doc-head'>")
    parts.append("<h1>Datalyze analysis report</h1>")
    parts.append(
        f"<p class='meta'>Run <strong>{_esc(run_slug)}</strong> · "
        f"Track {_esc(track or '—')} · "
        f"Status {_esc(run_data.get('status', '—'))}<br/>"
        f"Started {_esc(run_data.get('started_at', '—'))} · "
        f"Ended {_esc(run_data.get('ended_at', '—'))}</p>"
    )
    if run_data.get("summary"):
        parts.append(f"<p class='meta'>{_esc(run_data['summary'])}</p>")
    parts.append(
        "<p class='meta'>Open this file in a browser for interactive charts. "
        "Use <strong>Print → Save as PDF</strong> for a PDF copy.</p>"
    )
    parts.append("</header>")

    parts.append(_kpi_row_html([x for x in kpi_cards if isinstance(x, dict)]))
    parts.append(_insight_cards_html(insights_list))
    parts.append(_exec_summary_html(ex))
    parts.append(_render_track_charts(track, ar))
    parts.append(_recs_html(recs))
    parts.append(_swot_html(swot))
    parts.append(_confidence_html(viz))

    parts.append("</div></body></html>")
    return "\n".join(parts)
