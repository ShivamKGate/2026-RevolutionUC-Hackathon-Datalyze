"""
Run directory management for filesystem-first pipeline runs.

Root: data/pipeline_runs/<track>/<companySlug>-<userSlug>-save-<timestamp>-<runSlug>/
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from core.config import settings


def _slugify(name: str, max_len: int = 40) -> str:
    if not name or not str(name).strip():
        return "unknown"
    s = re.sub(r"[^\w\s-]", "", name.strip(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s).lower()
    return (s[:max_len] or "unknown")


def build_run_dir_name(
    company_name: str,
    user_name: str,
    run_slug: str,
    timestamp: datetime | None = None,
) -> str:
    ts = timestamp or datetime.now(UTC)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    return f"{_slugify(company_name)}-{_slugify(user_name, 20)}-save-{ts_str}-{run_slug}"


def create_run_directory(
    track: str,
    company_name: str,
    user_name: str,
    run_slug: str,
    timestamp: datetime | None = None,
) -> Path:
    """Create the full run directory tree and return the root path."""
    dir_name = build_run_dir_name(company_name, user_name, run_slug, timestamp)
    root = settings.repo_root / "data" / "pipeline_runs" / _slugify(track) / dir_name

    root.mkdir(parents=True, exist_ok=True)
    (root / "context").mkdir(exist_ok=True)
    (root / "context" / "inputs").mkdir(exist_ok=True)
    (root / "context" / "agent_outputs").mkdir(exist_ok=True)
    (root / "context" / "artifacts").mkdir(exist_ok=True)
    (root / "context" / "quality_gates").mkdir(exist_ok=True)
    (root / "artifacts").mkdir(exist_ok=True)

    return root


def run_dir_relative(run_dir: Path) -> str:
    """Get path relative to repo root in POSIX format."""
    try:
        return run_dir.relative_to(settings.repo_root).as_posix()
    except ValueError:
        return run_dir.as_posix()
