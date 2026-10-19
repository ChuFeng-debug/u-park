# U-Park — Backlog produit

État au 19/10/2026, présenté à la soutenance mensuelle 1. Le backlog est mis à jour avant chaque soutenance ; les changements de priorité sont notés dans le [journal de décisions](journal-de-decisions.md).

**Priorités (MoSCoW)** : **M** = Must (MVP du cahier des charges), **S** = Should (souhaitable), **C** = Could (extension), **W** = Won't (hors périmètre).
**États** : ✅ Fait · 🟡 En cours · ⬜ Prévu · ⛔ Bloqué.

Une story est **faite** quand : le code est fusionné dans `main` par une pull request relue, ses règles sont couvertes par des tests automatisés, elle est utilisable dans l'interface (ordinateur et mobile), et le jeu de démonstration permet de la montrer.

## Synthèse

| Bloc | Stories | Fait | En cours | Prévu | Bloqué |
|---|---|---|---|---|---|
| Cadrage et UX | 7 | 0 | 4 | 3 | 0 |
| Catalogue et réservation | 9 | 9 | 0 | 0 | 0 |
| Visiteurs | 2 | 2 | 0 | 0 | 0 |
| Administration | 6 | 6 | 0 | 0 | 0 |
| Tableau de bord et données | 4 | 3 | 0 | 0 | 1 |
| Comptes, sécurité, RGPD | 6 | 6 | 0 | 0 | 0 |
| Qualité et livraison | 7 | 2 | 1 | 4 | 0 |
| Extensions | 4 | 0 | 0 | 4 | 0 |

Les fonctionnalités du MVP existent déjà sous forme de **prototype technique**. Elles doivent encore être **validées par les utilisateurs** (questionnaire, maquettes, tests) : c'est l'objet des stories de cadrage, qui peuvent faire évoluer le prototype.

## Cadrage et UX

