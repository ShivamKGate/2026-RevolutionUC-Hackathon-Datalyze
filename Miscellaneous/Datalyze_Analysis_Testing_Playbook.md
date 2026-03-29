# Datalyze — Analysis & testing playbook (Cursor / Claude Code)

This document is a **repeatable operating procedure** for manual and semi-automated testing of the Datalyze stack during the **testing phase**. Attach it to Cursor or Claude Code **together with your custom instructions** for the specific feature, agent, or flow under test. The assistant should treat this file as **non-negotiable process** unless you explicitly override a step in your custom prompt.

---

## 1. Purpose

- Run **focused, evidence-backed** test campaigns that match **exactly** what you (the human) asked for.
- Prefer **real UI verification** (browser) plus **API/terminal** checks when the UI is insufficient.
- Capture **iteration history** in a **per-campaign `report.md`** so you can see what changed, what improved, and what still misses the bar.
- Iterate **implement → test → measure → refine** until behavior matches your intent at **≥ 90%** on the rubric in §10 (or document why not and what would be required).

---

## 2. Pasteable system instructions (give this block to the agent)

Copy everything inside the fence below into your Cursor rule, Claude Code project instruction, or chat preface **in addition to** your custom test request.

```text
You are executing the Datalyze Analysis Testing Playbook (repository: Miscellaneous/Datalyze_Analysis_Testing_Playbook.md).

Hard rules:
1) If a dev server or long-running process for this app is already running in the workspace (e.g. `npm run dev`, uvicorn), STOP: do not stack duplicate servers. Either use the existing server if it is healthy, or terminate it cleanly and start ONE fresh run for this task—state which you did in the campaign report.
2) Create a dedicated campaign folder under Miscellaneous/tests/playbook-runs/<slug>/ (kebab-case, descriptive). Store all raw artifacts there (JSON, HAR exports, screenshots, curl transcripts). Maintain Miscellaneous/tests/playbook-runs/<slug>/report.md; append a new section after EVERY test batch (minimum three batches per campaign unless the user caps it).
3) Prefer browser-based verification for user-visible behavior (Cursor browser MCP or Chrome DevTools MCP). Use terminal/API (curl, httpx, TestClient) when testing auth headers, webhooks, or non-UI contracts.
4) Run at least THREE sequential test batches aligned with the user’s goal (e.g. baseline → after fix #1 → after fix #2). Each batch must end with observations and a score vs the acceptance criteria.
5) If the user names a misbehaving agent or subsystem, scope tests to that agent’s inputs/outputs (logs, artifacts, replay) and name the campaign folder accordingly (e.g. playbook-runs/insight-generation-contract/).
6) Company/data selection is STRICTLY one of: (A) demo company "End-to-End Analytics Co." (canonical demo tenant) for demo-account and synthetic-data flows, (B) user-provided synthetic data / prior fixtures, (C) user custom instructions only, or (D) "Google" scenario using the canonical sample workbook path in §6. Do not invent a fourth company for regression tests without user approval.
7) If synthetic data must be created (user asks, or test cannot run without fixtures), generate it for "End-to-End Analytics Co." only and persist it through the app upload flow so files land under `data/company/<company-slug>/private/` with DB metadata, matching normal saved-file behavior.
8) Treat demo tenant naming as fixed for tests: display name "End-to-End Analytics Co." (short alias "E2E Analytics Co." is acceptable only if existing data already uses it). Do not create additional demo-company variants.
9) After changes, re-run the same core checks from earlier batches and explicitly DIFF results (before vs after) in report.md.
10) End with a Final verdict (§11 template): what was done, accuracy vs target, residual risk, recommended follow-ups.

Do not commit noisy artifacts; report.md under each campaign is intended to be trackable (see .gitignore rules). If you add a new top-level scratch pattern, update .gitignore as described in the playbook.
```

---

## 3. Preconditions: running processes and “fresh run”

| Situation                                               | Required action                                                                                                                                                            |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm run dev` (or API only) already running and healthy | **Do not** start a second instance on the same ports. Reuse it; note in `report.md` which terminal/session is authoritative.                                               |
| Stale / crashed / wrong branch server                   | Stop the process (Ctrl+C or task kill), confirm port free, start **one** clean `npm run dev` (or documented API command). Record commands and URLs in the campaign folder. |
| User asked for isolated repro                           | Prefer a **new campaign slug** and a clean DB state only if the user asked for it (destructive: coordinate with Developer “Clear all analyses” or documented reset).       |

**Why this matters:** Duplicate servers cause wrong logs, wrong `pipeline_runs` rows, and flaky browser tests.

---

## 4. Campaign workspace layout

All playbook campaigns live here:

```text
Miscellaneous/tests/playbook-runs/
  <campaign-slug>/
    report.md                 # Primary human log — append after each batch (tracked)
    artifacts/                # Optional: raw dumps (gitignored via blanket rule)
    screenshots/              # Optional (gitignored)
    transcripts/              # curl / CLI logs (gitignored)
