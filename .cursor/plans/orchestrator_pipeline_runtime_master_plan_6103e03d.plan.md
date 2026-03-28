---
name: orchestrator_pipeline_runtime_master_plan
overview: Implement a production-grade orchestrator-driven pipeline runtime with filesystem-first run artifacts, DB-backed UI replay, deterministic+adaptive execution policies, and merge-safe boundaries from agent specialization work.
todos:
  - id: phase1-runtime-contracts
    content: Create orchestrator runtime scaffolding, adapter contracts, track profile packs, and config flags with strict merge-safe boundaries.
    status: pending
  - id: phase2-filesystem-state
    content: Implement filesystem-first run lifecycle with memory.json, context folder, decision ledger, artifact index, and manifest generation.
    status: pending
  - id: phase3-db-replay-live
    content: Add DB migrations and API updates for live logs, replay-by-slug payloads, and same-company shared file visibility.
    status: pending
  - id: phase4-reliability-policy
    content: Implement retry/time-budget policies, stage quality gates, sequential+parallel toggle behavior, and completion_with_warnings outputs.
    status: pending
  - id: phase5-verification-handoff
    content: Execute comprehensive validation matrix, save test evidence in Miscellaneous/tests, and produce merge-integration notes for Shivam branch.
    status: pending
isProject: false
---

# Pipeline Orchestrator Runtime Plan [Kartavya]

## Scope And Outcome

Build a run-time orchestration layer that replaces placeholder pipeline execution with a real orchestrator engine that:

- Chooses and dispatches every agent step (agents never self-chain).
- Persists rich run artifacts under `data/pipeline_runs/<track>/<company-user-save-timestamp-runSlug>/`.
- Maintains `memory.json` and `context/` at every step.
- Streams and stores UI-ready run logs/events in DB for replay-by-slug.
- Supports deterministic DAG + adaptive policy adjustments + stage-gated safety.
- Keeps changes isolated from Shivam’s specialization branch by using adapter interfaces.

## Existing Code Anchors To Reuse

- Run route is currently placeholder and should be replaced with real orchestration entrypoint: [apps/api/src/api/v1/routes/runs.py](apps/api/src/api/v1/routes/runs.py)
- Agent dependency catalog already exists and should be treated as graph source metadata: [apps/api/src/services/agent_registry.py](apps/api/src/services/agent_registry.py)
- Upload storage path model already exists and should be mirrored for run artifacts: [apps/api/src/services/company_paths.py](apps/api/src/services/company_paths.py)
- Company settings + onboarding path are already persisted and can drive track selection for future runs: [apps/api/src/api/v1/routes/users.py](apps/api/src/api/v1/routes/users.py), [apps/api/src/schemas/auth.py](apps/api/src/schemas/auth.py)
- Current migration has base `pipeline_runs` and `uploaded_files`; extend additively: [apps/api/src/db/migrations/003_uploads_pipeline.sql](apps/api/src/db/migrations/003_uploads_pipeline.sql)
- Frontend company settings currently include public scrape toggle and can be extended with editable track settings: [apps/web/src/pages/settings/CompanyPage.tsx](apps/web/src/pages/settings/CompanyPage.tsx)

## Hard Boundaries To Minimize Merge Conflicts

- **Your scope (Kartavya):** orchestrator runtime, workflow/pipeline policy, run persistence, logs/events, run APIs, replay loading, analysis UX flow.
- **Shivam scope:** per-agent module specialization, deep prompts, agent-internal output behavior.
- **Integration contract:** orchestrator only depends on a stable `AgentExecutionAdapter` contract (`status`, `summary`, `artifacts`, `next_hints`, `confidence`, `errors`) and never depends on prompt internals.
- **Rule:** avoid modifying specialization module internals; only add adapter wrappers or contract normalization layers.

## Architecture Pattern (Hybrid)

Use a hybrid of all three modes:

