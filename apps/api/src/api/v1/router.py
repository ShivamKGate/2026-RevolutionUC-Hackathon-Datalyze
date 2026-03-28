from fastapi import APIRouter

from api.v1.routes.agents import router as agents_router
from api.v1.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(agents_router)
