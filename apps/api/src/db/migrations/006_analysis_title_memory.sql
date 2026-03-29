-- Per-run display title + full orchestrator memory snapshot (JSON) for future features.
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS analysis_title VARCHAR(500);
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS memory_json JSONB;
