# Scripts

Automation helpers for setup, data generation, and CI.

## Root scripts

- `run-api.mjs` — used by `npm run dev:api`: resolves **Python 3.12**, ensures `apps/api/.venv`, installs `apps/api/requirements.txt` when it changes, starts Uvicorn.

## Subdirectories

- `setup/`: environment bootstrap scripts.
- `data/`: fixture/synthetic dataset generation scripts.
- `ci/`: quality and release scripts.
