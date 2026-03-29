# Datalyze — Staged change manifest (full index)

This document inventories **everything currently in the Git index (staged)** for one reviewable snapshot: code moves, feature work, media, tests, and removals. It is meant to sit alongside **`Datalyze Orchestrator Runtime - Master Plan vs Implementation Report.md`**, **`Datalyze_Analysis_Testing_Playbook.md`**, **`Datalyze_Integration_Baseline_Report.md`**, and **`Datalyze Agent Specialization - Performance Report.md`** as a **session-level delta** rather than a permanent architecture spec.

**How to use:** After you commit, either delete this file, move it under `Miscellaneous/Test Runs/`, or trim it to match what actually landed on `main`.

---

## 1. Executive overview

Staged work spans **orchestrator/runtime and export hardening**, **analysis UI** (3D orchestration, confidence strip, sectioning, dashboard run actions), **auth and onboarding** (demo seeding, track helpers, login/company tweaks), **repository hygiene** (removal of placeholder `docs/`, `infra/`, `tests/`, `scripts/*` README trees, `.cursorrules`, and a duplicate hackathon PDF), and **asset reorganization** (media under `Media/`, task notes under `.cursor/plans/Old/`, test logs under `Miscellaneous/Test Runs/tests/`). Net: **~6k lines added** across API, web, and supporting files versus **~574 lines removed**, across **106 paths**.

---

## 2. Repository layout, docs, and removals

| Action             | Path / note                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Deleted**        | `.cursorrules`                                                                                                                                                                     |
| **Deleted**        | `Hackathon-Setup-Guide-REVOLUTIONUC26 (1).pdf`                                                                                                                                     |
| **Modified**       | `.gitignore` — adds ignore rule for `.superpowers/`                                                                                                                                |
| **Renamed**        | `Miscellaneous/Tasks/KartavyaTasks.md` → `.cursor/plans/Old/Tasks/KartavyaTasks.md`                                                                                                |
| **Renamed**        | `Miscellaneous/Tasks/ShivamTasks.md` → `.cursor/plans/Old/Tasks/ShivamTasks.md`                                                                                                    |
| **Renamed**        | `Miscellaneous/Media/Progress/Datalyze_MVP_Progress_Demo.mkv` → `Media/Progress/Datalyze_MVP_Progress_Demo.mkv`                                                                    |
| **New**            | `Media/Progress/Datalyze_MVP_Progress_Latest_Demo.mkv`                                                                                                                             |
| **New**            | `Media/Progress/Orchestration Graph.png`                                                                                                                                           |
| **Renamed**        | `Miscellaneous/tests/*` → `Miscellaneous/Test Runs/tests/*` (several dated validation artifacts + `report.md`)                                                                     |
| **New**            | `Miscellaneous/Test Runs/tests/Orchestrator_tests/` — API smoke, orchestrator validation, pipeline replay, live metrics JSON, live run summary (2026-03-29 timestamps)             |
| **New**            | `Miscellaneous/exported-reports/full-design.html.pdf`                                                                                                                              |
| **Deleted (bulk)** | `docs/README.md`, `docs/api/README.md`, `docs/architecture/README.md`, `docs/decisions/.gitkeep`, `docs/onboarding/README.md`, `docs/qa/README.md`, `docs/runbooks/README.md`      |
| **Deleted (bulk)** | `infra/README.md`, `infra/compose/.gitkeep`, `infra/compose/README.md`, `infra/docker/README.md`, `infra/terraform/.gitkeep`, `infra/terraform/README.md`                          |
| **Deleted (bulk)** | `packages/shared/README.md`, `packages/shared/src/constants/.gitkeep`, `packages/shared/src/types/.gitkeep`, `packages/shared/src/utils/.gitkeep`                                  |
| **Deleted (bulk)** | `scripts/ci/.gitkeep`, `scripts/ci/README.md`, `scripts/data/.gitkeep`, `scripts/data/README.md`, `scripts/setup/.gitkeep`, `scripts/setup/README.md`                              |
| **Deleted (bulk)** | `tests/README.md`, `tests/e2e/.gitkeep`, `tests/e2e/README.md`, `tests/fixtures/.gitkeep`, `tests/fixtures/README.md`, `tests/integration/.gitkeep`, `tests/integration/README.md` |

---

## 3. Backend (`apps/api`)

| Area              | Files                                                                                       | Summary                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Config / boot** | `.env.example`, `core/config.py`, `main.py`                                                 | New settings and wiring for runtime and services.                              |
| **Startup**       | **`services/startup_bootstrap.py`** (new)                                                   | Substantial bootstrap logic (schema/service initialization path).              |
| **Runs API**      | `api/v1/routes/runs.py`, `router.py`                                                        | Stop single run, delete single run, related routing.                           |
| **Auth**          | `routes/auth.py`, `schemas/auth.py`                                                         | Auth flow and schema updates (e.g. company/track-related fields).              |
| **Exports**       | `routes/exports.py`, **`services/export_pdf.py`**, **`services/pdf_chart_assets.py`** (new) | PDF export enhancements; chart/KG asset generation helpers.                    |
| **Agents**        | `services/agents/contracts.py`, **`output_evaluator.py`**                                   | Evaluator output shape (e.g. chart priority / confidence breakdown alignment). |
| **Orchestrator**  | `orchestrator_runtime/engine.py`, `policies.py`                                             | Engine and policy adjustments (parallelism, gates, or lifecycle).              |
| **Tooling**       | **`scripts/seed_demo_users.py`** (new), `requirements.txt`                                  | Demo user seeding; new Python dependencies.                                    |

