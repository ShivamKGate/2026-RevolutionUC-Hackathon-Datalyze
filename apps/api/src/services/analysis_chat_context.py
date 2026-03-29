"""
Build bounded text context for post-run Analysis Chat (memory + source file excerpts).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text

from core.config import settings
from db.session import SessionLocal


def _truncate(s: str, max_chars: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."


def _read_text_excerpt(abs_path: Path, max_chars: int) -> str:
    if not abs_path.is_file():
        return ""
    suffix = abs_path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json"}:
        try:
            raw = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return _truncate(raw, max_chars)
    if suffix == ".pdf":
        return (
            f"[PDF binary omitted from chat context: {abs_path.name}; "
            "orchestrator outputs and memory below still apply.]"
        )
    if suffix in {".xlsx", ".xls"}:
        return (
            f"[Excel binary omitted from chat context: {abs_path.name}; "
            "use orchestrator outputs and memory below.]"
        )
    try:
        raw = abs_path.read_text(encoding="utf-8", errors="replace")
        return _truncate(raw, min(max_chars, 8000))
    except OSError:
        return ""


def build_analysis_chat_context(
    *,
    company_id: int,
    memory_json: dict[str, Any] | None,
    replay_payload: dict[str, Any] | None,
    source_file_ids: list[int],
    budget_chars: int = 72000,
) -> str:
    parts: list[str] = []
    used = 0

    def add_block(title: str, body: str) -> None:
        nonlocal used
        chunk = f"### {title}\n{body}\n\n"
        if used + len(chunk) > budget_chars:
            remain = budget_chars - used
            if remain > 200:
                parts.append(chunk[:remain] + "\n[truncated]\n")
            used = budget_chars
            return
        parts.append(chunk)
        used += len(chunk)

    mem = memory_json or {}
    add_block(
        "Orchestrator memory (memory.json snapshot)",
        _truncate(json.dumps(mem, indent=2, default=str), min(32000, budget_chars // 3)),
    )

    if replay_payload:
        rp_excerpt = {
            k: replay_payload[k]
            for k in (
                "final_report",
                "visualization_plan",
                "agent_results",
            )
            if k in replay_payload
        }
        if not rp_excerpt:
            rp_excerpt = {"keys": list(replay_payload.keys())[:40]}
        add_block(
            "Replay payload (subset)",
            _truncate(json.dumps(rp_excerpt, indent=2, default=str), min(24000, budget_chars // 3)),
        )

    if not source_file_ids:
        return "".join(parts)

    in_clause = ",".join(str(int(x)) for x in sorted(set(source_file_ids)))
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                f"SELECT id, original_filename, storage_relative_path, visibility, content_type "
                f"FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause}) "
                f"ORDER BY id ASC"
            ),
            {"cid": company_id},
        ).fetchall()
    finally:
        db.close()

    per_file_budget = max(4000, (budget_chars - used) // max(1, len(rows)))

    for r in rows:
        rel = str(r.storage_relative_path or "")
        vis = str(r.visibility or "unknown")
        name = str(r.original_filename or rel)
        abs_path = (settings.repo_root / rel).resolve() if rel else None
        try:
            if abs_path and str(abs_path).startswith(str(settings.repo_root.resolve())):
                excerpt = _read_text_excerpt(abs_path, per_file_budget)
            else:
                excerpt = ""
        except Exception:
            excerpt = ""
        if not excerpt:
            excerpt = f"[No text excerpt available for {name}]"
        add_block(
            f"Source file id={r.id} ({vis}) — {name}",
            excerpt,
        )
        if used >= budget_chars:
            break

    return "".join(parts)
