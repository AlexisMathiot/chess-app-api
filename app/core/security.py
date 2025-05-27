from passlib.context import CryptContext
from passlib.hash import bcrypt
from typing import Union
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.schemas.auth import TokenData

import jwt
from jwt.exceptions import InvalidTokenError

from app.db.database import get_db
from app.db.models.user import User
from app.config import settings

db_dependency = Annotated[Session, Depends(get_db)]
# Configuration du contexte de hachage
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Niveau de sécurité (plus = plus lent mais plus sûr)
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    """
    Hacher un mot de passe en texte clair

    Args:
        password: Mot de passe en texte clair

    Returns:
        str: Mot de passe haché

    Example:
        hashed = hash_password("monmotdepasse123")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifier qu'un mot de passe correspond au hash stocké en BDD

    Args:
        plain_password: Mot de passe en texte clair (saisi par l'utilisateur)
        hashed_password: Hash stocké en base de données

    Returns:
        bool: True si le mot de passe correspond, False sinon

    Example:
        # Lors de la connexion
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password_saisi, user.hashed_password):
            print("Connexion réussie!")
        else:
            print("Mot de passe incorrect")
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # En cas d'erreur (hash corrompu, etc.), retourner False
        return False


def need_password_rehash(hashed_password: str) -> bool:
    """
    Vérifier si un mot de passe doit être re-haché
    (utile si tu changes la configuration de sécurité)

    Args:
        hashed_password: Hash existant

    Returns:
        bool: True si le hash doit être refait
    """
    return pwd_context.needs_update(hashed_password)


def generate_password_reset_token() -> str:
    """
    Générer un token sécurisé pour la réinitialisation de mot de passe

    Returns:
        str: Token unique et sécurisé
    """
    import secrets

    return secrets.token_urlsafe(32)


def get_user(db: db_dependency, email: str):
    return db.query(User).filter_by(email=email).first()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: db_dependency
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username = payload.get("sub")
        print(username)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
