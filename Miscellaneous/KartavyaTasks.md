# Kartavya — workstream & checklist (50/50 FE + BE)

**Split:** You own **half the frontend** and **half the backend** — not the whole stack. Shivam mirrors the same balance on complementary slices.

**Teammate:** `Miscellaneous/ShivamTasks.md`

---

## Your ownership (exclusive zones)

| Layer                   | Your paths / scope                                                                                                                                                                                                                                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend**            | App shell, global layout, **router entry**, **onboarding** flow (forms, validation UX, `run_id` handoff). Prefer folder: `apps/web/src/features/onboarding/` (and shared layout under `components/layout/` you create).                                                                                                                              |
| **Frontend API client** | `apps/web/src/lib/api/runs.ts` (and re-exports from `lib/api/index.ts` if you add one) — create run, get run, start run, get logs/insights if those routes are yours.                                                                                                                                                                                |
| **Backend**             | Run lifecycle + mock pipeline: e.g. `apps/api/src/api/v1/routes/runs.py`, `apps/api/src/schemas/run*.py`, `apps/api/src/services/run_store.py`, `apps/api/src/services/pipeline_mock.py`. Endpoints: `POST/GET /api/v1/runs`, `POST .../start`, `GET .../logs`, `GET .../insights` (or embed logs/insights in `GET run` — pick one and tell Shivam). |
| **Do not own**          | Shivam’s `routes/files.py`, upload/dashboard feature folders, `lib/api/files.ts` — see his doc.                                                                                                                                                                                                                                                      |

**Merge-light rules**

- Avoid editing Shivam’s feature folders under `apps/web/src/features/` unless pairing.
- Avoid editing `apps/api/.../routes/files.py` and his file service module.
- **`apps/api/src/api/v1/router.py`:** add `include_router(runs_router, ...)` in your PR; Shivam adds files router — whoever merges second rebases and includes **both** lines.
- **`packages/shared`:** either of you may propose types; **pair for 10 minutes** when a field touches both runs and files (e.g. `run_id` everywhere).

---

## Day 1 — MVP (your half of the story)

**Whole-team outcome:** onboarding → upload → start → dashboard shows progress + insights.

### P0 — Your must ship

**Backend**

1. In-memory (or SQLite) **run store**: create run, fetch by id, attach `stage`, `status`, timestamps.
2. **Mock pipeline** after `start`: advance stages on a timer or steps; append **log lines**; when “synthesizing”, attach **3–5 mock insights** (title, summary, confidence, sources).
3. **REST:** `POST /api/v1/runs`, `GET /api/v1/runs/{run_id}`, `POST /api/v1/runs/{run_id}/start`, plus **logs + insights** (dedicated GETs or embedded in run — document in Swagger).

**Frontend**

4. **Router + shell** (e.g. React Router): routes for `/`, `/onboarding`, leave mount points or links for Shivam’s `/upload` and `/dashboard` (he registers his pages; you wire the router table together **once** — see sync).
5. **Onboarding page:** company context + track; call your `POST /runs`; persist `run_id` (`sessionStorage` or query).
6. **Thin API client** in `lib/api/runs.ts` with types aligned to your Pydantic schemas.

### P1 — If P0 is done

- SSE for run events **or** document polling contract for Shivam’s dashboard (if you implement SSE, put route under your `runs` module or agree a single `events` module).
- SQLite persistence for runs.
- pytest for run creation + pipeline transition.

---

## If you finish early — backlog

1. Orchestration **diagram** data endpoint (JSON nodes/edges from mock pipeline).
2. Export run summary JSON from your service.
3. Ollama: single **summarize run** call behind feature flag.
4. FE: accessibility pass on onboarding; empty/error states.

---

## Sync with Shivam

| When          | What                                                                                                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Before coding | Agree **Run**, **Insight**, **LogEvent** JSON shapes (copy into `packages/shared` or README snippet).                                                                                             |
| Router        | Decide who edits `App.tsx` / route table **once** per day: recommended — **you** own the router file; Shivam exports `UploadPage` / `DashboardPage` from his feature folders and you import them. |
| `run_id`      | After onboarding, navigate to upload with `run_id` in route or state so his upload calls `.../runs/{id}/files`.                                                                                   |
| End of day    | Joint `npm run dev` walkthrough.                                                                                                                                                                  |

---

## Definition of done (your side)

- [ ] Onboarding creates a run and lands the user on the next step with a valid `run_id`.
- [ ] Start + poll (or SSE) produces stages, logs, and insights from **your** API.
- [ ] No merge conflicts with Shivam’s owned files; `router.py` includes both routers.

---

## Future (post-MVP)

- Real orchestrator, Gemini classifier, pgvector — split new modules the same way (contract first, then parallel files).
