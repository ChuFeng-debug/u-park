# Backend — API U-Park

API FastAPI + SQLAlchemy + Alembic, connectée à PostgreSQL.

## Démarrage (via Docker Compose, depuis la racine du projet)

```bash
docker compose up -d --build
```

L'API est alors disponible sur http://localhost:8000 (`/health` pour vérifier, `/docs` pour la documentation Swagger).

## Développement local (hors Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# la base doit tourner (docker compose up -d db) ; adapter l'hôte/port
POSTGRES_HOST=localhost POSTGRES_PORT=5433 alembic upgrade head
POSTGRES_HOST=localhost POSTGRES_PORT=5433 uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Structure

```
app/
├── main.py          # point d'entrée FastAPI
├── core/            # configuration (variables d'environnement)
├── db/              # session SQLAlchemy, base déclarative
├── models/          # modèles SQLAlchemy (voir docs/schema.sql)
├── schemas/          # schémas Pydantic (à venir)
└── api/routes/       # routes de l'API (à venir)
```
