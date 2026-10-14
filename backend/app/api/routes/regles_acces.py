from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import RegleAcces, Utilisateur
from app.schemas.regle_acces import RegleAccesCreate, RegleAccesOut, RegleAccesUpdate
from app.services import regles_acces as regle_service
from app.services.journal import champs_modifies, journaliser

router = APIRouter(prefix="/regles-acces", tags=["administration"])


@router.get("", response_model=list[RegleAccesOut])
def list_regles(
    id_zone: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[RegleAccesOut]:
    query = db.query(RegleAcces)
    if id_zone is not None:
        query = query.filter(RegleAcces.id_zone == id_zone)
    regles = query.order_by(RegleAcces.id_zone, RegleAcces.niveau_priorite).all()
    return [regle_service.to_out(db, regle) for regle in regles]


@router.post("", response_model=RegleAccesOut, status_code=status.HTTP_201_CREATED)
def create_regle(
    payload: RegleAccesCreate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> RegleAccesOut:
    regle = regle_service.create_regle(db, payload)
    journaliser(db, admin.id_utilisateur, "regle.creation", "regle_acces", regle.id_regle,
                f"zone {regle.id_zone}, rôles : {', '.join(sorted(payload.roles))}")
    return regle_service.to_out(db, regle)


@router.patch("/{id_regle}", response_model=RegleAccesOut)
def update_regle(
    id_regle: int,
    payload: RegleAccesUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> RegleAccesOut:
    regle = regle_service.update_regle(db, id_regle, payload)
    journaliser(db, admin.id_utilisateur, "regle.modification", "regle_acces", id_regle,
                champs_modifies(payload.model_dump(exclude_unset=True)))
    return regle_service.to_out(db, regle)


@router.delete("/{id_regle}", status_code=status.HTTP_204_NO_CONTENT)
def delete_regle(
    id_regle: int,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> None:
    regle_service.delete_regle(db, id_regle)
    journaliser(db, admin.id_utilisateur, "regle.suppression", "regle_acces", id_regle)
