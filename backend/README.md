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

## Jeu de données de démonstration

Réinitialise les données métier et recrée un jeu de données réaliste :
5 comptes fictifs sur les 4 rôles et les parkings réels du campus de
Marne-la-Vallée (6 parkings, 11 zones dont une bloquée, 1 053 places,
d'après la page « Accès aux bâtiments » de l'université), règles
d'accès et réservations confirmées/annulées.

```bash
docker compose exec backend python -m app.seed.seed_data
```

Tous les comptes de démo utilisent le mot de passe `motdepasse123`
(ex. `alice.etudiante@campus.fr`, `admin@campus.fr` — voir la sortie
du script pour la liste complète).

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
├── schemas/          # schémas Pydantic
├── services/         # règles de gestion (réservations, disponibilités, back-office)
├── api/routes/       # routes de l'API (auth, catalogue, réservations, demandes
│                     # visiteurs, incidents, blocages, règles d'accès, admin)
└── seed/             # jeu de données de démonstration
```
