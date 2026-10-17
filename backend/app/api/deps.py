"""Dépendances d'authentification et d'autorisation partagées par les routes.

Tout le contrôle d'accès de l'API passe par ce fichier. Une route n'écrit
jamais de test de droits dans son corps : elle déclare la dépendance dont elle
a besoin, et FastAPI l'exécute avant d'appeler la fonction. Si la dépendance
lève, la route n'est jamais atteinte.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import AttributionRole, Utilisateur

# Extrait le jeton de l'en-tête « Authorization: Bearer ... ». `tokenUrl` ne
# sert pas à l'exécution : il indique à la documentation Swagger quelle route
# appeler pour obtenir un jeton, ce qui rend l'API testable depuis /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Identifiants invalides",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Utilisateur:
    """Jeton JWT → utilisateur en base, ou 401.

    La signature du jeton prouve qu'il a bien été émis par l'API, mais ne dit
    rien de l'état actuel du compte. On recharge donc l'utilisateur depuis la
    base à chaque requête : un compte suspendu après l'émission du jeton est
    rejeté immédiatement, sans attendre son expiration.
    """
    try:
        payload = decode_access_token(token)
        # « sub » (subject) est le champ standard JWT portant l'identité.
        user_id = payload.get("sub")
    except JWTError:
        # Signature invalide ou jeton expiré. On renvoie le même message que
        # pour un utilisateur inexistant : distinguer les deux cas
        # renseignerait un attaquant sur la validité de sa clé.
        raise credentials_exception
    if user_id is None:
        raise credentials_exception

    user = db.get(Utilisateur, int(user_id))
    if user is None:
        raise credentials_exception
    if user.statut_compte != "actif":
        # 403 et non 401 : le jeton est valide, c'est le compte qui est fermé.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif")
    return user


def get_user_roles(user: Utilisateur, db: Session) -> set[str]:
    """Codes des rôles détenus par l'utilisateur.

    Les rôles vivent dans une table d'association (relation n-n) et non dans
    une colonne de `utilisateur` : un même compte peut en cumuler plusieurs.
    Ils sont relus en base plutôt que stockés dans le jeton, afin qu'un retrait
    de rôle prenne effet sans attendre une reconnexion.
    """
    rows = db.query(AttributionRole).filter_by(id_utilisateur=user.id_utilisateur).all()
    return {row.code_role for row in rows}


def require_roles(*allowed_roles: str):
    """Fabrique une dépendance exigeant au moins un des rôles donnés.

    C'est une fonction qui *retourne* une fonction (une closure capturant
    `allowed_roles`). Ce détour est nécessaire car FastAPI attend dans
    `Depends(...)` une fonction sans paramètre supplémentaire : impossible de
    lui passer directement la liste des rôles autorisés.

    Usage côté route :
        @router.get("/admin", dependencies=[Depends(require_roles("administrateur"))])
    """

    def dependency(
        user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Utilisateur:
        # Intersection de deux ensembles : non vide dès qu'un seul rôle
        # correspond. Un administrateur qui serait aussi personnel passe donc
        # les contrôles réservés à l'un comme à l'autre.
        if not get_user_roles(user, db) & set(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants"
            )
        return user

    return dependency
