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

## Boot-Time Agent Registry

- Route: `GET /api/v1/agents/boot-status`
- Purpose: expose startup status for the full architecture registry.
- Behavior:
  - Registry initializes at API startup (`src/main.py` startup hook).
  - Includes all scoped agents with dependencies, model type, runtime mode, and initialization state.
  - Returns orchestrator policy (`ORCHESTRATOR_MAX_RETRIES`, `ORCHESTRATOR_TIMEOUT_SECONDS`).

## Model catalog (Featherless)

- Route: `GET /api/v1/agents/ollama-catalog` (name is historical; data is Featherless defaults + model matrix)
- Purpose: return the active model matrix and provider defaults used by the API.
- Env vars (see `.env.example`): `LLM_BASE_URL`, `LLM_API_KEY`, `HEAVY_MODEL`, `HEAVY_ALT_MODEL`, `LIGHT_MODEL`, `EMBEDDING_MODEL`.

Inference targets **Featherless** only (`https://api.featherless.ai/v1` by default). No local GPU or Ollama is required.
