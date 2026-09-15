from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import AttributionRole, Utilisateur

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Identifiants invalides",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Utilisateur:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise credentials_exception
    if user_id is None:
        raise credentials_exception

    user = db.get(Utilisateur, int(user_id))
    if user is None:
        raise credentials_exception
    if user.statut_compte != "actif":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif")
    return user


def get_user_roles(user: Utilisateur, db: Session) -> set[str]:
    rows = db.query(AttributionRole).filter_by(id_utilisateur=user.id_utilisateur).all()
    return {row.code_role for row in rows}


def require_roles(*allowed_roles: str):
    def dependency(
        user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Utilisateur:
        if not get_user_roles(user, db) & set(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants"
            )
        return user

    return dependency
