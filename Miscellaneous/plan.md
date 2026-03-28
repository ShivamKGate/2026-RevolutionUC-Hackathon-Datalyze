# Datalyze

## Tagline

Raw Data ↓, AI-Driven Strategies ↑

## Description

Datalyze is a local-first, multi-agent business intelligence platform for teams that need fast, practical decisions from raw data. Companies can upload internal files or pair them with targeted public data collection, then receive structured insights, forecasts, automation opportunities, and executive-ready outputs. The platform is designed to run at near-zero cost with open tooling, while still delivering enterprise-style analysis through orchestrated AI agents.

## Inspiration

Most companies already have valuable signals hidden in spreadsheets, PDFs, exports, logs, and documents, but those signals stay trapped in disconnected tools and inconsistent formats. Traditional BI platforms are often expensive, rigid, or too technical for lean teams, especially startups and small organizations that still need high-quality strategic direction.

We were inspired by a simple question: what if teams could drop in all their data exactly as-is and still get clear, reliable recommendations without a long setup process? Multi-agent AI made that feel achievable, because specialized agents can each handle one part of the problem (classification, cleaning, synthesis, forecasting, reporting) while an orchestrator keeps the system coherent.

RevolutionUC gave us the forcing function to build this quickly, prove it live, and shape it around real constraints: a two-person team, a compressed build window, local hardware, zero-cost principles, and a product experience that judges can understand immediately.

## What It Does

Datalyze runs in two modes. In Private Mode, a company uploads internal files and all processing stays local. In Public Mode, an admin can optionally run a controlled scraper session to gather credible, relevant public data aligned to the selected business goal.

During onboarding, users choose the problem track they want to optimize: predictive forecasting, automation strategy, business optimization, or supply-chain/operations insights. That choice configures the downstream pipeline so the system prioritizes the most relevant processing logic and evidence types.

A central orchestrator coordinates specialized agents that classify files, parse mixed formats, clean and normalize extracted content, aggregate high-value signals, detect contradictions, generate forecasts, synthesize insights, produce SWOT output, and compile an executive summary. Every major result is tagged with confidence and source provenance so users can see what evidence supports each recommendation.

The dashboard then surfaces insight cards, interactive charts, a knowledge graph, a live agent feed, an orchestration view, and a conversational data interface for natural-language follow-up questions. Teams can export deliverables as PDF and CSV, share a local run link, and generate a podcast-style narration of findings through ElevenLabs.

Everything is built to be local-first, budget-aware, and practical in a hackathon setting: run the app from terminal, run local models with Ollama, use credits only where external APIs are strategically valuable, and keep the system understandable end-to-end.

## How We Built It

### Frontend

We built the UI in Next.js (App Router) with TypeScript and Tailwind CSS to move fast without losing component consistency. Shadcn/ui and Radix UI patterns are used for reusable primitives such as cards, drawers, toggles, dialogs, and status indicators. The frontend is structured around the core user journey: onboarding, pipeline progress, insight review, and export.

### Backend & Data Layer

The web backend uses Next.js API routes (TypeScript) for session control, uploads, status polling, SSE streaming, export triggers, and dashboard queries. A Python service layer (FastAPI or Flask) handles agent-heavy tasks and LLM-facing workflows. PostgreSQL is the primary store for files, chunks, run metadata, insights, logs, and graph entities, while `pgvector` supports semantic retrieval over processed content.

### AI Agent Architecture

The system is designed as a 21-agent architecture with clear separation of concerns. A heavy orchestrator controls execution order, error handling, retries, and branch logic. Lightweight agents handle repetitive format-specific and hygiene operations, while heavy agents handle synthesis-heavy work such as insight generation, forecasting, and strategic summary production. Optional modules (Presage and Solana) remain non-blocking so MVP reliability stays high.

### LLM Infrastructure (Ollama)

We run Ollama locally as the base inference server and split workloads between a heavy reasoning model and a lighter throughput model. Heavy tasks run on models such as `deepseek-r1:14b` or `qwen2.5:14b` constrained to <12GB VRAM compatibility across both machines; lighter tasks run on faster models such as `llama3.2:3b` or `phi3:mini` for lower latency.

### Data Ingestion Pipeline

Ingestion starts with onboarding context, then Gemini classification configures the active track. Uploaded files are typed, routed to specialized processors, normalized, categorized, and scored by usefulness before synthesis. Public scraping can run asynchronously when enabled, with admin play/pause controls and one-company-at-a-time scheduling. Duplicate detection and metadata enrichment reduce wasted compute and improve downstream relevance.

### Visualization Layer

We combine D3.js, Chart.js, and Plotly.js depending on chart type and interactivity needs. D3 powers the knowledge graph and orchestration views; Chart.js and Plotly support KPI trend and comparison visualizations. Insight cards include chart context, confidence values, and source tags for explainability.

### Voice & Audio (ElevenLabs)

Executive summaries are transformed into podcast-style narration through ElevenLabs so teams can consume analysis in audio form during reviews, standups, or async decision cycles. The UI includes playback and download controls for immediate demoability.

