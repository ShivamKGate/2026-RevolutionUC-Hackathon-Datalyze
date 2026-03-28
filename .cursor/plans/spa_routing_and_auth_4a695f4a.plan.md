---
name: SPA routing and auth
overview: Add React Router with a public home (login/signup modals), protected app routes (setup gate, dashboard, data surfaces, settings with sidebar), and FastAPI-backed JWT sessions delivered via HttpOnly cookies—with schema work to support company linkage and progressive user setup.
todos:
  - id: phase-1-router-shell
    content: "Add react-router-dom, layouts (Public/App), stub pages for all routes, navbar + login/signup modals on /, 404, RequireAuth skeleton + credentials: include in api client"
    status: pending
  - id: phase-2-auth-api
    content: SQL migration (users extend, companies, setup flags); FastAPI /auth register|login|logout|me + HttpOnly JWT cookies; wire modals and redirects
    status: pending
  - id: phase-3-onboarding-dashboard
    content: Implement /setup flow + API persistence; guards for setup_complete; dashboard layout placeholders for status/results
    status: pending
  - id: phase-4-settings-sidebar
    content: Upload, pipeline, agents pages + settings nested routes with sidebar; migrate dev demo widgets off landing if needed
    status: pending
  - id: phase-5-verify
    content: Manual auth/session checklist; document deferred demo mock toggle; optional E2E later
    status: pending
isProject: false
---

# Datalyze: routing, auth session, and page map

## Decisions locked from your answers

- **First screen after auth:** `/setup` until onboarding is complete; otherwise `/dashboard`.
- **Auth UI:** Login and signup are **modals on `[/](apps/web/src/App.tsx)`** (not dedicated `/login` or `/signup` routes).
- **Auth backend:** Register + login against **FastAPI + Postgres**; **password reset out of scope**.
- **Session:** **HttpOnly cookies** set by the API; **JWT inside the cookie** (or split access/refresh—see Session design below). Target **session validity ~48 hours** (you said 1–2 days; plan assumes **2d** with env-tunable TTL).
- **Stack:** Stay on **Vite SPA**; “middleware” = **FastAPI dependencies / route protection** + **React route guards** (no Next.js).
- **Navigation:** **Logo/title always → `/`**. When authenticated, navbar right: **Dashboard**, **profile menu** (Settings, Logout).
- **Settings:** Primary **hub for app configuration**; **sidebar lives inside Settings** (and optionally extended to other app sections if you want one consistent app chrome later).
- **Admin vs user:** **Same screens** for everyone for now; keep `**role` in DB for future (e.g. account provisioning) without a separate admin-only UI in v1.
- **Marketing extras:** No separate marketing pages required; **About ≈ home**.
- **Errors:** **404** only for now; no dedicated 500/maintenance/offline.
- **Deep linking:** **Happy-path URLs** first; bookmarkable detail URLs (e.g. `/runs/:id`) explicitly **non-priority**.
- **Deferred (document only):** **Demo “mock logged in” toggle**—implement later, not in initial delivery.

---

## Route map (what exists in the browser)

| Path         | Access  | Purpose                                                                                                                  |
| ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------ |
| `/`          | Public  | Landing + project scope; **opens Login / Signup modals**                                                                 |
| `/setup`     | Private | Onboarding: company/profile fields + **path choice** (DevOps / automations / deep analysis, etc.) until `setup_complete` |
| `/dashboard` | Private | Single pane for **status, running jobs, consolidated results**                                                           |
| `/upload`    | Private | **Dedicated file / data import** (sidebar entry)                                                                         |
| `/pipeline`  | Private | **Pipeline / job status** (same info visible to all roles)                                                               |
| `/agents`    | Private | **Agent output / history** (or runs list—name to match your copy)                                                        |
| `/settings`  | Private | **Redirect** to first settings child (e.g. profile)                                                                      |
| `/settings/` | Private | **Nested settings** with **left sidebar** (profile, company, preferences, integrations placeholders as needed)           |
| `*`          | Public  | **404**                                                                                                                  |

**Public vs private (resolved):** Only `**/`** and **404** are fully public without session. Everything under `/setup`, `/dashboard`, `/upload`, `/pipeline`, `/agents`, `/settings` **must not render app chrome as authenticated** without a valid session; unauthenticated users should be **redirected to `/` (and can open modals from there).

**Post-auth redirects:**

```mermaid
flowchart TD
  signup[Signup success]
  login[Login success]
  check{setup_complete?}
  setup[/setup]
  dash[/dashboard]
  signup --> check
  login --> check
  check -->|no| setup
  check -->|yes| dash
```

---

## Session design (JWT + HttpOnly cookie)

