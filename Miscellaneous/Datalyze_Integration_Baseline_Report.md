# Datalyze — Integration baseline, changelog, and first successful run

This document is the **single narrative index** for the post-merge integration state: what changed, how the stack connects, what the **first successful end-to-end run** proved, and how that compares to original product expectations. Use it as the baseline before you upload or demo the full repository.

**Companion evidence (read these for raw detail):**

| Artifact                                                                                | Role                                                                                                                 |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `Miscellaneous/First Successful Run/`                                                   | Captured filesystem state of the first **green** UI-driven run (manifest, memory, ledger, agent outputs, `logs.txt`) |
| `Miscellaneous/tests/2026-03-28_21-22-42_excel-sequential-e2e-report.md`                | Scripted API E2E with Excel fixture (sequential config)                                                              |
| `Miscellaneous/tests/2026-03-28_21-22-42_excel-sequential-e2e.json`                     | Machine-readable metrics for the same scripted run                                                                   |
| `Miscellaneous/Datalyze Agent Specialization - Performance Report.md`                   | Per-agent specialization + verification summary                                                                      |
| `Miscellaneous/Datalyze Orchestrator Runtime - Master Plan vs Implementation Report.md` | Orchestrator plan vs implementation scoring                                                                          |

---

## 1. Executive summary

After merging agent specialization work with orchestrator runtime work, the **wiring layer** was corrected so the orchestrator can actually dispatch agents (DAG readiness, registry boot, DB migration chain). The **first successful run** completed **20/20 agents** in **~90s** wall time with **zero stage-gate warnings**, persisted **DB replay + filesystem artifacts**, and produced **insight + executive summary** text suitable for demo. A second scripted validation used the **Google sample Excel** fixture over **~240s** with the same structural outcome; both runs expose the same remaining polish items (Gemini quota fallback, ElevenLabs context handoff, optional routing fidelity).

---

## 2. Scope of “current changes” (working tree baseline)

_Note: At documentation time, these edits were present in the working tree as the integration baseline. If you stage only a subset, treat this section as the full story of what landed for the demo-ready pipeline._

### 2.1 Backend — runs API and safety

**File:** `apps/api/src/api/v1/routes/runs.py`

- **Clear all analyses:** `DELETE /api/v1/runs` removes all `pipeline_runs` for the authenticated user’s company (cascades logs/artifacts in DB). Optionally deletes on-disk run folders under the repo root using `run_dir_path`, with path validation so only repo-relative safe paths are removed.
- **Race guard:** If any run for the company is still `pending` or `running`, clear returns **409** so a background thread is never left writing into a deleted directory.

### 2.2 Backend — orchestrator engine and policies

**Files:** `apps/api/src/services/orchestrator_runtime/engine.py`, `apps/api/src/services/orchestrator_runtime/policies.py`

- **DAG fix:** `orchestrator` is a **controller**, not a dispatchable prerequisite. Dependencies on `orchestrator` are stripped from the dependency map used for “ready to run” checks, so agents like `pipeline_classifier` and `file_type_classifier` are no longer deadlocked forever.
- **Registry boot:** If `AgentRegistry` nodes are empty when dispatch runs, `initialize()` is called so CrewAI agents exist before `crew.kickoff()`.

### 2.3 Database bootstrap

**File:** `scripts/setup-schema.mjs`

- Applies **`004_orchestrator_runtime.sql`** on every `npm run dev` / API boot path, so new clones get `pipeline_run_logs`, `pipeline_run_artifacts`, and expanded `pipeline_runs` columns (`track`, `config_json`, `replay_payload`, `run_dir_path`, etc.).

### 2.4 Frontend — developer tooling

**Files:** `apps/web/src/lib/api.ts`, `apps/web/src/pages/DeveloperPage.tsx`

- **`clearAllPipelineRuns()`** calls `DELETE /api/v1/runs`.
- Developer settings page adds **Clear all analyses** with confirm + success line (counts deleted DB rows and folders).

### 2.5 Repository layout / docs moves

Under `Miscellaneous/`, older loose files (`plan.md`, `report.md`, task lists, etc.) were reorganized into **`Miscellaneous/Plans/`**, **`Miscellaneous/Tasks/`**, and test evidence under **`Miscellaneous/tests/`**. This README-style file replaces the need for a single scattered “what happened” narrative.

