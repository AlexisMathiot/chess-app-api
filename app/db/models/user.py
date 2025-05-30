from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .chess import ChessGame

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Informations utilisateur
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Informations échecs
    elo_rating = Column(Integer, default=1200)
    chess_com_username = Column(String(100), nullable=True)
    lichess_username = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations - Parties jouées avec les pièces blanches
    games_as_white = relationship(
        "ChessGame",
        back_populates="white_player",
        foreign_keys="ChessGame.white_player_id",
    )

    # Relations - Parties jouées avec les pièces noires
    games_as_black = relationship(
        "ChessGame",
        back_populates="black_player",
        foreign_keys="ChessGame.black_player_id",
    )

    @property
    def all_games(self):
        """Retourne toutes les parties jouées par cet utilisateur"""
        return self.games_as_white + self.games_as_black

    @property
    def total_games(self):
        """Nombre total de parties jouées"""
        return len(self.games_as_white) + len(self.games_as_black)

    @property
    def wins(self):
        """Nombre de victoires"""
        wins_white = sum(1 for game in self.games_as_white if game.winner == "white")
        wins_black = sum(1 for game in self.games_as_black if game.winner == "black")
        return wins_white + wins_black

    @property
    def losses(self):
        """Nombre de défaites"""
        losses_white = sum(1 for game in self.games_as_white if game.winner == "black")
        losses_black = sum(1 for game in self.games_as_black if game.winner == "white")
        return losses_white + losses_black

    @property
    def draws(self):
        """Nombre de nulles"""
        draws_white = sum(1 for game in self.games_as_white if game.winner is None)
        draws_black = sum(1 for game in self.games_as_black if game.winner is None)
        return draws_white + draws_black

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
