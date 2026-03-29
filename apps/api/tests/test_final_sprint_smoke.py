"""Fast smoke checks aligned with final sprint plans (orchestrator, admin, agents, OpenAPI)."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient


def test_is_agent_ready_treats_skipped_deps_as_satisfied() -> None:
    from services.orchestrator_runtime import policies

    deps = {"insight_generation": ["aggregator", "trend_forecasting"]}
    assert not policies.is_agent_ready(
        "insight_generation",
        ["aggregator"],
        deps,
        skipped=[],
    )
    assert policies.is_agent_ready(
        "insight_generation",
        ["aggregator"],
        deps,
        skipped=["trend_forecasting"],
    )


def test_time_budget_includes_wrap_up_phase() -> None:
    from services.orchestrator_runtime import policies

    budget = policies.check_time_budget(time.time(), max_seconds=420)
    assert set(budget.keys()) >= {
        "elapsed_seconds",
        "max_seconds",
        "remaining_seconds",
        "budget_exceeded",
        "in_wrap_up_phase",
        "wrap_up_started_at",
    }
    assert budget["max_seconds"] == 420


def test_track_profiles_cover_all_tracks() -> None:
    from services.orchestrator_runtime.track_profiles import TRACK_PROFILES, TrackID

    assert set(TRACK_PROFILES.keys()) == set(TrackID)


def test_file_type_classifier_routing_shape() -> None:
    from services.agents.file_type_classifier import classify_file_types

    meta = [
        {"path": "revenue.csv", "mime": "text/csv"},
        {"path": "book.xlsx", "mime": ""},
    ]
    out = classify_file_types(meta)
    assert "file_routing_map" in out
    assert isinstance(out["file_routing_map"], dict)


def test_pipeline_classifier_schema_includes_routing_fields() -> None:
    from services.agents import pipeline_classifier as pc

    assert "recommended_agents" in pc.OUTPUT_SCHEMA["required"]
    assert "skip_agents" in pc.OUTPUT_SCHEMA["required"]


def test_openapi_includes_sprint_routes() -> None:
    from main import app

    with TestClient(app) as client:
        r = client.get("/openapi.json")
        assert r.status_code == 200
        paths = r.json().get("paths") or {}
        path_keys = set(paths.keys())

    assert "/api/v1/admin/replay" in path_keys
    assert any(
        pk.startswith("/api/v1/admin/replay/") and "track" in pk for pk in path_keys
    )
    assert any("/export/pdf" in pk for pk in path_keys)
    assert any("/export/html" in pk for pk in path_keys)


def test_root_ok() -> None:
    from main import app

    with TestClient(app) as client:
        r = client.get("/")
    assert r.status_code == 200
    assert "running" in r.json().get("message", "").lower()