---

## 3. How the application flows today (architecture)

### 3.1 Runtime topology

```text
Browser (Vite + React, :5173)
  → proxy /api/v1/* → FastAPI (:8000)
       → PostgreSQL (runs, users, uploads, pipeline_run_logs, …)
       → OrchestratorEngine (background thread per run)
            → AgentRegistry + CrewAI / external clients
            → data/pipeline_runs/<track>/<run-folder>/  (filesystem truth during run)
```

### 3.2 User journey (happy path)

1. **Auth:** register/login; cookie session.
2. **Setup:** company name, **default analysis track** (`onboarding_path` in settings), optional **public scrape** toggle.
3. **Upload:** `POST /api/v1/files/upload` → row in `uploaded_files`.
4. **Start run:** `POST /api/v1/runs/start` with `uploaded_file_ids` (or empty if scrape-only mode is allowed).
5. **Background execution:** `OrchestratorEngine.execute()` builds run dir, walks **track profile stages**, dispatches agents in DAG order (sequential when parallel flag is off), appends `pipeline_run_logs`, updates `memory.json` / `decision_ledger.jsonl`, finalizes `final_report.json` and DB `replay_payload`.
6. **UI:** Analysis detail polls `GET /api/v1/runs/{slug}` and `.../logs` until status leaves `pending`/`running`.

### 3.3 Integration seams (merge safety)

- **Shivam side:** per-agent modules, JSON contracts, normalizer → **adapter envelope** (`status`, `summary`, `artifacts`, `next_hints`, `confidence`, `errors`).
- **Kartavya side:** `OrchestratorEngine` + persistence + runs API; calls agents only through registry dispatch, not by embedding prompt internals.

---

## 4. First successful run (baseline capture)

### 4.1 Where it lives

Folder: **`Miscellaneous/First Successful Run/`**

Primary run directory snapshot:

`google-kartavya_singh-save-20260329_012948-GAF2xGgJz5Xj_zd_/`

Supporting **`logs.txt`** is a flattened pipeline log + config excerpt suitable for quick human review.

### 4.2 Run identity

| Field               | Value                                                  |
| ------------------- | ------------------------------------------------------ |
| Run slug            | `GAF2xGgJz5Xj_zd_`                                     |
| Track               | `predictive` (from user theme / onboarding resolution) |
| Terminal status     | `completed`                                            |
| Agents completed    | **20 / 20**                                            |
| Failed agents       | **0**                                                  |
| Skipped agents      | **0**                                                  |
| Stage gate warnings | **0** (empty `warnings` in `final_report.json`)        |
| Wall duration       | **89.8 s** (under `max_seconds` 900)                   |
| Parallel            | `false`                                                |
| Adaptive policy     | `false`                                                |
| Stage gates         | `true`                                                 |

### 4.3 Stage sequence (from `logs.txt`)

1. `classify` → `pipeline_classifier`
2. `ingest` → file processors (pdf, csv, excel, json, plain text, image deferred)
3. `process` → `data_cleaning`, `smart_categorizer_metadata`
4. `aggregate` → `public_data_scraper`, `aggregator`
5. `analyze` → conflict, trend, sentiment, knowledge graph
6. `synthesize` → `insight_generation`, `swot_analysis`
7. `finalize` → `executive_summary`, `elevenlabs_narration`

### 4.4 What this run proved

| Claim                          | Evidence                                                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| End-to-end orchestration works | 7 stages started and completed; 20 dispatch steps in ledger                                                                               |
| Insights path works            | `insight_generation` + `swot_analysis` completed                                                                                          |
| Executive narrative works      | Non-empty `executive_summary` in `final_report.json` → `agent_results`                                                                    |
| Filesystem + DB contract       | `run_manifest.json`, `memory.json`, `decision_ledger.jsonl`, `final_report.json`, `context/agent_outputs/*` present under captured folder |
| Sequential mode honored        | `parallel_enabled: false` in runtime config; single-agent dispatch pattern in logs                                                        |

### 4.5 Baseline limitations (still true on first success)

| Issue                              | Symptom in baseline                                                                                   |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Gemini classifier quota / fallback | `pipeline_classifier` summary: rule-based fallback to predictive                                      |
| ElevenLabs context                 | `elevenlabs_narration`: “No executive summary available for narration” despite summary existing       |
| Processor realism                  | Some agent outputs are still **LLM-shaped**; not all paths parse real file bytes in every environment |

