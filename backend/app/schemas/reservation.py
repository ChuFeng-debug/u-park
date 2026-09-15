from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

StatutReservation = Literal["confirmee", "annulee"]


class ReservationCreate(BaseModel):
    id_place: int
    date_debut: datetime
    date_fin: datetime

    @model_validator(mode="after")
    def check_dates(self) -> "ReservationCreate":
        if self.date_fin <= self.date_debut:
            raise ValueError("date_fin doit être postérieure à date_debut")
        return self


class ReservationCancel(BaseModel):
    motif_annulation: str | None = None


class ReservationOut(BaseModel):
    id_reservation: int
    id_utilisateur: int
    id_place: int
    date_debut: datetime
    date_fin: datetime
    statut_reservation: StatutReservation
    date_creation_resa: datetime
    date_annulation: datetime | None
    motif_annulation: str | None

    model_config = {"from_attributes": True}
