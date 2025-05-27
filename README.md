# Chess API 🏆

API FastAPI pour l'analyse de parties d'échecs avec authentification JWT et base de données PostgreSQL.

WORK IN PROGRESS

## 🚀 Fonctionnalités

- **Authentification** : Inscription/connexion avec JWT
- **Gestion utilisateurs** : Profils et données utilisateur
- **Analyse d'échecs** : Analyse de parties et coups
- **Base de données** : PostgreSQL pour la persistance
- **Documentation** : API docs automatique avec Swagger

## 🛠️ Technologies

- **Backend** : FastAPI (Python 3.11+)
- **Base de données** : PostgreSQL 17
- **ORM** : SQLAlchemy 2.0
- **Authentification** : JWT tokens
- **Migrations** : Alembic
- **Conteneurisation** : Docker & Docker Compose

## 📋 Prérequis

- Python 3.11+
- Docker & Docker Compose
- Git

## 🏁 Installation rapide

### 1. Cloner le projet
```bash
git clone https://github.com/AlexisMathiot/chess-app-api.git
cd chess_api
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer les variables d'environnement
nano .env
```

### 5. Lancer la base de données
```bash
docker-compose up -d postgres
```


### 6. Lancer l'API
```bash
uvicorn app.main:app --reload
```

L'API est maintenant accessible sur `http://localhost:8000` 🎉

## 🐳 Docker Compose

### Services disponibles

```bash
# Lancer tous les services
docker-compose up -d

# Lancer seulement PostgreSQL
docker-compose up -d postgres

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down
```

### Services inclus

- **PostgreSQL** : Base de données principale (port 5432)
- **PgAdmin** : Interface d'administration web (port 8080)
- **Redis** : Cache et sessions (port 6379)

## 📚 Utilisation de l'API

### Documentation interactive
- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

## 🏗️ Structure du projet

```
chess_api/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── dependencies.py      # Dépendances communes
│   ├── routers/            # Routes API
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── chess.py
│   ├── core/               # Logique métier
│   │   ├── security.py
│   │   └── chess_engine.py
│   ├── db/                 # Base de données
│   │   ├── database.py
│   │   └── models/
│   └── schemas/            # Modèles Pydantic
├── alembic/                # Migrations
├── tests/                  # Tests
├── docker-compose.yml
├── .env
└── requirements.txt
```

## 🔧 Développement

### Variables d'environnement

```bash
# Base de données
DATABASE_URL=postgresql://chess_user:chess_password@localhost:5432/chess_api
POSTGRES_DB=chess_api
POSTGRES_USER=chess_user
POSTGRES_PASSWORD=chess_password

# JWT
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

### Connexion à PostgreSQL
```bash
# Via Docker
docker-compose exec postgres psql -U chess_user -d chess_api

# Ou depuis l'host
psql -h localhost -U chess_user -d chess_api
```

```bash
# Exemple avec Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Si vous rencontrez des problèmes :

1. Consultez la [documentation](http://localhost:8000/docs)
2. Vérifiez les [issues existantes](../../issues)
3. Créez une nouvelle issue si nécessaire

---

Développé avec ❤️ et FastAPI