### Semantic Search (pgvector)

Processed chunks and metadata are embedded and indexed in PostgreSQL with `pgvector`. The chat interface uses semantic retrieval to answer natural-language questions grounded in current run context and can trigger visualization generation when user prompts request chart outputs.

### External API Integrations (Gemini, ElevenLabs, optional: Solana, Presage)

Gemini is integrated in a high-leverage role as the pipeline classifier and vision fallback for chart/OCR extraction from mixed PDFs/images. ElevenLabs is used for narrated summary output. Solana and Presage are treated as optional stretch integrations that do not impact core pipeline success.

### Development Environment & Tooling

The project is developed in Cursor with Claude assistance, versioned with Git/GitHub, and tested across Windows/Linux environments. The local runtime model is intentionally simple: run `ollama serve` in one terminal and the Next.js app in another.

## Challenges We Ran Into

### Multi-Agent Coordination and Deadlock Avoidance

Keeping many specialized agents productive without circular waits required strict dependency ordering, explicit handoff contracts, and orchestrator guardrails to detect and recover from stalled states.

### VRAM-Aware Model Selection

We needed heavy reasoning quality while honoring the 12GB VRAM floor across both machines. That forced careful model benchmarking, token budgeting, and fallback planning.

### Multi-Format Reliability

The pipeline needed to treat PDFs, CSVs, Excel, JSON, images, and plain text consistently enough for shared downstream logic, which required robust extraction normalization and file-type specific edge-case handling.

### Real-Time Activity Streaming

The live agent feed and orchestration visuals had to feel instantaneous without slowing core processing, so we separated stream updates from heavy compute and tuned event payload granularity.

### Zero-Cost Constraint

Balancing product ambition with strict cost discipline meant prioritizing local inference and open tooling while using external APIs only where they provide outsized strategic value.

### Compressed Timeline

A short delivery window forced ruthless MVP decisions, clear priorities, and parallel task ownership while preserving end-to-end coherence.

### Equal Contribution Across Domains

With two builders and three major domains (frontend, backend, agents), we planned cross-domain pairing and rotation to keep contribution balanced.

[To be filled in as the project progresses]

## Accomplishments That We're Proud Of

### Local-First Multi-Agent Stack Under Hackathon Constraints

We designed a practical, full-pipeline architecture that runs locally with near-zero cost while still delivering credible business outputs.

### Real-Time Agent Orchestration Visualization

The live orchestration diagram turns complex backend behavior into something judges and users can instantly understand.

### Interactive Knowledge Graph

Entity-level drill-down gives users a navigable map of relationships, not just static charts.

### Podcast-Style Insight Narration

Turning summaries into listenable audio improves accessibility and demo impact.

### Broad File-Format Support

Specialized processors let teams work with the data they already have, instead of forcing rigid input templates.

### Reproducible Build Workflow

The architecture and tooling choices keep setup approachable for anyone cloning and running locally.

[To be filled in as the project progresses]

## What We Learned

### Agent Systems Need Strong Contracts

Agent quality is not enough by itself; clearly defined handoffs and state semantics are what keep complex pipelines reliable.

### Constraints Improve Architecture

Hardware and budget limits pushed us toward simpler, more durable design choices that improved practicality.

### Explainability Is a Product Feature

Confidence scoring, provenance tags, and plain-language explanations significantly increase trust in generated recommendations.

### UX Matters as Much as Model Quality

Live feeds, progress tracking, and interactive diagrams make sophisticated systems understandable and usable in real workflows.

### Scope Control Is Strategic

Separating core, optional, and stretch modules preserved momentum and reduced risk under a tight delivery schedule.

## What's Next for Datalyze

- Optional cloud deployment mode alongside local-first runtime.
- Industry benchmarking against publicly available peer/company signals.
- White-label offering for consulting workflows with explicit licensing controls.
- Scheduled incremental ingestion and automated weekly reruns.
- Deeper Solana integration for auditable data/event trails.
- Mobile companion for executive summary viewing and approvals.
- CRM/ERP connectors (Salesforce, SAP, and similar systems).
- Subscription intelligence reports delivered on a recurring cadence.

## Built With

- Next.js
- TypeScript
- Tailwind CSS
- D3.js
- Chart.js
- Plotly.js
- Shadcn/ui
- Radix UI
- Python
- FastAPI
- Flask
- PostgreSQL
- pgvector
- Ollama
- LangChain
- Google Gemini API
- ElevenLabs API
- Firecrawl
- Playwright
- BeautifulSoup
- Git
- GitHub
- Cursor
- Claude
- Windows
- Linux
- NVIDIA CUDA
- deepseek-r1
- qwen2.5
- llama3.2
- phi3

## Links

- GitHub Repository: [INSERT GITHUB LINK]
- Demo Video: [INSERT VIDEO LINK]
- Live Demo (if deployed): [INSERT LINK]
- Devpost: [INSERT DEVPOST LINK]
