"""Cooperative cancellation for in-flight orchestrator runs (per run slug)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_cancel_slugs: set[str] = set()


def request_cancel_run(slug: str) -> None:
    """Mark a run for cancellation; the engine checks this between agents/stages."""
    with _lock:
        _cancel_slugs.add(slug)


def is_cancel_requested(slug: str) -> bool:
    with _lock:
        return slug in _cancel_slugs


def clear_cancel_request(slug: str) -> None:
    with _lock:
        _cancel_slugs.discard(slug)
