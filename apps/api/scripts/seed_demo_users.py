#!/usr/bin/env python3
"""
Runs the same startup bootstrap as the API: migrations, companies (Google +
E2E_Analytics_Co), seven seeded users, optional Miscellaneous file copies, and
demo pipeline run `dJwT53yrxIo7OLdY` (see `services.startup_bootstrap`).

Run from `apps/api` with PYTHONPATH including `src`:

  cd apps/api
  ..\\.venv\\Scripts\\python.exe scripts/seed_demo_users.py

Idempotent: heavy file/run seed is skipped once `datalyze_bootstrap.seed_version`
matches; user and company rows are still synced when the API starts.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> int:
    from services.startup_bootstrap import run_startup_bootstrap

    try:
        run_startup_bootstrap()
        print("seed_demo_users: OK — startup_bootstrap finished")
        return 0
    except Exception as exc:
        print(f"seed_demo_users: FAILED — {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