1. **Deterministic DAG baseline** from selected track + registry dependencies.
2. **Policy-driven adaptive override** by orchestrator based on confidence/failure heuristics.
3. **Stage-gated guardrails** to prevent deadlocks and enforce progress.

```mermaid
flowchart TD
    runStart[RunStart] --> trackSelect[TrackFromOnboardingPath]
    trackSelect --> dagBuild[BuildDeterministicDag]
    dagBuild --> stageGate[StageGateController]
    stageGate --> orchLoop[OrchestratorDecisionLoop]
    orchLoop --> dispatch[DispatchAgentViaAdapter]
    dispatch --> agentOut[NormalizedAgentOutput]
    agentOut --> memUpdate[UpdateMemoryJson]
    agentOut --> ctxWrite[WriteContextArtifacts]
    memUpdate --> logWrite[PersistLogEvent]
    ctxWrite --> logWrite
    logWrite --> policyEval[PolicyAndQualityGates]
    policyEval -->|continue| orchLoop
    policyEval -->|stageDone| stageGate
    stageGate -->|finalize| dbFinalize[PersistUiProjectionToDb]
    dbFinalize --> replayReady[SlugReplayReady]
```

## Run Storage Design

Root: `data/pipeline_runs/<track>/<companySlug>-<userSlug>-save-<timestamp>-<runSlug>/`

Mandatory files/folders:

- `run_manifest.json`: static run metadata (track, toggles, user/company IDs, model settings, flags, time budgets).
- `memory.json`: full mutable state + append-only events + retries + next options + failure analysis.
- `decision_ledger.jsonl`: one record per orchestrator decision (`why_this_agent`, `alternatives_considered`, `policy_mode`, `confidence`).
- `context/`
  - `context.json` (context index/meta)
  - `inputs/` (selected uploaded files metadata, scrape toggles)
  - `agent_outputs/<agentId>/<step>.json`
  - `artifacts/` (public scrape docs, extracted files, transformed payloads)
  - `quality_gates/` (validation outputs)
- `artifacts/index.json`: artifact catalog with producer, timestamp, provenance pointers.
- `final_report.json`: UI-ready final projection snapshot before DB write.

## Data Authority Model

- **During run:** filesystem is source-of-truth for runtime state.
- **For UI/live + replay:** DB is source-of-truth for display surfaces.
- Strategy:
  - Write log/event rows to DB incrementally for live feed.
  - Keep full heavy runtime internals in filesystem.
  - On completion/finalization, persist UI projection to DB (insights/summary/activity/log snapshots required for replay).

## Phase 1 — Foundation And Contracts

### Objectives

- Introduce orchestration runtime module(s) and contracts without touching specialization internals.
- Normalize track mapping from `onboarding_path` to canonical track IDs.
- Add feature flags for execution policy (parallel enabled/disabled, adaptive enabled/disabled).

### Implementation

- Create new services package:
  - `apps/api/src/services/orchestrator_runtime/engine.py`
  - `apps/api/src/services/orchestrator_runtime/policies.py`
  - `apps/api/src/services/orchestrator_runtime/contracts.py`
  - `apps/api/src/services/orchestrator_runtime/persistence.py`
  - `apps/api/src/services/orchestrator_runtime/track_profiles.py`
- Define canonical track enum and mapper for existing/future onboarding values.
- Create `AgentExecutionAdapter` abstraction that calls current agents through registry/runtime and returns normalized payload.
- Add policy flags in config:
  - `ORCH_ENABLE_PARALLEL_BRANCHES`
  - `ORCH_ENABLE_ADAPTIVE_POLICY`
  - `ORCH_ENABLE_STAGE_GATES`
  - `ORCH_MAX_RUN_SECONDS` (900 default)

### Deliverables

- Runtime scaffolding compiles and can execute no-op/dry-run path.
- Track profile packs as config files per track (priority order, optional nodes, quality gates).

## Phase 2 — Filesystem Run State And Orchestrator Loop

