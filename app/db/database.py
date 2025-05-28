from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Configuration de l'engine SQLAlchemy
engine = create_engine(
    settings.database_url,
    # Configuration pour PostgreSQL
    pool_pre_ping=True,  # Vérifier la connexion avant usage
    pool_recycle=300,  # Recycler les connexions après 5min
    pool_size=20,  # Nombre de connexions dans le pool
    max_overflow=0,  # Pas de connexions supplémentaires
    echo=settings.debug,  # Log SQL en mode debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Générateur de session de base de données pour FastAPI dependency injection

    Usage:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Créer toutes les tables (utile pour les tests ou premier démarrage)
    En production, utiliser Alembic pour les migrations
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Supprimer toutes les tables (utile pour les tests)
    """
    Base.metadata.drop_all(bind=engine)
