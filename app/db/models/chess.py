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

from app.db.database import Base


class ChessGame(Base):
    __tablename__ = "chess_games"

    id = Column(Integer, primary_key=True, index=True)

    # Identifiants externes
    chess_com_game_id = Column(String(50), unique=True, index=True, nullable=True)
    lichess_game_id = Column(String(50), unique=True, index=True, nullable=True)
    chess_com_url = Column(Text, nullable=True)
    lichess_url = Column(Text, nullable=True)

    # Relations avec les joueurs
    white_player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    black_player_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relations
    white_player = relationship(
        "User", back_populates="games_as_white", foreign_keys=[white_player_id]
    )
    black_player = relationship(
        "User", back_populates="games_as_black", foreign_keys=[black_player_id]
    )

    # Informations sur la partie
    game_date = Column(DateTime(timezone=True), nullable=False)
    time_control = Column(String(20), nullable=True)  # "600+5", "180+0"
    time_class = Column(String(20), nullable=True)  # "rapid", "blitz", "bullet"
    rules = Column(String(50), default="chess")
    rated = Column(Boolean, default=True)
    tournament_name = Column(String(200), nullable=True)

    # Ratings au moment de la partie
    white_player_rating = Column(Integer, nullable=True)
    black_player_rating = Column(Integer, nullable=True)

    # Résultat
    result = Column(String(10), nullable=False)  # "1-0", "0-1", "1/2-1/2"
    termination = Column(
        String(50), nullable=True
    )  # "checkmated", "resigned", "timeout"
    winner = Column(String(10), nullable=True)  # "white", "black", or NULL for draw

    # Données de la partie
    pgn = Column(Text, nullable=False)
    fen_final = Column(String(100), nullable=True)
    total_moves = Column(Integer, nullable=True)
    game_duration_seconds = Column(Integer, nullable=True)

    # Fichiers PNG
    png_filename = Column(String(255), nullable=True)
    png_file_path = Column(Text, nullable=True)
    png_file_size = Column(Integer, nullable=True)
    png_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Analyse
    analyzed = Column(Boolean, default=False)
    engine_evaluation = Column(JSON, nullable=True)
    blunders_count = Column(Integer, nullable=True)
    accuracy_white = Column(Float, nullable=True)
    accuracy_black = Column(Float, nullable=True)

    # Timestamps
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def white_player_username(self):
        """Username du joueur blanc"""
        return self.white_player.username if self.white_player else None

    @property
    def black_player_username(self):
        """Username du joueur noir"""
        return self.black_player.username if self.black_player else None

    @property
    def is_draw(self):
        """True si la partie est nulle"""
        return self.winner is None

    @property
    def duration_formatted(self):
        """Durée formatée de la partie"""
        if not self.game_duration_seconds:
            return None

        hours = self.game_duration_seconds // 3600
        minutes = (self.game_duration_seconds % 3600) // 60
        seconds = self.game_duration_seconds % 60

        if hours > 0:
            return f"{hours}h{minutes:02d}m{seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        else:
            return f"{seconds}s"

    def get_opponent(self, user_id):
        """Retourne l'adversaire d'un utilisateur donné"""
        if self.white_player_id == user_id:
            return self.black_player
        elif self.black_player_id == user_id:
            return self.white_player
        return None

    def get_user_color(self, user_id):
        """Retourne la couleur jouée par un utilisateur"""
        if self.white_player_id == user_id:
            return "white"
        elif self.black_player_id == user_id:
            return "black"
        return None

    def did_user_win(self, user_id):
        """True si l'utilisateur a gagné cette partie"""
        user_color = self.get_user_color(user_id)
        return self.winner == user_color

    def __repr__(self):
        return f"<ChessGame(id={self.id}, white={self.white_player_username}, black={self.black_player_username}, result='{self.result}')>"


# Table optionnelle pour les positions détaillées
class GamePosition(Base):
    __tablename__ = "game_positions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(
        Integer, ForeignKey("chess_games.id", ondelete="CASCADE"), nullable=False
    )

    # Relations
    game = relationship("ChessGame", backref="positions")

    # Position
    move_number = Column(Integer, nullable=False)
    half_move = Column(Integer, nullable=False)  # Pour distinguer blanc/noir
    fen = Column(String(100), nullable=False)
    move_san = Column(String(20), nullable=True)  # e4, Nf3, O-O
    move_uci = Column(String(10), nullable=True)  # e2e4, g1f3

    # Analyse
    evaluation = Column(Float, nullable=True)  # En centipawns
    is_blunder = Column(Boolean, default=False)
    is_brilliant = Column(Boolean, default=False)
    is_mistake = Column(Boolean, default=False)
    is_inaccuracy = Column(Boolean, default=False)

    # Temps
    time_left_white = Column(Integer, nullable=True)
    time_left_black = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GamePosition(game_id={self.game_id}, move={self.move_number}, san='{self.move_san}')>"
