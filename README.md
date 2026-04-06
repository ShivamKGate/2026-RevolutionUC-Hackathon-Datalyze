# Datalyze

**Raw Data ↓, AI-Driven Strategies ↑**

Datalyze is a local-first, multi-agent business intelligence platform built for RevolutionUC. It takes messy business inputs such as CSVs, Excel workbooks, PDFs, JSON, text files, and optional public context, then turns them into structured analysis runs with dashboards, reports, chat, narration, and replayable artifacts.

**Team:** Kartavya Singh & Shivam Kharangate

## What The Project Does

Datalyze is designed around one idea: most organizations already have the data they need, but it is fragmented across incompatible formats and disconnected tools. Instead of forcing users into a rigid BI workflow, Datalyze accepts raw uploads, classifies the analysis track, routes files to specialized processors, and coordinates a set of focused agents that build decision-ready output.

Current product flow:

1. User signs in and selects an analysis path during onboarding.
2. User uploads company files through the web app.
3. The backend stores files privately and starts a pipeline run.
4. The orchestrator dispatches specialized agents based on track, file types, and policy.
5. Results are stored in PostgreSQL plus filesystem run artifacts for replay and export.
6. The frontend surfaces dashboards, analysis detail, grounded chat, and downloadable HTML/PDF reports.

The app currently includes:

- Auth, onboarding, dashboard, upload, analysis detail, chat, admin, and settings flows in the React frontend.
- FastAPI endpoints for auth, users, files, runs, exports, admin replay, health, and agent boot status.
- A replayable orchestrator runtime with logs, artifacts, run memory, and cancellation support.
- HTML/PDF export generation and ElevenLabs narration support.

## Why The Agent System Matters

The highlight of this repository is the multi-agent architecture. Datalyze does not rely on one model to do everything. It uses a boot-time registry of specialized agents with explicit dependencies, different model tiers, and clear responsibilities. That lets the orchestrator run a dependency-aware pipeline instead of a single opaque LLM call.

This gives the project a few important properties:

- Better routing for mixed-format data.
- Clear separation between ingestion, cleaning, analysis, synthesis, and delivery.
- More reliable control over retries, timeouts, optional steps, and fallbacks.
- Better observability because each stage produces its own logs and artifacts.

## Architecture Overview

### Monorepo

- `apps/web`: React + TypeScript + Vite frontend.
- `apps/api`: FastAPI backend, orchestrator runtime, agents, exports, auth, and database access.
- `scripts`: root automation for Python setup, DB schema setup, and dev startup.
- `data`: private uploads and generated pipeline run artifacts.
- `Miscellaneous`: planning docs, demo assets, exported reports, and test runs.

### Frontend

The web app is a feature-rich client rather than a placeholder. It includes:

- Public landing and authentication entry.
- Protected app shell with dashboard, upload, and analysis routes.
- Analysis detail views with charts, knowledge graph, orchestration visualization, and export actions.
- Datalyze Chat and per-analysis grounded chat.
- Admin replay tools and developer-focused inspection surfaces.

### Backend

The API is organized around thin route handlers and service-heavy business logic:

- `api/v1/routes`: auth, users, files, runs, exports, admin, health, database, and agents.
- `services/orchestrator_runtime`: execution engine, policies, persistence, cancellation, run job management, and track profiles.
- `services/agents`: specialized agent implementations and output contracts.
- `services/export_*`: HTML/PDF report generation.
- `services/startup_bootstrap.py`: migrations, seed users, demo data, and seeded analysis runs.
- `db/migrations`: schema for auth, uploads, pipeline runs, replay/admin features, and analysis metadata.

### Data And Persistence

Datalyze uses a hybrid persistence model:

- PostgreSQL stores users, companies, uploaded files, pipeline runs, logs, titles, and replay metadata.
- Filesystem run directories store artifacts such as final reports, intermediate agent outputs, narration assets, and replay context.

