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

## 2026-10-12

- **Auto-inscription limitée** à `etudiant`, `personnel`, `visiteur` : un administrateur est créé par le seed ou par un autre administrateur.
- **Règle d'accès = restriction** : si une zone a des règles actives à la date du créneau, seuls les rôles ciblés (`cible_role`) peuvent y réserver ; sans règle, la zone est ouverte à tous. L'administrateur n'est pas concerné. La notion de priorité (`niveau_priorite`) sera exploitée avec la liste d'attente.
- **Places PMR** réservables uniquement par un utilisateur avec `besoin_pmr`.
- **Créneau valide** : dans le futur, sur une seule journée, dans les horaires de la zone (exprimés en heure de Paris, `CAMPUS_TIMEZONE`). Un utilisateur ne peut pas tenir deux réservations confirmées qui se chevauchent.
- **Contrainte d'exclusion PostgreSQL** (`btree_gist`) sur `reservation` : empêche deux réservations confirmées qui se chevauchent sur une même place, même en cas de requêtes simultanées.
- **Couche `app/services/`** : la logique métier sort des routes ; les erreurs métier (`ServiceError`) sont converties en réponses HTTP par un gestionnaire global.
- **Jeu de données basé sur les parkings réels** de la Cité Descartes (source : page « Accès aux bâtiments » de univ-gustave-eiffel.fr) : Copernic, Lavoisier, Clément Ader, Bibliothèque François Rabelais, IUT de Champs-sur-Marne, Alexandra David-Néel, avec leurs capacités et publics (ouvert à tous / réservé aux personnels). Hypothèses faute de données publiques : horaires 7h-20h, 2 % de places PMR, 20 places visiteurs prises sur l'aérien Copernic, zone IUT à accès contrôlé bloquée pour la démo. Le parking personnel du Bois de l'Étang n'est pas inclus (capacité inconnue). Les comptes utilisateurs restent fictifs.
- **Disponibilités par créneau** : `GET /zones` et `GET /places` acceptent `debut`/`fin` (ISO 8601). Une place est disponible si elle n'est pas hors service, si sa zone n'est ni désactivée ni couverte par un `blocage` sur le créneau, et si aucune réservation confirmée ne la chevauche. Sans créneau, le calcul porte sur l'instant présent et l'état `occupee` (simulé) est aussi pris en compte. Les zones exposent `roles_autorises` pour que le front ne propose que les places réservables par l'utilisateur.
- **Catalogue** : l'utilisateur choisit d'abord un jour et une plage horaire, puis réserve en un clic sur ce créneau.
