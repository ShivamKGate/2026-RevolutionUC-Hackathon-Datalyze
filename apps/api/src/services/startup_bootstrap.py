"""
One-time and idempotent startup seeding: SQL migrations, companies, seven users,
sample uploads, and a completed demo pipeline run for export/UI testing.

Bootstrap version is stored in table `datalyze_bootstrap` (created here if missing).
User/company rows are upserted on every startup so passwords and roles stay aligned.
Heavy file + run clone runs only until seed version bumps.
"""

from __future__ import annotations

import json
import logging
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import bcrypt
from sqlalchemy import text
from sqlalchemy.engine import Engine

from core.config import settings
from db.session import SessionLocal, engine
from services.company_paths import company_data_private_dir, relative_posix_path
from services.run_paths import run_dir_relative

logger = logging.getLogger("startup_bootstrap")

SEED_VERSION = "v4_google_seeded_run"
TEMPLATE_RUN_REL = (
    "data/pipeline_runs/predictive/"
    "google-kartavya_singh-save-20260329_062439-FbGi7T3R9LVlAsJd"
)
SEED_RUN_SLUG = "dJwT53yrxIo7OLdY"

_COMPANY_GOOGLE = "Google"
_COMPANY_E2E = "E2E_Analytics_Co"

_USERS: list[tuple[str, str, str, str, str]] = [
    # name, email, password, role, company_name
    ("Kartavya Singh", "singhk6@mail.uc.edu", "Kart@1710", "admin", _COMPANY_GOOGLE),
    ("Shivam Kharangate", "sinayksp@mail.uc.edu", "Shivam@1802", "admin", _COMPANY_GOOGLE),
    ("Demo User", "demo@revuc.com", "Demo@123", "viewer", _COMPANY_E2E),
    ("Demo Automation", "demo.automation@revuc.com", "Demo@123", "viewer", _COMPANY_E2E),
    ("Demo Optimization", "demo.optimization@revuc.com", "Demo@123", "viewer", _COMPANY_E2E),
    ("Demo Predictive", "demo.predictive@revuc.com", "Demo@123", "viewer", _COMPANY_E2E),
    ("Demo Supply Chain", "demo.supplychain@revuc.com", "Demo@123", "viewer", _COMPANY_E2E),
]

_MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"


def _apply_raw_sql_file(engine_: Engine, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    raw = engine_.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(sql)
        raw.commit()
    finally:
        raw.close()


def apply_sql_migrations() -> None:
    if not _MIGRATIONS_DIR.is_dir():
        return
    for p in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        try:
            _apply_raw_sql_file(engine, p)
            logger.info("Applied migration %s", p.name)
        except Exception:
            logger.exception("Migration failed: %s", p.name)


def _ensure_bootstrap_table(db) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS datalyze_bootstrap (
                id INTEGER PRIMARY KEY,
                seed_version TEXT NOT NULL DEFAULT '',
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ),
    )
    db.commit()


def _current_seed_version(db) -> str:
    row = db.execute(
        text("SELECT seed_version FROM datalyze_bootstrap WHERE id = 1"),
    ).fetchone()
    if not row:
        return ""
    v = getattr(row, "seed_version", None)
    if v is None and row:
        v = row[0]
    return str(v) if v is not None else ""


def _set_seed_version(db, ver: str) -> None:
    db.execute(
        text(
            """
            INSERT INTO datalyze_bootstrap (id, seed_version, applied_at)
            VALUES (1, :v, NOW())
            ON CONFLICT (id) DO UPDATE SET
                seed_version = EXCLUDED.seed_version,
                applied_at = NOW()
            """
        ),
        {"v": ver},
    )
    db.commit()


