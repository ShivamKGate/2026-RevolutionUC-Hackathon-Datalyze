-- Phase 1: demo replay, admin role, analysis deduplication, file track association (idempotent)

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
