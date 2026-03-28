from fastapi import APIRouter, Request
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from db.session import SessionLocal
from schemas.auth import SetupRequest, UserOut

router = APIRouter()


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
        row = db.execute(
            text("SELECT id, email, name, role, setup_complete, onboarding_path FROM users WHERE id=:uid"),
            {"uid": user_id},
        ).fetchone()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return UserOut(
        id=row.id,
        email=row.email,
        name=row.name,
        role=row.role,
        setup_complete=row.setup_complete,
        onboarding_path=row.onboarding_path,
    )
