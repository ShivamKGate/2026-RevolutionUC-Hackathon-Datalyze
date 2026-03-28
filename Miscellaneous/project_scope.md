# Project Scope — Datalyze

## Overview

Datalyze is a local-first, multi-agent business intelligence system designed for hackathon delivery under strict time, hardware, and cost constraints. The platform ingests mixed-format company data, optionally augments it with targeted public data, and produces explainable insights, forecasting outputs, strategic recommendations, and exportable executive artifacts.

Primary goal: transform raw, siloed documents and datasets into actionable business decisions through orchestrated AI agents.  
Operating model: two-terminal local runtime (`npm run dev` + `ollama serve`), with optional external API calls for specific high-value tasks (Gemini classifier/vision and ElevenLabs narration).

## Team & Contribution Model

- Team size: 2 (`Kartavya Singh`, `Shivam Kharangate`)
- Delivery model: equal contribution across frontend, backend/data, and AI/agent systems
- Working principle: avoid siloing; both members touch each major subsystem
- Implementation discipline:
  - Pair on architecture-critical changes (orchestrator, schema, streaming)
  - Split independent features in parallel (dashboard components, processor adapters)
  - Rotate ownership to keep domain overlap and resilience

## Hardware Specifications & Constraints

- Machine A: Intel i9-12900K, 64GB DDR5 RAM, 16GB VRAM GPU
- Machine B: Ryzen 7 7700X, 32GB DDR5 RAM, RTX 4070 (12GB VRAM)
- Constraint: heavy inference profile must fit on 12GB VRAM system
- Resulting model policy:
  - Heavy model: <12GB VRAM target (reasoning and synthesis tasks)
  - Light model: low-latency sub-agent execution

## Architecture Overview (with text diagram of the full system)

```text
[Next.js Frontend]
  | Onboarding, Uploads, Dashboard, Chat, Exports, Live Feed
  v
[Next.js API Routes (TypeScript)]
  | session control, upload orchestration, SSE, export endpoints
  |---------------> [Python Agent Service (FastAPI/Flask)]
                    | LangChain workflows + agent execution bus
                    v
                [Orchestrator Agent (Heavy Ollama)]
                    | dispatch/sequence/retry/fallback
                    +-> [Gemini Classifier Agent]
                    +-> [File/Format Processor Agents]
                    +-> [Cleaning + Metadata Agents]
                    +-> [Aggregator + Analysis Agents]
                    +-> [Summary/Narration Agents]
                    v
                [PostgreSQL + pgvector]
                    | runs, files, chunks, insights, graph, logs, exports
                    v
                [SSE Stream + Dashboard Views]
```

Data path summary:

1. Onboarding defines context and desired track.
2. Gemini classifies and configures active pipeline profile.
3. Ingestion routes files by type and extraction strategy.
4. Data is cleaned, categorized, aggregated, and analyzed.
5. Results stream to frontend in real time via SSE.
6. User explores outputs, asks follow-up questions, and exports report assets.

## Tech Stack (exhaustive, with version notes and rationale for each choice)

- `Next.js` (App Router) — fullstack web app framework; fast route-level development
- `TypeScript` — strong contracts across frontend/API boundaries
- `Tailwind CSS` — rapid, consistent design system implementation
- `D3.js` — graph visualizations (knowledge graph + orchestration graph)
- `Chart.js` — straightforward KPI charts
- `Plotly.js` — richer analytical plotting where needed
- `shadcn/ui` and/or `Radix UI` — accessible component primitives
- `Python` — agent orchestration, data processing flexibility
- `FastAPI` or `Flask` — lightweight service for agent runtime
- `PostgreSQL` — primary relational and operational store
- `pgvector` — semantic retrieval over processed chunks/metadata
- `Ollama` — local model serving
- Heavy local models: `deepseek-r1:14b` or `qwen2.5:14b`
- Light local models: `llama3.2:3b` or `phi3:mini`
- `LangChain` — agent/tool orchestration scaffolding
- `Google Gemini API` — track classifier + vision/OCR and chart extraction fallback
- `ElevenLabs API` — executive-summary narration audio
- `Firecrawl` or custom (`Playwright` + `BeautifulSoup`) — public data scraping
- `Git` + `GitHub` — version control and delivery
- `Cursor` + `Claude` — accelerated implementation workflow
- OS targets: `Windows` + `Linux`
- GPU runtime support: `NVIDIA CUDA`

