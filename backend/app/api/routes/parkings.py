from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Parking, Utilisateur
from app.schemas.parking import ParkingCreate, ParkingOut, ParkingUpdate
from app.services.journal import champs_modifies, journaliser

router = APIRouter(prefix="/parkings", tags=["parkings"])


@router.get("", response_model=list[ParkingOut])
def list_parkings(db: Session = Depends(get_db)) -> list[Parking]:
    return db.query(Parking).order_by(Parking.nom_parking).all()


@router.get("/{id_parking}", response_model=ParkingOut)
def get_parking(id_parking: int, db: Session = Depends(get_db)) -> Parking:
    parking = db.get(Parking, id_parking)
    if parking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking introuvable")
    return parking


@router.post("", response_model=ParkingOut, status_code=status.HTTP_201_CREATED)
def create_parking(
    payload: ParkingCreate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Parking:
    parking = Parking(**payload.model_dump())
    db.add(parking)
    db.commit()
    db.refresh(parking)
    journaliser(db, admin.id_utilisateur, "parking.creation", "parking", parking.id_parking)
    return parking


@router.patch("/{id_parking}", response_model=ParkingOut)
def update_parking(
    id_parking: int,
    payload: ParkingUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Parking:
    parking = db.get(Parking, id_parking)
    if parking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking introuvable")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(parking, field, value)
    db.commit()
    db.refresh(parking)
    journaliser(db, admin.id_utilisateur, "parking.modification", "parking", parking.id_parking,
                champs_modifies(changes))
    return parking