**Recommended pattern for SPA + FastAPI** (balances your requirements and security):

1. **Access JWT** (short TTL, e.g. 15–60m) in an **HttpOnly** cookie **or** returned once and held in memory—**cookie is simpler** for “always send with `fetch`.
2. **Refresh token** (long TTL, up to **48h**) in a **separate HttpOnly** cookie with **path** limited to e.g. `/api/v1/auth/refresh` to reduce XSS blast radius.

If you want **minimal moving parts** for the hackathon, a **single JWT** in one HttpOnly cookie with `**max_age` = 48h** is acceptable; document **CSRF**: use `**SameSite=Lax`**, and for state-changing requests prefer `**fetch(..., { credentials: 'include' })`**plus a **custom header** (e.g.`X-Requested-With`) or **double-submit** token on mutating routes—FastAPI can enforce the header on POST/PUT/PATCH/DELETE.

**Frontend contract:** All API calls from `[apps/web/src/lib/api.ts](apps/web/src/lib/api.ts)` must use `**credentials: 'include'`** so the browser sends cookies through the existing Vite proxy (`[apps/web/vite.config.ts](apps/web/vite.config.ts)`). CORS already has `**allow_credentials=True\*\*`in`[apps/api/src/main.py](apps/api/src/main.py)`.

**Backend contract:** New auth routes under `**/api/v1/auth`** (e.g. `register`, `login`, `logout`, `me`, optional `refresh`). A **FastAPI dependency** (e.g. `get_current_user`) reads the cookie, verifies JWT, loads user; **router-level dependencies protect private API namespaces.

---

## Data model (users + company + progressive completion)

Current skeleton: `[apps/api/src/db/migrations/001_initial_schema.sql](apps/api/src/db/migrations/001_initial_schema.sql)` (`users`: id, name, email, role, created_at).

**New migration (002 or replace strategy)**—conceptual fields (exact names in implementation):

- `**companies`: id, name, slug or external id, created_at; optional metadata for “company context” used by agents later.
- `**users`** (extend): `password_hash`, `company_id` FK (nullable until signup assigns default company or user picks during setup), `**setup_complete`boolean** (default false),`**onboarding_path`** (enum/string: devops | automations | analysis | …), profile fields you want at signup vs later (e.g. `display_name`, `job_title`), `updated_at`.
- Optional: `**user_sessions`** or **refresh token hash table if using refresh rotation (better for logout-all-devices later).

**Progressive completion:** On **register**, insert user (+ company row if your flow creates one immediately), set `**setup_complete = false`**. `**/setup`**PATCH/POST endpoints finalize onboarding and set`**setup_complete = true`**and chosen path.`\*\*/me\*\*` returns flags so the SPA guard can route correctly.

---

## Frontend architecture

- **Dependency:** Add `**react-router-dom` to `[apps/web/package.json](apps/web/package.json)`.
- **Entry:** `[apps/web/src/main.tsx](apps/web/src/main.tsx)` wraps app with `**BrowserRouter`.
- **Replace monolith:** Refactor `[apps/web/src/App.tsx](apps/web/src/App.tsx)` into **route definitions** + small page components under e.g. `**apps/web/src/pages/`** and layouts under `**apps/web/src/layouts/\*\*`.
- **Layouts:**
  - `**PublicLayout`: navbar for `/` (brand + tagline left; right: Login / Signup buttons or Dashboard + avatar menu when session exists).
  - `**AppLayout`** (for all private routes except optionally settings): top navbar consistent with above; main **outlet** for child routes. **Sidebar for primary app sections** (Dashboard, Upload, Pipeline, Agents) can live here **or** only under settings per your preference—you specified sidebar **inside Settings**; simplest v1: **sidebar on all private routes** listing those five areas + Settings, **or** top-nav only outside settings and sidebar **only** under `/settings/*`. **Recommendation:** one `**AppLayout`with sidebar** for`/dashboard`, `/upload`, `/pipeline`, `/agents`, and a **nested `SettingsLayout`** for `/settings/\*` with a second-level sidebar for settings sections—avoids duplicating chrome.
- **Guards:** `**RequireAuth`** wrapper: on mount, call `**GET /api/v1/auth/me`**(or trust a lightweight context populated once); if 401,`**Navigate`to`/`**. `\*\*RequireSetupComplete\*\*`inverted for`/setup`vs`/dashboard` (if complete, skip setup; if incomplete, block dashboard).
- **Modals:** `LoginModal` / `SignupModal` controlled from **home page** or a tiny **auth UI context** so navbar can open them from `/` when logged out.
- **Profile menu:** Hover/click disclosure with **Settings** → `/settings/profile`, **Logout** → `POST /api/v1/auth/logout` + clear client state + redirect `/`.

