from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from core.config import settings
from services.agent_registry import boot_registry


app = FastAPI(
    title="Datalyze API",
    version="0.1.0",
    description="Backend API for Datalyze hackathon project.",
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
