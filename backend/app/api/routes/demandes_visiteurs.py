from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import DemandeVisiteur, Utilisateur
from app.schemas.demande_visiteur import (
    DemandeRefus,
    DemandeValidation,
    DemandeVisiteurCreate,
    DemandeVisiteurOut,
)
from app.services import demandes_visiteurs as demande_service
from app.services.journal import journaliser

router = APIRouter(prefix="/demandes-visiteurs", tags=["demandes visiteurs"])


@router.post("", response_model=DemandeVisiteurOut, status_code=status.HTTP_201_CREATED)
def create_demande(
    payload: DemandeVisiteurCreate,
    db: Session = Depends(get_db),
    visiteur: Utilisateur = Depends(require_roles("visiteur")),
) -> DemandeVisiteur:
    demande = demande_service.create_demande(db, visiteur, payload)
    journaliser(db, visiteur.id_utilisateur, "demande.creation", "demande_visiteur",
                demande.id_demande)
    return demande


@router.get("/mes-demandes", response_model=list[DemandeVisiteurOut])
def list_my_demandes(
    db: Session = Depends(get_db),
    visiteur: Utilisateur = Depends(require_roles("visiteur")),
) -> list[DemandeVisiteur]:
    return (
        db.query(DemandeVisiteur)
        .filter(DemandeVisiteur.id_demandeur == visiteur.id_utilisateur)
        .order_by(DemandeVisiteur.date_demande.desc())
        .all()
    )


@router.get("", response_model=list[DemandeVisiteurOut])
def list_demandes(
    statut: Literal["en_attente", "validee", "refusee"] | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[DemandeVisiteur]:
    query = db.query(DemandeVisiteur)
    if statut is not None:
        query = query.filter(DemandeVisiteur.statut_demande == statut)
    return query.order_by(DemandeVisiteur.date_visite_souhaitee).all()


@router.post("/{id_demande}/valider", response_model=DemandeVisiteurOut)
def valider_demande(
    id_demande: int,
    payload: DemandeValidation,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> DemandeVisiteur:
    """Valide la demande et crée la réservation (place choisie ou attribuée)."""
    demande = demande_service.valider_demande(db, admin, id_demande, payload)
    journaliser(db, admin.id_utilisateur, "demande.validation", "demande_visiteur", id_demande,
                f"réservation {demande.id_reservation}")
    return demande


@router.post("/{id_demande}/refuser", response_model=DemandeVisiteurOut)
def refuser_demande(
    id_demande: int,
    payload: DemandeRefus,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> DemandeVisiteur:
    demande = demande_service.refuser_demande(db, admin, id_demande, payload)
    journaliser(db, admin.id_utilisateur, "demande.refus", "demande_visiteur", id_demande)
    return demande
