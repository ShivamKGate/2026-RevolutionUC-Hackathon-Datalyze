from fastapi import APIRouter

from api.v1.routes.agents import router as agents_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.database import router as database_router
from api.v1.routes.health import router as health_router
from api.v1.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(agents_router)
api_router.include_router(database_router, prefix="/database", tags=["database"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
