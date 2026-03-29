---
name: ""
overview: ""
todos: []
isProject: false
---

# Final Sprint Plan — Shivam Kharangate

## Meta

- **Owner:** Shivam Kharangate
- **Teammate plan:** `.cursor/plans/final_sprint_kartavya_singh.plan.md`
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

| Layer                    | Files / Directories                                                                                                     |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **Agent Modules**        | `apps/api/src/services/agents/*.py` (all per-agent files, contracts, normalizer, shared_prompts)                        |
| **Agent Specialization** | `apps/api/src/services/crew_specialized.py`                                                                             |
| **Chart Components**     | `apps/web/src/components/charts/` (NEW — all Plotly/D3 wrappers)                                                        |
| **Analysis Components**  | `apps/web/src/components/analysis/` (NEW — track-specific output renderers)                                             |
| **Knowledge Graph**      | `apps/web/src/components/knowledge-graph/` (NEW — interactive graph viewer)                                             |
| **Export Service**       | `apps/api/src/services/export_pdf.py` (NEW)                                                                             |
| **Synthetic Data**       | `Miscellaneous/data/sources/E2E_Analytics_Co/predictive/` and `Miscellaneous/data/sources/E2E_Analytics_Co/automation/` |

### Files You Must NOT Edit (Kartavya Owns)

- `apps/api/src/services/orchestrator_runtime/*.py`
- `apps/api/src/api/v1/routes/runs.py`
- `apps/api/src/db/migrations/*.sql`
- `apps/web/src/pages/DashboardPage.tsx`
- `apps/web/src/pages/AnalysisDetailPage.tsx` (Kartavya owns the page; you export components he imports)
- `apps/web/src/pages/AdminPage.tsx` (NEW — Kartavya creates)
- `apps/web/src/layouts/AppLayout.tsx`

### Shared Files (Coordinate Before Editing)

- `apps/web/src/App.tsx` — Kartavya owns routes; you export page/component modules only
- `apps/web/src/lib/api.ts` — You add chart/export API functions; Kartavya adds admin/replay functions
- `apps/api/src/api/v1/router.py` — You add export router; Kartavya adds admin router
- `.gitignore` — Kartavya handles the E2E data ignore rules
- `apps/api/src/services/agent_registry.py` — Read-only dependency; if edits needed, coordinate

---

## Phase 1: Agent Output Quality & Structured JSON (Backend)

**Goal:** Transform agent outputs from generic 2–3 sentence responses into chart-ready, structured JSON that the frontend can render as KPI cards, charts, recommendations, and interactive elements.

### 1.1 Per-Agent Prompt Overhaul

For every agent in `apps/api/src/services/agents/`, rewrite the system prompts and task templates to produce **structured, chart-ready JSON** instead of generic text. Each agent must return data in a schema that maps directly to a frontend visualization component.

**Agents to update (in priority order):**

1. `**trend_forecasting.py`\*\* — Must return time-series arrays with confidence bands:

```json
   {
     "forecasts": [
       {
         "metric": "revenue",
         "historical": [{"date": "2024-01", "value": 180000}, ...],
         "predicted": [{"date": "2026-01", "value": 245000, "lower": 220000, "upper": 270000}, ...],
         "confidence": 0.82,
         "trend_direction": "upward",
         "seasonality_detected": true
       }
     ],
     "drivers": [{"factor": "seasonal_demand", "impact_pct": 35}, ...],
     "anomalies": [{"date": "2024-08", "metric": "revenue", "expected": 200000, "actual": 145000, "root_cause": "supply disruption"}]
   }


```

1. `**insight_generation.py**` — Must return insight cards with chart-type hints:

```json
{
  "insights": [
    {
      "title": "Revenue Growth Accelerating",
      "description": "...",
      "impact": "high",
      "confidence": 0.85,
      "chart_type": "kpi_card",
      "data": { "current": 3200000, "previous": 2800000, "change_pct": 14.3 }
    }
  ],
  "recommendations": [
    {
      "action": "...",
      "priority": "high",
      "expected_impact": "...",
      "confidence": 0.78
    }
  ]
}
```

