# Datalyze

**Raw Data ↓, AI-Driven Strategies ↑**

Local-first, multi-agent business intelligence platform scaffold for RevolutionUC.

**Team:** Kartavya Singh & Shivam Kharangate

## What This Repository Now Includes

- Full monorepo skeleton with backend, frontend, docs, infra, scripts, and tests.
- Strong folder boundaries to support parallel development during hackathon pressure.
- Directory-level `README.md` files describing what belongs in each area.
- `.gitkeep` placeholders for intentionally empty but required directories.
- A working frontend-backend connectivity baseline (`React + FastAPI`).
- One command (`npm run dev`) that starts both web and API servers together.

## Tech Baseline

- Frontend: React + TypeScript + Vite
- Backend: FastAPI (Python)
- Orchestration script: root `npm run dev` with `concurrently`
- Planned AI stack: Ollama + agent modules (to be implemented incrementally)

## Quick Start (Windows / PowerShell)

### Prerequisites

- **Node.js** 20+ or 22+ (LTS recommended)
- **Python 3.12** on your PATH (see below if missing)

`npm run dev` does **not** auto-download Python. Install 3.12 once per machine; the dev script then manages a **local venv** and dependencies for you.

### 1) Install Node dependencies at repo root

```bash
npm install
```

### 2) Optional env files

```bash
copy apps/web/.env.example apps/web/.env.local
copy apps/api/.env.example apps/api/.env
```

### 3) Run both servers together

```bash
npm run dev
```

### What `npm run dev` does for the API

`npm run dev:api` runs `node scripts/run-api.mjs`, which:

1. Finds an interpreter that is **exactly Python 3.12** (`py -3.12` on Windows, then `python3.12` / `python3` / `python` on other platforms).
2. Creates **`apps/api/.venv`** if it does not exist (no need to `activate` manually).
3. Runs **`pip install -r apps/api/requirements.txt`** when that file changes (tracked via a small hash stamp inside the venv).
4. Starts **Uvicorn** with the venv’s Python.

If Python 3.12 is missing, the script prints install hints (e.g. `winget install -e --id Python.Python.3.12` on Windows).

### Terminals

- **Typical:** **one** terminal — `npm run dev` (web + API).
- **With Ollama:** **two** terminals — `npm run dev` and `ollama serve`.

## Running Services

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

## Current Connectivity Contract

- Frontend button in `apps/web/src/App.tsx` calls:
  - `GET /api/v1/health`
- Backend route returns:
  - `status`
  - `service`
  - `timestamp`

This proves the web app and API are connected and communicating.

## Project Structure

```text
.
├── .github/                    # workflow and repo automation metadata
├── Miscellaneous/              # your planning and ideation files
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/v1/routes/  # versioned route modules
│   │   │   ├── core/           # config and app-level setup
│   │   │   ├── db/             # migration and seed placeholders
│   │   │   ├── models/         # domain/db model location
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # business logic services
│   │   └── tests/              # backend tests
│   └── web/                    # React + Vite frontend
│       ├── public/             # static public assets
│       └── src/
│           ├── assets/         # bundled static assets
│           ├── components/     # reusable UI components
│           ├── features/       # feature-first modules
│           ├── hooks/          # reusable React hooks
│           ├── lib/            # API client and utilities
│           ├── styles/         # global and shared styles
│           └── types/          # TypeScript contracts
├── docs/                       # architecture, API, QA, runbooks
├── infra/                      # docker/compose/terraform placeholders
├── packages/
│   └── shared/                 # cross-app shared contracts
├── scripts/                    # setup/data/ci script placeholders
├── tests/                      # e2e and integration test placeholders
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

## Folder Conventions

- Feature-first over layer-first for frontend (`src/features/*`).
- Thin route handlers and thick services for backend.
- Shared contracts should eventually be centralized in `packages/shared`.
- Keep docs close to reality: every major feature should update corresponding docs.

## Suggested Next Steps (Build Order)

1. Add onboarding route + schema contracts (frontend and API).
2. Add upload endpoint + file metadata persistence.
3. Add run pipeline bootstrap endpoint with mock orchestrator events.
4. Add dashboard polling + SSE log stream.
5. Add insight cards and knowledge-graph API shape.
6. Integrate first local model call through Ollama adapter service.

## Hackathon Notes

- This scaffold is intentionally strong on structure so both teammates can work in parallel with minimal merge conflicts.
- Empty strategic folders are tracked with `.gitkeep` so clone/pull reproduces the exact architecture.
- You can now scale quickly from skeleton to production-grade demo without re-organizing under time pressure.
