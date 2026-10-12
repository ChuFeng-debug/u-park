"""Gestion des règles d'accès aux zones et des rôles qu'elles ciblent."""

from sqlalchemy.orm import Session

from app.models import CibleRole, RegleAcces, Role, Zone
from app.schemas.regle_acces import RegleAccesCreate, RegleAccesOut, RegleAccesUpdate
from app.services.exceptions import InvalidRequestError, NotFoundError


def _check_roles(db: Session, roles: list[str]) -> None:
    connus = {row.code_role for row in db.query(Role.code_role).all()}
    inconnus = set(roles) - connus
    if inconnus:
        raise InvalidRequestError(f"Rôle(s) inconnu(s) : {', '.join(sorted(inconnus))}")


def _set_roles(db: Session, regle: RegleAcces, roles: list[str]) -> None:
    db.query(CibleRole).filter_by(id_regle=regle.id_regle).delete()
    db.add_all(CibleRole(id_regle=regle.id_regle, code_role=role) for role in set(roles))


def to_out(db: Session, regle: RegleAcces) -> RegleAccesOut:
    roles = db.query(CibleRole.code_role).filter_by(id_regle=regle.id_regle).all()
    return RegleAccesOut(
        id_regle=regle.id_regle,
        id_zone=regle.id_zone,
        libelle_regle=regle.libelle_regle,
        niveau_priorite=regle.niveau_priorite,
        date_debut_validite=regle.date_debut_validite,
        date_fin_validite=regle.date_fin_validite,
        regle_active=regle.regle_active,
        roles=sorted(row.code_role for row in roles),
    )


def get_regle(db: Session, id_regle: int) -> RegleAcces:
    regle = db.get(RegleAcces, id_regle)
    if regle is None:
        raise NotFoundError("Règle introuvable")
    return regle


def create_regle(db: Session, payload: RegleAccesCreate) -> RegleAcces:
    if db.get(Zone, payload.id_zone) is None:
        raise InvalidRequestError("Zone inconnue")
    _check_roles(db, payload.roles)
    regle = RegleAcces(**payload.model_dump(exclude={"roles"}))
    db.add(regle)
    db.flush()
    _set_roles(db, regle, payload.roles)
    db.commit()
    db.refresh(regle)
    return regle


def update_regle(db: Session, id_regle: int, payload: RegleAccesUpdate) -> RegleAcces:
    regle = get_regle(db, id_regle)
    changes = payload.model_dump(exclude_unset=True)
    roles = changes.pop("roles", None)
    for field, value in changes.items():
        setattr(regle, field, value)
    if regle.date_fin_validite and regle.date_fin_validite < regle.date_debut_validite:
        raise InvalidRequestError("date_fin_validite doit être postérieure à date_debut_validite")
    if roles is not None:
        _check_roles(db, roles)
        _set_roles(db, regle, roles)
    db.commit()
    db.refresh(regle)
    return regle


def delete_regle(db: Session, id_regle: int) -> None:
    regle = get_regle(db, id_regle)
    db.query(CibleRole).filter_by(id_regle=regle.id_regle).delete()
    db.delete(regle)
    db.commit()
