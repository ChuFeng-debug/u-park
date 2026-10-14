from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Place, Utilisateur, Zone
from app.schemas.place import PlaceCreate, PlaceOut, PlaceUpdate, PlaceWithDisponibilite
from app.services.disponibilites import Creneau, places_disponibles
from app.services.journal import champs_modifies, journaliser

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", response_model=list[PlaceWithDisponibilite])
def list_places(
    id_zone: int | None = Query(default=None),
    debut: datetime | None = Query(default=None, description="Début du créneau (ISO 8601)"),
    fin: datetime | None = Query(default=None, description="Fin du créneau (ISO 8601)"),
    db: Session = Depends(get_db),
) -> list[PlaceWithDisponibilite]:
    """Places avec leur disponibilité sur le créneau [debut, fin[ (par défaut : maintenant)."""
    creneau = Creneau(debut, fin)
    query = db.query(Place)
    if id_zone is not None:
        query = query.filter(Place.id_zone == id_zone)
    places = query.order_by(Place.numero_place).all()
    disponibles = places_disponibles(db, places, creneau)
    return [
        PlaceWithDisponibilite(
            **PlaceOut.model_validate(place).model_dump(),
            disponible=place.id_place in disponibles,
        )
        for place in places
    ]


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
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Place:
    if db.get(Zone, payload.id_zone) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zone inconnue")
    place = Place(**payload.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    journaliser(db, admin.id_utilisateur, "place.creation", "place", place.id_place)
    return place


@router.patch("/{id_place}", response_model=PlaceOut)
def update_place(
    id_place: int,
    payload: PlaceUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Place:
    place = db.get(Place, id_place)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place introuvable")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(place, field, value)
    db.commit()
    db.refresh(place)
    journaliser(db, admin.id_utilisateur, "place.modification", "place", place.id_place,
                champs_modifies(changes))
    return place
