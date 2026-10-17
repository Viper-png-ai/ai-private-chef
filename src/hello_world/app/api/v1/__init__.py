from fastapi import APIRouter

from hello_world.app.api.v1.chat import router as chat_router
from hello_world.app.api.v1.oss import router as oss_router
from hello_world.app.api.v1.auth import router as auth_router
from hello_world.app.api.v1.pantry import router as pantry_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat_router)
api_router.include_router(oss_router)
api_router.include_router(auth_router)
api_router.include_router(pantry_router)