Versioning note: use latest stable versions at implementation time unless hackathon environment constraints force pinning.

## Agent Specifications

### 1) Orchestrator Agent

- **Model Used:** Heavy Ollama model
- **Input:** Run context, onboarding config, agent statuses, failure telemetry
- **Output:** Ordered execution plan, next-agent dispatches, retries/fallback decisions
- **Responsibilities:** Global coordination, dependency enforcement, loop-back behavior, strategic recommendation orchestration
- **Dependencies:** Receives from all agents; all core agents depend on it
- **Implementation notes:** Stateful run controller; enforce max-retry and timeout windows
- **Priority:** Core

### 2) Pipeline Classifier Agent

- **Model Used:** Gemini API
- **Input:** Onboarding responses, company context, user-selected goals
- **Output:** Active track config + priority map + scraper targeting strategy
- **Responsibilities:** Choose one of four tracks; configure emphasis profile; vision support for PDFs/images
- **Dependencies:** Upstream of all downstream branches
- **Implementation notes:** Deterministic JSON schema output; fallback to local rules if unavailable
- **Priority:** Core

### 3) Public Data Scraper Agent

- **Model Used:** Light model + Firecrawl/Playwright stack
- **Input:** Track profile, company context, admin play/pause state
- **Output:** Scraped artifacts, source metadata, credibility tags
- **Responsibilities:** Gather public evidence aligned to track objective
- **Dependencies:** Triggered by orchestrator after classification
- **Implementation notes:** Single active company session; bounded crawl depth
- **Priority:** Core (for Public Mode)

### 4) File Type Classifier Agent

- **Model Used:** Light model
- **Input:** Uploaded file manifest + mime hints
- **Output:** File type routing map + metadata tags
- **Responsibilities:** Correct processor dispatch
- **Dependencies:** Depends on upload completion; processors depend on this routing
- **Implementation notes:** Include heuristic fallback by extension/mime
- **Priority:** Core

### 5a) PDF Processor Agent

- **Model Used:** Light model + RAG-style extraction
- **Input:** PDF bytes
- **Output:** Chunked text + table/chart extraction references
- **Responsibilities:** Parse PDFs, OCR via Gemini vision when needed
- **Dependencies:** Routed by file classifier; feeds cleaner
- **Implementation notes:** Track page-to-chunk mapping for provenance
- **Priority:** Core

### 5b) CSV Processor Agent

- **Model Used:** Rule-based + light model assist
- **Input:** CSV files
- **Output:** Structured rows, inferred schema, summary stats
- **Responsibilities:** Parse and normalize tabular data
- **Dependencies:** Routed by file classifier
- **Implementation notes:** Detect delimiter/header anomalies
- **Priority:** Core

### 5c) Excel Processor Agent

- **Model Used:** Rule-based + light model assist
- **Input:** XLS/XLSX files
- **Output:** Per-sheet extracted tables + workbook metadata
- **Responsibilities:** Handle multisheet extraction
- **Dependencies:** Routed by file classifier
- **Implementation notes:** Preserve sheet names and ranges
- **Priority:** Core

### 5d) JSON Processor Agent

- **Model Used:** Rule-based + light model assist
- **Input:** JSON documents
- **Output:** Flattened/normalized records + nested relation map
- **Responsibilities:** Extract nested structures to usable form
- **Dependencies:** Routed by file classifier
- **Implementation notes:** Keep parent-child path references
- **Priority:** Core

### 5e) Image/Multimodal Processor Agent

- **Model Used:** Gemini Vision
- **Input:** Images, chart screenshots, whiteboard photos
- **Output:** Extracted text/labels/chart interpretations
- **Responsibilities:** Recover information from non-text uploads
- **Dependencies:** Routed by file classifier
- **Implementation notes:** Confidence threshold + manual review flag
- **Priority:** Core

