-- Uploads, company scrape toggle, pipeline run placeholders (idempotent)

ALTER TABLE companies ADD COLUMN IF NOT EXISTS public_scrape_enabled BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS uploaded_files (
    id                   SERIAL PRIMARY KEY,
    company_id           INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id              INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename    VARCHAR(500) NOT NULL,
    stored_filename      VARCHAR(500) NOT NULL,
    storage_relative_path TEXT        NOT NULL,
    visibility           VARCHAR(20)  NOT NULL DEFAULT 'private',
    byte_size            BIGINT       NOT NULL DEFAULT 0,
    content_type         VARCHAR(200),
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_company ON uploaded_files(company_id);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id           SERIAL PRIMARY KEY,
    slug         VARCHAR(96)  NOT NULL UNIQUE,
    company_id   INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id      INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       VARCHAR(40)  NOT NULL DEFAULT 'pending',
    started_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ended_at     TIMESTAMPTZ,
    summary      TEXT,
    pipeline_log JSONB        NOT NULL DEFAULT '[]'::jsonb,
    agent_activity JSONB     NOT NULL DEFAULT '[]'::jsonb,
    source_file_ids INTEGER[] NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_company ON pipeline_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs(started_at DESC);