### Objectives

- Implement filesystem-first run lifecycle with full memory/context updates.
- Replace placeholder orchestration behavior behind `/runs/start`.

### Implementation

- In [apps/api/src/api/v1/routes/runs.py](apps/api/src/api/v1/routes/runs.py):
  - Replace placeholder logs generation with call to orchestrator runtime start method.
  - Keep response shape backward-compatible while extending with run status metadata.
- Add run directory utility module (sibling to company paths):
  - `apps/api/src/services/run_paths.py` for deterministic run folder creation and slug-safe names.
- Implement memory semantics:
  - `memory.json` includes `state`, `events[]`, `retries`, `done`, `pending`, `failed`, `next_candidates`, `timing_budget`, `warnings`, `fix_suggestions`.
- Implement context semantics:
  - `context/context.json` acts as index to all context assets.
  - Persist both compact summaries and selective raw prompts/responses where required.
- Add decision ledger append flow for every orchestrator step.

### Deliverables

- Real run folders created per run with expected structure.
- Orchestrator can progress through stage gates and update memory/context every step.

## Phase 3 — Database Replay, Live Feed, And Company-Shared File Access

### Objectives

- Make UI reproducible from DB by run slug.
- Support cross-user file visibility within same company.
- Preserve incremental live logging while run executes.

### Implementation

- Add migration(s) after `003_uploads_pipeline.sql`:
  - Expand `pipeline_runs` with replay projection fields (track, config, final status class, summary payload, final UI snapshot refs).
  - Add `pipeline_run_logs` table keyed by run ID (timestamp, stage, agent, action, detail, status, metadata JSON).
  - Add optional `pipeline_run_artifacts` table for lightweight artifact index references.
- Update run APIs in [apps/api/src/api/v1/routes/runs.py](apps/api/src/api/v1/routes/runs.py):
  - `POST /start` returns run slug and immediate status.
  - `GET /{slug}` returns replay payload sufficient to rebuild analysis UI.
  - Optional streaming/log endpoints for live panel.
- Update file listing behavior in [apps/api/src/api/v1/routes/files.py](apps/api/src/api/v1/routes/files.py):
  - Ensure all users in same company can list/select uploaded files.
  - Preserve secure company boundary.
- Add/adjust frontend flow:
  - New analysis route/page (e.g., `apps/web/src/pages/AnalysisPage.tsx`) as orchestration launch hub.
  - Upload page update to show company shared files + quick upload entry.
  - Analysis detail route by slug (existing/new page alignment with `AnalysisDetailPage.tsx`).

### Deliverables

- Copy-link by run slug works for same-company users and loads equivalent UI output from DB.
- Live logs are persisted and replayable.

## Phase 4 — Reliability: Retry, Time Budget, Parallel Branches, Quality Gates

### Objectives

- Enforce "don’t give up" behavior with bounded reliability controls.
- Implement parallel branches as configurable runtime option.
- Produce completion with warnings + actionable fix suggestions.

### Implementation

- Retry policy:
  - Per-step retry with exponential backoff.
  - Alternate-agent/model fallback via adapter when possible.
  - Global run budget hard cap 15 minutes (configurable 10-15 via env).
- Completion policy:
  - `completed`, `completed_with_warnings`, `failed_hard`.
  - For `completed_with_warnings`, include orchestrator-generated `fix_suggestions` in final payload.
- Parallel mode:
  - Run independent analysis branches concurrently after aggregation when enabled.
  - Auto-fallback to sequential if disabled or if dependency constraints fail.
- Quality gates:
  - schema validation, empty output checks, contradiction checks, confidence threshold checks before stage transitions.
- Caching / duplicate-analysis guard:
  - Hash salient input signature (company + selected file set + track + toggles + relevant config).
  - If equivalent completed run exists and fresh enough, return cached slug and mark as reused.

### Deliverables

- Stable runtime within max duration.
- Meaningful partial completion and warnings when some agents fail repeatedly.