### 5f) Plain Text Processor Agent

- **Model Used:** Light model
- **Input:** TXT/MD/log-like inputs
- **Output:** Clean chunks with semantic tags
- **Responsibilities:** Direct text extraction
- **Dependencies:** Routed by file classifier
- **Implementation notes:** Language detection optional
- **Priority:** Core

### 6) Data Cleaning Agent

- **Model Used:** Light model
- **Input:** Raw extracted chunks
- **Output:** Normalized chunks, dedup flags, standardized formats
- **Responsibilities:** Data hygiene before aggregation
- **Dependencies:** Receives from all processors; metadata agent depends on it
- **Implementation notes:** Date/number normalization and encoding cleanup
- **Priority:** Core

### 7) Smart Categorizer / Metadata Agent

- **Model Used:** Light model
- **Input:** Cleaned chunks
- **Output:** Domain tags (finance/HR/ops/etc.), content-type tags
- **Responsibilities:** Improve aggregation and retrieval precision
- **Dependencies:** Depends on cleaning; aggregator depends on tags
- **Implementation notes:** Multi-label tagging allowed
- **Priority:** Core

### 8) Aggregator Agent

- **Model Used:** Heavy model
- **Input:** Cleaned + categorized chunks + scraper artifacts
- **Output:** Structured analysis corpus, usefulness scores, storyline hypotheses
- **Responsibilities:** Prioritize evidence and prepare synthesis-ready dataset
- **Dependencies:** Depends on processors/cleaning/metadata; many downstream agents depend on it
- **Implementation notes:** Keep low-value data retained but deprioritized
- **Priority:** Core

### 9) Conflict Detection Agent

- **Model Used:** Light model
- **Input:** Aggregated corpus
- **Output:** Contradiction alerts with supporting references
- **Responsibilities:** Surface inconsistent records/statements
- **Dependencies:** Depends on aggregator; dashboard conflict card depends on outputs
- **Implementation notes:** Confidence + severity levels
- **Priority:** Core

### 10) Knowledge Graph Builder Agent

- **Model Used:** Heavy model
- **Input:** Aggregated corpus and entity map
- **Output:** Nodes/edges for graph tables and UI rendering
- **Responsibilities:** Build entity relationship network
- **Dependencies:** Depends on aggregator; graph UI depends on output
- **Implementation notes:** Typed nodes/edges for rich filtering
- **Priority:** Core

### 11) Trend Forecasting Agent

- **Model Used:** Heavy model
- **Input:** Time-series candidates from aggregated corpus
- **Output:** Forecast values, confidence bands, plotting payloads
- **Responsibilities:** Predict KPI trajectories when enabled
- **Dependencies:** Depends on aggregator; toggled by user
- **Implementation notes:** Strictly optional per run toggle
- **Priority:** Core (toggleable)

### 12) Sentiment Analysis Agent

- **Model Used:** Light model
- **Input:** Feedback/review/social text data
- **Output:** Sentiment labels, trend summaries, chart payloads
- **Responsibilities:** Customer sentiment interpretation
- **Dependencies:** Depends on aggregator
- **Implementation notes:** Track source channel metadata
- **Priority:** Core

### 13) Insight Generation Agent

- **Model Used:** Heavy model
- **Input:** Aggregated evidence + conflict/sentiment/forecast signals
- **Output:** Insight cards with confidence and provenance tags
- **Responsibilities:** Primary business insight synthesis
- **Dependencies:** Depends on most analysis agents
- **Implementation notes:** Must output structured JSON for UI compatibility
- **Priority:** Core

### 14) SWOT Analysis Agent

- **Model Used:** Heavy model
- **Input:** Insight set + aggregated corpus
- **Output:** Structured SWOT quadrants
- **Responsibilities:** Strategic framing
- **Dependencies:** Depends on insights/aggregator
- **Implementation notes:** Ground each quadrant item in cited evidence
- **Priority:** Core

### 15) Executive Summary Agent

