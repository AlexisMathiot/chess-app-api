from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from typing_extensions import Annotated
from passlib.context import CryptContext
from starlette import status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate
from app.db.models.user import User

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


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
    return user_create_model
