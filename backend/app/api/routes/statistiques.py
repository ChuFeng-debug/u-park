from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Utilisateur
from app.schemas.statistiques import Statistiques
from app.services import statistiques as statistiques_service

router = APIRouter(prefix="/admin/statistiques", tags=["administration"])


@router.get("", response_model=Statistiques)
def get_statistiques(
    du: date | None = Query(default=None, description="Premier jour (défaut : 30 derniers jours)"),
    au: date | None = Query(default=None, description="Dernier jour inclus (défaut : aujourd'hui)"),
    id_parking: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> Statistiques:
    """Taux d'occupation, réservations, annulations et no-shows par jour et par zone."""
    return statistiques_service.calculer(db, du, au, id_parking)
