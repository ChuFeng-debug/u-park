from datetime import date

from pydantic import BaseModel, Field, model_validator


class RegleAccesBase(BaseModel):
    libelle_regle: str = Field(min_length=3, max_length=100)
    niveau_priorite: int = Field(ge=1)
    date_debut_validite: date
    date_fin_validite: date | None = None
    regle_active: bool = True

    @model_validator(mode="after")
    def check_dates(self) -> "RegleAccesBase":
        if self.date_fin_validite and self.date_fin_validite < self.date_debut_validite:
            raise ValueError("date_fin_validite doit être postérieure à date_debut_validite")
        return self


class RegleAccesCreate(RegleAccesBase):
    id_zone: int
    roles: list[str] = Field(min_length=1)


class RegleAccesUpdate(BaseModel):
    libelle_regle: str | None = Field(default=None, min_length=3, max_length=100)
    niveau_priorite: int | None = Field(default=None, ge=1)
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    regle_active: bool | None = None
    roles: list[str] | None = Field(default=None, min_length=1)


class RegleAccesOut(RegleAccesBase):
    id_regle: int
    id_zone: int
    roles: list[str]
