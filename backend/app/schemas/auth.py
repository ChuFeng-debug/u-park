from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nom_utilisateur: str
    prenom_utilisateur: str
    role: str
    besoin_pmr: bool = False


class UserOut(BaseModel):
    id_utilisateur: int
    email: EmailStr
    nom_utilisateur: str
    prenom_utilisateur: str
    statut_compte: str
    besoin_pmr: bool
    roles: list[str]

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    nom_utilisateur: str | None = Field(default=None, min_length=1, max_length=80)
    prenom_utilisateur: str | None = Field(default=None, min_length=1, max_length=80)
    besoin_pmr: bool | None = None


class PasswordChange(BaseModel):
    mot_de_passe_actuel: str
    nouveau_mot_de_passe: str = Field(min_length=8)


class AccountDelete(BaseModel):
    mot_de_passe: str


class UserAdminOut(UserOut):
    date_creation_compte: datetime


class UserAdminUpdate(BaseModel):
    statut_compte: Literal["actif", "suspendu"] | None = None
    roles: list[str] | None = None