1. `**automation_strategy.py**` — Must return process analysis with bottleneck data:

```json
{
  "processes": [
    {
      "name": "Invoice Processing",
      "current_time_hours": 4.5,
      "automated_time_hours": 0.5,
      "cost_current": 15000,
      "cost_automated": 2000,
      "roi_months": 3,
      "implementation_effort": "medium",
      "impact_score": 0.9
    }
  ],
  "bottlenecks": [{ "stage": "...", "time_pct": 35, "cost_pct": 28 }],
  "sop_draft": { "steps": ["...", "..."], "estimated_savings_annual": 156000 }
}
```

1. `**swot_analysis.py**` — Must return structured quadrant data
2. `**sentiment_analysis.py**` — Must return sentiment distribution arrays
3. `**knowledge_graph_builder.py**` — Must return Neo4j-compatible nodes/edges with context
4. `**conflict_detection.py**` — Must return conflict items with severity and resolution suggestions
5. `**aggregator.py**` — Must produce corpus summary with categorized signals
6. `**executive_summary.py**` — Must return structured sections (not just a paragraph)
7. **All processors** (`csv_processor`, `excel_processor`, `pdf_processor`, `json_processor`, `plain_text_processor`) — Must return structured extraction results with column metadata, data previews, detected schemas

**Key rules for all agents:**

- JSON-only output (no prose outside JSON)
- Every agent must include a `chart_suggestions` field listing what visualizations its data supports
- Minimum 3 KPI-worthy data points per analysis agent
- Confidence score above 0.6 required for recommendations to be surfaced
- Token-conscious but depth-rich: aim for 300–800 tokens of structured data per agent

### 1.2 File-Type Aware Processor Selection

**Problem:** Currently ALL processors run regardless of actual file types uploaded (confirmed in the successful run — `pdf_processor`, `csv_processor`, `excel_processor`, `json_processor`, `plain_text_processor` ALL ran for an Excel-only upload).

**Fix in `apps/api/src/services/agents/file_type_classifier.py`:**

- The file_type_classifier agent must return a `file_routing_map` that maps each uploaded file to its correct processor
- Add a `classify_file_types(source_files_meta)` utility that uses file extension + MIME type to determine which processors to invoke
- This output is consumed by the orchestrator (Kartavya will update `engine.py` to skip processors not in the routing map)
- Emit the routing map as an artifact so it's available to the orchestrator via `prior_outputs`

### 1.3 Gemini Classifier Enhancement

**Current state:** `_run_pipeline_classifier` in `engine.py` already has Gemini → LIGHT_MODEL → rule-based fallback. Your job is to improve the classification prompt quality and add richer classification output.

**In `apps/api/src/services/agents/pipeline_classifier.py`:**

- Enhance the classification prompt to also analyze file contents summary (not just count)
- Return additional classification metadata:

```json
{
  "track": "predictive",
  "confidence": 0.92,
  "reasoning": "Sales and revenue data with temporal columns suggest forecasting use case",
  "secondary_track": "optimization",
  "file_types_detected": ["excel"],
  "data_domains_detected": ["sales", "finance"],
  "recommended_agents": [
    "trend_forecasting",
    "insight_generation",
    "sentiment_analysis"
  ],
  "skip_agents": ["automation_strategy"]
}
```

- The `recommended_agents` and `skip_agents` fields will be consumed by Kartavya's orchestrator to make smarter agent selection decisions

### 1.4 Knowledge Graph Builder Enhancement

**In `apps/api/src/services/agents/knowledge_graph_builder.py`:**

- Output must be Neo4j-compatible with nodes and edges:

```json
{
  "nodes": [
    {
      "id": "revenue_q1",
      "label": "Q1 Revenue",
      "type": "metric",
      "value": 820000,
      "context": "...",
      "insights": ["..."]
    }
  ],
  "edges": [
    {
      "source": "revenue_q1",
      "target": "marketing_spend",
      "relationship": "correlated_with",
      "strength": 0.78
    }
  ],
  "clusters": [
    { "name": "Financial Metrics", "node_ids": ["revenue_q1", "..."] }
  ]
}
```

- Each node must have a `context` field (what the aggregator provided) and an `insights` field (what was generated about this node)
- The frontend knowledge graph viewer will render these as interactive clickable nodes

### 1.5 Output Quality Evaluation

Add a new utility in `apps/api/src/services/agents/output_evaluator.py`:

- Given the final agent outputs, evaluate what UI elements can be rendered
- Return a `visualization_plan`:

```json
{
  "kpi_cards": [
    {
      "metric": "...",
      "value": "...",
      "change": "...",
      "source_agent": "insight_generation"
    }
  ],
  "charts": [
    {
      "type": "time_series",
      "title": "...",
      "data_source_agent": "trend_forecasting",
      "priority": 1
    }
  ],
  "recommendations": [
    { "text": "...", "confidence": 0.85, "source_agent": "..." }
  ],
  "knowledge_graph": { "available": true, "node_count": 15 },
  "overall_confidence": 0.78,
  "confidence_breakdown": {
    "data_quality": 0.82,
    "analysis_depth": 0.75,
    "actionability": 0.79
  }
}
```

- This agent runs as the LAST analysis step before executive_summary
- Kartavya will wire this into the orchestrator's finalize stage

---

## Phase 2: Visualization Components (Frontend)

**Goal:** Build a library of reusable, beautiful chart and data display components that any track can use.

All components go under `apps/web/src/components/charts/` and `apps/web/src/components/analysis/`.

### 2.1 Install Dependencies

Add to `apps/web/package.json`:

- `plotly.js` + `react-plotly.js` (primary charting)
- `d3` + `@types/d3` (custom visualizations: profit tree, network flow, Sankey)
- A lightweight graph visualization library (e.g., `react-force-graph-2d` or `vis-network`) for the knowledge graph (Neo4j data rendered client-side — no Neo4j server needed)

### 2.2 Shared Chart Primitives

Build these reusable components in `apps/web/src/components/charts/`:

