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

1. Copier les fichiers d'environnement :
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```
2. Lancer tout le stack :
   ```bash
   docker compose up -d --build
   ```
3. Charger un jeu de données de démonstration :
   ```bash
   docker compose exec backend python -m app.seed.seed_data
   ```

L'application est alors disponible sur http://localhost:5173 (front),
l'API sur http://localhost:8000 (`/docs` pour Swagger). Comptes de
démo : voir la sortie du script de seed (mot de passe commun
`motdepasse123`).

## Parcours de démonstration

| Profil | Compte | Ce qu'il peut faire |
|---|---|---|
| Étudiant | `alice.etudiante@campus.fr` | Choisir un créneau dans le catalogue, réserver, annuler, simuler son passage, signaler un incident |
| Étudiant PMR | `karim.pmr@campus.fr` | Idem, avec accès aux places PMR |
| Personnel | `marc.personnel@campus.fr` | Idem, avec accès aux zones réservées aux personnels |
| Visiteur | `julie.visiteuse@campus.fr` | Demander une place pour un créneau, suivre la réponse |
| Administrateur | `admin@campus.fr` | Tableau de bord, zones et blocages, règles d'accès, demandes visiteurs, incidents, réservations, comptes, journal |

Tous les utilisateurs disposent de « Mon compte » (profil, mot de passe, export et suppression RGPD).

## Documentation

Voir [docs/](docs/) : [cadrage](docs/cadrage.md) (besoin, personas, périmètre, rôles, risques), [backlog](docs/backlog.md), modèle conceptuel de données (`mcd_upark.html`), schéma relationnel (`schema.sql`), données personnelles (`rgpd.md`) et journal de décisions. La documentation de l'API est générée par FastAPI sur http://localhost:8000/docs.
