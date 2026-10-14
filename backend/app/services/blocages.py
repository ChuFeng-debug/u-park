"""Blocage temporaire d'une zone par un administrateur."""

from sqlalchemy.orm import Session

from app.models import Blocage, Utilisateur, Zone
from app.schemas.blocage import BlocageCreate
from app.services.disponibilites import to_utc_naive
from app.services.exceptions import InvalidRequestError, NotFoundError
from app.services.reservations import cancel_reservations_in_zone


def create_blocage(db: Session, admin: Utilisateur, payload: BlocageCreate) -> tuple[Blocage, int]:
    """Bloque la zone et annule les réservations confirmées sur la période.

    Renvoie le blocage et le nombre de réservations annulées.
    """
    if db.get(Zone, payload.id_zone) is None:
        raise InvalidRequestError("Zone inconnue")
    debut = to_utc_naive(payload.date_debut_blocage)
    fin = to_utc_naive(payload.date_fin_blocage)

    blocage = Blocage(
        id_zone=payload.id_zone,
        id_utilisateur=admin.id_utilisateur,
        motif_blocage=payload.motif_blocage,
        date_debut_blocage=debut,
        date_fin_blocage=fin,
    )
    db.add(blocage)
    annulees = cancel_reservations_in_zone(
        db, payload.id_zone, debut, fin, f"Zone bloquée : {payload.motif_blocage}"
    )
    db.commit()
    db.refresh(blocage)
    return blocage, annulees


def delete_blocage(db: Session, id_blocage: int) -> None:
    # Les réservations annulées par le blocage ne sont pas rétablies.
    blocage = db.get(Blocage, id_blocage)
    if blocage is None:
        raise NotFoundError("Blocage introuvable")
    db.delete(blocage)
    db.commit()
