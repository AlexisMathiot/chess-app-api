from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.db.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
