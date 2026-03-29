# Shivam — workstream & checklist (50/50 FE + BE)

**Split:** You own **half the frontend** and **half the backend** — complementary to Kartavya’s runs/onboarding slice.

**Teammate:** `Miscellaneous/KartavyaTasks.md`

---

## Your ownership (exclusive zones)

| Layer                   | Your paths / scope                                                                                                                                                                                                                                                                                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Frontend**            | **Upload** flow (drag-drop, file list, per-file status) and **Dashboard** (progress from run status, insight cards, activity/log strip). Prefer folders: `apps/web/src/features/upload/`, `apps/web/src/features/dashboard/`.                                                                                                                                |
| **Frontend API client** | `apps/web/src/lib/api/files.ts` plus small helpers for polling `GET run` / logs / insights if dashboard needs them (or a `dashboard.ts` that only calls Kartavya’s endpoints — that’s fine).                                                                                                                                                                 |
| **Backend**             | File ingestion: e.g. `apps/api/src/api/v1/routes/files.py`, `apps/api/src/schemas/file*.py`, `apps/api/src/services/file_storage.py`. Endpoints: `POST /api/v1/runs/{run_id}/files` (multipart), `GET /api/v1/runs/{run_id}/files`. Validate `run_id` exists (import shared `run_store` from Kartavya’s module **or** lightweight `GET` check — agree once). |
| **Do not own**          | Kartavya’s `routes/runs.py`, `pipeline_mock`, onboarding feature folder, `lib/api/runs.ts`.                                                                                                                                                                                                                                                                  |

**Merge-light rules**

- Avoid editing `apps/web/src/features/onboarding/` unless pairing.
- Avoid editing Kartavya’s run routes and pipeline services.
- **`apps/api/src/api/v1/router.py`:** you add `include_router(files_router, ...)`; coordinate with Kartavya so both routers stay included after merges.
- **`packages/shared`:** same pairing rule when shared fields change.

---

## Day 1 — MVP (your half of the story)

**Whole-team outcome:** onboarding → upload → start → dashboard shows progress + insights.

### P0 — Your must ship

**Backend**

1. **Multipart upload** to disk (e.g. `apps/api/data/uploads/{run_id}/`) with sane limits; return file metadata.
2. **List files** for a run; correct 404 if `run_id` unknown (use shared run store accessor if exposed).
3. Swagger examples for upload field name (`file` vs `files[]`) and max size — tell Kartavya for the UI.

**Frontend**

4. **Upload page:** accepts `run_id` from route/state; calls your upload API; shows errors and completion list.
5. **Dashboard page:** polls Kartavya’s `GET /runs/{id}` (and logs/insights as he exposed them); shows **progress**, **insight cards**, **recent activity**; button or link to **start** run if that action lives on dashboard (or onboarding hands off — align in sync).
6. Wire **navigation** from onboarding → upload → dashboard using the same `run_id` (Kartavya owns top-level router imports; you export page components).

### P1 — If P0 is done

- **SSE consumer** on dashboard if Kartavya adds `text/event-stream` (event names agreed upfront).
- **pytest** for upload + list + invalid run_id.
- Client-side **export** (download JSON) or call a stub export endpoint you add.

---

## If you finish early — backlog

1. File-type detection (extension/MIME) in metadata.
2. **SSE endpoint** for file-ingest events (optional) if you want streaming upload progress from API.
3. Stub **export** route: zip metadata + pointers to files.
4. Dashboard **charts** (Chart.js) from insight or run payload.
5. **Chat shell** UI + stub `POST /api/v1/chat` in **your** routes if you want full-stack ownership of that vertical later (coordinate path with Kartavya).

---

## Sync with Kartavya

| When         | What                                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| Start        | Lock **Run**, **FileMeta**, **Insight** shapes together.                                                                              |
| `run_store`  | If his run store is the source of truth, use his `get_run(run_id)` (or shared module) from your file routes — no duplicate run dicts. |
| Router       | Export `UploadPage` / `DashboardPage`; he imports into the central router.                                                            |
| Start run UX | Clarify whether **Start analysis** lives on upload screen, dashboard, or both.                                                        |
| End of day   | Joint demo path on one machine.                                                                                                       |

---

## Definition of done (your side)

- [ ] Upload works end-to-end with a `run_id` created from Kartavya’s onboarding.
- [ ] Dashboard reflects **his** pipeline state and insights without manual Swagger steps.
- [ ] Files persist on disk for the demo session; list API matches UI.

---

## Future (post-MVP)

- Virus scan hooks, S3-style storage, presigned URLs, scraper “public mode” APIs on your side if you keep owning ingestion-adjacent surface.
