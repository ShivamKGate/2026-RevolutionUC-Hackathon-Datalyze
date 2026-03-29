from fastapi import APIRouter

from api.v1.routes.admin import router as admin_router
from api.v1.routes.agents import router as agents_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.database import router as database_router
from api.v1.routes.exports import router as exports_router
from api.v1.routes.files import router as files_router
from api.v1.routes.health import router as health_router
from api.v1.routes.runs import router as runs_router
from api.v1.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(agents_router)
api_router.include_router(database_router, prefix="/database", tags=["database"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(runs_router, prefix="/runs", tags=["runs"])
api_router.include_router(exports_router, prefix="/runs", tags=["exports"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
