"""Gestion des comptes : profil, droits RGPD, administration des utilisateurs."""

import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import (
    AttributionRole,
    DemandeVisiteur,
    Incident,
    Reservation,
    Role,
    Utilisateur,
)
from app.services.exceptions import (
    AccessDeniedError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
)

STATUTS_COMPTE = {"actif", "suspendu"}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def roles_de(db: Session, id_utilisateur: int) -> list[str]:
    rows = db.query(AttributionRole.code_role).filter_by(id_utilisateur=id_utilisateur).all()
    return sorted(row.code_role for row in rows)


def modifier_profil(db: Session, user: Utilisateur, changes: dict) -> Utilisateur:
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def changer_mot_de_passe(db: Session, user: Utilisateur, actuel: str, nouveau: str) -> None:
    if not verify_password(actuel, user.mot_de_passe_hash):
        raise AccessDeniedError("Mot de passe actuel incorrect")
    user.mot_de_passe_hash = hash_password(nouveau)
    db.commit()


def exporter(db: Session, user: Utilisateur) -> dict:
    """Droit d'accès / portabilité : toutes les données liées au compte.

    Met en œuvre les articles 15 et 20 du RGPD. Les colonnes sont parcourues
    par introspection (`model.__table__.columns`) plutôt qu'énumérées à la
    main : une colonne ajoutée plus tard à une table apparaîtra
    automatiquement dans l'export, alors qu'une liste figée l'aurait omise
    en silence — et un export incomplet est un manquement réglementaire.
    """

    def valeur(value):
        # Dates stockées en UTC sans fuseau : on l'explicite dans l'export.
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def rows(model, *criteres) -> list[dict]:
        return [
            {col.name: valeur(getattr(obj, col.name)) for col in model.__table__.columns}
            for obj in db.query(model).filter(*criteres).all()
        ]

    # Seule exception à l'introspection : le hash du mot de passe. Ce n'est
    # pas une donnée utile à la personne, et l'exporter offrirait une prise
    # aux attaques par dictionnaire hors ligne si le fichier venait à fuiter.
    profil = {
        col.name: valeur(getattr(user, col.name))
        for col in Utilisateur.__table__.columns
        if col.name != "mot_de_passe_hash"
    }
    return {
        "date_export": _now(),
        "profil": profil,
        "roles": roles_de(db, user.id_utilisateur),
        "reservations": rows(Reservation, Reservation.id_utilisateur == user.id_utilisateur),
        "demandes_visiteurs": rows(
            DemandeVisiteur, DemandeVisiteur.id_demandeur == user.id_utilisateur
        ),
        "incidents_signales": rows(
            Incident, Incident.id_utilisateur_signalement == user.id_utilisateur
        ),
    }


def anonymiser(db: Session, user: Utilisateur, mot_de_passe: str) -> int:
    """Droit à l'effacement : le compte est anonymisé plutôt que supprimé, pour
    garder des statistiques et un journal cohérents sans donnée personnelle.
    Les réservations à venir sont annulées. Renvoie leur nombre.

    Choix central à défendre : l'article 17 du RGPD impose d'effacer les
    données *personnelles*, pas les enregistrements qui les référencent. Un
    DELETE sur la ligne utilisateur casserait les clés étrangères de toutes
    ses réservations, et fausserait l'historique d'occupation des parkings.

    La pseudonymisation répond aux deux exigences : plus aucune donnée
    identifiante ne subsiste, mais les lignes liées restent intègres et les
    statistiques agrégées inchangées.
    """
    if not verify_password(mot_de_passe, user.mot_de_passe_hash):
        raise AccessDeniedError("Mot de passe incorrect")
    now = _now()
    a_venir = (
        db.query(Reservation)
        .filter(
            Reservation.id_utilisateur == user.id_utilisateur,
            Reservation.statut_reservation == "confirmee",
            Reservation.date_fin > now,
        )
        .all()
    )
    for reservation in a_venir:
        reservation.statut_reservation = "annulee"
        reservation.date_annulation = now
        reservation.motif_annulation = "Compte supprimé"
    for demande in db.query(DemandeVisiteur).filter_by(
        id_demandeur=user.id_utilisateur, statut_demande="en_attente"
    ):
        demande.statut_demande = "refusee"
        demande.date_traitement = now
        demande.commentaire_traitement = "Compte supprimé"
        demande.motif_demande = "(anonymisé)"

    # L'identifiant technique est conservé dans l'email de remplacement : il
    # n'est pas une donnée personnelle, et la colonne reste soumise à une
    # contrainte d'unicité qu'une valeur fixe violerait au second effacement.
    user.email = f"compte-supprime-{user.id_utilisateur}@anonyme.u-park.fr"
    user.nom_utilisateur = "Utilisateur"
    user.prenom_utilisateur = "Supprimé"
    # Le besoin PMR est une donnée de santé, donc sensible : on la remet à sa
    # valeur par défaut au lieu de la laisser en place.
    user.besoin_pmr = False
    user.statut_compte = "supprime"
    # Mot de passe remplacé par une valeur aléatoire que personne ne connaît —
    # pas même le code, qui ne la conserve pas. Le compte devient définitivement
    # inconnectable. Vider le champ aurait été plus risqué : selon la fonction
    # de vérification, une chaîne vide peut correspondre à une saisie vide.
    user.mot_de_passe_hash = hash_password(secrets.token_urlsafe(32))
    db.commit()
    return len(a_venir)


def administrer(
    db: Session,
    admin: Utilisateur,
    id_utilisateur: int,
    statut_compte: str | None,
    roles: list[str] | None,
) -> Utilisateur:
    """Modification du statut et des rôles d'un compte par un administrateur.

    Les deux tests sur `soi_meme` sont des garde-fous anti-verrouillage : sans
    eux, un administrateur pourrait se suspendre ou se retirer son propre
    rôle, et plus personne ne pourrait administrer l'application — l'interface
    ne permettant pas de rétablir un droit qu'on vient de perdre.
    """
    user = db.get(Utilisateur, id_utilisateur)
    if user is None:
        raise NotFoundError("Utilisateur introuvable")
    if user.statut_compte == "supprime":
        # Réactiver un compte anonymisé n'aurait pas de sens : ses données
        # personnelles sont perdues et son propriétaire ne peut plus s'y
        # connecter.
        raise ConflictError("Compte supprimé : il ne peut plus être modifié")
    soi_meme = user.id_utilisateur == admin.id_utilisateur

    if statut_compte is not None:
        if statut_compte not in STATUTS_COMPTE:
            raise InvalidRequestError("Statut inconnu")
        if soi_meme and statut_compte != "actif":
            raise ConflictError("Vous ne pouvez pas suspendre votre propre compte")
        user.statut_compte = statut_compte

    if roles is not None:
        connus = {row.code_role for row in db.query(Role.code_role)}
        if not roles or set(roles) - connus:
            raise InvalidRequestError("Liste de rôles invalide")
        if soi_meme and "administrateur" not in roles:
            raise ConflictError("Vous ne pouvez pas retirer votre propre rôle administrateur")
        # Table d'association (n-n) : on remplace l'ensemble des rôles plutôt
        # que de calculer les ajouts et retraits. Pour quelques lignes, c'est
        # plus simple et moins sujet aux erreurs qu'une synchronisation fine.
        db.query(AttributionRole).filter_by(id_utilisateur=user.id_utilisateur).delete()
        db.add_all(
            AttributionRole(
                id_utilisateur=user.id_utilisateur, code_role=role, date_attribution=_now().date()
            )
            for role in set(roles)
        )
    db.commit()
    db.refresh(user)
    return user