```

### 4.1 Naming `<campaign-slug>`

Use **short, specific, kebab-case** names tied to the request:

- Good: `e2e-demo-upload-predictive`, `file-type-classifier-google-xlsx`, `executive-summary-elevenlabs-handoff`
- Bad: `test1`, `misc`, `fix`

If the user cites a **specific agent**, put the agent id or obvious alias in the slug.

### 4.2 `.gitignore` contract

The repository `.gitignore` is set up so that **bulk files under `playbook-runs/` are ignored**, while each campaign’s **`report.md` remains eligible to commit** (negation rule). Do **not** disable this pattern without team agreement.

If you introduce a **new** class of scratch directory **outside** `playbook-runs/`, add an explicit ignore line and document it in the campaign `report.md`.

---

## 5. Tools and order of operations

1. **Read** the user’s custom instructions and this playbook; extract **acceptance criteria** (bullet list).
2. **Resolve environment** (§3); record base URL (e.g. `http://localhost:5173`, API `http://localhost:8000`).
3. **Browser first** for flows that users perform: login, settings, upload, start analysis, poll status, read insights.
4. **Terminal / API** for: cookie-authenticated `curl`, reproducing race conditions, inspecting raw JSON for `replay_payload`, or when UI is not yet wired.
5. **Repository / logs**: correlate UI run with `data/pipeline_runs/` and DB-backed logs if the user cares about orchestration truth.

**MCP:** When available, use **Cursor IDE browser** or **Chrome DevTools MCP** per server instructions (navigate → snapshot → interact; avoid duplicate lock issues).

---

## 6. Company and data sources

The playbook standardizes **where** tests run so results are comparable across sessions.

### 6.1 Demo tenant — **End-to-End Analytics Co.**

- **Use when:** Exercising **demo accounts**, investor demos, or “clean slate” company behavior.
- **Expectation:** Anyone with a **demo account** is provisioned into this company so they can run the app without touching production customer data.
- **Name policy:** Canonical display name is **"End-to-End Analytics Co."**. Existing short alias **"E2E Analytics Co."** may be retained only for backward compatibility.
- **Tests:** onboarding, default track, upload limits, public scrape toggle, “happy path” narrative.

### 6.1.1 Synthetic data generation policy (default)

- **Trigger:** If the user asks for synthetic data, or tests are blocked without sample files.
- **Company lock:** Synthetic datasets are created for **End-to-End Analytics Co.** only.
- **Persistence contract:** Save synthetic files via app upload (UI or `/api/v1/files/upload`) so persisted paths and DB rows match production behavior.
- **Expected storage shape:** `data/company/<slugified-company-name>/private/<uuid>_<original_filename>`.
- **Slug note:** slugification follows app logic (spaces/hyphens become underscores). For "End-to-End Analytics Co.", expected slug is typically `End_to_End_Analytics_Co`.
- **Reproducibility:** Record each generated file path, row count, and purpose in campaign `report.md`.

### 6.2 User synthetic / pre-created data

- **Use when:** The user (or repo docs) already defined fixtures, CSV/XLSX under a documented path, or seed scripts.
- **Action:** Point tests at **exact paths** and record file hashes or row counts in `report.md` for reproducibility.
- **If generating new synthetic fixtures:** Prefer §6.1.1 policy and persist under the End-to-End demo tenant unless the user explicitly overrides company scope.

### 6.3 User custom instructions only

- **Use when:** The user specifies a bespoke scenario (edge case file, malicious input, concurrency steps) with no fixture in repo.
- **Action:** Capture the **exact prompt** and steps in `report.md` Batch 0 so future readers can replay.

### 6.4 “Google” dataset scenario (canonical workbook)

- **Use when:** The user says the company is **Google** or the test should mirror the **Google sample analytics** workbook flow.
- **Canonical path (repo convention):**  
  `Miscellaneous/data/sources/Google_Dataset_Analytics_Sample.xlsx`  
  (Filename may vary slightly if renamed; prefer the **Google_Dataset_Analytics_Sample** basename the team standardizes on.)

**Note:** The folder `Miscellaneous/data/sources/` may be **gitignored** in this repository to avoid committing large binaries. That does **not** change the playbook: testers keep the file locally or obtain it from team storage; always record **actual path used** on disk in `report.md`.

As the team adds more sanctioned files under `Miscellaneous/data/sources/`, extend this section with a small table (filename → intended test purpose).