- **Model Used:** Heavy model
- **Input:** Finalized insight package + SWOT + risk/conflict highlights
- **Output:** Board-ready concise summary
- **Responsibilities:** Human-readable synthesis for decision-makers
- **Dependencies:** Depends on analysis completion
- **Implementation notes:** Export-safe formatting
- **Priority:** Core

### 16) Automation Strategy Agent

- **Model Used:** Light/Heavy hybrid
- **Input:** Aggregated operations/process evidence
- **Output:** 2–3 step automation prototype suggestions
- **Responsibilities:** Recommend practical automation opportunities
- **Dependencies:** Depends on aggregator and selected track
- **Implementation notes:** Suggestive only; no full auto-implementation
- **Priority:** Core

### 17) Data Provenance Tracker (System Layer)

- **Model Used:** N/A (system service)
- **Input:** All transformations and source references
- **Output:** Source lineage links on every insight/output artifact
- **Responsibilities:** Explainability and auditability
- **Dependencies:** Cross-cutting layer used by all output agents
- **Implementation notes:** Store lineage at chunk + insight levels
- **Priority:** Core

### 18) Natural Language Search Agent

- **Model Used:** Light model + pgvector retrieval
- **Input:** User chat query + embedded corpus
- **Output:** Grounded answer + optional chart spec
- **Responsibilities:** Conversational analytics
- **Dependencies:** Depends on embeddings/index availability
- **Implementation notes:** Retrieval-augmented answer policy with source citations
- **Priority:** Core

### 19) ElevenLabs Narration Agent

- **Model Used:** ElevenLabs API
- **Input:** Executive summary text
- **Output:** MP3 narration asset
- **Responsibilities:** Audio delivery channel
- **Dependencies:** Depends on executive summary
- **Implementation notes:** Store and expose downloadable file URL
- **Priority:** Core (for ElevenLabs prize objective)

### 20) Presage Focus Agent

- **Model Used:** Presage SDK (optional)
- **Input:** Session interaction telemetry
- **Output:** Focus/fatigue hints
- **Responsibilities:** UX enhancement only
- **Dependencies:** None required for core pipeline
- **Implementation notes:** Fully skippable
- **Priority:** Optional/Stretch

### 21) Solana Audit Ledger

- **Model Used:** Solana integration (optional)
- **Input:** Run metadata hash and timestamp records
- **Output:** Immutable audit entries
- **Responsibilities:** Proof-of-processing timeline
- **Dependencies:** None required for core pipeline
- **Implementation notes:** Minimal non-blocking layer
- **Priority:** Optional/Stretch

## Database Schema

Schema target: PostgreSQL with `pgvector` extension enabled.

### `companies`

- `id` UUID PK
- `name` TEXT NOT NULL
- `industry` TEXT
- `context` TEXT
- `mode` TEXT CHECK (`private`,`public`)
- `created_at` TIMESTAMPTZ DEFAULT now()
- `updated_at` TIMESTAMPTZ DEFAULT now()

### `pipeline_runs`

- `id` UUID PK
- `company_id` UUID FK -> companies.id
- `track` TEXT CHECK (`predictive`,`automation`,`optimization`,`supply_chain`)
- `status` TEXT CHECK (`queued`,`running`,`completed`,`failed`,`paused`)
- `forecast_enabled` BOOLEAN DEFAULT false
- `public_scrape_enabled` BOOLEAN DEFAULT false
- `started_at` TIMESTAMPTZ
- `finished_at` TIMESTAMPTZ
- `error_message` TEXT
- `config_json` JSONB

### `uploaded_files`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `company_id` UUID FK -> companies.id
- `original_name` TEXT NOT NULL
- `mime_type` TEXT
- `file_ext` TEXT
- `file_size_bytes` BIGINT
- `storage_path` TEXT
- `sha256` TEXT
- `uploaded_at` TIMESTAMPTZ DEFAULT now()

### `file_metadata`

