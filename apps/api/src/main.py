import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.v1.router import api_router
from core.config import settings
from db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Log host:port/db only — never log the password
        db_host = settings.database_url.rsplit("@", 1)[-1]
        logger.info("Database connection: OK  (%s)", db_host)
    except Exception as exc:
        logger.error("Database connection FAILED: %s", exc)
    yield
from services.agent_registry import boot_registry


app = FastAPI(
    title="Datalyze API",
    version="0.1.0",
    description="Backend API for Datalyze hackathon project.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def initialize_agents_on_boot() -> None:
    boot_registry()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Datalyze API is running."}
