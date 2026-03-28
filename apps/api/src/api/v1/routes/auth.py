from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy import text

from core.config import settings
from db.session import SessionLocal
from schemas.auth import LoginRequest, RegisterRequest, UserOut

router = APIRouter()

_USER_SELECT_BY_ID = """
SELECT u.id, u.email, u.name, u.role, u.setup_complete, u.onboarding_path,
       u.display_name, u.job_title, c.id AS company_id, c.name AS company_name,
       COALESCE(c.public_scrape_enabled, false) AS public_scrape_enabled
FROM users u
LEFT JOIN companies c ON c.id = u.company_id
WHERE u.id = :uid
"""


def _user_out_from_row(row) -> UserOut:
    return UserOut(
        id=row.id,
        email=row.email,
        name=row.name,
        role=row.role,
        setup_complete=row.setup_complete,
        onboarding_path=row.onboarding_path,
        display_name=row.display_name,
        job_title=row.job_title,
        company_id=row.company_id,
        company_name=row.company_name,
        public_scrape_enabled=bool(row.public_scrape_enabled),
    )


def fetch_user_out(db, user_id: int) -> UserOut:
    row = db.execute(text(_USER_SELECT_BY_ID), {"uid": user_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_out_from_row(row)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_hours * 3600,
    )


def get_current_user(request: Request) -> dict:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = SessionLocal()
    try:
        out = fetch_user_out(db, int(user_id))
    finally:
        db.close()
    return out.model_dump()


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, response: Response):
    db = SessionLocal()
    try:
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        company_row = db.execute(
            text("INSERT INTO companies (name) VALUES (:name) RETURNING id"),
            {"name": f"{body.name}'s Company"},
        ).fetchone()
        user_row = db.execute(
            text(
                "INSERT INTO users (name, email, role, password_hash, company_id) "
                "VALUES (:name, :email, 'viewer', :pw_hash, :company_id) "
                "RETURNING id"
            ),
            {
                "name": body.name,
                "email": body.email,
                "pw_hash": _hash_password(body.password),
                "company_id": company_row.id,
            },
        ).fetchone()
        db.commit()
        profile = fetch_user_out(db, user_row.id)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    token = _create_token(profile.id)
    _set_auth_cookie(response, token)
    return profile


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response):
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()
        if row is None or not row.password_hash or not _verify_password(body.password, row.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        profile = fetch_user_out(db, row.id)
    finally:
        db.close()
    token = _create_token(profile.id)
    _set_auth_cookie(response, token)
    return profile


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.cookie_name)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(request: Request):
    return UserOut(**get_current_user(request))
