from fastapi import FastAPI

from app.config import settings

from .router import auth, chess, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(chess.router, tags=["chess"])
app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
