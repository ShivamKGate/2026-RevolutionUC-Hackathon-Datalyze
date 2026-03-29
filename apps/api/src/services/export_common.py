"""Shared helpers for HTML/PDF exports (replay merge, agent output parsing)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def read_agent_outputs(run_dir: str) -> dict[str, dict[str, Any]]:
    """Read individual agent output envelopes from the run directory."""
    agent_dir = Path(run_dir) / "context" / "agent_outputs"
    outputs: dict[str, dict[str, Any]] = {}
    if not agent_dir.is_dir():
        return outputs
    for child in agent_dir.iterdir():
        if not child.is_dir():
            continue
        agent_id = child.name
        steps = sorted(child.glob("step_*.json"), key=lambda p: p.name)
        if not steps:
            continue
        try:
            data = json.loads(steps[-1].read_text(encoding="utf-8"))
            outputs[agent_id] = data
        except (json.JSONDecodeError, OSError):
            pass
    return outputs


def extract_parsed_output(envelope: dict[str, Any]) -> dict[str, Any]:
    """Pull structured data from an agent envelope's artifacts."""
    for artifact in envelope.get("artifacts", []):
        if isinstance(artifact, dict):
            parsed = artifact.get("parsed_output") or artifact.get("data")
            if isinstance(parsed, dict):
                return parsed
            if isinstance(artifact.get("content"), dict):
                return artifact["content"]
    if isinstance(envelope.get("summary"), dict):
        return envelope["summary"]
    return {}


def parse_loose_json(val: Any) -> Any:
    if isinstance(val, dict):
        return val
    if not isinstance(val, str):
        return val
    s = val.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", s)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return val


def is_weak_section(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        return len(val.strip()) < 2
    if isinstance(val, dict):
        return len(val) == 0
    return False


def merge_replay_agent_results(replay: dict[str, Any] | None) -> dict[str, Any]:
    """Agent results exactly as stored for the UI (replay JSON only — no on-disk step merges)."""
    if not replay:
        return {}
    ar: dict[str, Any] = {}
    raw = replay.get("agent_results")
    if isinstance(raw, dict):
        ar = {k: v for k, v in raw.items()}
    fr = replay.get("final_report")
    if isinstance(fr, dict):
        far = fr.get("agent_results")
        if isinstance(far, dict):
            for k, v in far.items():
                if k not in ar or is_weak_section(ar.get(k)):
                    ar[k] = v
    out: dict[str, Any] = {}
    for k, v in ar.items():
        coerced = parse_loose_json(v)
        out[k] = coerced if isinstance(coerced, dict) else v
    return out


def merge_agent_results(replay: dict[str, Any] | None, run_dir: str) -> dict[str, Any]:
    ar: dict[str, Any] = {}
    if replay:
        raw = replay.get("agent_results")
        if isinstance(raw, dict):
            ar = {k: v for k, v in raw.items()}
        fr = replay.get("final_report")
        if isinstance(fr, dict):
            far = fr.get("agent_results")
            if isinstance(far, dict):
                for k, v in far.items():
                    if k not in ar or is_weak_section(ar.get(k)):
                        ar[k] = v
    disk = read_agent_outputs(run_dir)
    for aid, env in disk.items():
        parsed = extract_parsed_output(env)
        if isinstance(parsed, dict) and parsed:
            if aid not in ar or is_weak_section(ar.get(aid)):
                ar[aid] = parsed
    out: dict[str, Any] = {}
    for k, v in ar.items():
        coerced = parse_loose_json(v)
        out[k] = coerced if isinstance(coerced, dict) else v
    return out


def chart_export_allowed(track: str | None, chart_key: str) -> bool:
    """
    Which chart groups to include in HTML/PDF exports — aligned with TrackRenderer
    (analysis tab). Keys: forecasts, drivers, anomalies, radar, sentiment, sankey,
    opportunity_matrix, roi_bubbles, knowledge_graph.

    Sentiment is omitted: no Sentiment chart on predictive/automation/etc. templates.
    On-disk merged agent outputs are not used for chart parity (see merge_replay_agent_results).
    """
    ck = chart_key.strip().lower()
    if ck == "sentiment":
        return False
    t = (track or "").strip().lower()
    if t == "predictive":
        return ck in {"forecasts", "drivers", "anomalies", "radar", "knowledge_graph"}
    if t == "automation":
        return ck in {"sankey", "opportunity_matrix", "roi_bubbles", "knowledge_graph"}
    if t == "optimization":
        return ck in {"knowledge_graph"}
    if t == "supply_chain":
        return ck in {"knowledge_graph"}
    return ck in {
        "forecasts",
        "drivers",
        "anomalies",
        "radar",
        "sankey",
        "opportunity_matrix",
        "roi_bubbles",
        "knowledge_graph",
    }


def section_dict(ar: dict[str, Any], key: str) -> dict[str, Any]:
    """Get agent section as dict, parsing JSON strings when needed."""
    v = ar.get(key)
    if isinstance(v, str):
        v = parse_loose_json(v)
    return v if isinstance(v, dict) else {}
