"""Tests for Datalyze Auto pipeline routing (no live Gemini in CI)."""

from __future__ import annotations

import pytest

from services.datalyze_pipeline_pick import (
    normalize_pipeline_id,
    pick_custom_base_track,
)


def test_normalize_pipeline_id_basic() -> None:
    assert normalize_pipeline_id("predictive") == "predictive"
    assert normalize_pipeline_id("AUTOMATION") == "automation"
    assert normalize_pipeline_id("supply_chain") == "supply_chain"


def test_normalize_supply_chain_spaced() -> None:
    assert normalize_pipeline_id("supply chain") == "supply_chain"


def test_normalize_unknown_defaults() -> None:
    assert normalize_pipeline_id("nope") == "predictive"
    assert normalize_pipeline_id("") == "predictive"


def test_pick_custom_base_track_uses_model_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_pipeline_pick_completion(
        user_msg: str, system: str | None = None, max_tokens: int = 450
    ) -> str:
        assert "public_scrape_enabled" in user_msg
        assert "reduce stockouts" in user_msg
        return '{"pipeline": "supply_chain", "rationale": "Warehouse and inventory focus."}'

    monkeypatch.setattr(
        "services.datalyze_pipeline_pick.gemini_or_light_chat_completion",
        stub_pipeline_pick_completion,
    )

    pid, rationale = pick_custom_base_track(
        company_id=1,
        company_name="TestCo",
        conversation_transcript="user: reduce stockouts in our warehouses",
        uploaded_file_ids=[],
        public_scrape_enabled=True,
    )
    assert pid == "supply_chain"
    assert "warehouse" in rationale.lower() or "inventory" in rationale.lower()


def test_pick_custom_base_track_fallback_on_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_invalid_json_completion(
        u: str, s: str | None = None, max_tokens: int = 450
    ) -> str:
        return "not json"

    monkeypatch.setattr(
        "services.datalyze_pipeline_pick.gemini_or_light_chat_completion",
        stub_invalid_json_completion,
    )
    pid, rationale = pick_custom_base_track(
        company_id=1,
        company_name="X",
        conversation_transcript="hello",
        uploaded_file_ids=[],
        public_scrape_enabled=False,
    )
    assert pid == "predictive"
    assert "predictive" in rationale.lower()
