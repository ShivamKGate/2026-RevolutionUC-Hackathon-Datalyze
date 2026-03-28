-- =============================================================
-- Datalyze – seed data (temp / demo rows)
-- Run after 001_initial_schema.sql:
--   psql -U postgres -p 5433 -d datalyze -f apps/api/src/db/seeds/001_seed.sql
-- =============================================================

INSERT INTO users (name, email, role) VALUES
    ('Kartavya Singh',    'singhk6@mail.uc.edu',  'admin'),
    ('Shivam Kharangate', 'sinayksp@mail.uc.edu',    'admin'),
    ('Demo Viewer',       'demo@datalyze.dev',       'viewer')
ON CONFLICT (email) DO NOTHING;

INSERT INTO datasets (name, description, file_type, row_count, created_by) VALUES
    ('Sales Q1 2026',     'Quarterly sales data, Jan–Mar 2026',  'csv',   1500, 1),
    ('Customer Survey',   'Post-purchase satisfaction survey',   'xlsx',   320, 2),
    ('Web Analytics Mar', 'March 2026 traffic and conversions',  'json',  8200, 1);

INSERT INTO analyses (dataset_id, type, status, result) VALUES
    (1, 'trend_analysis',     'completed', '{"trend": "upward", "growth_pct": 12.4}'),
    (1, 'anomaly_detection',  'completed', '{"anomalies_found": 3, "severity": "low"}'),
    (2, 'sentiment_analysis', 'pending',   NULL),
    (3, 'traffic_forecast',   'completed', '{"next_month_est": 9100, "confidence": 0.87}');
