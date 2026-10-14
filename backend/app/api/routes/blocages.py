from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Blocage, Utilisateur
from app.schemas.blocage import BlocageCreate, BlocageCreated, BlocageOut
from app.services import blocages as blocage_service
from app.services.journal import journaliser

router = APIRouter(prefix="/blocages", tags=["administration"])


@router.get("", response_model=list[BlocageOut])
def list_blocages(
    id_zone: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[Blocage]:
    query = db.query(Blocage)
    if id_zone is not None:
        query = query.filter(Blocage.id_zone == id_zone)
    return query.order_by(Blocage.date_debut_blocage.desc()).all()


@router.post("", response_model=BlocageCreated, status_code=status.HTTP_201_CREATED)
def create_blocage(
    payload: BlocageCreate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> BlocageCreated:
    """Bloque une zone sur une période ; les réservations concernées sont annulées."""
    blocage, annulees = blocage_service.create_blocage(db, admin, payload)
    journaliser(db, admin.id_utilisateur, "blocage.creation", "zone", blocage.id_zone,
                f"blocage {blocage.id_blocage}, {annulees} réservation(s) annulée(s)")
    return BlocageCreated(
        **BlocageOut.model_validate(blocage).model_dump(), reservations_annulees=annulees
    )


@router.delete("/{id_blocage}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blocage(
    id_blocage: int,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> None:
    blocage_service.delete_blocage(db, id_blocage)
    journaliser(db, admin.id_utilisateur, "blocage.suppression", "blocage", id_blocage)