- `id` UUID PK
- `file_id` UUID FK -> uploaded_files.id
- `detected_type` TEXT
- `domain_tags` TEXT[]
- `content_tags` TEXT[]
- `is_duplicate` BOOLEAN DEFAULT false
- `duplicate_of_file_id` UUID NULL
- `extraction_confidence` NUMERIC(5,2)
- `metadata_json` JSONB
- `created_at` TIMESTAMPTZ DEFAULT now()

### `processed_chunks`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `file_id` UUID FK -> uploaded_files.id
- `chunk_index` INT
- `text_content` TEXT
- `embedding` VECTOR(1536)
- `token_count` INT
- `quality_score` NUMERIC(5,2)
- `created_at` TIMESTAMPTZ DEFAULT now()

### `insights`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `company_id` UUID FK -> companies.id
- `title` TEXT
- `insight_text` TEXT
- `insight_type` TEXT
- `confidence_score` NUMERIC(5,2)
- `provenance_file_ids` UUID[]
- `visualization_type` TEXT
- `visualization_payload` JSONB
- `explanation_text` TEXT
- `created_at` TIMESTAMPTZ DEFAULT now()

### `agents_log`

- `id` BIGSERIAL PK
- `run_id` UUID FK -> pipeline_runs.id
- `timestamp` TIMESTAMPTZ DEFAULT now()
- `agent_name` TEXT
- `action` TEXT
- `detail` TEXT
- `status` TEXT CHECK (`start`,`progress`,`success`,`warning`,`error`)
- `meta_json` JSONB

### `knowledge_graph_nodes`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `node_type` TEXT
- `label` TEXT
- `attributes` JSONB
- `created_at` TIMESTAMPTZ DEFAULT now()

### `knowledge_graph_edges`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `source_node_id` UUID FK -> knowledge_graph_nodes.id
- `target_node_id` UUID FK -> knowledge_graph_nodes.id
- `edge_type` TEXT
- `weight` NUMERIC(8,3)
- `attributes` JSONB
- `created_at` TIMESTAMPTZ DEFAULT now()

### `exports`

- `id` UUID PK
- `run_id` UUID FK -> pipeline_runs.id
- `export_type` TEXT CHECK (`pdf`,`csv`,`audio`,`share_link`)
- `file_path` TEXT
- `public_url` TEXT
- `status` TEXT CHECK (`queued`,`ready`,`failed`)
- `created_at` TIMESTAMPTZ DEFAULT now()

## API Routes

### `POST /api/pipeline/start`

- Input: company context, track, toggles, mode
- Action: create company/run, invoke classifier, enqueue orchestrator
- Output: `{ runId, status }`

### `POST /api/upload`

- Input: multipart files + `runId`
- Action: persist files, checksum, route to file classifier
- Output: uploaded file summary

### `GET /api/pipeline/status/:runId`

- Input: run ID
- Action: return stage + progress metrics
- Output: run status payload

### `GET /api/insights/:companyId`

- Input: company ID
- Action: fetch latest run insights and visual payloads
- Output: insight list + metadata

### `POST /api/chat`

- Input: `{ runId, query, voiceEnabled? }`
- Action: semantic retrieval + response generation
- Output: grounded answer + optional chart config

### `GET /api/export/pdf/:runId`

- Action: generate or fetch PDF report
- Output: downloadable PDF asset

### `GET /api/export/csv/:runId`

- Action: bundle structured exports
- Output: downloadable CSV file

### `POST /api/admin/scraper/play`

- Input: `{ runId }`
- Action: set scraper state to active
- Output: `{ ok: true }`

### `POST /api/admin/scraper/pause`

- Input: `{ runId }`
- Action: set scraper state to paused
- Output: `{ ok: true }`

### `GET /api/knowledge-graph/:runId`

- Action: fetch graph nodes/edges for visualization
- Output: graph payload

### `GET /api/agents/log/:runId` (SSE)

- Action: stream log events in near real time
- Event schema: `{ timestamp, agentName, action, detail, status }`

### `POST /api/narration/generate`

- Input: `{ runId }`
- Action: send executive summary to ElevenLabs
- Output: audio export reference

## Frontend Pages & Components

### Pages

