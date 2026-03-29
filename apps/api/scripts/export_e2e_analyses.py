"""Export E2E_Analytics_Co pipeline_runs to Miscellaneous/data/sources/E2E_Analytics_Co/analyses.json.

Run from repo: `cd apps/api && .venv\\Scripts\\python.exe scripts/export_e2e_analyses.py`
(uses DATABASE_URL from apps/api/.env via db.session).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from sqlalchemy import text  # noqa: E402

from db.session import SessionLocal  # noqa: E402


def main() -> None:
    out_path = (
        _ROOT.parent.parent
        / "Miscellaneous"
        / "data"
        / "sources"
        / "E2E_Analytics_Co"
        / "analyses.json"
    )
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT pr.slug, pr.status,
                  to_char(pr.started_at AT TIME ZONE 'UTC',
                    'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS started_at,
                  to_char(pr.ended_at AT TIME ZONE 'UTC',
                    'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS ended_at,
                  pr.summary, pr.pipeline_log, pr.agent_activity, pr.source_file_ids,
                  pr.track, pr.config_json, pr.final_status_class, pr.analysis_title,
                  pr.replay_payload, pr.run_dir_path, pr.input_hash, pr.memory_json
                FROM pipeline_runs pr
                JOIN companies co ON co.id = pr.company_id
                WHERE co.name = :n
                ORDER BY pr.started_at ASC
                """
            ),
            {"n": "E2E_Analytics_Co"},
        ).fetchall()
        analyses = []
        for r in rows:
            fids = r.source_file_ids or []
            if not isinstance(fids, list):
                fids = []
            fids = [int(x) for x in fids]
            source_files = []
            for fid in fids:
                fr = db.execute(
                    text(
                        "SELECT id, original_filename, analysis_track "
                        "FROM uploaded_files WHERE id = :id AND company_id = "
                        "(SELECT id FROM companies WHERE name = :cn)"
                    ),
                    {"id": fid, "cn": "E2E_Analytics_Co"},
                ).fetchone()
                if fr:
                    source_files.append(
                        {
                            "original_filename": fr.original_filename,
                            "analysis_track": fr.analysis_track,
                        }
                    )
                else:
                    source_files.append(
                        {
                            "original_filename": None,
                            "analysis_track": None,
                            "_missing_id": fid,
                        }
                    )
            analyses.append(
                {
                    "slug": r.slug,
                    "status": r.status,
                    "started_at": r.started_at,
                    "ended_at": r.ended_at,
                    "summary": r.summary,
                    "pipeline_log": r.pipeline_log,
                    "agent_activity": r.agent_activity,
                    "source_files": source_files,
                    "track": r.track,
                    "config_json": r.config_json or {},
                    "final_status_class": r.final_status_class,
                    "analysis_title": r.analysis_title,
                    "replay_payload": r.replay_payload,
                    "run_dir_path": r.run_dir_path,
                    "input_hash": r.input_hash,
                    "memory_json": r.memory_json,
                }
            )
        payload = {
            "version": 1,
            "company_name": "E2E_Analytics_Co",
            "analyses": analyses,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {len(analyses)} analyses to {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
