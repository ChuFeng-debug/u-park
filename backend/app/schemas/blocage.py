from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class BlocageCreate(BaseModel):
    id_zone: int
    motif_blocage: str = Field(min_length=3, max_length=255)
    date_debut_blocage: datetime
    date_fin_blocage: datetime

    @model_validator(mode="after")
    def check_dates(self) -> "BlocageCreate":
        if self.date_fin_blocage <= self.date_debut_blocage:
            raise ValueError("date_fin_blocage doit être postérieure à date_debut_blocage")
        return self


class BlocageOut(BaseModel):
    id_blocage: int
    id_zone: int
    id_utilisateur: int
    motif_blocage: str
    date_debut_blocage: datetime
    date_fin_blocage: datetime

    model_config = {"from_attributes": True}


class BlocageCreated(BlocageOut):
    reservations_annulees: int
