# API App (`apps/api`)

FastAPI backend for Datalyze.

## Local Python environment

From the repo root, `npm run dev:api` runs `scripts/run-api.mjs`, which creates **`apps/api/.venv`** with **Python 3.12** and installs dependencies from `requirements.txt`. You do not need to activate the venv manually.

## Purpose

- Provide versioned REST endpoints for frontend and agents.
- Centralize pipeline orchestration entry points.
- Keep business logic separate from transport concerns.

## Current Files

- `src/main.py`: FastAPI bootstrapping + CORS + route mounting.
- `src/api/v1`: Versioned route layer.
- `src/core`: Configuration and framework setup.
- `src/schemas`: API request/response models.

## Suggested Next Implementations

- `src/services/*`: core orchestration, ingestion, and analysis logic.
- `src/repositories/*`: PostgreSQL persistence abstraction.
- `src/models/*`: ORM models or table contracts.
- `tests/*`: endpoint tests, service tests, and integration tests.