That split is important to the architecture: the database gives the app queryable state, while the run directory gives reproducibility and export-friendly artifacts.

## Agent Architecture

Datalyze boots a registry of **24 specialized agents** from `apps/api/src/services/agent_registry.py`. Each agent has:

- An `id`
- A model type
- A declared dependency list
- A defined responsibility
- A runtime kind such as CrewAI-backed LLM agent, external service, or system-layer service

The orchestrator uses those specs to build and execute a DAG-like pipeline.

### Core agent groups

**1. Orchestration and planning**

- `orchestrator`: global coordination, dispatch, retries, dependency enforcement, strategic control.
- `pipeline_classifier`: chooses the active analysis track and configures emphasis.
- `public_data_scraper`: optional public evidence gathering for public-mode enrichment.

**2. Ingestion and file routing**

- `file_type_classifier`
- `pdf_processor`
- `csv_processor`
- `excel_processor`
- `json_processor`
- `image_multimodal_processor`
- `plain_text_processor`

These agents decide how each upload should be interpreted and transformed into usable chunks.

**3. Data preparation**

- `data_cleaning`
- `smart_categorizer_metadata`
- `aggregator`

These stages normalize extracted data, tag it, and consolidate it into a synthesis-ready corpus.

**4. Analysis and synthesis**

- `conflict_detection`
- `knowledge_graph_builder`
- `trend_forecasting`
- `sentiment_analysis`
- `insight_generation`
- `swot_analysis`
- `executive_summary`
- `automation_strategy`

These agents generate the actual business intelligence layer: insights, forecasts, SWOT framing, contradictions, and executive-level summaries.

**5. Explainability, retrieval, and delivery**

- `data_provenance_tracker`
- `natural_language_search`
- `elevenlabs_narration`

These agents support lineage, grounded chat, and audio output.

### Dependency flow

At a high level, the pipeline works like this:

`pipeline_classifier` and `file_type_classifier` decide how the run should proceed.  
Format-specific processors extract content.  
`data_cleaning` and `smart_categorizer_metadata` prepare the data.  
`aggregator` creates the analysis corpus.  
Downstream agents such as `trend_forecasting`, `conflict_detection`, `knowledge_graph_builder`, `insight_generation`, and `swot_analysis` build higher-level outputs.  
`executive_summary` and `elevenlabs_narration` convert the result into executive-facing delivery formats.

## Model Architecture

The model stack is another major highlight of the project. Datalyze does not bind every task to the same model. It routes work by capability and cost.

### Primary provider

- **Featherless** is the main inference provider.
- It is used through an OpenAI-compatible API and wired into CrewAI.
- The backend normalizes model IDs and environment variables so CrewAI-backed agents can run against Featherless without local model hosting.

### Default model roles

The core runtime model split is:

- **`Kimi-K2.5` for the orchestrator**
  Chosen for the orchestration layer because it is the most agentic model in the stack and is used for planning, dispatch, dependency-aware coordination, and higher-level run control.

- **`DeepSeek-V3.2` for aggregation and reasoning-heavy tasks**
  Used for the aggregator and the heavier synthesis stages where deeper reasoning matters most, including insight generation, SWOT-style framing, and executive-summary level output.

- **`Qwen/Qwen2.5-7B-Instruct` for light tasks**
  Used for faster and cheaper utility work such as routing, normalization, tagging, cleaning, and other structured intermediate stages.

- **`nomic-embed-text` for embeddings**
  Used for retrieval-oriented workflows such as grounded search and chat support.

### Specialized external models and services

- **Gemini `gemini-2.5-flash`**
  Used for classifier and multimodal/vision-heavy situations where image or document interpretation is helpful.

- **ElevenLabs**
  Used for narration output, turning executive summary text into MP3 audio.

### Runtime strategy

The runtime uses a tiered model policy:

- Heavy reasoning only where it matters.
- Lighter models for repetitive or structured intermediate work.
- External specialist services for vision and narration.
- Optional heavy-brain refinement after classification to decide skips and shared context.