---

## 4. Frontend (`apps/web`)

| Area                 | Files                                                                                                                                                                                                 | Summary                                                                                                |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Analysis page**    | **`AnalysisDetailPage.tsx`** (large rewrite), **`analysisPipelineSummary.ts`** (new)                                                                                                                  | Live vs completed layouts, sections (execution / charts / footer), orchestration + pipeline summaries. |
| **Orchestration UI** | **`OrchestrationModeling.tsx`**, **`OrchestrationGraph3D.tsx`**, **`buildOrchestrationModel.ts`** (new)                                                                                               | 3D graph, embedded/live modes.                                                                         |
| **Confidence**       | **`shared/ConfidenceStrip.tsx`** (new), `analysis.css`                                                                                                                                                | Compact header card; expandable breakdown beside ring.                                                 |
| **Templates**        | `AutomationTemplate.tsx`, `PredictiveTemplate.tsx`, `OptimizationTemplate.tsx`, `SupplyChainTemplate.tsx`, `StrategicPriorities.tsx`, `ExecutiveSummarySection.tsx`, `CollapsibleAnalysisSection.tsx` | Chart ordering, collapsibles, automation “Analysis charts” section, track-specific panels.             |
| **Shared**           | **`AnalysisErrorBoundary.tsx`**, **`chartSectionOrder.ts`**, `TrackRenderer.tsx`, `types.ts`, `index.ts`                                                                                              | Error boundary, chart sort helper, types exports.                                                      |
| **Dashboard**        | **`DashboardPage.tsx`**, **`styles/index.css`**                                                                                                                                                       | Per-run Open / Force stop / Delete; cancelled vs active styling; action row layout.                    |
| **API client**       | **`lib/api.ts`**                                                                                                                                                                                      | `stopPipelineRun`, `deletePipelineRun`, related types.                                                 |
| **Libs**             | **`renderSafe.ts`**, **`runViewNormalize.ts`**, **`trackOnboarding.ts`**, **`agentActivityUi.ts`** (new)                                                                                              | Safe rendering, run view normalization, onboarding path helpers.                                       |
| **Auth / settings**  | `LoginModal.tsx`, `AuthContext.tsx`, `CompanyPage.tsx`, `UploadPage.tsx`, `AgentsPage.tsx`                                                                                                            | Login, company settings, upload/agents touchpoints.                                                    |
| **Charts**           | `KPICard.tsx`, `RecommendationCard.tsx`                                                                                                                                                               | Card presentation tweaks.                                                                              |
| **Deps**             | `package.json`, `package-lock.json`, `tsconfig.app.tsbuildinfo`                                                                                                                                       | New deps (e.g. 3D stack) and lockfile.                                                                 |

---

## 5. Root and documentation

| File            | Change                                                                |
| --------------- | --------------------------------------------------------------------- |
| **`README.md`** | Updated project/setup/demo narrative (e.g. seed script, demo logins). |

---

## 6. Suggested commit message (3–4 sentences)

Ship the orchestrator-aligned analysis experience end-to-end: backend adds startup bootstrap, richer PDF export with chart assets, output-evaluator and engine/policy tweaks, single-run stop/delete APIs, and demo user seeding plus env and dependency updates. The web app gains a rebuilt analysis detail page with 3D orchestration modeling, normalized run views, compact interactive confidence, track templates with ordered chart sections (including an automation “Analysis charts” block), dashboard per-run actions, and supporting libs and error boundaries. Repository hygiene removes placeholder doc/infra/test scaffold files and relocates media, task notes, and test artifacts into clearer folders under `Media/`, `.cursor/plans/Old/`, and `Miscellaneous/Test Runs/`, and drops obsolete root artifacts such as `.cursorrules` and the duplicate hackathon PDF.

---

## 7. Cross-links to related reports

| Document                                                                                | Relationship                                                                                                                            |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `Miscellaneous/Datalyze Orchestrator Runtime - Master Plan vs Implementation Report.md` | Plan fidelity and orchestrator test conventions (note: some paths in that doc may predate the `Miscellaneous/Test Runs/tests/` rename). |
| `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md`                                   | Manual and scripted analysis testing guidance.                                                                                          |
| `Miscellaneous/Datalyze_Integration_Baseline_Report.md`                                 | Post-merge integration narrative and baseline flows.                                                                                    |
| `Miscellaneous/Datalyze Agent Specialization - Performance Report.md`                   | Per-agent specialization and performance notes.                                                                                         |

---

_End of staged manifest. Regenerate with `git diff --staged --stat` after future staging sessions._