## Phase 5 — Test Harness, Demo Hardening, And Merge Readiness

### Objectives

- Validate end-to-end orchestration flow and produce reproducible test artifacts.
- Prepare clean merge path with Shivam’s specialization branch.

### Implementation

- Fixture strategy:
  - Use `Google_Dataset_Analytics_Sample.xlsx` as deterministic test fixture (when accessible in runtime environment).
  - Add fixture loader hooks for local test runs.
- Test matrix:
  - no-upload + public scrape enabled run.
  - uploaded-files run.
  - same-company cross-user replay-by-slug.
  - sequential mode.
  - parallel mode.
  - forced non-critical failures -> `completed_with_warnings`.
  - cache-hit rerun behavior.
- Save test outputs to `Miscellaneous/tests/` with timestamped filenames.
- Merge prep checklist:
  - Verify orchestrator changes only depend on adapter contract.
  - Confirm no direct dependency on specialized prompt internals.
  - Document integration points for post-merge alignment.

### Deliverables

- Test evidence files captured in `Miscellaneous/tests/`.
- Integration notes ready for merge with specialization branch.

## Frontend Interaction Plan

- Add/adjust settings so pipeline track is editable for future runs only.
- New analysis launch UX:
  - If public scrape disabled and no files selected -> guidance to upload.
  - If public scrape enabled -> analysis can start immediately.
  - File picker shows company-shared uploads and allows adding new files.
- Analysis detail/replay page renders from DB snapshot + log stream/history.

## Non-Goals (This Plan)

- Deep per-agent prompt specialization changes.
- Full crash-resume implementation (checkpoint metadata will be prepared; complete resume can be future phase).
- External auth expansion beyond current same-company constraints.

## Risks And Mitigations

- Runtime complexity risk: mitigate via stage gates + deterministic baseline path.
- Merge conflict risk with specialization branch: mitigate via strict adapter boundary.
- Performance risk under parallel mode: mitigate with runtime toggle and fallback sequential mode.
- Data volume/log bloat: mitigate with selective raw retention + compact summaries + artifact indexing.

## Claude Code Execution Prompt (Large Block)

