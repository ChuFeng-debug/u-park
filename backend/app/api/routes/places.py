from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Place, Zone
from app.schemas.place import PlaceCreate, PlaceOut, PlaceUpdate

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", response_model=list[PlaceOut])
def list_places(
    id_zone: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Place]:
    query = db.query(Place)
    if id_zone is not None:
        query = query.filter(Place.id_zone == id_zone)
    return query.order_by(Place.numero_place).all()


@router.get("/{id_place}", response_model=PlaceOut)
def get_place(id_place: int, db: Session = Depends(get_db)) -> Place:
    place = db.get(Place, id_place)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place introuvable")
    return place


@router.post("", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
def create_place(
    payload: PlaceCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("administrateur")),
) -> Place:
    if db.get(Zone, payload.id_zone) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zone inconnue")
    place = Place(**payload.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@router.patch("/{id_place}", response_model=PlaceOut)
def update_place(
    id_place: int,
    payload: PlaceUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("administrateur")),
) -> Place:
    place = db.get(Place, id_place)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(place, field, value)
    db.commit()
    db.refresh(place)
    return place