### 6.1.2 E2E_Analytics_Co synthetic data location

Synthetic data for the demo company lives at:

```
Miscellaneous/data/sources/E2E_Analytics_Co/
├── predictive/       # Sales, revenue, churn, KPIs, market trends
├── automation/       # Workflow logs, efficiency metrics, SOPs, system audit
├── optimization/     # Operational costs, department performance, goals, benchmarks
└── supply_chain/     # Supplier deliveries, inventory, logistics, procurement
```

Each subdirectory contains at least 4 files (CSV, XLSX, PDF, JSON) covering that analysis track's domain. This directory is **NOT gitignored** — it is committed to the repo so demo data is always available.

The `.gitignore` rule is: `Miscellaneous/data/sources/Google*` stays ignored, but `Miscellaneous/data/sources/E2E_Analytics_Co/` and all contents are tracked.

### 6.1.3 Demo account credentials

| Field | Value |
|---|---|
| **Email** | `demo@revuc.com` |
| **Password** | `admin@123` |
| **Company** | `E2E_Analytics_Co` (End-to-End Analytics Co.) |
| **Role** | `admin` |

This account is seeded via `apps/api/src/db/seeds/001_seed.sql`. When testing demo flows, always use this account and this company.

---

## 7. Minimum test structure: three sequential batches

Unless the user explicitly allows fewer, run **at least three** batches **in order**:

| Batch                          | Goal                                                                                                                                                       |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Batch A — Baseline**         | Reproduce current behavior with no code changes. Capture evidence (screenshots, API JSON snippets, log excerpts). Score vs acceptance criteria.            |
| **Batch B — First correction** | After targeted fixes or config changes, re-run the **same** core steps as Batch A. Diff observations; score again.                                         |
| **Batch C — Hardening**        | Stress edge cases the user cares about (refresh mid-run, second upload, wrong track, etc.). Re-run a **subset** of A’s checks for regression. Final score. |

**Optional batches D+:** Continue until ≥ 90% on the rubric or until diminishing returns—document stop reason.

---

## 8. Fine-tuning loop (align with user intent)

For each cycle:

1. **Infer acceptance criteria** from the user message; if ambiguous, state assumptions **once** in Batch A and ask the user only if blocked.
2. **Measure:** map each criterion to pass/partial/fail.
3. **Change minimally:** prefer the smallest diff that addresses the failure mode (agent prompt, routing, API contract, UI copy).
4. **Re-test:** never claim success without re-running the checks that failed before.
5. **Stop rule:** Target **≥ 90%** weighted pass (§10). If below, list **concrete** next engineering actions (not vague “improve quality”).

---

## 9. `report.md` template (per campaign)

Create `Miscellaneous/tests/playbook-runs/<slug>/report.md` **before Batch A** and **append** after each batch.

```markdown
# Campaign: <slug>

## Metadata

- **Owner / tool:** Cursor or Claude Code (version if known)
- **Date:**
- **Branch / commit:**
- **App URLs:** web = …, API = …
- **Data mode:** End-to-End Analytics Co | synthetic | custom only | Google workbook
- **Acceptance criteria (from user):**
  1. …

## Environment notes

- Servers running / restarted (yes/no, commands)

---

## Batch A — Baseline (YYYY-MM-DD HH:MM)

### Steps executed

1. …

### Evidence

- Links/paths to artifacts (screenshots, JSON under artifacts/)

### Observations

- …

### Criterion scoring (see §10)

| #   | Criterion | Result            | Notes |
| --- | --------- | ----------------- | ----- |
| 1   | …         | pass/partial/fail | …     |

### Batch accuracy

- **Weighted score:** \_\_%

---

## Batch B — After change set 1 (…)

(repeat structure; include **Diff vs Batch A** subsection)

---

## Batch C — Hardening (…)

(repeat structure; include **Regression check** vs A)

---

## Final verdict

(See §11)
```

---

## 10. Accuracy rubric (90% bar)

Define weights in Batch A (default if user silent):

| Priority    | Weight | Description                                                                |
| ----------- | ------ | -------------------------------------------------------------------------- |
| P0 — Must   | 50%    | Broken core flow, wrong data persisted, crash, security issue              |
| P1 — Should | 35%    | Incorrect agent output shape, misleading UI, failed handoff between agents |
| P2 — Nice   | 15%    | Copy, layout, minor latency, non-blocking warnings                         |

**Scoring:**

- **pass** = 100% of that row’s intent met
- **partial** = 50%
- **fail** = 0%

**Weighted accuracy** = sum(weight × score) / sum(weight). **Campaign success** if ≥ **90%** and **no P0 fail**.

---

## 11. Final verdict template (end of every campaign)