| ID | Story | Prio | État | Échéance |
|---|---|---|---|---|
| C-01 | Diffuser le questionnaire (voir [cadrage](cadrage.md#questionnaire)) et analyser au moins 30 réponses | M | 🟡 | Oct. |
| C-02 | Mener 3 entretiens : un étudiant motorisé, un personnel, un responsable du parking ou de la logistique | M | 🟡 | Oct. |
| C-03 | Finaliser les 4 personas à partir des résultats | M | 🟡 | Oct. |
| C-04 | Attribuer nominativement les 6 rôles de l'équipe | M | 🟡 | Oct. |
| C-05 | Maquettes mobile et desktop des 2 parcours principaux | M | ⬜ | Nov. |
| C-06 | Tests rapides des maquettes auprès de 3 à 5 utilisateurs | M | ⬜ | Nov. |
| C-07 | Tests utilisateurs du produit et corrections | M | ⬜ | Fév. |

## Catalogue et réservation

| ID | En tant que… | je veux… | Prio | État | Preuve |
|---|---|---|---|---|---|
| R-01 | usager | consulter les parkings et zones avec capacité, horaires et règles d'accès | M | ✅ | `test_list_parkings_is_public` |
| R-02 | étudiant | voir les places libres pour le créneau que je choisis | M | ✅ | `test_reservation_reduces_availability_only_on_its_slot` |
| R-03 | étudiant | réserver une place libre et recevoir une confirmation | M | ✅ | `test_create_and_list_reservation` |
| R-04 | étudiant | annuler ma réservation pour libérer la place | M | ✅ | `test_cancel_reservation`, `test_cancellation_frees_the_slot` |
| R-05 | usager | retrouver mes réservations à venir et passées | M | ✅ | page « Mes réservations » |
| R-06 | usager | être sûr qu'une place n'est jamais réservée deux fois | M | ✅ | `test_overlapping_reservation_rejected`, `test_database_rejects_overlapping_confirmed_reservations` |
| R-07 | usager | un message clair si mon créneau est passé, hors horaires ou déjà pris | M | ✅ | `test_past_slot_rejected`, `test_slot_outside_opening_hours_rejected`, `test_user_cannot_hold_two_places_on_same_slot` |
| R-08 | personnel | des zones qui me sont réservées | M | ✅ | `test_access_rule_restricts_zone_to_target_roles` |
| R-09 | usager PMR | que les places PMR restent disponibles pour moi | S | ✅ | `test_pmr_place_requires_pmr_need` |

## Visiteurs

| ID | En tant que… | je veux… | Prio | État | Preuve |
|---|---|---|---|---|---|
| V-01 | visiteur | demander une place pour une date et un créneau, puis suivre la réponse | M | ✅ | `test_visitor_request_refused`, page « Mes demandes » |
| V-02 | administrateur | valider une demande visiteur (place choisie ou attribuée automatiquement) ou la refuser avec un motif | M | ✅ | `test_visitor_request_validated_with_chosen_place`, `test_visitor_request_auto_assigns_a_place` |

## Administration

| ID | En tant qu'administrateur, je veux… | Prio | État | Preuve |
|---|---|---|---|---|
| A-01 | créer des parkings, des zones et des places | M | ✅ | `test_create_zone_and_disponibilite` |
| A-02 | bloquer une zone sur une période et voir l'impact sur les disponibilités | M | ✅ | `test_blocage_cancels_overlapping_reservations`, `test_blocage_makes_zone_unavailable_on_its_period` |
| A-03 | mettre une place hors service | M | ✅ | page « Zones et blocages » |
| A-04 | gérer les règles d'accès des zones, sans qu'un utilisateur simple puisse les modifier | M | ✅ | `test_admin_manages_access_rules`, `test_simple_user_cannot_modify_parking_rules` |
| A-05 | consulter toutes les réservations et en annuler une | S | ✅ | `test_admin_lists_and_cancels_any_reservation` |
| A-06 | suivre et traiter les incidents signalés par les usagers | S | ✅ | `test_incident_lifecycle` |

## Tableau de bord et données

| ID | Story | Prio | État | Preuve |
|---|---|---|---|---|
| T-01 | Tableau de bord : taux d'occupation, réservations par jour, annulations, no-show, par zone | M | ✅ | `test_statistics_reflect_dataset` |
| T-02 | Passage à l'entrée simulé et détection des no-show | S | ✅ | `test_missed_reservation_becomes_no_show` |
| T-03 | Jeu de données réaliste : parkings réels de la Cité Descartes, comptes fictifs sur 4 profils, simulateur de fréquentation | M | ✅ | `python -m app.seed.seed_data` |
| T-04 | Calibrer le simulateur sur de vraies données de fréquentation | S | ⛔ | Aucune donnée réelle disponible : demande d'arbitrage |

## Comptes, sécurité, RGPD

| ID | Story | Prio | État | Preuve |
|---|---|---|---|---|
| S-01 | Comptes fictifs par rôle, mots de passe hachés, connexion par jeton | M | ✅ | `test_login_success_and_me`, `test_register_as_admin_forbidden` |
| S-02 | Contrôle d'accès par rôle sur toutes les routes d'administration | M | ✅ | `test_*_requires_admin` |
| S-03 | Journal des actions importantes sans donnée personnelle | M | ✅ | `test_important_actions_are_logged_without_personal_data` |
| S-04 | Droits RGPD : export, rectification, suppression par anonymisation | M | ✅ | `test_export_contains_user_data_without_password`, `test_delete_account_anonymizes_and_cancels_future_reservations` |
| S-05 | Administration des comptes : suspendre, changer de rôle | S | ✅ | `test_admin_promotes_and_suspends_users` |
| S-06 | Page d'information sur les données personnelles | M | ✅ | page « Données personnelles », [rgpd.md](rgpd.md) |

## Qualité et livraison

| ID | Story | Prio | État | Échéance |
|---|---|---|---|---|
| Q-01 | Lancement en une commande avec Docker Compose | M | ✅ | — |
| Q-02 | Tests API automatisés (60 tests, dont les 4 critères d'acceptation) | M | ✅ | — |
| Q-03 | Interface responsive et accessible : audit clavier, contrastes, lecteur d'écran | M | 🟡 | Déc. |
| Q-04 | Base de données de test isolée de la base de développement | M | ⬜ | Nov. |
| Q-05 | Intégration continue GitHub Actions (tests et lint à chaque PR) | S | ⬜ | Déc. |
| Q-06 | Tests du front-end | S | ⬜ | Déc. |
| Q-07 | Plan de tests, cahier de recette et guide utilisateur | M | ⬜ | Déc. – fév. |

## Extensions

| ID | Story | Prio | État | Remarque |
|---|---|---|---|---|
| X-01 | QR code de contrôle à l'entrée, scan simulé et journal de passage | C | ⬜ | Le passage simulé (T-02) sert de base |
| X-02 | Liste d'attente et réattribution automatique des places libérées | C | ⬜ | |
| X-03 | Prévision de saturation à partir de l'historique | C | ⬜ | L'historique simulé existe |
| X-04 | Carte interactive des zones | C | ⬜ | |

## Hors périmètre (Won't)

Barrières, caméras ou capteurs réels ; paiement et abonnements ; données personnelles réelles ; connexion SSO de l'université.
