from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import AttributionRole, Trace, Utilisateur
from app.schemas.auth import UserAdminOut, UserAdminUpdate
from app.schemas.trace import TraceOut
from app.services import comptes as compte_service
from app.services.journal import champs_modifies, journaliser

router = APIRouter(prefix="/admin", tags=["administration"])


def _to_admin_out(db: Session, user: Utilisateur) -> UserAdminOut:
    return UserAdminOut(
        id_utilisateur=user.id_utilisateur,
        email=user.email,
        nom_utilisateur=user.nom_utilisateur,
        prenom_utilisateur=user.prenom_utilisateur,
        statut_compte=user.statut_compte,
        besoin_pmr=user.besoin_pmr,
        roles=compte_service.roles_de(db, user.id_utilisateur),
        date_creation_compte=user.date_creation_compte,
    )


@router.get("/utilisateurs", response_model=list[UserAdminOut])
def list_utilisateurs(
    recherche: str | None = Query(default=None, description="Nom, prénom ou email"),
    role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[UserAdminOut]:
    query = db.query(Utilisateur)
    if recherche:
        motif = f"%{recherche}%"
        query = query.filter(
            or_(
                Utilisateur.nom_utilisateur.ilike(motif),
                Utilisateur.prenom_utilisateur.ilike(motif),
                Utilisateur.email.ilike(motif),
            )
        )
    if role:
        query = query.join(
            AttributionRole, AttributionRole.id_utilisateur == Utilisateur.id_utilisateur
        ).filter(AttributionRole.code_role == role)
    users = query.order_by(Utilisateur.nom_utilisateur, Utilisateur.prenom_utilisateur).limit(limit)
    return [_to_admin_out(db, user) for user in users]


@router.patch("/utilisateurs/{id_utilisateur}", response_model=UserAdminOut)
def update_utilisateur(
    id_utilisateur: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_roles("administrateur")),
) -> UserAdminOut:
    """Suspend / réactive un compte ou modifie ses rôles (dont la promotion administrateur)."""
    user = compte_service.administrer(
        db, admin, id_utilisateur, payload.statut_compte, payload.roles
    )
    detail = champs_modifies(payload.model_dump(exclude_unset=True))
    if payload.roles is not None:
        detail += f" ; rôles : {', '.join(sorted(set(payload.roles)))}"
    journaliser(db, admin.id_utilisateur, "utilisateur.administration", "utilisateur",
                id_utilisateur, detail)
    return _to_admin_out(db, user)


@router.get("/traces", response_model=list[TraceOut])
def list_traces(
    type_action: str | None = Query(default=None, description="Préfixe, ex. « reservation. »"),
    id_utilisateur: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles("administrateur")),
) -> list[Trace]:
    query = db.query(Trace)
    if type_action:
        query = query.filter(Trace.type_action.startswith(type_action))
    if id_utilisateur is not None:
        query = query.filter(Trace.id_utilisateur == id_utilisateur)
    return query.order_by(Trace.horodatage.desc(), Trace.id_trace.desc()).limit(limit).all()
