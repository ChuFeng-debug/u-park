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

## 2026-10-12 (back-office)

- **Blocage de zone** (`POST /blocages`) : bloque une zone sur une période et **annule automatiquement** les réservations confirmées qui la chevauchent (motif « Zone bloquée : … »). Supprimer un blocage ne rétablit pas ces réservations. `zone_active` reste disponible pour une fermeture sans date de fin.
- **Visiteurs** : ils ne réservent pas directement ; ils déposent une demande (`POST /demandes-visiteurs`) avec un créneau. L'administrateur la valide en choisissant une place, ou laisse l'API attribuer la première place libre accessible (zones réservées aux visiteurs d'abord), ce qui crée la réservation ; ou il la refuse avec un commentaire. Ajout de la colonne `date_fin_visite_souhaitee`.
- **Règles d'accès** gérées par l'administrateur (`/regles-acces`) avec la liste des rôles ciblés.
- **Incidents** : tout utilisateur connecté signale un incident sur une zone ; l'administrateur change sa priorité et son statut (`ouvert`, `en_cours`, `resolu`).
- **Vue administrateur des réservations** (`/admin/reservations`) avec filtres et annulation de n'importe quelle réservation. Seuls le nom et le prénom de l'utilisateur sont exposés (minimisation RGPD).

## 2026-10-13 (tableau de bord)

- **Passage et no-show** : nouvelle colonne `reservation.date_passage`, renseignée par la simulation du scan à l'entrée (`POST /reservations/{id}/passage`, possible 15 min avant le début et jusqu'à la fin). Une réservation confirmée sans passage 30 min après son début devient `no_show` (`POST /admin/reservations/no-shows`, appliqué aussi à chaque calcul de statistiques). Une réservation no-show libère la place ; une réservation honorée ou no-show ne peut plus être annulée.
- **Taux d'occupation** = heures réservées et honorées / (places en service × amplitude d'ouverture × jours). Les annulations et no-shows ne consomment pas de capacité ; les zones désactivées sont exclues. Les jours sont comptés en heure de Paris, selon le début de la réservation.
- **Statistiques** (`GET /admin/statistiques?du&au&id_parking`) : totaux, détail par jour et par zone (réservations, honorées, annulations, no-shows et leurs taux). Période par défaut : les 30 derniers jours.
- **Simulateur de fréquentation** déterministe (`app/seed/simulateur.py`), lancé par le seed : comptes fictifs `simu.*@campus.fr`, profil de fréquentation selon le jour et le public de la zone, environ 8 % d'annulations et 5 % de no-shows. Les règles d'accès du seed s'appliquent depuis la rentrée pour couvrir l'historique.

## 2026-10-14 (RGPD et traçabilité)

- **Journalisation** des actions importantes dans `trace` depuis les routes (`app/services/journal.py`) : identifiants techniques et détail court uniquement, jamais de donnée personnelle ni de texte libre (voir `docs/rgpd.md`). Les échecs de connexion sur un compte existant sont journalisés.
- **Effacement RGPD par anonymisation** plutôt que suppression physique : les clés étrangères (réservations, journal) restent valides et les statistiques restent justes, sans donnée identifiante. Statut de compte `supprime`.
- **Export RGPD** au format JSON, profil sans le hash du mot de passe.
- **Administration des comptes** : un administrateur peut suspendre / réactiver un compte et modifier ses rôles, y compris promouvoir un administrateur ; il ne peut pas se suspendre ni se retirer son propre rôle administrateur.

## 2026-10-14 (interface)

- **Interface d'administration** (`/admin`, réservée au rôle administrateur) : tableau de bord (indicateurs, réservations et taux d'occupation par jour, détail par zone), zones et blocages, places, règles d'accès, demandes visiteurs, incidents, réservations, utilisateurs et journal.
- **Pages par profil** : « Mes demandes » pour les visiteurs, « Incidents » et « Mon compte » pour tous, page publique « Données personnelles ». Après connexion, l'administrateur arrive sur le tableau de bord et le visiteur sur ses demandes.
- **Graphiques** en SVG sans dépendance (`ColumnChart`) : une seule échelle, info-bulle au survol, légende et vue tableau (accessibilité) ; palette validée pour les daltonismes (indigo, orange, vert d'eau).
- **Dates** : l'API renvoie désormais les dates avec leur fuseau (`+00:00`). Avant, les dates UTC sans fuseau étaient lues comme des heures locales par le navigateur, avec un décalage de 2 h à l'affichage.
