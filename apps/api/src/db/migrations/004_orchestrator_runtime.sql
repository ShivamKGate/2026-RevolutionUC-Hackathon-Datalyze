-- Orchestrator runtime: expand pipeline_runs, add run logs and artifacts (idempotent)

-- Expand pipeline_runs with orchestrator-specific columns
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS track VARCHAR(40);
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS config_json JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS final_status_class VARCHAR(40);
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS replay_payload JSONB;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS run_dir_path TEXT;

-- Pipeline run logs for live feed and replay
CREATE TABLE IF NOT EXISTS pipeline_run_logs (
    id           BIGSERIAL PRIMARY KEY,
    run_id       INTEGER      NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    timestamp    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    stage        VARCHAR(60)  NOT NULL DEFAULT '',
    agent        VARCHAR(120) NOT NULL DEFAULT '',
    action       VARCHAR(120) NOT NULL DEFAULT '',
    detail       TEXT         NOT NULL DEFAULT '',
    status       VARCHAR(40)  NOT NULL DEFAULT 'info',
    meta_json    JSONB        NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_run_logs_run_id ON pipeline_run_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_run_logs_timestamp ON pipeline_run_logs(run_id, timestamp);

-- Lightweight artifact references (optional, for UI queries)
CREATE TABLE IF NOT EXISTS pipeline_run_artifacts (
    id           BIGSERIAL PRIMARY KEY,
    run_id       INTEGER      NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    agent_id     VARCHAR(120) NOT NULL,
    artifact_type VARCHAR(60) NOT NULL DEFAULT 'output',
    artifact_path TEXT,
    meta_json    JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_run_id ON pipeline_run_artifacts(run_id);
