"""
Entry point for the orchestrator when run in a subprocess (see runs.py).

Must stay a top-level importable function so multiprocessing "spawn" can pickle it.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Spawned worker may not inherit the parent's sys.path (depends on launcher).
_src = Path(__file__).resolve().parent.parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from services.orchestrator_runtime.engine import OrchestratorEngine

logger = logging.getLogger("orchestrator.run_job")


def run_orchestrator_job(
    run_id: int,
    run_slug: str,
    company_id: int,
    company_name: str,
    user_id: int,
    user_name: str,
    source_file_ids: list[int],
    source_files_meta: list[dict[str, Any]],
    onboarding_path: str | None,
    public_scrape_enabled: bool,
) -> None:
    """Execute one pipeline run (blocking until completion or process termination)."""
    try:
        engine = OrchestratorEngine(
            run_id=run_id,
            run_slug=run_slug,
            company_id=company_id,
            company_name=company_name,
            user_id=user_id,
            user_name=user_name,
            source_file_ids=source_file_ids,
            source_files_meta=source_files_meta,
            onboarding_path=onboarding_path,
            public_scrape_enabled=public_scrape_enabled,
        )
        engine.execute()
    except Exception:
        logger.exception("Orchestrator subprocess failed for run %s", run_slug)
