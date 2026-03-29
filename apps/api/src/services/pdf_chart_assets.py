"""Render static chart images for PDF export (matplotlib / networkx)."""

from __future__ import annotations

import io
import logging
from typing import Any

logger = logging.getLogger("pdf_chart_assets")

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None  # type: ignore[assignment]

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None  # type: ignore[assignment]


def _fig_bytes(fig) -> bytes | None:
    if fig is None:
        return None
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#1e293b")
        plt.close(fig)
        return buf.getvalue()
    except Exception as exc:  # pragma: no cover
        logger.warning("matplotlib savefig failed: %s", exc)
        try:
            plt.close(fig)
        except Exception:
            pass
        return None


def render_forecast_bar_chart(forecasts: list[dict[str, Any]]) -> bytes | None:
    """Bar chart of forecast metric vs a numeric value if parseable."""
    if plt is None or not forecasts:
        return None
    labels: list[str] = []
    values: list[float] = []
    for fc in forecasts[:12]:
        if not isinstance(fc, dict):
            continue
        m = str(fc.get("metric") or fc.get("name") or "—")[:24]
        labels.append(m)
        raw = fc.get("forecast") or fc.get("value") or fc.get("prediction")
        try:
            if raw is None and isinstance(fc.get("predicted"), list) and fc["predicted"]:
                last = fc["predicted"][-1]
                raw = last.get("value") if isinstance(last, dict) else last
            v = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            v = 0.0
        values.append(v)
    if not labels:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.barh(labels[::-1], values[::-1], color="#38bdf8")
    ax.set_facecolor("#1e293b")
    fig.patch.set_facecolor("#1e293b")
    ax.tick_params(colors="#e2e8f0", labelsize=8)
    ax.xaxis.label.set_color("#e2e8f0")
    ax.set_title("Forecast snapshot", color="#f1f5f9", fontsize=11)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    return _fig_bytes(fig)


def render_driver_bar_chart(drivers: list[dict[str, Any]]) -> bytes | None:
    if plt is None or not drivers:
        return None
    labels = [str(d.get("factor", "?"))[:28] for d in drivers[:10] if isinstance(d, dict)]
    vals = []
    for d in drivers[:10]:
        if not isinstance(d, dict):
            continue
        try:
            vals.append(float(d.get("impact_pct", 0)))
        except (TypeError, ValueError):
            vals.append(0.0)
    if len(vals) != len(labels):
        return None
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.barh(labels[::-1], vals[::-1], color="#4ade80")
    ax.set_facecolor("#1e293b")
    fig.patch.set_facecolor("#1e293b")
    ax.tick_params(colors="#e2e8f0", labelsize=8)
    ax.set_title("Driver impact (%)", color="#f1f5f9", fontsize=11)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    return _fig_bytes(fig)


def render_knowledge_graph_png(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> bytes | None:
    """Spring-layout graph PNG; falls back if networkx/matplotlib unavailable."""
    if plt is None or nx is None or not nodes:
        return None
    G = nx.Graph()
    node_ids: list[str] = []
    for n in nodes[:40]:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or n.get("label") or "")
        if not nid:
            continue
        lbl = str(n.get("label") or nid)[:20]
        G.add_node(nid, label=lbl)
        node_ids.append(nid)
    for e in edges[:80]:
        if not isinstance(e, dict):
            continue
        s, t = str(e.get("source", "")), str(e.get("target", ""))
        if s and t and s in G and t in G:
            G.add_edge(s, t)
    if G.number_of_nodes() == 0:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.set_facecolor("#1e293b")
    fig.patch.set_facecolor("#1e293b")
    pos = nx.spring_layout(G, seed=42, k=0.8)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#64748b", width=1.0, alpha=0.7)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#38bdf8", node_size=380, alpha=0.9)
    labels_map = {n: G.nodes[n].get("label", n)[:12] for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels_map, ax=ax, font_size=6, font_color="#f8fafc")
    ax.set_title("Knowledge graph (layout)", color="#f1f5f9", fontsize=11)
    ax.axis("off")
    return _fig_bytes(fig)
