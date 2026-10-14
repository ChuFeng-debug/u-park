from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.types import UtcDatetime

StatutDemande = Literal["en_attente", "validee", "refusee"]


class DemandeVisiteurCreate(BaseModel):
    date_visite_souhaitee: datetime
    date_fin_visite_souhaitee: datetime
    motif_demande: str = Field(min_length=3, max_length=255)

    @model_validator(mode="after")
    def check_dates(self) -> "DemandeVisiteurCreate":
        if self.date_fin_visite_souhaitee <= self.date_visite_souhaitee:
            raise ValueError("La fin de visite doit être postérieure au début")
        return self


class DemandeValidation(BaseModel):
    # Sans place indiquée, la première place disponible accessible est attribuée.
    id_place: int | None = None
    commentaire_traitement: str | None = Field(default=None, max_length=255)


class DemandeRefus(BaseModel):
    commentaire_traitement: str = Field(min_length=3, max_length=255)


class DemandeVisiteurOut(BaseModel):
    id_demande: int
    id_demandeur: int
    id_administrateur: int | None
    id_reservation: int | None
    date_demande: UtcDatetime
    date_visite_souhaitee: UtcDatetime
    date_fin_visite_souhaitee: UtcDatetime
    motif_demande: str
    statut_demande: StatutDemande
    date_traitement: UtcDatetime | None
    commentaire_traitement: str | None

    model_config = {"from_attributes": True}


class DemandeVisiteurAdminOut(DemandeVisiteurOut):
    nom_demandeur: str
    prenom_demandeur: str