```text
You are implementing a production-grade orchestrator runtime for Datalyze.

CONTEXT:
- Repo has placeholder pipeline run flow and a rich agent registry.
- Shivam is simultaneously implementing agent specialization internals.
- Your mission is orchestration/workflow/runtime/storage/logging/UI replay, NOT agent specialization prompt internals.

STRICT BOUNDARIES:
1) Do not modify specialized per-agent behavior contracts unless through adapter normalization.
2) Keep merge conflicts minimal with Shivam’s branch.
3) Additive, backward-compatible API/db changes where possible.

PRIMARY GOALS:
A) Replace placeholder run execution with real orchestrator loop.
B) Persist filesystem artifacts per run:
   data/pipeline_runs/<track>/<companySlug>-<userSlug>-save-<timestamp>-<runSlug>/
   with run_manifest.json, memory.json, context/context.json, artifacts/index.json, decision_ledger.jsonl, final_report.json.
C) Orchestrator chooses next agent every step; all agent calls return to orchestrator.
D) Implement hybrid execution model:
   - deterministic DAG baseline,
   - adaptive policy overrides,
   - stage-gated quality checks.
E) Add resilient retry with max run budget <= 15 min and completion_with_warnings + fix suggestions.
F) DB-backed live/replay model by run slug so same-company users can open identical analysis views.
G) Company-shared uploaded files: users in same company can view/use each other’s uploads.
H) Add sequential/parallel orchestration toggle flags.
I) Save all test run outputs under Miscellaneous/tests/ with timestamped files.

TRACK SOURCE OF TRUTH:
- Track comes from onboarding path / profile setting.
- Track edits affect future runs only.

DATA AUTHORITY:
- During execution: filesystem is runtime truth.
- For UI: DB is truth (logs, summary projection, replay payload).

I/O CONTRACT FOR ADAPTER (CURRENT PHASE):
{
  "status": "ok|warning|error",
  "summary": "string",
  "artifacts": [],
  "next_hints": [],
  "confidence": 0.0,
  "errors": []
}

CONFIG FLAGS TO ADD:
- ORCH_ENABLE_PARALLEL_BRANCHES=true|false
- ORCH_ENABLE_ADAPTIVE_POLICY=true|false
- ORCH_ENABLE_STAGE_GATES=true|false
- ORCH_MAX_RUN_SECONDS=900

FILES TO PRIORITIZE:
- apps/api/src/api/v1/routes/runs.py
- apps/api/src/services/agent_registry.py (read-only dependency graph usage, minimal edits)
- apps/api/src/services/company_paths.py
- apps/api/src/db/migrations/003_uploads_pipeline.sql (add subsequent migration files)
- apps/web/src/pages/settings/CompanyPage.tsx
- apps/web/src/pages/UploadPage.tsx
- apps/web/src/pages/AnalysisDetailPage.tsx (or create/update)
- apps/web/src/lib/api.ts

NEW BACKEND MODULES TO ADD (suggested):
- apps/api/src/services/orchestrator_runtime/engine.py
- apps/api/src/services/orchestrator_runtime/policies.py
- apps/api/src/services/orchestrator_runtime/contracts.py
- apps/api/src/services/orchestrator_runtime/persistence.py
- apps/api/src/services/orchestrator_runtime/track_profiles.py
- apps/api/src/services/run_paths.py

DB CHANGES (add new migration):
- expand pipeline_runs for track/config/replay fields
- create pipeline_run_logs(run_id fk, timestamp, stage, agent, action, detail, status, meta_json)
- optional pipeline_run_artifacts for lightweight artifact references

LIVE + REPLAY REQUIREMENTS:
- run slug copy/share inside same company should open full analysis detail.
- replay endpoint must return enough payload to recreate dashboard cards/logs/status.

TEST FIXTURE REQUIREMENT:
- Use Miscellaneous/data/sources/Google_Dataset_Analytics_Sample.xlsx for deterministic tests when available.
- If fixture path unavailable in environment, fail gracefully and log reason.

MANDATORY VALIDATION:
1) Run backend tests/lint/type checks relevant to changed files.
2) Run frontend tests/lint/type checks relevant to changed files.
3) Run end-to-end manual flow checks for:
   - start run with uploads
   - start run with public scrape enabled and no uploads
   - replay by slug in same company
   - sequential vs parallel mode
   - forced warning completion path
4) Save verification report files in Miscellaneous/tests/:
   - <timestamp>_orchestrator-runtime-validation.md
   - <timestamp>_pipeline-replay-validation.md
   - <timestamp>_api-web-smoke.txt

IMPLEMENTATION QUALITY RULES:
- Keep code ASCII and concise.
- Add comments only where logic is non-obvious.
- Do not introduce secrets in code or test logs.
- Never hardcode user credentials.
- Keep API response compatibility where feasible.

MERGE SAFETY NOTES:
- Assume Shivam’s branch will later alter agent internals.
- Preserve adapter boundary so specialization merges cleanly.
- Add concise integration notes in code comments/docs near adapter interfaces.

DONE CRITERIA:
- Placeholder run flow removed/replaced.
- Filesystem artifacts generated and updated every step.
- DB replay works by slug for same-company users.
- Logs persist and render in UI.
- Track/profile controls drive future runs.
- Parallel/sequential toggles functional.
- Test evidence files saved under Miscellaneous/tests/.
```

## Future Enhancements (Post-Primary)

- Full checkpoint-resume execution from last successful stage.
- Shadow evaluation mode comparing placeholder/legacy vs specialized outputs post-merge.
- Rich artifact compression/retention lifecycle policies.
- Deterministic benchmark suite across multiple sample datasets.
