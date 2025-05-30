from sqlalchemy import (
    Column,
    Integer,
    String,
    UniqueConstraint
)

from app.db.database import Base

class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    platform = Column(String(20), nullable=False)  # "chess.com" ou "lichess"
    rating = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("username", "platform", name="_username_platform_uc"),
    )

    def __repr__(self):
        return f"<PlayerProfile({self.platform}:{self.username})>"