- `/` — landing and mode selection
- `/onboarding` — company context + track and toggle setup
- `/dashboard` — primary analytics interface
- `/admin` — scraper controls + system diagnostics
- `/export` — report and asset management

### Components

- `OnboardingWizard` — guided multi-step setup
- `FileUpload` — bulk upload and file queue
- `PipelineTracker` — stage-level status view
- `AgentLiveFeed` — collapsible SSE log console
- `OrchestrationDiagram` — animated D3 node-edge execution graph
- `InsightCard` — confidence/provenance-enabled insight tiles
- `KnowledgeGraph` — interactive data relationship graph
- `TrendChart` — forecasting output renderer
- `SWOTGrid` — strengths/weaknesses/opportunities/threats panel
- `ExecutiveSummary` — concise narrative output panel
- `DataChat` — NL question/answer interface
- `VoiceToggle` — speech input/output interaction control
- `ExportPanel` — PDF/CSV/share-link actions
- `AudioPlayer` — ElevenLabs narration playback
- `ProgressBar` — run progress indicator
- `InsightVoting` — upvote/downvote feedback capture
- `ConflictWarning` — contradictory-data alert card

## Pipeline Track Configurations

### Predictive / Trend Forecasting

- **Active focus agents:** Classifier, Aggregator, Trend Forecasting, Insight, Summary
- **Prioritized outputs:** KPI projection charts, confidence bands, executive projections
- **Scraper targeting:** benchmark time-series and performance trend references
- **Visualization profile:** line charts, interval bands, trend tables
- **Insight emphasis:** trajectory, risk windows, likely outcomes

### Automation Strategy

- **Active focus agents:** Classifier, Aggregator, Automation Strategy, Insight, Summary
- **Prioritized outputs:** process bottlenecks, automation opportunities, prototype steps
- **Scraper targeting:** automation case studies, tooling patterns, workflow benchmarks
- **Visualization profile:** before/after process flow summaries, impact cards
- **Insight emphasis:** actionable automation roadmaps

### Business Optimization

- **Active focus agents:** Classifier, Aggregator, Conflict Detection, Insight, SWOT
- **Prioritized outputs:** operational inefficiency findings, strategic recommendations
- **Scraper targeting:** optimization practices, comparative operational benchmarks
- **Visualization profile:** KPI cards, heatmaps, category comparisons
- **Insight emphasis:** high-ROI optimization opportunities

### Supply Chain & Operations

- **Active focus agents:** Classifier, Aggregator, Conflict, Trend, Insight
- **Prioritized outputs:** operational stability indicators, delay/cost risk signals
- **Scraper targeting:** logistics trends, supply disruptions, cost indicators
- **Visualization profile:** route/cost trend lines, anomaly and delay summaries
- **Insight emphasis:** resilience and throughput improvements

## File Format Support Matrix

| File Type            | Processor Agent            | Extraction Method                         | Output Format                     |
| -------------------- | -------------------------- | ----------------------------------------- | --------------------------------- |
| PDF                  | PDF Processor              | Text extraction + chunking + OCR fallback | Chunked text + references         |
| CSV                  | CSV Processor              | Structured parser + schema inference      | Normalized table rows             |
| Excel (XLS/XLSX)     | Excel Processor            | Sheet iteration + cell normalization      | Per-sheet normalized tables       |
| JSON                 | JSON Processor             | Recursive parse + flattening              | Structured records + relation map |
| Image (PNG/JPG/WebP) | Image/Multimodal Processor | Gemini vision extraction                  | Text observations + chart labels  |
| TXT/MD/LOG           | Plain Text Processor       | Direct chunking + cleanup                 | Chunked text                      |

## LLM Configuration

### Heavy Model

- Candidates: `deepseek-r1:14b`, `qwen2.5:14b`
- VRAM target: <12GB effective profile
- Use cases: orchestrator decisions, insight synthesis, summary, SWOT, forecasting
- Ollama pull examples:
  - `ollama pull deepseek-r1:14b`
  - `ollama pull qwen2.5:14b`
- Suggested defaults: low-medium temperature for deterministic business reasoning

