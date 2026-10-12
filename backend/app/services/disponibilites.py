"""Calcul des disponibilités des places sur un créneau."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Blocage, Place, Reservation, Zone
from app.services.exceptions import InvalidRequestError


class Creneau:
    """Créneau [debut, fin[ en UTC sans fuseau. Sans bornes : l'instant présent."""

    def __init__(self, debut: datetime | None = None, fin: datetime | None = None) -> None:
        if (debut is None) != (fin is None):
            raise InvalidRequestError("Indiquer à la fois debut et fin, ou aucun des deux")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.maintenant = debut is None
        self.debut = to_utc_naive(debut) if debut else now
        self.fin = to_utc_naive(fin) if fin else now
        if not self.maintenant and self.fin <= self.debut:
            raise InvalidRequestError("fin doit être postérieure à debut")

    @property
    def jour(self) -> date:
        """Jour du début du créneau, en heure locale du campus."""
        local = self.debut.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(settings.campus_timezone))
        return local.date()


def to_utc_naive(value: datetime) -> datetime:
    """Les colonnes TIMESTAMP sont sans fuseau : on y stocke de l'UTC."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _chevauche(debut_col, fin_col, creneau: Creneau):
    if creneau.maintenant:
        return and_(debut_col <= creneau.debut, fin_col > creneau.debut)
    return and_(debut_col < creneau.fin, fin_col > creneau.debut)


def zones_indisponibles(db: Session, ids_zone: list[int], creneau: Creneau) -> set[int]:
    """Zones désactivées ou couvertes par un blocage pendant le créneau."""
    if not ids_zone:
        return set()
    inactives = db.scalars(
        select(Zone.id_zone).where(Zone.id_zone.in_(ids_zone), Zone.zone_active.is_(False))
    ).all()
    bloquees = db.scalars(
        select(Blocage.id_zone).where(
            Blocage.id_zone.in_(ids_zone),
            _chevauche(Blocage.date_debut_blocage, Blocage.date_fin_blocage, creneau),
        )
    ).all()
    return set(inactives) | set(bloquees)


def _condition_place_libre(creneau: Creneau):
    reservee = exists().where(
        Reservation.id_place == Place.id_place,
        Reservation.statut_reservation == "confirmee",
        _chevauche(Reservation.date_debut, Reservation.date_fin, creneau),
    )
    # "occupee" décrit l'état physique actuel (simulé) : il ne compte que pour
    # l'instant présent, pas pour un créneau futur.
    etats_exclus = ["hors_service", "occupee"] if creneau.maintenant else ["hors_service"]
    return and_(Place.etat_place.not_in(etats_exclus), ~reservee)


def compter_places(db: Session, ids_zone: list[int], creneau: Creneau) -> dict[int, tuple[int, int]]:
    """Pour chaque zone : (nombre de places, nombre de places libres sur le créneau)."""
    if not ids_zone:
        return {}
    totaux = dict(
        db.execute(
            select(Place.id_zone, func.count(Place.id_place))
            .where(Place.id_zone.in_(ids_zone))
            .group_by(Place.id_zone)
        ).all()
    )
    libres = dict(
        db.execute(
            select(Place.id_zone, func.count(Place.id_place))
            .where(Place.id_zone.in_(ids_zone), _condition_place_libre(creneau))
            .group_by(Place.id_zone)
        ).all()
    )
    fermees = zones_indisponibles(db, ids_zone, creneau)
    return {
        id_zone: (totaux.get(id_zone, 0), 0 if id_zone in fermees else libres.get(id_zone, 0))
        for id_zone in ids_zone
    }


def places_disponibles(db: Session, places: list[Place], creneau: Creneau) -> set[int]:
    """Identifiants des places réservables sur le créneau parmi `places`."""
    if not places:
        return set()
    fermees = zones_indisponibles(db, list({place.id_zone for place in places}), creneau)
    candidates = [place.id_place for place in places if place.id_zone not in fermees]
    if not candidates:
        return set()
    return set(
        db.scalars(
            select(Place.id_place).where(
                Place.id_place.in_(candidates), _condition_place_libre(creneau)
            )
        ).all()
    )
