# Agent Specialization — Integration Guide

## Architecture Overview

```
services/
├── agents/                          # Per-agent specialization modules (Shivam scope)
│   ├── __init__.py                  # Central module index
│   ├── shared_prompts.py            # Shared prompt guardrails
│   ├── contracts.py                 # Per-agent JSON schemas + strictness profiles
│   ├── normalizer.py                # Output normalization to adapter envelope
│   ├── pipeline_classifier.py       # ... one file per specialized agent
│   ├── public_data_scraper.py
│   ├── file_type_classifier.py
│   ├── pdf_processor.py
│   ├── csv_processor.py
│   ├── excel_processor.py
│   ├── json_processor.py
│   ├── image_multimodal_processor.py
│   ├── plain_text_processor.py
│   ├── data_cleaning.py
│   ├── smart_categorizer_metadata.py
│   ├── aggregator.py
│   ├── conflict_detection.py
│   ├── knowledge_graph_builder.py
│   ├── trend_forecasting.py
│   ├── sentiment_analysis.py
│   ├── insight_generation.py
│   ├── swot_analysis.py
│   ├── executive_summary.py
│   ├── automation_strategy.py
│   ├── natural_language_search.py
│   └── elevenlabs_narration.py
├── agent_registry.py                # Model assignment + dependency graph (shared)
├── crew_specialized.py              # Modular runtime entrypoint (replaces crew_mvp.py)
├── crew_mvp.py                      # Legacy MVP runtime (preserved for transition)
└── external_agent_clients.py        # HTTP clients for Gemini/ElevenLabs
```

## Where to Edit Prompts

Each agent's system prompt lives in its own file at:
`services/agents/<agent_id>.py`

The `SYSTEM_PROMPT` constant is built using `shared_prompts.build_system_prompt()`, which assembles:
1. Role identity and agent_id
2. Core instructions (role-specific, in per-agent file)
3. JSON-only enforcement
4. Deterministic naming enforcement
5. Token budget guidance
6. Scope guard language
7. Strictness mode suffix (strict or guarded)

To modify an agent's behavior, edit the `core_instructions` string in that agent's file.

## How to Add New Agents

1. Create `services/agents/<new_agent_id>.py` following the existing pattern.
2. Add a contract in `services/agents/contracts.py` → `AGENT_CONTRACTS` dict.
3. Register the module in `services/agents/__init__.py` → `AGENT_MODULES` dict.
4. Add the `AgentSpec` in `services/agent_registry.py` → `_agent_specs()`.
5. The registry will auto-discover the module via `get_agent_module()`.

## How Schema Checks Are Enforced

- `contracts.py` defines `AgentContract` per agent with `required_keys` and `optional_keys`.
- `AgentContract.validate_output(output_dict)` checks required key presence.
- The verification endpoint (`/verify/all`) runs behavior prompts, parses JSON, and validates schemas.
- `normalizer.py` maps per-agent output to adapter envelope format.

## How Normalization Bridges to Orchestrator Adapter

The orchestrator adapter expects this envelope:
```json
{
  "status": "ok|warning|error",
  "summary": "string",
  "artifacts": [],
  "next_hints": [],
  "confidence": 0.0,
  "errors": []
}
```

`normalizer.normalize_agent_output(agent_id, raw_output)` handles the conversion:
- Parses raw JSON output from agent
- Extracts summary from relevant fields
- Collects artifacts from array fields
- Computes confidence from agent-provided values
- Validates against agent contract schema
- Returns a valid adapter envelope

The orchestrator runtime should call `normalize_agent_output()` after each agent dispatch.

## Merge Integration Notes for Kartavya

### Files YOU Can Safely Edit (Kartavya Scope)
- `services/orchestrator_runtime/*` — your exclusive domain
- `api/v1/routes/runs.py` — orchestration run endpoints
- DB migrations — additive only
- Frontend analysis pages

### Files We Share (Minimal Conflict Surface)
- `services/agent_registry.py` — Shivam added `get_agent_module()` import; your edits should be additive
- `api/v1/routes/agents.py` — Shivam added specialized endpoint + behavior verification; your changes go in runs routes

### Integration Point
Your `AgentExecutionAdapter` should:
1. Import `from services.agents.normalizer import normalize_agent_output`
2. After calling an agent, pass raw output through `normalize_agent_output(agent_id, raw_text)`
3. The returned dict matches your adapter envelope schema exactly

### Post-Merge Sequence
1. Merge specialization branch first (smaller surface area)
2. Merge orchestrator runtime branch
3. In orchestrator adapter, wire `normalize_agent_output()` calls
4. Run combined verification: `python apps/api/scripts/verify_all_agents.py`

## Strictness Classification

| Mode | Agents | Behavior |
|------|--------|----------|
| **strict** | pipeline_classifier, public_data_scraper, file_type_classifier, all processors, data_cleaning, smart_categorizer_metadata, conflict_detection, sentiment_analysis, natural_language_search | Hard in-scope; rejects off-topic requests |
| **guarded** | aggregator, knowledge_graph_builder, trend_forecasting, insight_generation, swot_analysis, executive_summary, automation_strategy, elevenlabs_narration | Scoped synthesis with drift guardrails |
