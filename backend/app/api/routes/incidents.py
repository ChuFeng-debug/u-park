from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Incident, Utilisateur
from app.schemas.incident import IncidentCreate, IncidentOut, IncidentUpdate
from app.services import incidents as incident_service
from app.services.journal import journaliser

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Incident:
    incident = incident_service.create_incident(db, user, payload)
    journaliser(db, user.id_utilisateur, "incident.creation", "incident", incident.id_incident,
                f"zone {incident.id_zone}, priorité {incident.priorite_incident}")
    return incident


@router.get("/mes-signalements", response_model=list[IncidentOut])
def list_my_incidents(
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> list[Incident]:
    return (
        db.query(Incident)
        .filter(Incident.id_utilisateur_signalement == user.id_utilisateur)
        .order_by(Incident.date_signalement.desc())
        .all()
    )


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    statut: Literal["ouvert", "en_cours", "resolu"] | None = Query(default=None),
    id_zone: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[Incident]:
    query = db.query(Incident)
    if statut is not None:
        query = query.filter(Incident.statut_incident == statut)
    if id_zone is not None:
        query = query.filter(Incident.id_zone == id_zone)
    return query.order_by(Incident.date_signalement.desc()).all()


@router.patch("/{id_incident}", response_model=IncidentOut)
def update_incident(
    id_incident: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Incident:
    incident = incident_service.update_incident(db, admin, id_incident, payload)
    journaliser(db, admin.id_utilisateur, "incident.modification", "incident", id_incident,
                f"statut {incident.statut_incident}, priorité {incident.priorite_incident}")
    return incident
