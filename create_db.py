#!/usr/bin/env python3
"""
Script pour créer toutes les tables de la base de données
Usage: python create_db.py
"""

from app.db.database import Base, engine, create_tables, drop_tables
from app.db.models.chess import ChessGame, GamePosition
from app.db.models.user import User  # si vous en avez un
# from app.db.models.chess_game import ChessGame  # Quand tu l'auras


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_tables()

    create_tables()