def _upsert_companies_and_users(db) -> dict[str, int]:
    """Returns map company_name -> company_id and ensures user ids exist."""
    cid: dict[str, int] = {}
    for cname, scrape in ((_COMPANY_GOOGLE, True), (_COMPANY_E2E, True)):
        row = db.execute(
            text("SELECT id FROM companies WHERE name = :n"),
            {"n": cname},
        ).fetchone()
        if row:
            cid[cname] = int(row.id)
        else:
            ins = db.execute(
                text(
                    "INSERT INTO companies (name, public_scrape_enabled) "
                    "VALUES (:n, :ps) RETURNING id"
                ),
                {"n": cname, "ps": scrape},
            ).fetchone()
            cid[cname] = int(ins.id)
    db.commit()

    for name, email, password, role, company_name in _USERS:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        company_id = cid[company_name]
        onboard = (
            "Deep Analysis"
            if email == "singhk6@mail.uc.edu"
            else "DevOps/Automations"
            if email == "sinayksp@mail.uc.edu"
            else "Deep Analysis"
        )
        db.execute(
            text(
                """
                INSERT INTO users (
                    name, email, role, password_hash, company_id,
                    setup_complete, onboarding_path
                )
                VALUES (:name, :email, :role, :pw, :cid, true, :ob)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    password_hash = EXCLUDED.password_hash,
                    company_id = EXCLUDED.company_id,
                    role = EXCLUDED.role,
                    setup_complete = true,
                    onboarding_path = EXCLUDED.onboarding_path
                """
            ),
            {
                "name": name,
                "email": email.lower(),
                "role": role,
                "pw": pw_hash,
                "cid": company_id,
                "ob": onboard,
            },
        )
    db.commit()
    return cid


def _copy_seed_file_to_company(
    db,
    company_id: int,
    user_id: int,
    company_name: str,
    src: Path,
    analysis_track: str | None,
) -> int | None:
    if not src.is_file():
        return None
    dest_dir = company_data_private_dir(company_name)
    safe_base = src.name[:180]
    stored = f"{uuid.uuid4().hex}_{safe_base}"
    dest = dest_dir / stored
    shutil.copy2(src, dest)
    rel = relative_posix_path(dest)
    suffix = src.suffix.lower()
    ct = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if suffix == ".xlsx"
        else "text/csv"
        if suffix == ".csv"
        else "application/json"
        if suffix == ".json"
        else "text/plain"
    )
    row = db.execute(
        text(
            """
            INSERT INTO uploaded_files (
                company_id, user_id, original_filename, stored_filename,
                storage_relative_path, visibility, byte_size, content_type, analysis_track
            )
            VALUES (:cid, :uid, :orig, :stored, :path, 'private', :size, :ct, :at)
            RETURNING id
            """
        ),
        {
            "cid": company_id,
            "uid": user_id,
            "orig": src.name,
            "stored": stored,
            "path": rel,
            "size": dest.stat().st_size,
            "ct": ct,
            "at": analysis_track,
        },
    ).fetchone()
    db.commit()
    return int(row.id) if row else None


def _seed_google_misc_files(db, google_cid: int, uid_google: int) -> list[int]:
    ids: list[int] = []
    root = settings.repo_root / "Miscellaneous" / "data" / "sources" / "Google"
    if not root.is_dir():
        logger.info("Google misc sources dir missing; skip Google file seed")
        return ids
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (
            ".xlsx",
            ".xls",
            ".csv",
            ".json",
            ".pdf",
        ):
            fid = _copy_seed_file_to_company(
                db, google_cid, uid_google, _COMPANY_GOOGLE, p, "predictive"
            )
            if fid is not None:
                ids.append(fid)
    return ids


