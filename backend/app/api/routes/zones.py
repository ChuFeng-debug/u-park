from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Parking, Utilisateur, Zone
from app.schemas.zone import ZoneCreate, ZoneOut, ZoneUpdate, ZoneWithDisponibilite
from app.services.disponibilites import Creneau, compter_places
from app.services.journal import champs_modifies, journaliser
from app.services.reservations import roles_autorises

router = APIRouter(prefix="/zones", tags=["zones"])


def _sorted_or_none(roles: set[str] | None) -> list[str] | None:
    return None if roles is None else sorted(roles)


def _with_disponibilite(
    zones: list[Zone], db: Session, creneau: Creneau
) -> list[ZoneWithDisponibilite]:
    # Une zone bloquée n'offre aucune place, même si certaines sont "libres".
    comptes = compter_places(db, [zone.id_zone for zone in zones], creneau)
    return [
        ZoneWithDisponibilite(
            **ZoneOut.model_validate(zone).model_dump(),
            nombre_places=comptes[zone.id_zone][0],
            nombre_places_libres=comptes[zone.id_zone][1],
            roles_autorises=_sorted_or_none(roles_autorises(db, zone.id_zone, creneau.jour)),
        )
        for zone in zones
    ]


@router.get("", response_model=list[ZoneWithDisponibilite])
def list_zones(
    id_parking: int | None = Query(default=None),
    debut: datetime | None = Query(default=None, description="Début du créneau (ISO 8601)"),
    fin: datetime | None = Query(default=None, description="Fin du créneau (ISO 8601)"),
    db: Session = Depends(get_db),
) -> list[ZoneWithDisponibilite]:
    """Zones avec leurs places libres sur le créneau [debut, fin[ (par défaut : maintenant)."""
    creneau = Creneau(debut, fin)
    query = db.query(Zone)
    if id_parking is not None:
        query = query.filter(Zone.id_parking == id_parking)
    return _with_disponibilite(query.order_by(Zone.nom_zone).all(), db, creneau)


@router.get("/{id_zone}", response_model=ZoneWithDisponibilite)
def get_zone(
    id_zone: int,
    debut: datetime | None = Query(default=None),
    fin: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ZoneWithDisponibilite:
    creneau = Creneau(debut, fin)
    zone = db.get(Zone, id_zone)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone introuvable")
    return _with_disponibilite([zone], db, creneau)[0]


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Zone:
    if db.get(Parking, payload.id_parking) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parking inconnu")
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    journaliser(db, admin.id_utilisateur, "zone.creation", "zone", zone.id_zone)
    return zone


@router.patch("/{id_zone}", response_model=ZoneOut)
def update_zone(
    id_zone: int,
    payload: ZoneUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Zone:
    zone = db.get(Zone, id_zone)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone introuvable")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(zone, field, value)
    db.commit()
    db.refresh(zone)
    journaliser(db, admin.id_utilisateur, "zone.modification", "zone", zone.id_zone,
                champs_modifies(changes))
    return zone
