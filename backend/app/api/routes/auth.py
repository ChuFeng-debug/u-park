from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import AttributionRole, Role, Utilisateur
from app.schemas.auth import Token, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


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
    return _to_user_out(user, db)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(Utilisateur).filter_by(email=form_data.username).first()
    if user is None or not verify_password(form_data.password, user.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.statut_compte != "actif":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif")

    token = create_access_token(subject=str(user.id_utilisateur))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)) -> UserOut:
    return _to_user_out(user, db)
