# U-Park — Données personnelles (RGPD)

Le POC fonctionne uniquement avec des **données fictives**. Ce document décrit ce que l'application ferait des données réelles et comment les droits des personnes sont mis en œuvre.

## Données collectées (minimisation)

| Donnée | Finalité | Obligatoire |
|---|---|---|
| Email | Identifiant de connexion | Oui |
| Nom, prénom | Identification par l'administration (validation visiteur, incident) | Oui |
| Mot de passe | Authentification, stocké **haché (bcrypt)**, jamais restitué | Oui |
| Rôle(s) | Droits d'accès aux zones et à l'administration | Oui |
| Besoin PMR | Accès aux places PMR (donnée déclarative, aucun justificatif stocké) | Non |
| Réservations, passages, demandes, incidents signalés | Service rendu et statistiques d'occupation | — |

Aucune plaque d'immatriculation, aucun numéro étudiant, aucune donnée de santé détaillée n'est collecté.

## Droits des personnes

| Droit | Mise en œuvre |
|---|---|
| Information | Page « Mon compte » de l'application |
| Accès / portabilité | `GET /auth/me/export` : export JSON de toutes les données du compte |
| Rectification | `PATCH /auth/me` (nom, prénom, besoin PMR) |
| Effacement | `DELETE /auth/me` (mot de passe requis) : le compte est **anonymisé** (email, nom, prénom, besoin PMR effacés, mot de passe remplacé, connexion impossible), les réservations à venir et demandes en attente sont annulées. Les réservations passées sont conservées sans lien avec une personne identifiable, pour garder des statistiques justes. |

## Traçabilité

Les actions importantes (connexion, réservation, annulation, passage, blocage, règle d'accès, demande visiteur, incident, administration des comptes, export et suppression RGPD) sont écrites dans la table `trace` avec l'identifiant technique de l'auteur, l'entité visée et un détail court. On n'y écrit **jamais** d'email, de nom, de mot de passe ni de texte libre saisi par l'utilisateur ; pour une modification, seuls les noms des champs modifiés sont journalisés. Le journal est consultable par les administrateurs (`GET /admin/traces`).

## Limites connues

- Pas de purge automatique : la durée de conservation proposée (12 mois pour le journal, 3 ans d'inactivité pour un compte) n'est pas encore appliquée par un traitement planifié.
- Les comptes de démonstration et simulés (`*@campus.fr`) sont fictifs.
