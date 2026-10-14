"""Signalement et traitement des incidents de stationnement."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Incident, Utilisateur, Zone
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.exceptions import InvalidRequestError, NotFoundError


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_incident(db: Session, user: Utilisateur, payload: IncidentCreate) -> Incident:
    if db.get(Zone, payload.id_zone) is None:
        raise InvalidRequestError("Zone inconnue")
    incident = Incident(
        id_zone=payload.id_zone,
        id_utilisateur_signalement=user.id_utilisateur,
        description_incident=payload.description_incident,
        priorite_incident=payload.priorite_incident,
        statut_incident="ouvert",
        date_signalement=_now(),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(
    db: Session, admin: Utilisateur, id_incident: int, payload: IncidentUpdate
) -> Incident:
    incident = db.get(Incident, id_incident)
    if incident is None:
        raise NotFoundError("Incident introuvable")
    if payload.priorite_incident is not None:
        incident.priorite_incident = payload.priorite_incident
    if payload.statut_incident is not None:
        incident.statut_incident = payload.statut_incident
        incident.id_utilisateur_traitant = admin.id_utilisateur
        incident.date_resolution = _now() if payload.statut_incident == "resolu" else None
    db.commit()
    db.refresh(incident)
    return incident