Move existing dev/demo controls (health, agents MVP, etc.) either to `**/dashboard`** as a **“Developer”** card or temporarily to `**/settings/developer`** so the landing page stays product-shaped—decide during implementation so `/` stays clean.

---

## Backend architecture

- **Routers:** Add `[apps/api/src/api/v1/routes/auth.py](apps/api/src/api/v1/routes/auth.py)` and include in `[apps/api/src/api/v1/router.py](apps/api/src/api/v1/router.py)`.
- **Security:** Password hashing (**argon2** or **bcrypt** via `passlib` or similar), JWT encode/decode with secrets from `[apps/api/src/core/config.py](apps/api/src/core/config.py)` (`jwt_secret`, cookie name, TTLs).
- **Cookies:** `response.set_cookie(..., httponly=True, secure=production, samesite="lax", max_age=...)`.
- **Protection:** Dependency `get_current_user_optional` / `get_current_user_required` for routes that need it; future agent/upload routes attach `required` user.
- **Onboarding:** `PATCH /api/v1/users/me/setup` or dedicated `/api/v1/onboarding` to persist path + company fields and flip `setup_complete`.

---

## Phased delivery (4 core + 1 optional)

### Phase 1 — Routing shell and static UX

- Add React Router; create **stub pages** for every route in the table above.
- Implement `**PublicLayout`** and `**AppLayout`** (+ **404).
- Navbar: **Datalyze** + tagline **“Raw Data ↓, AI-Driven Strategies ↑”**; **Login/Signup** open modals (placeholder forms).
- `**RequireAuth`** stub: temporarily use a **fake `isAuthenticated`** flag or skip API until Phase 2, **or** call real `/me` if Phase 2 is done in parallel—prefer **wiring `credentials: 'include'` early even with 401.

### Phase 2 — Auth API and session

- Migration for **password + company linkage + setup flags** (minimal set to unblock auth).
- Implement **register**, **login**, **logout**, **me**; set/clear **HttpOnly JWT cookie(s)**.
- Wire **modal forms** to these endpoints; on success, **redirect** per flow (signup → `/setup`, login → `/setup` or `/dashboard`).
- `**RequireAuth`** uses `**/me\*\` truthfully.

### Phase 3 — Onboarding and dashboard

- Build `**/setup`** UI: company + user fields + **path selection**; persist via API; set `**setup_complete`.
- **Route guards:** incomplete users **cannot** open `/dashboard` (redirect `/setup`); complete users **skip** `/setup` when opening it (redirect `/dashboard`).
- `**/dashboard`:** layout for **runs, status, results**—start with **placeholder cards wired later to real agent/dataset endpoints.

### Phase 4 — App sections and settings shell

- `**/upload`, `/pipeline`, `/agents`: page skeletons + copy; hook to existing or future API (`datasets`, `analyses`, agents routes) incrementally.
- `**/settings` + nested routes + sidebar: profile (name, email), company, placeholders for integrations/API keys if needed later.
- Ensure **sidebar links** use `**NavLink`** for active states; **happy-path navigation only.

### Phase 5 (optional) — Verification and follow-ups

- Manual checklist: register → setup → dashboard → logout → login; cookie present/absent; refresh behavior.
- Document **demo mock auth toggle** in README or issue (no code in v1).
- Optional: minimal **E2E** later (Playwright) if time allows—not required for initial merge.

---

## Files you will touch most

- Web: `[apps/web/src/main.tsx](apps/web/src/main.tsx)`, `[apps/web/src/App.tsx](apps/web/src/App.tsx)`, new `pages/`, `layouts/`, `components/` (modals, sidebar), `[apps/web/src/lib/api.ts](apps/web/src/lib/api.ts)`.
- API: `[apps/api/src/main.py](apps/api/src/main.py)` (if adding custom middleware—often unnecessary if using dependencies), `[apps/api/src/api/v1/router.py](apps/api/src/api/v1/router.py)`, new `routes/auth.py`, `schemas` for auth/me, new SQL migration next to `[001_initial_schema.sql](apps/api/src/db/migrations/001_initial_schema.sql)`, `[apps/api/src/core/config.py](apps/api/src/core/config.py)` for secrets/TTLs.
- Env: `[apps/api/.env.example](apps/api/.env.example)` for `JWT_SECRET`, cookie settings.

---

## Out of scope for this plan (explicit)

- Password reset, email verification, OAuth providers.
- Dedicated marketing, pricing, legal pages.
- Deep-linked resource URLs, offline/500 pages.
- **Demo mock logged-in toggle** (tracked as future work).
