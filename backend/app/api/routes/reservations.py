from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Place, Reservation, Utilisateur, Zone
from app.schemas.reservation import ReservationCancel, ReservationCreate, ReservationOut

router = APIRouter(prefix="/reservations", tags=["reservations"])


def _has_overlap(db: Session, id_place: int, date_debut: datetime, date_fin: datetime) -> bool:
    return (
        db.query(Reservation)
        .filter(
            Reservation.id_place == id_place,
            Reservation.statut_reservation == "confirmee",
            Reservation.date_debut < date_fin,
            Reservation.date_fin > date_debut,
        )
        .first()
        is not None
    )


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
    reservation = db.get(Reservation, id_reservation)
    if reservation is None or reservation.id_utilisateur != user.id_utilisateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Réservation introuvable"
        )
    return reservation


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    place = db.get(Place, payload.id_place)
    if place is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Place inconnue")
    if place.etat_place == "hors_service":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Place hors service")

    zone = db.get(Zone, place.id_zone)
    if zone is None or not zone.zone_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Zone bloquée ou inconnue")

    if _has_overlap(db, payload.id_place, payload.date_debut, payload.date_fin):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Place déjà réservée sur ce créneau"
        )

    now = datetime.now(timezone.utc)
    reservation = Reservation(
        id_utilisateur=user.id_utilisateur,
        id_place=payload.id_place,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        statut_reservation="confirmee",
        date_creation_resa=now,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{id_reservation}/annuler", response_model=ReservationOut)
def cancel_reservation(
    id_reservation: int,
    payload: ReservationCancel,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Reservation:
    reservation = db.get(Reservation, id_reservation)
    if reservation is None or reservation.id_utilisateur != user.id_utilisateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Réservation introuvable"
        )
    if reservation.statut_reservation == "annulee":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Réservation déjà annulée"
        )

    reservation.statut_reservation = "annulee"
    reservation.date_annulation = datetime.now(timezone.utc)
    reservation.motif_annulation = payload.motif_annulation
    db.commit()
    db.refresh(reservation)
    return reservation
