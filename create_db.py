#!/usr/bin/env python3
"""
Script pour créer toutes les tables de la base de données
Usage: python create_db.py
"""

from app.db.database import create_tables, drop_tables

from app.db.models.chess import ChessGame, GamePosition
from app.db.models.player_profil import PlayerProfile
from app.db.models.user import User


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_tables()

    create_tables()
