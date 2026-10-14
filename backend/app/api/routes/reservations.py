from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_roles
from app.db.session import get_db
from app.models import Reservation, Utilisateur
from app.schemas.reservation import ReservationCancel, ReservationCreate, ReservationOut
from app.services import reservations as reservation_service
from app.services.journal import journaliser

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationOut])
def list_my_reservations(
    db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)
) -> list[Reservation]:
    return (
        db.query(Reservation)
        .filter(Reservation.id_utilisateur == user.id_utilisateur)
        .order_by(Reservation.date_debut.desc())
        .all()
    )


@router.get("/{id_reservation}", response_model=ReservationOut)
def get_reservation(
    id_reservation: int,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    return reservation_service.get_user_reservation(db, user, id_reservation)


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    reservation = reservation_service.create_reservation(
        db,
        user,
        get_user_roles(user, db),
        payload.id_place,
        payload.date_debut,
        payload.date_fin,
    )
    journaliser(db, user.id_utilisateur, "reservation.creation", "reservation",
                reservation.id_reservation, f"place {reservation.id_place}")
    return reservation


@router.patch("/{id_reservation}/annuler", response_model=ReservationOut)
def cancel_reservation(
    id_reservation: int,
    payload: ReservationCancel,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    reservation = reservation_service.cancel_reservation(
        db, user, id_reservation, payload.motif_annulation
    )
    journaliser(db, user.id_utilisateur, "reservation.annulation", "reservation", id_reservation)
    return reservation


@router.post("/{id_reservation}/passage", response_model=ReservationOut)
def enregistrer_passage(
    id_reservation: int,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    """Simule le scan du QR code de la réservation à l'entrée du parking."""
    reservation = reservation_service.enregistrer_passage(db, user, id_reservation)
    journaliser(db, user.id_utilisateur, "reservation.passage", "reservation", id_reservation)
    return reservation
