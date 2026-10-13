from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Place, Reservation, Utilisateur
from app.schemas.reservation import ReservationAdminOut, ReservationCancel, ReservationOut
from app.services import reservations as reservation_service
from app.services.disponibilites import to_utc_naive

router = APIRouter(prefix="/admin/reservations", tags=["administration"])


@router.get("", response_model=list[ReservationAdminOut])
def list_reservations(
    id_zone: int | None = Query(default=None),
    statut: Literal["confirmee", "annulee", "no_show"] | None = Query(default=None),
    du: datetime | None = Query(default=None, description="Réservations finissant après"),
    au: datetime | None = Query(default=None, description="Réservations commençant avant"),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[ReservationAdminOut]:
    query = (
        db.query(Reservation, Place, Utilisateur)
        .join(Place, Place.id_place == Reservation.id_place)
        .join(Utilisateur, Utilisateur.id_utilisateur == Reservation.id_utilisateur)
    )
    if id_zone is not None:
        query = query.filter(Place.id_zone == id_zone)
    if statut is not None:
        query = query.filter(Reservation.statut_reservation == statut)
    if du is not None:
        query = query.filter(Reservation.date_fin > to_utc_naive(du))
    if au is not None:
        query = query.filter(Reservation.date_debut < to_utc_naive(au))
    rows = query.order_by(Reservation.date_debut.desc()).limit(limit).all()
    return [
        ReservationAdminOut(
            **ReservationOut.model_validate(reservation).model_dump(),
            numero_place=place.numero_place,
            id_zone=place.id_zone,
            nom_utilisateur=user.nom_utilisateur,
            prenom_utilisateur=user.prenom_utilisateur,
        )
        for reservation, place, user in rows
    ]


@router.post("/no-shows")
def marquer_no_shows(
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> dict[str, int]:
    """Marque "no_show" les réservations non honorées après le délai de grâce."""
    return {"reservations_marquees": reservation_service.marquer_no_shows(db)}


@router.patch("/{id_reservation}/annuler", response_model=ReservationOut)
def cancel_reservation(
    id_reservation: int,
    payload: ReservationCancel,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Reservation:
    return reservation_service.admin_cancel_reservation(
        db, id_reservation, payload.motif_annulation
    )
