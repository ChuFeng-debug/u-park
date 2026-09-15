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
