#!/usr/bin/env python3
"""
Script pour créer toutes les tables de la base de données
Usage: python create_db.py
"""

from app.db.database import Base, engine

# from app.db.models.chess_game import ChessGame  # Quand tu l'auras


def create_all_tables():
    """Créer toutes les tables définies dans les modèles"""
    print("🚀 Création des tables...")

    try:
        # Créer toutes les tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès!")

        # Afficher les tables créées
        print("\n📋 Tables créées:")
        for table_name in Base.metadata.tables:
            print(f"  - {table_name}")

    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")


def drop_all_tables():
    """Supprimer toutes les tables (ATTENTION!)"""
    print("⚠️  Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables supprimées!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_all_tables()

    create_all_tables()
