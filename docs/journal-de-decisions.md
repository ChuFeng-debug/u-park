# Journal de décisions — U-Park

## 2026-09-14

- **Stack technique retenue** : React + TypeScript (front), FastAPI + SQLAlchemy + Alembic (API), PostgreSQL (base de données), Docker Compose (conteneurisation).
- **Structure de projet** : monorepo avec `backend/`, `frontend/`, `docs/`.
- **Dépôt Git initialisé**, base PostgreSQL lancée via Docker Compose.

## 2026-09-14 (suite)

- **Schéma relationnel fusionné** (`docs/schema.sql`, `docs/mcd_upark.html`) : combine le MCD initial et une version plus normalisée.
  - `role` + `attribution_role` remplacent le champ `role` libre sur `utilisateur` (multi-rôles possible).
  - `cible_role` (M-N entre `regle_acces` et `role`) remplace le `type_public` en texte libre.
  - Ajout de `blocage` (admin bloque une zone), `demande_visiteur` (workflow de validation visiteur) et `trace` (journalisation RGPD) pour coller aux critères d'acceptation et exigences non fonctionnelles du cahier des charges.
  - `reservation` référence directement `place` (pas `zone`) : plus simple pour calculer le taux d'occupation dans le tableau de bord du MVP.
  - `incident` distingue `id_utilisateur_signalement` et `id_utilisateur_traitant` (repris du MCD initial).
