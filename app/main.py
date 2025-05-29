from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from .router import auth, chess, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # URL de votre app React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chess.router, tags=["chess"])
app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
