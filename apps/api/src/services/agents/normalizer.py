"""
Agent output normalizer: maps per-agent JSON output into the orchestrator
adapter envelope format.

Adapter envelope contract:
{
    "status": "ok|warning|error",
    "summary": "string",
    "artifacts": [],
    "next_hints": [],
    "confidence": 0.0,
    "errors": []
}

This module is the integration seam between Shivam's specialization work
and Kartavya's orchestrator runtime. The orchestrator adapter should call
normalize_agent_output() rather than parsing raw agent text.
"""

from __future__ import annotations

import json
from typing import Any

from services.agents.contracts import AGENT_CONTRACTS, AgentContract


def _extract_summary(agent_id: str, output: dict[str, Any]) -> str:
    for key in ("summary", "answer", "narration_text"):
        if key in output:
            val = output[key]
            if isinstance(val, str):
                return val[:500]
    if "insights" in output and isinstance(output["insights"], list):
        count = len(output["insights"])
        return f"Generated {count} insight(s)"
    if "chunks" in output and isinstance(output["chunks"], list):
        return f"Processed {len(output['chunks'])} chunk(s)"
    if "nodes" in output:
        return f"Built graph with {len(output.get('nodes', []))} nodes"
    return f"Agent {agent_id} completed successfully"


def _extract_artifacts(output: dict[str, Any]) -> list[Any]:
    artifacts = []
    for key in ("artifacts", "chunks", "records", "sheets", "forecasts", "suggestions", "insights"):
        if key in output and isinstance(output[key], list):
            artifacts.extend(output[key])
    return artifacts


def _extract_confidence(output: dict[str, Any]) -> float:
    if "confidence" in output:
        try:
            return float(output["confidence"])
        except (TypeError, ValueError):
            pass
    if "confidence_scores" in output and isinstance(output["confidence_scores"], list):
        scores = [s for s in output["confidence_scores"] if isinstance(s, (int, float))]
        if scores:
            return sum(scores) / len(scores)
    return 0.85


def normalize_agent_output(
    agent_id: str,
    raw_output: str | dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []

    if isinstance(raw_output, str):
        text = raw_output.strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "summary": f"Agent {agent_id} returned invalid JSON",
                    "artifacts": [],
                    "next_hints": [],
                    "confidence": 0.0,
                    "errors": [f"JSON parse error: {e}"],
                }
        else:
            return {
                "status": "warning",
                "summary": text[:500],
                "artifacts": [],
                "next_hints": [],
                "confidence": 0.3,
                "errors": ["Output was plain text, not JSON"],
            }
    elif isinstance(raw_output, dict):
        parsed = raw_output
    else:
        return {
            "status": "error",
            "summary": f"Agent {agent_id} returned unexpected type: {type(raw_output).__name__}",
            "artifacts": [],
            "next_hints": [],
            "confidence": 0.0,
            "errors": ["Unexpected output type"],
        }

    if "errors" in parsed and isinstance(parsed["errors"], list) and parsed["errors"]:
        errors.extend(str(e) for e in parsed["errors"])

    contract = AGENT_CONTRACTS.get(agent_id)
    if contract:
        valid, schema_errors = contract.validate_output(parsed)
        if not valid:
            errors.extend(schema_errors)

    status = "ok"
    if errors:
        status = "warning" if any(k in parsed for k in (contract.required_keys if contract else [])) else "error"

    next_hints = parsed.get("next_hints", [])
    if not isinstance(next_hints, list):
        next_hints = []

    return {
        "status": status,
        "summary": _extract_summary(agent_id, parsed),
        "artifacts": _extract_artifacts(parsed),
        "next_hints": next_hints,
        "confidence": _extract_confidence(parsed),
        "errors": errors,
    }


def validate_envelope(envelope: dict[str, Any]) -> tuple[bool, list[str]]:
    required = {"status", "summary", "artifacts", "next_hints", "confidence", "errors"}
    missing = required - set(envelope.keys())
    errors = [f"Missing envelope key: {k}" for k in missing]
    if envelope.get("status") not in ("ok", "warning", "error"):
        errors.append(f"Invalid status value: {envelope.get('status')}")
    return len(errors) == 0, errors
