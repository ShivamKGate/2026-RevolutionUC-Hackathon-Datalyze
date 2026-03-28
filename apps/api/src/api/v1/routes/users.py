from fastapi import APIRouter, Request
from sqlalchemy import text

from api.v1.routes.auth import fetch_user_out, get_current_user
from db.session import SessionLocal
from schemas.auth import CompanyUpdateRequest, ProfileUpdateRequest, SetupRequest, UserOut

router = APIRouter()


def _normalize_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.patch("/me/profile", response_model=UserOut)
def patch_profile(body: ProfileUpdateRequest, request: Request):
    user = get_current_user(request)
    user_id = user["id"]
    job_title = _normalize_optional_str(body.job_title)
    db = SessionLocal()
    try:
        db.execute(
            text(
                "UPDATE users SET name=:name, display_name=:name, job_title=:job_title, "
                "updated_at=NOW() WHERE id=:uid"
            ),
            {"name": body.name.strip(), "job_title": job_title, "uid": user_id},
        )
        db.commit()
        return fetch_user_out(db, user_id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.patch("/me/company", response_model=UserOut)
def patch_company(body: CompanyUpdateRequest, request: Request):
    user = get_current_user(request)
    user_id = user["id"]
    db = SessionLocal()
    try:
        if body.public_scrape_enabled is not None:
            db.execute(
                text(
                    "UPDATE companies SET name=:company_name, public_scrape_enabled=:pse "
                    "WHERE id=(SELECT company_id FROM users WHERE id=:uid)"
                ),
                {
                    "company_name": body.company_name.strip(),
                    "pse": body.public_scrape_enabled,
                    "uid": user_id,
                },
            )
        else:
            db.execute(
                text(
                    "UPDATE companies SET name=:company_name "
                    "WHERE id=(SELECT company_id FROM users WHERE id=:uid)"
                ),
                {"company_name": body.company_name.strip(), "uid": user_id},
            )
        db.commit()
        return fetch_user_out(db, user_id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.patch("/me/setup", response_model=UserOut)
def setup_me(body: SetupRequest, request: Request):
    user = get_current_user(request)
    user_id = user["id"]
    db = SessionLocal()
    try:
        db.execute(
            text(
                "UPDATE users SET display_name=:display_name, job_title=:job_title, "
                "onboarding_path=:onboarding_path, setup_complete=true, updated_at=NOW() WHERE id=:uid"
            ),
            {
                "display_name": body.display_name,
                "job_title": body.job_title,
                "onboarding_path": body.onboarding_path,
                "uid": user_id,
            },
        )
        db.execute(
            text(
                "UPDATE companies SET name=:company_name "
                "WHERE id=(SELECT company_id FROM users WHERE id=:uid)"
            ),
            {"company_name": body.company_name, "uid": user_id},
        )
        db.commit()
        return fetch_user_out(db, user_id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