```markdown
## Final verdict

- **User request summary:**
- **What we changed (files / config):**
- **Evidence pointers:**
- **Accuracy:** \_\_% (P0/P1/P2 breakdown)
- **Comparison to baseline:** …
- **Residual risks / known gaps:**
- **Recommended next changes (ordered):**
- **Demo readiness statement:** (one honest sentence)
```

---

## 12. Agent-specific investigations

When the user names **one agent** (or small set):

1. Identify **inputs** (which prior artifacts, file paths, track).
2. Capture **outputs** (adapter envelope, `pipeline_run_logs` text, filesystem JSON under the run dir).
3. Re-run **only** the subgraph if possible (or full run if orchestration coupling requires it).
4. In `report.md`, include a **timeline** of agent order and **where** divergence appeared.

---

## 13. What not to do

- Do not commit **secrets** (API keys, cookies, JWT) into `report.md` or artifacts; redact.
- Do not flood GitHub with **large** binaries, full HAR files, or entire `pipeline_runs` trees—keep those under `artifacts/` inside the ignored playbook workspace.
- Do not change **unrelated** product behavior “while we’re here” unless the user asked or a P0 regression demands it.

---

## 14. Quick checklist (printable)

- [ ] Servers: reused cleanly or restarted once; documented
- [ ] Campaign folder created under `Miscellaneous/tests/playbook-runs/<slug>/`
- [ ] `report.md` created and updated after **each** batch (≥3 batches)
- [ ] Data mode chosen from §6 only
- [ ] Browser used for primary UX path
- [ ] API/terminal used where needed; evidence saved under `artifacts/`
- [ ] Before/after diff written for failed criteria
- [ ] Weighted accuracy computed; final verdict filled
- [ ] `.gitignore` updated if a **new** scratch root was introduced outside the standard pattern

---

## 15. Related repository docs

- **Integration baseline:** `Miscellaneous/Datalyze.md` or `Miscellaneous/Datalyze_Integration_Baseline_Report.md` (if renamed)
- **Test index:** `Miscellaneous/tests/report.md`
- **Orchestrator plan vs implementation:** `Miscellaneous/Datalyze Orchestrator Runtime - Master Plan vs Implementation Report.md`

---

## 16. Agent prompt version tracking

When agent prompts are modified (especially during the fine-tuning sprint), log every change to:

```
Miscellaneous/tests/agent_prompt_versions.jsonl
```

Each line is a JSON record:
```json
{"timestamp": "2026-03-29T...", "agent_id": "trend_forecasting", "change": "Added chart-ready JSON schema with confidence bands", "version": 2, "author": "shivam"}
```

This enables comparing run-to-run quality. When testing, note the prompt version used in the campaign `report.md`.

---

## 17. Demo replay testing procedure

When testing admin replay mode:

1. Run a full analysis on the demo account (`demo@revuc.com`) for a specific track
2. Verify the run completes successfully
3. Navigate to Admin → Demo Replay
4. Verify the replay for that track is captured (shows in the replay list)
5. Click "Play Replay" and verify:
   - Pipeline log entries appear progressively (animated)
   - Charts and KPIs render correctly
   - Playback speed controls work (1x, 2x, 5x)
6. Record evidence in campaign `report.md`

---

## 18. Upload track association testing

When testing file uploads with track association:

1. Upload a file with `analysis_track = "predictive"`
2. Upload another file with `analysis_track = "automation"`
3. Upload a third file with no track (should be visible in all tracks)
4. Navigate to Upload page, select track filter:
   - "Predictive" filter → should show file 1 + file 3 only
   - "Automation" filter → should show file 2 + file 3 only
5. Start an analysis for "Predictive" → verify only files 1 and 3 are used
6. Record results in campaign `report.md`

---

## 19. E2E_Analytics_Co synthetic data location

All synthetic demo data lives under:

```
Miscellaneous/data/sources/E2E_Analytics_Co/
├── predictive/
│   ├── sales_revenue_24months.csv
│   └── market_trends_2024_2025.json
└── automation/
    ├── workflow_process_logs.csv
    └── system_audit_results.json
```

Use these files when running predictive or automation track test campaigns on the demo account (`demo@revuc.com`). The data tells a coherent story about a ~75-employee analytics startup with 24 months of multi-regional data, seasonal patterns, and realistic anomalies (Aug 2024 supply disruption, Mar 2025 dip).

---

## 20. Demo account credentials for testing

| Field       | Value            |
|-------------|------------------|
| Email       | `demo@revuc.com` |
| Password    | `admin@123`      |
| Company     | `E2E_Analytics_Co` (End-to-End Analytics Co.) |
| Role        | Admin            |

---

_End of playbook — attach user custom instructions below this line when pasting into a chat._