### Light Model

- Candidates: `llama3.2:3b`, `phi3:mini`
- Use cases: classification assists, cleaning support, metadata tagging, chat response draft
- Ollama pull examples:
  - `ollama pull llama3.2:3b`
  - `ollama pull phi3:mini`

### Model Swapping Logic

- Orchestrator selects model tier by task class:
  - `synthesis/reasoning/strategy` -> heavy
  - `parsing/tagging/routing/repetitive transforms` -> light
- Retry/fallback rule:
  - Light timeout/failure on critical step -> escalate to heavy once
  - Heavy failure -> structured fallback response + mark partial completion

### Ollama Server Setup

- Start command: `ollama serve`
- Default local endpoint: `http://localhost:11434`
- Env vars (example):
  - `OLLAMA_HOST=http://127.0.0.1:11434`
  - `HEAVY_MODEL=deepseek-r1:14b`
  - `LIGHT_MODEL=llama3.2:3b`

## Gemini API Integration

- Role: pipeline track classifier and multimodal/vision fallback
- API usage:
  - Classification endpoint for deterministic JSON track config
  - Vision analysis for chart/image/PDF extraction support
- Prompt template design:
  - Input: company context, user goal, mode toggles
  - Output schema: `{ track, priorityAgents, scrapeTargets, confidence }`
- Fallback strategy:
  - If Gemini unavailable, use local rule-based classifier + cached profile heuristics
- Credit management:
  - Restrict Gemini calls to onboarding classification and select vision tasks only

## ElevenLabs Integration

- Role: convert executive summary into podcast-style narration
- Voice selection: single professional preset for consistency
- Input payload: finalized executive summary text
- Output: MP3 file persisted in export store
- UI surface:
  - Embedded player on dashboard
  - Direct download in export panel

## pgvector Semantic Search

- Enable extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Embedding option: `nomic-embed-text` via Ollama (or compatible local embedding model)
- Flow:
  1. Embed processed chunks at ingestion/analysis boundary
  2. Store vectors in `processed_chunks.embedding`
  3. Query by cosine similarity for chat retrieval
  4. Return top-k evidence with source IDs
  5. Generate grounded answer and optional chart payload

## Agent Activity Live Feed

- Transport: Server-Sent Events from `GET /api/agents/log/:runId`
- Event format:
  - `{ timestamp, agentName, action, detail, status }`
- UI behavior:
  - Collapsible panel
  - Auto-scroll and severity color coding
  - Agent-specific filtering optional
- Performance strategy:
  - Non-blocking publish queue
  - Throttled UI rendering for bursty event windows

## Animated Agent Orchestration Diagram

- Library: D3 force-directed graph
- Nodes: one per agent (21 total; optional agents visually marked)
- Edges: declared dependencies and runtime handoffs
- Real-time animation:
  - Active node glow/pulse
  - Edge pulse on transfer event
- Data source: same SSE stream used by live feed
- Fallback: static dependency graph when streaming unavailable

## Knowledge Graph

- Visualization: D3 force-directed graph
- Node types: company, department, metric, time period, entity, file
- Edge types: `reports-to`, `contains`, `related-to`, `contradicts`
- Interaction:
  - Click node opens contextual side panel with linked insights
- Storage:
  - `knowledge_graph_nodes`
  - `knowledge_graph_edges`
- Builder:
  - Generated by Knowledge Graph Builder Agent after aggregation

## Export System

- PDF export:
  - Generate from dashboard-state HTML with Puppeteer or `pdfkit`
- CSV export:
  - Flatten selected processed chunks + insight summaries
- Shareable link:
  - Base64-encoded run reference for local network sharing
- Audio export:
  - MP3 from ElevenLabs job output and persisted in `exports`

## Security Considerations

- Local-first data policy: company raw data remains local by default
- External API minimization:
  - Gemini receives only minimal required content (prefer summaries)
  - ElevenLabs receives summary text, not full raw dataset
- Admin surface:
  - Password-protected local admin controls
- Upload hardening:
  - MIME validation, file-size caps, extension sanity checks
