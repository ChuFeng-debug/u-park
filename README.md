# U-Park

Gestion intelligente des parkings universitaires — SAE BUT3, Université Gustave Eiffel (2026-2027).

Réserver, suivre et piloter les places de stationnement du campus, sans dépendre de capteurs réels pour le POC (données simulées ou administrées manuellement).

## Stack

- **Front-end** : React + TypeScript + Vite
- **API** : FastAPI + SQLAlchemy + Alembic
- **Base de données** : PostgreSQL
- **Conteneurisation** : Docker Compose

## Structure du projet

```
u-park/
├── backend/    # API FastAPI
├── frontend/   # Application React
├── docs/       # Cahier des charges, MCD, journal de décisions
└── docker-compose.yml
```

## Démarrage rapide

1. Copier le fichier d'environnement :
   ```bash
   cp .env.example .env
   ```
2. Lancer la base de données :
   ```bash
   docker compose up -d db
   ```

Le service `backend` (API) et `frontend` seront ajoutés à `docker-compose.yml` au fur et à mesure de leur développement.

## Documentation

Voir [docs/](docs/) pour le cahier des charges, le modèle conceptuel de données et le journal de décisions du projet.
