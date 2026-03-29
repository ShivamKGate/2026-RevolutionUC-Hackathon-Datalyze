"""Analysis Chat path: OpenAI-compat multi-turn uses heavy_alt_model."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx


def test_llm_chat_with_messages_uses_heavy_alt_model_and_maps_roles() -> None:
    from core import config as conf
    from services.external_agent_clients import (
        llm_chat_with_messages,
        normalize_openai_compat_model_slug,
    )

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}

    expected_model = normalize_openai_compat_model_slug(
        conf.settings.heavy_alt_model or conf.settings.heavy_model,
    )

    with patch.object(httpx.Client, "post", return_value=mock_resp) as mock_post:
        with patch.object(conf.settings, "llm_api_key", "sk-test-key"):
            out = llm_chat_with_messages(
                [("user", "hi"), ("model", "hello")],
                system_instruction="sys",
            )

    assert out == "OK"
    body = mock_post.call_args[1]["json"]
    assert body["model"] == expected_model
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
