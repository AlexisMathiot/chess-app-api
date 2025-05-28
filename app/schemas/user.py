from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Base commune
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


# Pour la création d'utilisateur
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    # confirm_password: str

    # # Validation custom
    # def validate_passwords_match(self):
    #     if self.password != self.confirm_password:
    #         raise ValueError("Les mots de passe ne correspondent pas")


# Pour la mise à jour
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    chess_com_username: Optional[str] = Field(None, max_length=100)
    lichess_username: Optional[str] = Field(None, max_length=100)


# Pour les réponses (sans mot de passe)
class UserResponse(UserBase):
    id: int
    is_active: bool
    elo_rating: int
    chess_com_username: Optional[str]
    lichess_username: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Configuration pour SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# Pour l'authentification
class UserLogin(BaseModel):
    email: EmailStr
    password: str
