"""Gemini → light model fallback (shared helper)."""

from __future__ import annotations

import services.external_agent_clients as eac
from core import config as conf


def test_gemini_or_light_pair_uses_gemini_when_ok(monkeypatch) -> None:
    monkeypatch.setattr(conf.settings, "gemini_api_key", "gk")
    monkeypatch.setattr(conf.settings, "llm_api_key", "lk")

    def stub_gemini_primary_completion(u: str, s: str | None = None) -> str:
        return "from-gemini"

    monkeypatch.setattr(eac, "gemini_chat_completion", stub_gemini_primary_completion)
    monkeypatch.setattr(eac, "llm_chat_completion", lambda *a, **k: "should-not-call")

    text, src = eac.gemini_or_light_chat_completion_pair("u", "sys")
    assert text == "from-gemini"
    assert src == "gemini"


def test_gemini_or_light_pair_falls_back_when_gemini_raises(monkeypatch) -> None:
    monkeypatch.setattr(conf.settings, "gemini_api_key", "gk")
    monkeypatch.setattr(conf.settings, "llm_api_key", "lk")
    monkeypatch.setattr(conf.settings, "light_model", "my-light-model")

    def gemini_raises(u: str, s: str | None = None) -> str:
        raise RuntimeError("gemini down")

    monkeypatch.setattr(eac, "gemini_chat_completion", gemini_raises)

    def stub_light_model_completion(model: str, user_message: str, **kw: object) -> str:
        assert model == "my-light-model"
        assert user_message == "u"
        return "from-light"

    monkeypatch.setattr(eac, "llm_chat_completion", stub_light_model_completion)

    text, src = eac.gemini_or_light_chat_completion_pair("u", "sys", max_tokens=100)
    assert text == "from-light"
    assert src == "light_model"


def test_gemini_or_light_pair_skips_gemini_without_key(monkeypatch) -> None:
    monkeypatch.setattr(conf.settings, "gemini_api_key", "")
    monkeypatch.setattr(conf.settings, "llm_api_key", "lk")
    monkeypatch.setattr(conf.settings, "light_model", "L")

    monkeypatch.setattr(eac, "llm_chat_completion", lambda model, **kw: "L-out")

    text, src = eac.gemini_or_light_chat_completion_pair("x", None)
    assert text == "L-out"
    assert src == "light_model"
