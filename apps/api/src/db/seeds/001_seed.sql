-- Demo company + admin demo user (password: admin@123)
-- Apply after migrations (includes 005_demo_replay_admin.sql for users.role).

INSERT INTO companies (name, public_scrape_enabled)
SELECT 'E2E_Analytics_Co', true
WHERE NOT EXISTS (SELECT 1 FROM companies WHERE name = 'E2E_Analytics_Co');

INSERT INTO users (
    email, password_hash, name, display_name, company_id, role, setup_complete, onboarding_path
)
SELECT
    'demo@revuc.com',
    '$2b$12$MYumFBrAAwFsWF6AsM03j.GVifMwRja/zqhexW1ummpEC9v6C9S0u',
    'Demo User',
    'Demo User',
    c.id,
    'admin',
    true,
    'Deep Analysis'
FROM companies c
WHERE c.name = 'E2E_Analytics_Co'
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    company_id = EXCLUDED.company_id,
    role = 'admin',
    setup_complete = true;
