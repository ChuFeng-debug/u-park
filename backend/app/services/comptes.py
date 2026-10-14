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
    """Droit d'accès / portabilité : toutes les données liées au compte."""

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
    Les réservations à venir sont annulées. Renvoie leur nombre."""
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

    user.email = f"compte-supprime-{user.id_utilisateur}@anonyme.u-park.fr"
    user.nom_utilisateur = "Utilisateur"
    user.prenom_utilisateur = "Supprimé"
    user.besoin_pmr = False
    user.statut_compte = "supprime"
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
    user = db.get(Utilisateur, id_utilisateur)
    if user is None:
        raise NotFoundError("Utilisateur introuvable")
    if user.statut_compte == "supprime":
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
