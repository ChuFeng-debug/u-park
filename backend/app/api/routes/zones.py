from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Parking, Place, Zone
from app.schemas.zone import ZoneCreate, ZoneOut, ZoneUpdate, ZoneWithDisponibilite

router = APIRouter(prefix="/zones", tags=["zones"])


def _with_disponibilite(zone: Zone, db: Session) -> ZoneWithDisponibilite:
    total = db.query(func.count(Place.id_place)).filter(Place.id_zone == zone.id_zone).scalar() or 0
    # Une zone bloquée (zone_active=False) n'offre plus aucune place, même si
    # certaines places sont encore marquées "libre" individuellement.
    libres = 0
    if zone.zone_active:
        libres = (
            db.query(func.count(Place.id_place))
            .filter(Place.id_zone == zone.id_zone, Place.etat_place == "libre")
            .scalar()
            or 0
        )
    return ZoneWithDisponibilite(
        **ZoneOut.model_validate(zone).model_dump(),
        nombre_places=total,
        nombre_places_libres=libres,
    )


@router.get("", response_model=list[ZoneWithDisponibilite])
def list_zones(
    id_parking: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ZoneWithDisponibilite]:
    query = db.query(Zone)
    if id_parking is not None:
        query = query.filter(Zone.id_parking == id_parking)
    return [_with_disponibilite(zone, db) for zone in query.order_by(Zone.nom_zone).all()]


@router.get("/{id_zone}", response_model=ZoneWithDisponibilite)
def get_zone(id_zone: int, db: Session = Depends(get_db)) -> ZoneWithDisponibilite:
    zone = db.get(Zone, id_zone)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone introuvable")
    return _with_disponibilite(zone, db)


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("administrateur")),
) -> Zone:
    if db.get(Parking, payload.id_parking) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parking inconnu")
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.patch("/{id_zone}", response_model=ZoneOut)
def update_zone(
    id_zone: int,
    payload: ZoneUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("administrateur")),
) -> Zone:
    zone = db.get(Zone, id_zone)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    db.commit()
    db.refresh(zone)
    return zone
