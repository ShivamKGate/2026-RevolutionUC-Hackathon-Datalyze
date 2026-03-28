-- =============================================================
-- Datalyze – initial schema
-- Run once against the datalyze database:
--   psql -U postgres -p 5433 -d datalyze -f apps/api/src/db/migrations/001_initial_schema.sql
-- =============================================================

CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    role       VARCHAR(50)  NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS datasets (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    file_type   VARCHAR(20)  NOT NULL,
    row_count   INTEGER      NOT NULL DEFAULT 0,
    created_by  INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id         SERIAL PRIMARY KEY,
    dataset_id INTEGER      REFERENCES datasets(id) ON DELETE CASCADE,
    type       VARCHAR(100) NOT NULL,
    status     VARCHAR(50)  NOT NULL DEFAULT 'pending',
    result     JSONB,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
