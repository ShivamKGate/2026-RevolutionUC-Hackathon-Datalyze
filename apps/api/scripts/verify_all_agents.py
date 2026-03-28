"""
One-shot agent health check.

Usage (from repo root):
  python apps/api/scripts/verify_all_agents.py

This script calls the API endpoint `/api/v1/agents/verify/all` and prints
per-agent status so you can quickly see which model/key/integration is failing.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _ensure_project_venv_python(repo_root: Path) -> None:
    venv_python = repo_root / "apps" / "api" / ".venv" / "Scripts" / "python.exe"
    current = Path(sys.executable).resolve()

    if not venv_python.exists():
        return

    # Re-run under project venv to ensure compatible Python and deps.
    if current != venv_python.resolve():
        proc = subprocess.run([str(venv_python), __file__], check=False)
        raise SystemExit(proc.returncode)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    _ensure_project_venv_python(repo_root)
    src_dir = repo_root / "apps" / "api" / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from fastapi.testclient import TestClient  # noqa: PLC0415
    from main import app  # noqa: PLC0415

    client = TestClient(app)
    response = client.post("/api/v1/agents/verify/all")

    if response.status_code != 200:
        print(f"[ERROR] verify/all returned {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)
        return 2

    payload = response.json()
    print(
        f"[SUMMARY] status={payload['status']} "
        f"total={payload['checks_total']} "
        f"passed={payload['checks_passed']} "
        f"failed={payload['checks_failed']} "
        f"skipped={payload['checks_skipped']}",
    )
    print("-" * 120)

    for item in payload["results"]:
        preview = item.get("reply_preview") or ""
        print(
            f"{item['status'].upper():7} | {item['agent_id']:28} | {item['model_type']:18} | "
            f"{item['model'][:28]:28} | {preview[:40]}",
        )
        if item["status"] != "ok":
            print(f"          detail: {item['detail']}")

    if payload["checks_failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