| Component            | Props Interface                                                          | Used By                  |
| -------------------- | ------------------------------------------------------------------------ | ------------------------ |
| `TimeSeriesChart`    | `{series: {date, value, lower?, upper?}[], title, showConfidenceBands?}` | Predictive, Supply Chain |
| `BarChart`           | `{categories: string[], values: number[], title, horizontal?}`           | All tracks               |
| `KPICard`            | `{title, value, previousValue?, changePct?, trend?, confidence?}`        | All tracks               |
| `RadarChart`         | `{dimensions: {label, current, predicted}[], title}`                     | Predictive               |
| `HeatmapChart`       | `{rows, cols, values, title, colorScale?}`                               | Predictive, Supply Chain |
| `WaterfallChart`     | `{steps: {label, value, type: 'increase'                                 | 'decrease'               |
| `SankeyDiagram`      | `{nodes: {id, label}[], links: {source, target, value}[], title}`        | Automation               |
| `BubbleChart`        | `{points: {x, y, size, label, color?}[], xLabel, yLabel, title}`         | Automation               |
| `TornadoChart`       | `{factors: {label, low, high, baseline}[], title}`                       | Optimization             |
| `ScatterPlot`        | `{points: {x, y, label?, color?}[], xLabel, yLabel, title}`              | Supply Chain             |
| `ParetoChart`        | `{categories: string[], values: number[], title}`                        | Supply Chain             |
| `GanttChart`         | `{tasks: {name, start, end, dependencies?}[], title}`                    | Optimization             |
| `ConfidenceGauge`    | `{score: number, breakdown?: {label, score}[], title?}`                  | All tracks               |
| `RecommendationCard` | `{action, priority, impact, confidence, source_agent}`                   | All tracks               |

### 2.3 Track-Specific Template Components

Build in `apps/web/src/components/analysis/`:

```
analysis/
├── TrackRenderer.tsx          # Dynamic dispatcher: given track + data → renders correct template
├── predictive/
│   ├── PredictiveTemplate.tsx  # Layout for predictive track results
│   ├── ForecastPanel.tsx       # Time-series + confidence bands
│   ├── DriverWaterfall.tsx     # Decomposition waterfall
│   ├── CohortHeatmap.tsx       # Retention heatmap + LTV
│   ├── AnomalyTimeline.tsx     # Annotated anomaly strip
│   └── SegmentForecasts.tsx    # Small multiples by segment
├── automation/
│   ├── AutomationTemplate.tsx
│   ├── BottleneckSankey.tsx
│   ├── OpportunityMatrix.tsx   # Impact vs effort scatter
│   ├── ROIBubbles.tsx
│   ├── StrategicPriorities.tsx
│   ├── SOPPanel.tsx            # Editable SOP draft
│   └── CapacityForecast.tsx
├── optimization/               # Kartavya builds these
│   └── (Kartavya's domain)
├── supply_chain/               # Kartavya builds these
│   └── (Kartavya's domain)
└── shared/
    ├── ExecutiveSummarySection.tsx
    ├── KPIRow.tsx
    ├── RecommendationsPanel.tsx
    ├── ConfidencePanel.tsx
    └── ExportButton.tsx
```

`**TrackRenderer.tsx**` is the key integration point — Kartavya imports this component into `AnalysisDetailPage.tsx`. It receives the `track` string and the `visualization_plan` + `agent_results` from the API, then renders the correct track template.

### 2.4 Knowledge Graph Viewer

Build in `apps/web/src/components/knowledge-graph/KnowledgeGraphViewer.tsx`:

- Renders the nodes/edges from `knowledge_graph_builder` agent output
- Interactive: click a node to see its context and insights in a side panel
- Color-coded by cluster
- Zoom/pan support
- Edge labels show relationship type and strength
- Integrated into all track templates as an optional expandable section

---

## Phase 3: Predictive Deep Analysis Track — Visual Integration

Wire the following visualizations into `PredictiveTemplate.tsx`, consuming data from the agent outputs:

### 3.1 Time-Series Forecast with Confidence Bands

- Source: `trend_forecasting` agent → `forecasts[]` array
- Component: `TimeSeriesChart` with `showConfidenceBands=true`
- Shows historical data (solid line) + predicted (dashed) + upper/lower confidence (shaded area)
- Each forecast metric gets its own chart panel

### 3.2 Driver Decomposition Waterfall

- Source: `trend_forecasting` agent → `drivers[]` array
- Component: `WaterfallChart`
- Shows which factors contribute to forecast changes (positive/negative impacts)
- Sorted by absolute impact

### 3.3 Cohort Retention Heatmap + LTV Trend

- Source: `insight_generation` agent → insights with `chart_type: "heatmap"`
- Component: `HeatmapChart` (cohorts on Y, time periods on X, retention % as color)
- Secondary: `TimeSeriesChart` for projected LTV over time

### 3.4 Anomaly Timeline with Root-Cause Annotations

- Source: `trend_forecasting` agent → `anomalies[]` array
- Component: Custom timeline strip with markers + tooltips showing root cause
- Clickable markers expand to show agent-generated root-cause analysis

### 3.5 KPI Radar — Current vs Predicted Quarter

- Source: `insight_generation` agent → KPI data points
- Component: `RadarChart` with current (solid) and predicted (dashed) overlays
- Minimum 5 dimensions (revenue, cost, margin, growth rate, customer satisfaction)

### 3.6 Segment-Level Forecast Small Multiples

- Source: `trend_forecasting` agent → forecasts broken by segment (region/product/channel)
- Component: Grid of small `TimeSeriesChart` instances
- Each shows one segment's forecast with its own confidence band

### 3.7 Future Enhancement (NOT in MVP): Scenario Simulator Sliders

- Interactive sliders to adjust parameters (price, demand, churn) with instant re-forecast
- Mark as "Coming Soon" placeholder in the UI

---

## Phase 4: Automation Strategy Track — Visual Integration

Wire the following into `AutomationTemplate.tsx`:

### 4.1 Process Bottleneck Sankey

- Source: `automation_strategy` agent → `bottlenecks[]` + process flow data
- Component: `SankeyDiagram`
- Shows time/cost leakage at each stage of business processes
- Color intensity reflects severity

### 4.2 Automation Opportunity Matrix

- Source: `automation_strategy` agent → `processes[]` with `impact_score` and `implementation_effort`
- Component: `BubbleChart` (X=effort, Y=impact, size=ROI)
- Quadrant lines at effort=0.5 and impact=0.5 divide into Quick Wins / Strategic / Long-term / Low Priority

### 4.3 Task-Level ROI Bubble Chart

- Source: `automation_strategy` agent → `processes[]` with ROI details
- Component: `BubbleChart` (X=hours_saved, Y=error_reduction, size=payback_period)
- Tooltips show full process details

### 4.4 Strategic Priority Board

- Source: `automation_strategy` agent → processes filtered by `priority: "strategic"`
- Component: Custom card layout showing strategic automation opportunities
- Each card: process name, current state, proposed automation, expected savings, timeline

### 4.5 Agent-Generated SOP Panel

- Source: `automation_strategy` agent → `sop_draft` with steps
- Component: `SOPPanel` — editable checklist of automation implementation steps
- Exportable as part of PDF report

### 4.6 Capacity Release Forecast

- Source: `automation_strategy` agent → capacity projections
- Component: `BarChart` showing FTE equivalent saved month-over-month for 6 months
- Overlay with `trend_forecasting` data showing predicted cost impact (reusable cross-track component)

### 4.7 Predictive Overlay (Cross-Track Reuse)

- Reuse `TimeSeriesChart` from predictive track to show "if automation is implemented, here's how predictions change"
- Source: Combined data from `automation_strategy` + `trend_forecasting` agents

---

## Phase 5: Synthetic Data — Predictive + Automation Tracks

Generate and save data files under `Miscellaneous/data/sources/E2E_Analytics_Co/`:

### 5.1 Predictive Track Data (`predictive/`)

Create at least **4 files** with rich, realistic data:

1. `**sales_revenue_24months.csv`\*\* — Monthly revenue, units sold, customer count, avg order value by region (US East, US West, EU) for Jan 2024–Dec 2025. Include seasonal dips (Aug, Dec holiday spike), one anomaly month (supply disruption Aug 2024).
2. `**customer_churn_analysis.xlsx**` — Sheet 1: Customer cohort data (signup month, last activity, lifetime value, segment). Sheet 2: Monthly churn rates by segment. Sheet 3: Retention rates by cohort quarter. ~500 customer records.
3. `**quarterly_kpi_report.pdf**` — Narrative PDF with KPIs: revenue growth, customer acquisition cost, NPS score, employee productivity index, gross margin. Include tables and written analysis for 8 quarters.
4. `**market_trends_2024_2025.json**` — Industry benchmark data, competitor pricing trends, market size estimates, growth projections. Structured JSON with quarterly data points.

### 5.2 Automation Track Data (`automation/`)

Create at least **4 files**:

1. `**workflow_process_logs.csv`\*\* — 2000+ rows of task completion events: task_type, department, start_time, end_time, assigned_to, status, error_count, manual_steps, automatable_flag. Cover invoice processing, report generation, data entry, customer onboarding, inventory updates.
2. `**department_efficiency_metrics.xlsx**` — Sheet 1: Department-level KPIs (processing time, error rate, throughput, cost per task). Sheet 2: Employee time allocation (manual vs automated vs meetings). Sheet 3: System integration status (what tools each department uses).
3. `**process_documentation.pdf**` — Current SOPs for 5 key processes with step-by-step descriptions, time estimates, pain points noted by staff.
4. `**system_audit_results.json**` — Integration audit: which systems are connected, data flow gaps, manual handoff points, API availability, automation readiness scores per process.

### 5.3 Data Quality Requirements

- All data must tell a coherent story about E2E_Analytics_Co
- Include realistic imperfections: some missing values (~2%), a few outliers, slight inconsistencies between sources (that conflict_detection should catch)
- Date ranges should overlap across files for cross-referencing
- Include enough variety that each agent has meaningful work to do
- Data should support generating at least 3 charts and 4 recommendations per track

---

## Phase 6: Testing — Predictive + Automation Tracks

### 6.1 Test Protocol

Follow `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md` strictly. For each track:

1. **Login** as `demo@revuc.com` on the demo account
2. **Upload** the corresponding synthetic data files for that track
3. **Select the track** (via onboarding path or track selector)
4. **Start analysis** and monitor in real-time
5. **Verify**:

- Only relevant agents run (not all 21)
- Only matching file processors run (Excel file → only excel_processor)
- Agent outputs are structured JSON with chart-ready data
- Analysis completes within 5-7 minute budget
- Confidence scores are above 0.6
- At least 3 KPI cards can be rendered
- At least 2-3 charts can be rendered
- At least 3-4 recommendations are generated
- Knowledge graph has meaningful nodes/edges

### 6.2 Predictive Track Test Campaign

Campaign slug: `playbook-runs/predictive-track-e2e-validation/`

**Acceptance criteria:**

- Time-series forecast chart renders with confidence bands
- Driver decomposition waterfall shows meaningful factors
- KPI radar shows current vs predicted
- Segment forecasts show at least 2 segments
- Anomaly timeline flags the Aug 2024 disruption
- Executive summary references specific data points from charts

### 6.3 Automation Track Test Campaign

Campaign slug: `playbook-runs/automation-track-e2e-validation/`

**Acceptance criteria:**

- Bottleneck Sankey renders with correct flow data
- Opportunity matrix plots processes correctly
- ROI bubble chart shows meaningful distribution
- SOP panel has editable steps
- Capacity forecast shows 6-month projection
- Cross-track predictive overlay renders

### 6.4 Test Evidence

Save all evidence under `Miscellaneous/tests/playbook-runs/<slug>/`:

- `report.md` — campaign report with 3+ batches
- Agent output JSON snapshots
- Screenshots of rendered charts
- Confidence score summaries

---

## Phase 7: Export to PDF

### 7.1 Backend — PDF Generation Service

Create `apps/api/src/services/export_pdf.py`:

- Accept a `run_id` and generate a PDF report from the analysis results
- Use a Python PDF library (e.g., `reportlab` or `weasyprint`)
- Include:
  - Company header + analysis metadata
  - Executive summary section
  - All KPI cards as a grid
  - All generated charts (render Plotly charts server-side as static images or use chart data to draw in PDF)
  - Recommendations table
  - Knowledge graph as a static image
  - Confidence breakdown
  - Appendix: agent activity log

### 7.2 Backend — Export API Route

Add to `apps/api/src/api/v1/routes/exports.py` (NEW):

- `GET /api/v1/runs/{slug}/export/pdf` — Returns PDF file download
- Requires authentication; must be same-company user

### 7.3 Frontend — Export Button

Build `apps/web/src/components/analysis/shared/ExportButton.tsx`:

- Button in the analysis detail page header
- Triggers download of the PDF
- Loading state while PDF generates

---

## Phase 8: Presentation — Tech Stack & Architecture Section

### 8.1 HTML Presentation File

Create `Miscellaneous/presentation/datalyze_demo.html` (or contribute to a shared presentation file if Kartavya creates the shell first).

**Your sections:**

- **Tech Stack Deep Dive:**
  - Frontend: React + Vite + TypeScript + Plotly + D3 + Knowledge Graph Lib
  - Backend: FastAPI + CrewAI + SQLAlchemy + PostgreSQL + pgvector
  - AI: Ollama (local LLMs) + Featherless (cloud LLMs) + Gemini (classification) + ElevenLabs (narration)
  - 21 specialized AI agents with structured JSON contracts
- **Architecture Diagram:**
  - User → Upload → Classifier → Orchestrator → Smart Agent Selection → Agents → Aggregation → Visualization
  - Show the DAG-based execution with stage gates
- **Agent Specialization:**
  - How each agent has a unique role, strict JSON schema, and confidence scoring
  - How the normalizer bridges agent output to orchestrator contracts
- **Live Demo Walkthrough:**
  - Step-by-step screenshots/recordings of:
    1. Login as demo user
    2. Upload E2E Analytics data
    3. Select analysis track
    4. Watch agents work in real-time
    5. See charts and insights render
    6. Export PDF report
    7. View knowledge graph

### 8.2 Coordination with Kartavya

Kartavya builds the business strategy and demo flow sections. Coordinate so the HTML file has a consistent design. Suggested structure:

1. Cover slide (shared)
2. Business strategy + social impact (Kartavya)
3. Tech stack + architecture (Shivam)
4. Live demo (shared)
5. Future roadmap (shared)
6. Q&A (shared)

---

## Future Enhancements (NOT in Current Sprint — Document Only)

These are explicitly deferred and should be documented in the plan but NOT implemented now:

- **Scenario simulator sliders** (interactive what-if for predictive track)
- **Risk-adjusted automation scorecard** (complex compliance dependencies)
- **Before/after workflow map** (process visualization)
- **Decision memo auto-generation** (business optimization track)
- **Benchmark gauges vs synthetic peer baseline** (unclear scope)
- **Observability dashboard** (latency/error/token metrics per agent) — last priority, future task
- **Full checkpoint-resume execution** (crash recovery mid-pipeline)
- **Shadow evaluation mode** (comparing old vs new outputs)
- **Chat-based Q&A** on analysis results

---

## Execution Order & Priority

| Priority | Phase                         | Est. Effort  | Dependencies             |
| -------- | ----------------------------- | ------------ | ------------------------ |
| **P0**   | Phase 1: Agent Output Quality | 2–3 sessions | None — start immediately |
| **P0**   | Phase 5: Synthetic Data       | 1 session    | Needed for testing       |
| **P1**   | Phase 2: Chart Components     | 2 sessions   | Phase 1 output schemas   |
| **P1**   | Phase 3: Predictive Visuals   | 1 session    | Phase 2 components       |
| **P1**   | Phase 4: Automation Visuals   | 1 session    | Phase 2 components       |
| **P2**   | Phase 6: Testing              | 1–2 sessions | Phases 1-5 complete      |
| **P2**   | Phase 7: Export to PDF        | 1 session    | Phase 2 components       |
| **P3**   | Phase 8: Presentation         | 1 session    | After all testing passes |

**Total estimated sessions:** 10–12 focused work sessions

---

## Version Prompt Tracking

When changing agent prompts, log changes in `Miscellaneous/tests/agent_prompt_versions.jsonl`:

```json
{
  "timestamp": "2026-03-29T...",
  "agent_id": "trend_forecasting",
  "change": "Added chart-ready JSON schema",
  "version": 2
}
```

This enables comparing run-to-run quality improvements.

---

## Playbook Additions

Add the following to `Miscellaneous/Datalyze_Analysis_Testing_Playbook.md`:

- Section 6.1.2: E2E_Analytics_Co synthetic data location → `Miscellaneous/data/sources/E2E_Analytics_Co/`
- Section 6.1.3: Demo account credentials for testing → `demo@revuc.com` / `admin@123`
- Section 16: Agent prompt version tracking → `Miscellaneous/tests/agent_prompt_versions.jsonl`

---

_End of Shivam Kharangate's Final Sprint Plan_