- Database hardening:
  - Parameterized queries only
- Licensing:
  - Proprietary restrictions on reproduction/redistribution

## Zero-Cost Strategy

- Ollama local inference: free
- PostgreSQL local deployment: free
- Gemini API: hackathon credits
- ElevenLabs: hackathon credits or free tier
- Firecrawl fallback to custom scraper if needed
- Remaining stack: open-source and free tooling

## Development Environment Setup

1. Clone repository
2. Install Node dependencies: `npm install`
3. Install Python dependencies: `pip install -r requirements.txt`
4. Install and start Ollama: `ollama serve`
5. Pull required models (heavy + light + embedding)
6. Install/start PostgreSQL and enable `pgvector`
7. Run DB migrations/seed scripts
8. Configure `.env` with Gemini and ElevenLabs keys
9. Start app: `npm run dev`
10. Open `http://localhost:3000`

## Hackathon Submission Checklist

- [ ] Demo video (<= 3 minutes)
- [ ] Public GitHub repository (during hackathon)
- [ ] Devpost submission complete
- [ ] `plan.md` finalized with build outcomes
- [ ] Prize integration evidence documented
- [ ] Synthetic demo datasets prepared and tested

## Prize Category Requirements

### 1st Place Overall (Primary)

- **What we build:** End-to-end, local-first, working pipeline with clear business value
- **Judging alignment:** Completeness, usability, execution quality, real-world relevance
- **Implementation evidence:** Live onboarding -> processing -> dashboard -> exports demo
- **Priority:** Primary

### Most Technically Impressive (Primary)

- **What we build:** 21-agent orchestration with real-time feed + animated orchestration graph + knowledge graph
- **Judging alignment:** Technical depth, architecture sophistication, integration complexity
- **Implementation evidence:** Live agent stream, dynamic graph, explainability/provenance
- **Priority:** Primary

### Best Business Plan (Primary)

- **What we build:** Clear value proposition, practical enterprise use cases, go-forward roadmap
- **Judging alignment:** Business clarity, monetization potential, market applicability
- **Implementation evidence:** Executive summary outputs, roadmap, positioning narrative
- **Priority:** Primary

### Best Social Impact (Secondary)

- **What we build:** Free local analytics capability accessible to startups/nonprofits
- **Judging alignment:** Practical accessibility and positive operational impact
- **Implementation evidence:** Local no-cost setup and reusable workflows
- **Priority:** Secondary

### Best Use of Gemini API (Secondary)

- **What we build:** Gemini-based pipeline classifier + vision extraction
- **Judging alignment:** Meaningful, non-trivial Gemini integration
- **Implementation evidence:** Track selection and multimodal extraction demos
- **Priority:** Secondary

### Best Use of ElevenLabs (Secondary)

- **What we build:** Podcast-style summary narration
- **Judging alignment:** Clear value-added audio UX integration
- **Implementation evidence:** In-app player + downloadable narration
- **Priority:** Secondary

### Best Use of Solana (Stretch)

- **What we build:** Optional immutable audit trail layer
- **Judging alignment:** On-chain utility without disrupting core delivery
- **Implementation evidence:** Run hash/timestamp write path
- **Priority:** Stretch

### Best Use of Presage (Stretch)

- **What we build:** Optional focus/fatigue advisory layer
- **Judging alignment:** Meaningful adjunct feature for analyst workflow
- **Implementation evidence:** Focus hints independent from core pipeline
- **Priority:** Stretch

### Best Use of .Tech (Stretch)

- **What we build:** Optional demo domain for presentation polish
- **Judging alignment:** Branding and demo readiness
- **Implementation evidence:** Routed demo URL if time permits
- **Priority:** Stretch

## Future Roadmap

- Optional cloud mode parallel to local-first mode
- Industry benchmarking module
- Scheduled incremental ingestion and recurring re-analysis
- Mobile companion app for executives
- CRM/ERP integrations (Salesforce, SAP, others)
- Subscription intelligence report delivery
- Full Solana-based data marketplace extension
- Public API for third-party integrations
