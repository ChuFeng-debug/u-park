from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import AttributionRole, Role, Utilisateur
from app.schemas.auth import (
    AccountDelete,
    PasswordChange,
    Token,
    UserOut,
    UserRegister,
    UserUpdate,
)
from app.services import comptes as compte_service
from app.services.journal import champs_modifies, journaliser

router = APIRouter(prefix="/auth", tags=["auth"])

# Un compte administrateur ne peut pas être créé par auto-inscription.
SELF_REGISTER_ROLES = {"etudiant", "personnel", "visiteur"}


def _to_user_out(user: Utilisateur, db: Session) -> UserOut:
    return UserOut(
        id_utilisateur=user.id_utilisateur,
        email=user.email,
        nom_utilisateur=user.nom_utilisateur,
        prenom_utilisateur=user.prenom_utilisateur,
        statut_compte=user.statut_compte,
        besoin_pmr=user.besoin_pmr,
        roles=sorted(get_user_roles(user, db)),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserOut:
    if db.query(Utilisateur).filter_by(email=payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

    role = db.get(Role, payload.role)
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu")
    if role.code_role not in SELF_REGISTER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Ce rôle ne peut pas être choisi à l'inscription"
        )

    now = datetime.now(timezone.utc)
    user = Utilisateur(
        email=payload.email,
        mot_de_passe_hash=hash_password(payload.password),
        nom_utilisateur=payload.nom_utilisateur,
        prenom_utilisateur=payload.prenom_utilisateur,
        statut_compte="actif",
        besoin_pmr=payload.besoin_pmr,
        date_creation_compte=now,
    )
    db.add(user)
    db.flush()
    db.add(
        AttributionRole(
            id_utilisateur=user.id_utilisateur, code_role=role.code_role, date_attribution=now.date()
        )
    )
    db.commit()
    db.refresh(user)
    journaliser(db, user.id_utilisateur, "compte.creation", "utilisateur", user.id_utilisateur,
                f"rôle : {role.code_role}")
    return _to_user_out(user, db)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(Utilisateur).filter_by(email=form_data.username).first()
    if user is None or not verify_password(form_data.password, user.mot_de_passe_hash):
        if user is not None:
            journaliser(db, user.id_utilisateur, "connexion.echec", "utilisateur", user.id_utilisateur)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.statut_compte != "actif":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif")

    token = create_access_token(subject=str(user.id_utilisateur))
    journaliser(db, user.id_utilisateur, "connexion.reussie", "utilisateur", user.id_utilisateur)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)) -> UserOut:
    return _to_user_out(user, db)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    compte_service.modifier_profil(db, user, changes)
    journaliser(db, user.id_utilisateur, "compte.modification", "utilisateur",
                user.id_utilisateur, champs_modifies(changes))
    return _to_user_out(user, db)


@router.post("/me/mot-de-passe", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    compte_service.changer_mot_de_passe(
        db, user, payload.mot_de_passe_actuel, payload.nouveau_mot_de_passe
    )
    journaliser(db, user.id_utilisateur, "compte.mot_de_passe", "utilisateur", user.id_utilisateur)


@router.get("/me/export")
def export_me(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Droit d'accès RGPD : export de toutes les données liées au compte."""
    data = compte_service.exporter(db, user)
    journaliser(db, user.id_utilisateur, "rgpd.export", "utilisateur", user.id_utilisateur)
    return data


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    payload: AccountDelete,
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Droit à l'effacement RGPD : le compte est anonymisé et désactivé."""
    annulees = compte_service.anonymiser(db, user, payload.mot_de_passe)
    journaliser(db, user.id_utilisateur, "rgpd.suppression", "utilisateur", user.id_utilisateur,
                f"{annulees} réservation(s) annulée(s)")