---

## 5. Scripted Excel E2E (second baseline)

| Field   | Value                                                                    |
| ------- | ------------------------------------------------------------------------ |
| Report  | `Miscellaneous/tests/2026-03-28_21-22-42_excel-sequential-e2e-report.md` |
| JSON    | `Miscellaneous/tests/2026-03-28_21-22-42_excel-sequential-e2e.json`      |
| Fixture | `Miscellaneous/data/sources/Google_Dataset_Analytics_Sample.xlsx`        |
| Outcome | `completed`, **20/20** agents, **~239.9 s**, sequential flags consistent |

Use this when you need a **reproducible** API-only proof independent of the UI session.

---

## 6. Accuracy sheet — expectations vs achieved

Scores are **qualitative** (High / Medium / Low) for hackathon tracking, not statistical guarantees.

| Area                        | Original expectation (from product vision / scope)                     | Achieved now                                                                      | Accuracy                                               |
| --------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Multi-agent pipeline exists | Many specialized agents + orchestrator                                 | Registry + orchestrator loop + 20-agent terminal completion on baseline           | **High**                                               |
| Track / theme from user     | Onboarding path drives predictive / automation / optimization / supply | `resolve_track` + company settings; runs show `predictive` for deep-analysis path | **High**                                               |
| Upload → analyze            | Real files drive processing                                            | Upload API + `source_file_ids` on run; Excel/PDF paths exercised                  | **High**                                               |
| Insights + SWOT + summary   | Business-facing outputs                                                | All three stages complete in first success + Excel E2E                            | **High**                                               |
| Gemini classifier           | Primary track selection via API                                        | Works when quota OK; **fallback** when 429 / key issues                           | **Medium**                                             |
| Public scrape               | Optional real web gather                                               | Agent runs; output quality varies (LLM-planned vs live crawl)                     | **Medium**                                             |
| ElevenLabs narration        | Audio from executive summary                                           | Stage completes but **context handoff** incomplete                                | **Low**                                                |
| Knowledge graph in UI       | D3 graph from structured nodes                                         | Builder agent completes; **full UI parity** from replay alone not baseline        | **Medium**                                             |
| pgvector chat               | Grounded Q&A                                                           | Not part of first-success path proof                                              | **Low** (not validated here)                           |
| Duplicate-run cache         | Reuse prior run by input hash                                          | Not implemented                                                                   | **Low**                                                |
| Production hardening        | 15m budgets, retries, warnings path                                    | Implemented at engine level; baseline run was **clean completed**                 | **High** (orchestration), **Medium** (content quality) |

### 6.1 Composite metrics (from baselines)

| Metric                             | First successful run | Excel sequential E2E                      |
| ---------------------------------- | -------------------- | ----------------------------------------- |
| Terminal status                    | `completed`          | `completed`                               |
| Agents completed                   | 20                   | 20                                        |
| Duration                           | 89.8 s               | 239.9 s                                   |
| `pipeline_run_logs` rows (approx.) | See `logs.txt` / DB  | 56 (per JSON)                             |
| Warnings in final report           | 0                    | 0 (E2E JSON path; see report for caveats) |

---

## 7. What to do next (from this baseline)

1. **ElevenLabs:** pass `executive_summary` text into `_run_elevenlabs_narration` context (or read from `prior_outputs`) so narration is not a false-negative.
2. **Gemini:** handle quota gracefully in product UX (banner: “using rule-based track”) and/or rotate key / paid tier for demos.
3. **Ingest fidelity:** tighten `file_type_classifier` + processor prompts to anchor on **real** `source_files_meta` filenames.
4. **CI smoke:** one API test that asserts ≥1 dispatch and terminal status in under a budget (regression guard for DAG + boot).

---

## 8. One-page “for judges” flow

Upload spreadsheet → orchestrator classifies track → routes through ingest → clean/tag → aggregate → analyze (conflict/trend/sentiment/graph) → synthesize insights + SWOT → executive summary → persisted run slug for replay/share.

That sentence matches what the **first successful run** folder demonstrates on disk and what the API replay endpoints expose for the UI.
