---
name: ""
overview: ""
todos: []
isProject: false
---

# Final Sprint Plan — Kartavya Singh

## Meta

- **Owner:** Kartavya Singh
- **Teammate plan:** `.cursor/plans/final_sprint_shivam_kharangate.plan.md`
- **Playbook:** `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md`
- **Old plans (reference):** `.cursor/plans/Old/`
- **Demo account:** `demo@revuc.com` / `admin@123`
- **Demo company:** `E2E_Analytics_Co` (End-to-End Analytics Company)
- **Admin emails:** `demo@revuc.com` (shared demo), plus team personal accounts

---

## E2E_Analytics_Co — Demo Company Profile

| Field                    | Value                                                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Display Name**         | End-to-End Analytics Co.                                                                                                              |
| **Slug/ID**              | `E2E_Analytics_Co`                                                                                                                    |
| **Full Form**            | End-to-End Analytics Company                                                                                                          |
| **Type**                 | Startup providing end-to-end analytics and operations intelligence for SMEs and nonprofits                                            |
| **Core Functions**       | Sales analytics, process automation recommendations, operational optimization, supply chain visibility                                |
| **Employee Count**       | ~75 employees across Sales, Operations, Finance, HR, Logistics                                                                        |
| **Revenue Range**        | $2.5M–$4M annual                                                                                                                      |
| **Operating History**    | ~24 months of data (Jan 2024 – Dec 2025)                                                                                              |
| **Data Characteristics** | Multi-department, multi-regional (US East, US West, EU), seasonal patterns, realistic anomalies, growth trajectory with 2 dip periods |
| **Demo Goal**            | Every analysis track produces rich insights, meaningful charts, and actionable recommendations from this company's data               |

This company profile must be referenced in all synthetic data generation, seed scripts, and testing. The demo user (`demo@revuc.com`) is provisioned into this company with admin role.

---

## Ownership & Merge-Safety

### Files You Own (Exclusive — No Merge Conflicts)

| Layer                    | Files / Directories                                                                                                         |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **Orchestrator Runtime** | `apps/api/src/services/orchestrator_runtime/*.py` (engine, policies, contracts, persistence, track_profiles)                |
| **Run Routes**           | `apps/api/src/api/v1/routes/runs.py`                                                                                        |
| **DB Migrations**        | `apps/api/src/db/migrations/005_*.sql`, `006_*.sql` (NEW)                                                                   |
| **DB Seeds**             | `apps/api/src/db/seeds/001_seed.sql`                                                                                        |
| **Pages**                | `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/pages/AnalysisDetailPage.tsx`, `apps/web/src/pages/UploadPage.tsx`    |
| **Layout**               | `apps/web/src/layouts/AppLayout.tsx`                                                                                        |
| **Admin**                | `apps/web/src/pages/AdminPage.tsx` (NEW), `apps/api/src/api/v1/routes/admin.py` (NEW)                                       |
| **Optimization Visuals** | `apps/web/src/components/analysis/optimization/` (NEW)                                                                      |
| **Supply Chain Visuals** | `apps/web/src/components/analysis/supply_chain/` (NEW)                                                                      |
| **Synthetic Data**       | `Miscellaneous/data/sources/E2E_Analytics_Co/optimization/` and `Miscellaneous/data/sources/E2E_Analytics_Co/supply_chain/` |
| **Gitignore**            | `.gitignore` (E2E data rules)                                                                                               |

### Files You Must NOT Edit (Shivam Owns)