def _seed_e2e_misc_files(db, e2e_cid: int, uid_demo: int) -> list[int]:
    ids: list[int] = []
    base = settings.repo_root / "Miscellaneous" / "data" / "sources" / _COMPANY_E2E
    if not base.is_dir():
        logger.info("E2E misc sources dir missing; skip E2E file seed")
        return ids
    exts = (
        ".xlsx",
        ".xls",
        ".csv",
        ".json",
        ".pdf",
        ".txt",
        ".md",
    )
    for p in base.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            fid = _copy_seed_file_to_company(
                db, e2e_cid, uid_demo, _COMPANY_E2E, p, "predictive"
            )
            if fid is not None:
                ids.append(fid)
    track_dirs = ["predictive", "automation", "optimization", "supply_chain"]
    for sub in track_dirs:
        d = base / sub
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() not in exts:
                continue
            fid = _copy_seed_file_to_company(
                db, e2e_cid, uid_demo, _COMPANY_E2E, p, sub
            )
            if fid is not None:
                ids.append(fid)
    return ids


def _clone_demo_pipeline_run(
    db,
    company_id: int,
    owner_user_id: int,
    source_file_ids: list[int],
) -> None:
    dst_name = (
        f"{_COMPANY_GOOGLE.lower()}-kartavya_singh-save-"
        f"20260329_seed-{SEED_RUN_SLUG}"
    )
    dst = settings.repo_root / "data" / "pipeline_runs" / "predictive" / dst_name
    src = settings.repo_root / TEMPLATE_RUN_REL

    existing = db.execute(
        text("SELECT id, company_id FROM pipeline_runs WHERE slug = :s"),
        {"s": SEED_RUN_SLUG},
    ).fetchone()
    if existing and int(existing.company_id) != company_id:
        db.execute(
            text(
                "UPDATE pipeline_runs SET company_id=:cid, user_id=:uid "
                "WHERE slug=:s"
            ),
            {
                "cid": company_id,
                "uid": owner_user_id,
                "s": SEED_RUN_SLUG,
            },
        )
        db.commit()
        logger.info(
            "Reassigned seeded run slug=%s to company_id=%s",
            SEED_RUN_SLUG,
            company_id,
        )

    if not dst.is_dir():
        if not src.is_dir():
            logger.warning(
                "Template run dir missing at %s; skip run clone",
                TEMPLATE_RUN_REL,
            )
            return
        shutil.copytree(src, dst)

    fr_path = dst / "final_report.json"
    if fr_path.is_file():
        try:
            fr_patch = json.loads(fr_path.read_text(encoding="utf-8"))
            fr_patch["run_slug"] = SEED_RUN_SLUG
            fr_path.write_text(json.dumps(fr_patch, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass

    rel_run = run_dir_relative(dst)
    fr: dict = {}
    if fr_path.is_file():
        try:
            fr = json.loads(fr_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            fr = {}

    agent_results = fr.get("agent_results") or {}
    viz = fr.get("visualization_plan") or {}
    summaries = fr.get("agent_summaries") or {}
    completed = fr.get("completed_agents") or []

    agent_activity = [
        {
            "agent_id": aid,
            "agent_name": str(aid).replace("_", " ").title(),
            "status": "completed",
            "message": str(summaries.get(aid, ""))[:800],
        }
        for aid in completed
        if isinstance(aid, str)
    ]
    pipeline_log = [
        f"[{SEED_RUN_SLUG}] Seeded completed run — track predictive",
        fr.get("summary", "completed"),
    ]
    replay_payload = {
        "final_report": fr,
        "agent_activity": agent_activity,
        "pipeline_log": pipeline_log,
        "run_dir": rel_run,
        "agent_results": agent_results,
        "visualization_plan": viz,
    }
    summary = str(fr.get("summary") or "Seeded predictive analysis (demo)")
    now = datetime.now(UTC)
    cfg = {
        "track": "predictive",
        "onboarding_path": "Deep Analysis",
        "seeded": True,
    }

    if existing:
        db.execute(
            text(
                """
                UPDATE pipeline_runs SET
                    company_id=:cid,
                    user_id=:uid,
                    status='completed',
                    summary=:summary,
                    pipeline_log=CAST(:plog AS jsonb),
                    agent_activity=CAST(:agents AS jsonb),
                    source_file_ids=:fids,
                    track='predictive',
                    config_json=CAST(:cfg AS jsonb),
                    final_status_class='completed',
                    replay_payload=CAST(:rp AS jsonb),
                    run_dir_path=:rdp,
                    ended_at=COALESCE(ended_at, :en)
                WHERE slug=:slug
                """
            ),
            {
                "slug": SEED_RUN_SLUG,
                "cid": company_id,
                "uid": owner_user_id,
                "summary": summary,
                "plog": json.dumps(pipeline_log),
                "agents": json.dumps(agent_activity),
                "fids": source_file_ids or [],
                "cfg": json.dumps(cfg),
                "rp": json.dumps(replay_payload),
                "rdp": rel_run,
                "en": now,
            },
        )
        db.commit()
        rid = int(existing.id)
        logger.info("Updated seeded pipeline run slug=%s id=%s", SEED_RUN_SLUG, rid)
        return

    row = db.execute(
        text(
            """
            INSERT INTO pipeline_runs (
                slug, company_id, user_id, status, started_at, ended_at,
                summary, pipeline_log, agent_activity, source_file_ids,
                track, config_json, final_status_class,
                replay_payload, run_dir_path
            )
            VALUES (
                :slug, :cid, :uid, 'completed', :st, :en,
                :summary, CAST(:plog AS jsonb), CAST(:agents AS jsonb), :fids,
                'predictive', CAST(:cfg AS jsonb), 'completed',
                CAST(:rp AS jsonb), :rdp
            )
            RETURNING id
            """
        ),
        {
            "slug": SEED_RUN_SLUG,
            "cid": company_id,
            "uid": owner_user_id,
            "st": now,
            "en": now,
            "summary": summary,
            "plog": json.dumps(pipeline_log),
            "agents": json.dumps(agent_activity),
            "fids": source_file_ids or [],
            "cfg": json.dumps(cfg),
            "rp": json.dumps(replay_payload),
            "rdp": rel_run,
        },
    ).fetchone()
    db.commit()
    rid = int(row.id)
    db.execute(
        text(
            """
            INSERT INTO pipeline_run_logs (run_id, stage, agent, action, detail, status)
            VALUES (:rid, 'system', 'bootstrap', 'seeded',
                    'Demo run materialized for UI/export testing', 'success')
            """
        ),
        {"rid": rid},
    )
    db.commit()
    logger.info("Seeded pipeline run slug=%s id=%s", SEED_RUN_SLUG, rid)


def run_startup_bootstrap() -> None:
    if not (settings.database_url or "").strip():
        logger.warning("DATABASE_URL empty; skip startup bootstrap")
        return
    try:
        apply_sql_migrations()
    except Exception:
        logger.exception("SQL migrations aborted")

    db = SessionLocal()
    try:
        _ensure_bootstrap_table(db)
        cids = _upsert_companies_and_users(db)

        uid_google = db.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": "singhk6@mail.uc.edu"},
        ).fetchone()
        uid_demo = db.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": "demo@revuc.com"},
        ).fetchone()
        if not uid_google or not uid_demo:
            logger.error("Bootstrap: missing core users after upsert")
            return

        ver = _current_seed_version(db)
        if ver == SEED_VERSION:
            logger.info("Startup bootstrap: users/companies synced; data seed %s already applied", ver)
            return

        google_fids = _seed_google_misc_files(
            db, cids[_COMPANY_GOOGLE], int(uid_google.id)
        )
        _seed_e2e_misc_files(db, cids[_COMPANY_E2E], int(uid_demo.id))
        # Globally unique slug: attach demo run to Google so both Google admins can export.
        _clone_demo_pipeline_run(
            db, cids[_COMPANY_GOOGLE], int(uid_google.id), google_fids
        )
        _set_seed_version(db, SEED_VERSION)
        logger.info("Startup bootstrap: applied %s", SEED_VERSION)
    except Exception:
        logger.exception("Startup bootstrap failed")
        db.rollback()
    finally:
        db.close()
