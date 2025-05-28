from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import (
    create_access_token,
    verify_password,
)
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependency,
    user_create_request: UserCreate,
):
    user_create_model = User(
        email=user_create_request.email,
        username=user_create_request.username,
        first_name=user_create_request.first_name,
        last_name=user_create_request.last_name,
        hashed_password=bcrypt_context.hash(user_create_request.password),
        is_active=True,
        is_superuser=False,
    )

    db.add(user_create_model)
    db.commit()


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency,
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}