- `apps/api/src/services/agents/*.py` (all per-agent modules)
- `apps/api/src/services/crew_specialized.py`
- `apps/web/src/components/charts/` (Shivam's chart primitives)
- `apps/web/src/components/analysis/predictive/` and `apps/web/src/components/analysis/automation/`
- `apps/web/src/components/knowledge-graph/`
- `apps/api/src/services/export_pdf.py`

### Shared Files (Coordinate Before Editing)

- `apps/web/src/App.tsx` — You own routes; add admin route, import Shivam's exported components
- `apps/web/src/lib/api.ts` — You add admin/replay/run API functions; Shivam adds chart/export functions
- `apps/api/src/api/v1/router.py` — You add admin router; Shivam adds export router
- `apps/api/src/services/agent_registry.py` — Read-only dependency; if edits needed, coordinate

---

## Phase 1: Smart Orchestrator Agent Selection Fix (Backend)

**Problem:** The orchestrator currently runs ALL agents in every track (confirmed: 21/21 agents ran for an automation track run, including ALL file processors regardless of file type). This is the #1 fix needed.

### 1.1 Track-Specific Agent Selection in Engine

**File: `apps/api/src/services/orchestrator_runtime/engine.py`**

The `_execute_stage()` method currently runs all agents listed in the track profile's stage config. The problem is that `track_profiles.py` includes the same large set of agents across all tracks. Fix this:

1. **Consume the `pipeline_classifier` output** from the classify stage:

- After the classify stage runs, read `prior_outputs["pipeline_classifier"]` for the `recommended_agents` and `skip_agents` fields (Shivam is adding these to the classifier output)
- Update the engine's context with this routing information

1. **Filter stage agents dynamically:**

```python
   # In _execute_stage(), after getting valid_agents:
   classifier_output = self.prior_outputs.get("pipeline_classifier", {})
   recommended = classifier_output.get("artifacts", [{}])[0].get("result", {}).get("recommended_agents", [])
   skip_list = classifier_output.get("artifacts", [{}])[0].get("result", {}).get("skip_agents", [])

   if skip_list:
       valid_agents = [a for a in valid_agents if a not in skip_list]


```

1. **File-type aware processor filtering:**

- After the `file_type_classifier` agent runs in the ingest stage, read its `file_routing_map` from `prior_outputs`
- Skip processors that have no matching files:

```python
     file_routing = self.prior_outputs.get("file_type_classifier", {})
     routing_map = ...  # extract from artifacts
     needed_processors = set(routing_map.values())
     # Skip processors not in needed_processors


```

### 1.2 Update Track Profiles for Smarter Defaults

**File: `apps/api/src/services/orchestrator_runtime/track_profiles.py`**

Make track profiles more differentiated:

- **Predictive:** Focus on `trend_forecasting`, `insight_generation`, `sentiment_analysis`. Skip `automation_strategy`.
- **Automation:** Focus on `automation_strategy`, `insight_generation`. Include `trend_forecasting` as optional for predictive overlay. Skip `swot_analysis` from required.
- **Optimization:** Focus on `conflict_detection`, `insight_generation`, `swot_analysis`. Make `trend_forecasting` optional.
- **Supply Chain:** Focus on `trend_forecasting`, `conflict_detection`, `insight_generation`. Skip `automation_strategy`, make `swot_analysis` optional.

Move agents between `agents` (required) and `optional_agents` lists in each track's stage configs to reflect these priorities.

### 1.3 Time Budget: 5-Minute Active + 2-Minute Wrap-Up

**File: `apps/api/src/services/orchestrator_runtime/policies.py`**

Update `check_time_budget()`:

```python
def check_time_budget(start_time: float, max_seconds: int | None = None) -> dict[str, Any]:
    max_s = max_seconds if max_seconds is not None else settings.orch_max_run_seconds
    elapsed = time.time() - start_time
    remaining = max(0, max_s - elapsed)
    wrap_up_threshold = max_s - 120  # 2 minutes before deadline
    in_wrap_up = elapsed >= wrap_up_threshold
    return {
        "elapsed_seconds": round(elapsed, 1),
        "max_seconds": max_s,
        "remaining_seconds": round(remaining, 1),
        "budget_exceeded": remaining <= 0,
        "in_wrap_up_phase": in_wrap_up,
        "wrap_up_started_at": wrap_up_threshold,
    }
```

**File: `apps/api/src/services/orchestrator_runtime/engine.py`**

In `_execute_stage()`, when `in_wrap_up_phase` is true:

- Skip all remaining optional agents
- Only run required synthesis/finalize agents
- Force the `executive_summary` agent to produce a final output with whatever data is available
- Add warning to memory: "Entered wrap-up phase — finalizing with available results"

**Config change:** Set `ORCH_MAX_RUN_SECONDS=420` (7 minutes) in `.env.example` and `config.py` default.

### 1.4 Analysis Deduplication Per Company

**File: `apps/api/src/services/orchestrator_runtime/engine.py`**

Before starting a new run, check for existing analyses with similar inputs:

- Hash: `company_id + sorted(source_file_ids) + track + onboarding_path`
- Query `pipeline_runs` for completed runs with matching hash
- If match found and within 24 hours:
  - Return a special response with `redirect_to_slug` pointing to the existing analysis
  - Message: "A similar analysis was recently completed. Redirecting to the most recent matching analysis."
- If match found but older than 24 hours: proceed with new run but note the previous slug in context

**New column:** Add `input_hash VARCHAR(64)` to `pipeline_runs` table (in a new migration).

### 1.5 Guardrails: No Empty Outputs

**File: `apps/api/src/services/orchestrator_runtime/engine.py`**

In `_dispatch_single()`, after receiving the envelope:

- If `envelope.summary` is empty or generic (< 20 chars, or matches known generic patterns like "completed", "done"):
  - Retry with an enhanced prompt that includes more context from prior_outputs
  - If retry also produces empty output, mark as `completed_with_warnings` (not failed)
  - Add to memory warnings: "Agent {agent_id} produced minimal output"
- If confidence < 0.4 on a required agent:
  - Retry once with additional context
  - If still low, proceed but flag in warnings

### 1.6 Wire Output Evaluator

After Shivam creates `apps/api/src/services/agents/output_evaluator.py`:

- Add it as the last agent in the SYNTHESIZE stage (before FINALIZE) for all tracks
- It receives all prior_outputs and produces the `visualization_plan`
- The visualization_plan is included in the `replay_payload` stored in DB
- The frontend reads this plan to decide which chart components to render

---

## Phase 2: Database & Infrastructure (Backend)

### 2.1 New Migration: `005_demo_replay_admin.sql`

```sql
-- Demo replay table: stores the latest successful run for demo playback
CREATE TABLE IF NOT EXISTS demo_replay (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    run_id       INTEGER      NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    track        VARCHAR(40)  NOT NULL,
    replay_data  JSONB        NOT NULL DEFAULT '{}'::jsonb,
    captured_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(company_id, track)
);

-- Admin role on users
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'member';

-- Analysis deduplication hash
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS input_hash VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_input_hash ON pipeline_runs(input_hash);

-- Track association on uploaded files
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS analysis_track VARCHAR(40);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_track ON uploaded_files(company_id, analysis_track);
```

### 2.2 Demo User Seed: `001_seed.sql`

Update `apps/api/src/db/seeds/001_seed.sql`:

```sql
-- Demo company
INSERT INTO companies (name, public_scrape_enabled)
VALUES ('E2E_Analytics_Co', true)
ON CONFLICT DO NOTHING;

-- Demo user (password: admin@123, hashed with bcrypt)
-- The password hash must be generated at seed time by the setup script
-- or hardcoded as a known bcrypt hash for "admin@123"
INSERT INTO users (email, password_hash, name, display_name, company_id, role, setup_complete)
SELECT 'demo@revuc.com',
       '$2b$12$LJ3m4ys3gZzVbOSe7LcXxeKjZ8yN0vRr5A4d6EXAMPLE_HASH_HERE',
       'Demo User',
       'Demo User',
       c.id,
       'admin',
       true
FROM companies c WHERE c.name = 'E2E_Analytics_Co'
ON CONFLICT (email) DO NOTHING;
```

**Important:** Generate the actual bcrypt hash for "admin@123" at implementation time using Python's `bcrypt` library. Do not use the placeholder above.

Also add the two team member accounts as admin:

```sql
-- Team admin accounts (Shivam + Kartavya)
-- These use the same demo company for testing
```

### 2.3 Demo Replay Capture

**File: `apps/api/src/services/orchestrator_runtime/persistence.py`**

Add function `db_capture_demo_replay()`:

- Called at the end of `_finalize()` in engine.py when a run completes successfully
- Upserts into `demo_replay` table (one row per company+track, keeps latest only)
- Stores the complete `replay_payload` + `visualization_plan` + `agent_results`
- This is what the admin replay mode reads

### 2.4 Admin API Routes

Create `apps/api/src/api/v1/routes/admin.py`:

- `GET /api/v1/admin/replay/{track}` — Returns the demo replay data for a track
- `GET /api/v1/admin/replay` — Lists all available replays
- Requires admin role (check `user.role == 'admin'`)
- Returns 403 for non-admin users

### 2.5 Upload Track Association

**File: `apps/api/src/api/v1/routes/files.py`**

- Add `analysis_track` field to file upload endpoint (optional parameter)
- When listing files, support filtering by `?track=predictive`
- Files uploaded without a track are visible in all tracks
- Files uploaded with a specific track are only visible when that track is selected

### 2.6 Auto-Save Uploads for Demo Company

When the demo user (`demo@revuc.com`) uploads files:

- In addition to normal storage in `data/company/...`, also copy the file to `Miscellaneous/data/sources/E2E_Analytics_Co/{track}/`
- This ensures synthetic data persists in the repo for seeding
- Only for the demo company — other companies don't get this behavior

### 2.7 Update `.gitignore`

```gitignore
# Keep Google sources ignored
Miscellaneous/data/sources/Google*

# Allow E2E_Analytics_Co synthetic data to be committed
!Miscellaneous/data/sources/E2E_Analytics_Co/
!Miscellaneous/data/sources/E2E_Analytics_Co/**
```

---

## Phase 3: Dashboard & Admin (Frontend)

### 3.1 Dashboard Redesign

**File: `apps/web/src/pages/DashboardPage.tsx`**

Transform from basic list into a rich analytics dashboard:

- **Top row:** 4 stat cards (Total Analyses, Completed, In Progress, Avg Confidence Score)
- **Analysis list redesign:** Each analysis card shows:
  - Track badge (color-coded: predictive=blue, automation=green, optimization=orange, supply_chain=purple)
  - Status pill with real-time indicator for running analyses
  - Mini summary preview (first 100 chars)
  - Timestamp + duration
  - Confidence score gauge (if completed)
  - "Open" button → navigates to `/analysis/{slug}`
- **Quick actions:**
  - "New Analysis" button → navigates to upload page
  - "Start Analysis" (uses existing uploaded files)
  - Track filter dropdown (show analyses for specific track only)
- **Empty state:** Beautiful illustration + "Start your first analysis" CTA

### 3.2 Admin Section in Sidebar

**File: `apps/web/src/layouts/AppLayout.tsx`**

Add "Admin" link to sidebar, visible only when `user.role === 'admin'`:

```tsx
{user?.role === 'admin' && (
  <NavLink to="/admin" className={...}>Admin</NavLink>
)}
```

### 3.3 Admin Page — Replay Mode

**File: `apps/web/src/pages/AdminPage.tsx` (NEW)**

- Header: "Admin Panel"
- Section: "Demo Replay"
  - Lists available track replays (one per track where a successful run exists)
  - Each replay card shows: track name, captured timestamp, agent count, duration
  - "Play Replay" button → opens the analysis in replay mode
- Replay mode renders the same `AnalysisDetailPage` but with cached data
  - Animate the pipeline log entries appearing one by one (simulates live analysis)
  - Charts and KPIs appear progressively as the "replay" advances
  - Speed control: 1x, 2x, 5x playback speed

### 3.4 Upload Page — Track Selector

**File: `apps/web/src/pages/UploadPage.tsx`**

Add track selection to the upload flow:

- **Track selector dropdown** at the top:
  - "Predictive Deep Analysis"
  - "Automation Strategy"
  - "Business Optimization"
  - "Supply Chain & Operations"
- When a track is selected:
  - File list filters to show only files uploaded for that track (+ files with no track)
  - New uploads get tagged with the selected track
  - "Start Analysis" button becomes enabled when at least one file is present
- **File selection checkboxes:**
  - User can select/deselect which files to include in the analysis
  - "Select All" / "Deselect All" buttons
  - Selected file count indicator

### 3.5 API Client Updates

**File: `apps/web/src/lib/api.ts`**

Add new functions:

```typescript
// Admin replay
export async function getReplayList(): Promise<ReplayEntry[]> { ... }
export async function getReplayData(track: string): Promise<ReplayData> { ... }

// Upload with track
export async function uploadDataFile(file: File, track?: string): Promise<UploadedFile> { ... }
export async function listUploadedFiles(track?: string): Promise<UploadedFile[]> { ... }

// Start analysis with file selection
export async function startPipelineRun(opts: {
  uploaded_file_ids: number[];
  track?: string;
}): Promise<PipelineRun> { ... }

// Visualization plan from run
export async function getVisualizationPlan(slug: string): Promise<VisualizationPlan> { ... }
```

---

## Phase 4: Analysis Detail Page Redesign (Frontend)

**File: `apps/web/src/pages/AnalysisDetailPage.tsx`**

This is the most important frontend page. It must transform from a raw log viewer into a rich, interactive analysis dashboard.

### 4.1 Page Structure

```
┌─────────────────────────────────────────────┐
│ ← Dashboard    Analysis: {slug}    [Export] │
│ Track: Predictive  Status: ● Completed      │
├─────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ │ KPI Card│ │ KPI Card│ │ KPI Card│  ...   │  ← KPI Row (min 3)
│ └─────────┘ └─────────┘ └─────────┘       │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │    Executive Summary Section         │  │  ← Narrative + confidence gauge
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │    Charts Section (Track-Specific)   │  │  ← TrackRenderer component (from Shivam)
│  │    [Tab: Charts] [Tab: Knowledge     │  │
│  │                         Graph]       │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │    Recommendations Panel             │  │  ← Action items with confidence
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │    Agent Activity (Collapsible)      │  │  ← Existing agent list, collapsed by default
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │    Pipeline Log (Collapsible)        │  │  ← Existing log, collapsed by default
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 4.2 Data Flow

1. Fetch `getPipelineRun(slug)` — returns run metadata, agent_activity, pipeline_log, replay_payload
2. Fetch `getVisualizationPlan(slug)` — returns the `visualization_plan` from the output evaluator agent
3. Extract `agent_results` from replay_payload (the raw structured JSON from each agent)
4. Pass `{track, visualization_plan, agent_results}` to `<TrackRenderer />` (Shivam's component)
5. `TrackRenderer` dynamically renders the correct track template with appropriate charts

### 4.3 Live Analysis Progress

When `run.status === 'running'` or `run.status === 'pending'`:

- Show a progress indicator with current stage name
- Show agents completing one by one (animate entries appearing)
- Show partial KPIs as they become available from completed agents
- Auto-refresh every 2.5 seconds (already implemented, keep this)
- When status changes to completed, fetch visualization_plan and render charts

### 4.4 Redirect for Duplicate Analysis

If the API returns `redirect_to_slug` (from deduplication in Phase 1.4):

- Show a notice: "A similar analysis was recently completed."
- Link to the existing analysis
- Option to "Run anyway" (force new analysis)

### 4.5 Integration of Shivam's Components

Import from Shivam's modules:

```tsx
import { TrackRenderer } from "../components/analysis/TrackRenderer";
import { ExportButton } from "../components/analysis/shared/ExportButton";
import { ConfidencePanel } from "../components/analysis/shared/ConfidencePanel";
import { KPIRow } from "../components/analysis/shared/KPIRow";
import { RecommendationsPanel } from "../components/analysis/shared/RecommendationsPanel";
import { ExecutiveSummarySection } from "../components/analysis/shared/ExecutiveSummarySection";
```

---

## Phase 5: Business Optimization Track — Visual Integration

Build in `apps/web/src/components/analysis/optimization/`:

### 5.1 Profit Tree Visualization

- Component: `ProfitTree.tsx`
- Uses D3 to render a hierarchical tree: Revenue → (Product Revenue, Service Revenue) → ... → Gross Margin → Operating Expenses → Net Profit
- Each node shows current value, change from prior period, and optimization suggestions
- Expandable/collapsible nodes
- Color-coded: green (improving), red (declining), yellow (flat)

### 5.2 Constraint Impact Chart

- Component: `ConstraintImpact.tsx`
- Uses Plotly horizontal bar chart
- Shows top 5 business constraints ranked by EBITDA impact
- Each bar labeled with constraint name + estimated annual cost
- Tooltip shows detailed explanation from agent output

### 5.3 Recommendation Ranking Table

- Component: `RecommendationTable.tsx`
- Sortable table with columns: Recommendation, Priority (High/Medium/Low), Expected Uplift, Confidence Score, Timeline
- Color-coded priority badges
- Click to expand → shows detailed explanation + supporting data

### 5.4 Sensitivity Tornado Chart

- Component: `SensitivityTornado.tsx`
- Uses Shivam's `TornadoChart` primitive
- Shows how sensitive business metrics are to key variables (price, volume, cost, FX rate)
- Horizontal bars extending left (decrease) and right (increase) from baseline

### 5.5 Goal Alignment Map

- Component: `GoalAlignment.tsx`
- Visual map linking business objectives → recommended actions → expected outcomes
- Uses a simple flowchart/tree layout
- Each node is clickable for details
- Shows which recommendations serve which business goals

### 5.6 Quarterly Optimization Roadmap

- Component: `OptimizationRoadmap.tsx`
- Uses Shivam's `GanttChart` primitive
- Shows recommended optimization initiatives on a timeline
- Dependencies between initiatives shown as arrows
- Color-coded by priority and department

### 5.7 Optimization Template

- Component: `OptimizationTemplate.tsx`
- Orchestrates all the above components
- Layout: Profit Tree (full width) → Constraint Impact + Sensitivity side by side → Recommendations → Goal Alignment → Roadmap

---

## Phase 6: Supply Chain & Operations Track — Visual Integration

Build in `apps/web/src/components/analysis/supply_chain/`:

### 6.1 End-to-End Lead-Time Distribution

- Component: `LeadTimeDistribution.tsx`
- Plotly histogram/box plot showing lead time distribution across suppliers/products
- Percentile markers (P50, P90, P95)
- Target vs actual lead time overlay

### 6.2 Inventory Health Dashboard

- Component: `InventoryHealth.tsx`
- Multi-panel view:
  - Stacked bar chart: Healthy Stock / Overstock / Stockout Risk / Dead Stock by category
  - KPI cards: Total inventory value, turnover rate, days of supply, stockout incidents
  - Trend line: inventory levels over time

### 6.3 Supplier Reliability Scatter

- Component: `SupplierReliability.tsx`
- Uses Shivam's `ScatterPlot` primitive
- X: On-time delivery rate, Y: Defect rate, Size: Annual spend
- Color: risk level (green/yellow/red)
- Quadrant labels: "Reliable + Quality", "On-time but Quality Issues", etc.

### 6.4 Network Flow Map

- Component: `NetworkFlowMap.tsx`
- Custom D3 visualization showing supply chain nodes (suppliers → warehouses → distribution → customers)
- Edge thickness = volume
- Node color = health status
- Disruption flags as warning icons on affected nodes
- Clickable nodes show details

### 6.5 Demand vs Fulfillment Mismatch Heatmap

- Component: `DemandFulfillment.tsx`
- Uses Shivam's `HeatmapChart` primitive
- Rows: SKU/Product category, Columns: Time periods (months)
- Color scale: green (fulfilled) → yellow (partial) → red (stockout)
- Hover shows exact demand, fulfilled, and gap numbers

### 6.6 Order Delay Root-Cause Pareto

- Component: `OrderDelayPareto.tsx`
- Uses Shivam's `ParetoChart` primitive
- Shows top causes of order delays with cumulative % line
- Each bar annotated with corrective action from agent output

### 6.7 Supply Chain Template

- Component: `SupplyChainTemplate.tsx`
- Layout: Lead-Time + Inventory side by side → Network Flow Map (full width) → Supplier Reliability + Demand Heatmap → Order Delay Pareto

---

## Phase 7: Synthetic Data — Optimization + Supply Chain Tracks

Generate and save under `Miscellaneous/data/sources/E2E_Analytics_Co/`:

### 7.1 Optimization Track Data (`optimization/`)

Create at least **4 files**:

1. `**operational_costs_breakdown.csv` — Monthly cost data by department (Sales, Operations, Finance, HR, Logistics) for 24 months. Columns: month, department, labor_cost, tech_cost, overhead, revenue_generated, margin_pct. ~288 rows (12 months × 5 departments × 2 years + quarterly summaries).
2. `**department_performance_metrics.xlsx` — Sheet 1: Department KPIs (productivity, quality, employee satisfaction, customer satisfaction). Sheet 2: Goal progress tracking (quarterly goals, actual vs target). Sheet 3: Resource allocation (headcount, budget, utilization %).
3. `**strategic_goals_alignment.pdf` — Company strategic plan document with mission, vision, 5 strategic objectives, current progress, constraints identified, and quarterly review notes.
4. `**financial_benchmarks.json` — Industry benchmark data: peer company ratios (gross margin, operating margin, revenue per employee, customer acquisition cost), E2E's relative position, trend over 8 quarters.

### 7.2 Supply Chain Track Data (`supply_chain/`)

Create at least **4 files**:

1. `**supplier_deliveries_log.csv` — 1500+ delivery records over 24 months. Columns: order_id, supplier_name, product_category, order_date, promised_delivery, actual_delivery, quantity_ordered, quantity_received, defect_count, cost. Include 8 suppliers with varying reliability.
2. `**inventory_levels_monthly.xlsx` — Sheet 1: Monthly inventory by product category (10 categories × 24 months). Sheet 2: Reorder points and safety stock levels. Sheet 3: Stockout incidents with root cause codes.
3. `**logistics_cost_analysis.pdf` — Transportation and warehousing cost report with route analysis, carrier performance, seasonal cost variations, and optimization recommendations.
4. `**procurement_orders_history.json` — Structured procurement data: purchase orders with supplier, items, quantities, prices, lead times, quality scores. ~500 orders over 24 months.

### 7.3 Data Quality Requirements

Same as Shivam's requirements:

- Coherent story about E2E_Analytics_Co
- Realistic imperfections (~2% missing values, some outliers)
- Date range overlap for cross-referencing
- Enough variety for meaningful agent analysis
- Support generating at least 3 charts and 4 recommendations per track

---

## Phase 8: Testing — Optimization + Supply Chain Tracks

### 8.1 Test Protocol

Follow `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md`. Same protocol as Shivam's testing:

1. Login as `demo@revuc.com`
2. Upload corresponding synthetic data
3. Select track
4. Start analysis
5. Verify smart agent selection, correct processors, structured outputs, time budget, confidence, charts, recommendations, knowledge graph

### 8.2 Optimization Track Test Campaign

Campaign slug: `playbook-runs/optimization-track-e2e-validation/`

**Acceptance criteria:**

- Profit tree renders with correct hierarchy
- Constraint impact chart shows top 5 constraints
- Recommendation table is sortable and shows confidence scores
- Sensitivity tornado shows meaningful variable ranges
- Goal alignment map links objectives to recommendations
- Optimization roadmap shows quarterly timeline
- Only optimization-relevant agents run (not automation_strategy as primary)

### 8.3 Supply Chain Track Test Campaign

Campaign slug: `playbook-runs/supply-chain-track-e2e-validation/`

**Acceptance criteria:**

- Lead-time distribution shows realistic histogram
- Inventory health shows multiple categories with correct classification
- Supplier reliability scatter correctly plots supplier performance
- Network flow map renders with clickable nodes
- Demand vs fulfillment heatmap highlights stockout periods
- Order delay Pareto identifies top delay causes
- Trend forecasting shows supply chain predictions

### 8.4 Cross-Track Test

After both tracks pass individually, run a cross-track test:

- Upload files for multiple tracks
- Start two analyses (one optimization, one supply chain)
- Verify:
  - Files with track=optimization only appear in optimization analysis
  - Files with track=supply_chain only appear in supply chain analysis
  - Both analyses produce unique, non-overlapping outputs
  - Analysis deduplication works (second identical run redirects)

---

## Phase 9: Presentation — Business Strategy & Demo Flow

### 9.1 HTML Presentation File

Create or contribute to `Miscellaneous/presentation/datalyze_demo.html`.

**Your sections:**

1. **Cover Slide:**

- "Datalyze — Intelligent Business Analytics for Everyone"
- Team: Shivam Kharangate & Kartavya Singh
- RevolutionUC 2026

1. **Business Strategy & Social Impact:**

- Problem: Small businesses and nonprofits lack access to advanced analytics
- Solution: AI-powered platform that makes enterprise-grade analysis accessible
- How it works: Upload data → AI agents analyze → Rich visual insights
- Social impact: Helping nonprofits understand their operations better
- Target users: SMEs, nonprofits, community organizations

1. **Demo Flow (Scripted):**

- Slide with step-by-step demo script:

1. Open Datalyze → Show home page
2. Login as [demo@revuc.com](mailto:demo@revuc.com)
3. Dashboard shows past analyses
4. Upload new data files (E2E Analytics Co.)
5. Select analysis track → Start analysis
6. Watch agents work in real-time (or use replay mode for speed)
7. See charts, KPIs, recommendations appear
8. Explore knowledge graph
9. Export PDF report
10. Show admin replay mode
11. **What's Next / Future Roadmap:**

- Scenario simulation (what-if analysis)
- Real-time data connectors (live API feeds)
- Multi-language support
- Mobile app
- Enterprise features (team collaboration, audit trails)
- Additional analysis tracks

### 9.2 Presentation Design Notes

- Use modern dark theme with accent colors matching the app
- Include embedded screenshots/GIFs of the actual running app
- Keep slides concise — max 5 bullet points per slide
- Include the Datalyze logo and team credits
- Total presentation: ~15-20 slides
- Target duration: 5-7 minutes for recording, expandable to 10 for live Q&A

### 9.3 Offline Demo Resilience

The presentation HTML should:

- Embed key screenshots/data inline (base64 images or local paths)
- Work completely offline (no CDN dependencies)
- Include a "Replay Mode" section that shows cached analysis results if live demo is unavailable
- Reference the demo_replay table data for showing real analysis outputs

---

## Future Enhancements (NOT in Current Sprint — Document Only)

These are explicitly deferred:

- **Observability dashboard** (latency/error/token metrics) — implement last if time permits
- **What changed since last analysis** — delta comparison panel
- **Analysis history with compare-two-runs mode** — side-by-side comparison
- **Risk-adjusted automation scorecard** (Automation track)
- **Decision memo auto-generation** (Optimization track)
- **Benchmark gauges** (Optimization track)
- **Before/after workflow map** (Automation track)
- **Reorder policy simulator** (Supply Chain track)
- **Full checkpoint-resume** (crash recovery mid-pipeline)
- **Chat-based Q&A** on analysis results

---

## Execution Order & Priority

| Priority | Phase                              | Est. Effort  | Dependencies                                 |
| -------- | ---------------------------------- | ------------ | -------------------------------------------- |
| **P0**   | Phase 1: Smart Orchestrator Fix    | 2 sessions   | None — start immediately                     |
| **P0**   | Phase 2: Database & Infrastructure | 1 session    | None — can parallel with Phase 1             |
| **P0**   | Phase 7: Synthetic Data            | 1 session    | Needed for testing                           |
| **P1**   | Phase 3: Dashboard & Admin         | 2 sessions   | Phase 2 (DB migrations)                      |
| **P1**   | Phase 4: Analysis Detail Page      | 2 sessions   | Shivam's Phase 2 (chart components)          |
| **P1**   | Phase 5: Optimization Visuals      | 1 session    | Phase 4 structure, Shivam's chart primitives |
| **P1**   | Phase 6: Supply Chain Visuals      | 1 session    | Phase 4 structure, Shivam's chart primitives |
| **P2**   | Phase 8: Testing                   | 1–2 sessions | Phases 1-7 complete                          |
| **P3**   | Phase 9: Presentation              | 1 session    | After all testing passes                     |

**Total estimated sessions:** 12–14 focused work sessions

---

## Coordination Checkpoints with Shivam

| When                 | What                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------- |
| **Before Phase 1**   | Agree on `pipeline_classifier` output schema (recommended_agents, skip_agents fields) |
| **Before Phase 4**   | Shivam exports `TrackRenderer` and shared components; agree on props interface        |
| **Before Phase 4**   | Agree on `visualization_plan` JSON schema (what fields, what chart types)             |
| **After Phase 2**    | Shivam generates bcrypt hash for demo password; insert into seed SQL                  |
| **After Phases 5-6** | Shivam reviews your chart components; you review his chart components                 |
| **Before Phase 9**   | Coordinate presentation HTML structure and design theme                               |
| **End of each day**  | Joint `npm run dev` walkthrough on one machine                                        |

---

## Playbook Additions

Add the following to `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md`:

- Section 6.1.2: E2E_Analytics_Co synthetic data location → `Miscellaneous/data/sources/E2E_Analytics_Co/`
- Section 6.1.3: Demo account credentials for testing → `demo@revuc.com` / `admin@123`
- Section 6.5: Upload track association testing — verify files are filtered by track
- Section 16: Agent prompt version tracking → `Miscellaneous/tests/agent_prompt_versions.jsonl`
- Section 17: Demo replay testing procedure — verify admin replay mode works end-to-end

---

_End of Kartavya Singh's Final Sprint Plan_