This is one of the strongest engineering ideas in the repository because it balances quality, speed, and cost instead of treating every pipeline stage equally.

## Orchestrator Runtime

The orchestrator runtime is implemented under `apps/api/src/services/orchestrator_runtime`. Its job is not just to call agents, but to manage the run as a controlled system.

It currently handles:

- Dependency-aware dispatch
- Policy-driven retries and timeout windows
- Parallel branches for safe non-heavy stages
- Run persistence and replay payload generation
- Worker-process based execution
- Stop/cancel support for active analyses
- Run logs and agent activity history

Pipeline runs are started through the API, persisted in PostgreSQL, executed in a spawned worker process, and written to a run directory under `data/pipeline_runs/...`.

## Local Setup

### Prerequisites

- Node.js 20+ or 22+
- Python 3.12
- PostgreSQL running locally or on a reachable LAN host

### Environment files

Copy the example files:

```bash
copy apps/api/.env.example apps/api/.env
copy apps/web/.env.example apps/web/.env.local
```

Important values in `apps/api/.env`:

- `DATABASE_URL`
- `LLM_API_KEY`
- `GEMINI_API_KEY` if Gemini-backed steps should work
- `ELEVENLABS_API_KEY` if narration should work

### Start the project

```bash
npm install
npm run dev
```

`npm run dev` does the following for the API:

1. Finds Python 3.12
2. Creates `apps/api/.venv` if needed
3. Installs `apps/api/requirements.txt` when dependencies change
4. Applies DB schema setup
5. Starts Uvicorn on port `8000`

Services:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## Demo Data And Seeded Users

On startup, the backend bootstrap process can:

- Apply SQL migrations
- Upsert demo companies and users
- Seed uploaded files
- Materialize demo pipeline runs and replay data

Default demo accounts include:

- `demo@revuc.com`
- `demo.automation@revuc.com`
- `demo.optimization@revuc.com`
- `demo.predictive@revuc.com`
- `demo.supplychain@revuc.com`

Password: `Demo@123`

## Project Structure

```text
.
├── apps/
│   ├── api/
│   │   ├── src/main.py
│   │   ├── src/api/v1/router.py
│   │   ├── src/api/v1/routes/
│   │   │   ├── agents.py
│   │   │   ├── auth.py
│   │   │   ├── files.py
│   │   │   ├── runs.py
│   │   │   └── exports.py
│   │   ├── src/core/
│   │   │   ├── config.py
│   │   │   └── ollama_models.py
│   │   ├── src/db/
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   └── src/services/
│   │       ├── agent_registry.py
│   │       ├── startup_bootstrap.py
│   │       ├── datalyze_chat.py
│   │       ├── export_html.py
│   │       ├── export_pdf.py
│   │       ├── orchestrator_runtime/
│   │       └── agents/
│   └── web/
│       ├── src/App.tsx
│       ├── src/main.tsx
│       ├── src/lib/api.ts
│       ├── src/contexts/AuthContext.tsx
│       ├── src/layouts/
│       ├── src/pages/
│       └── src/components/
├── scripts/
│   ├── run-api.mjs
│   └── setup-schema.mjs
├── data/
│   └── pipeline_runs/
├── Miscellaneous/
│   └── Plans/plan.md
├── package.json
└── README.md
```

## Useful References

- `Miscellaneous/Plans/plan.md`: original product and system planning notes
- `apps/api/README.md`: backend-focused notes
- `apps/web/README.md`: frontend-focused notes
- `Miscellaneous/Test Runs/`: captured runs, reports, and runtime evidence

## Summary

Datalyze is not just a frontend plus API demo. The core of the project is a model-aware, multi-agent orchestration system for turning fragmented business data into explainable strategic output. The agent architecture and tiered model routing are the most distinctive parts of the repository, and they are the main reason the project is interesting from both a product and engineering perspective.
