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

## CrewAI MVP Endpoint

- Route: `POST /api/v1/agents/mvp`
- Purpose: initialize a minimal Data Allies CrewAI setup (and optionally run it).
- Request body:
  - `company_context` (string)
  - `user_goal` (string)
  - `run` (boolean; default `false`)
- Notes:
  - `run=false` only initializes crew objects (safe MVP handshake with the API skeleton).
  - `run=true` runs a sequential crew: **`HEAVY_MODEL`** for the orchestrator only; **`LIGHT_MODEL`** for aggregator, insights, and executive summary (see `src/services/crew_mvp.py`).

## Ollama model catalog (team hardware)

- Route: `GET /api/v1/agents/ollama-catalog`
- Purpose: return the recommended model matrix (12GB VRAM floor) plus `ollama pull` lines.
- Env vars (see `.env.example`): `OLLAMA_HOST`, `HEAVY_MODEL`, `LIGHT_MODEL`, `EMBEDDING_MODEL`.

## One-shot model pulls (Windows)

From repo root:

```powershell
.\scripts\pull-datalyze-ollama-models.ps1
```
