from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PrioriteIncident = Literal["basse", "moyenne", "haute"]
StatutIncident = Literal["ouvert", "en_cours", "resolu"]


class IncidentCreate(BaseModel):
    id_zone: int
    description_incident: str = Field(min_length=5, max_length=500)
    priorite_incident: PrioriteIncident = "moyenne"


class IncidentUpdate(BaseModel):
    priorite_incident: PrioriteIncident | None = None
    statut_incident: StatutIncident | None = None


class IncidentOut(BaseModel):
    id_incident: int
    id_zone: int
    id_utilisateur_signalement: int
    id_utilisateur_traitant: int | None
    description_incident: str
    priorite_incident: PrioriteIncident
    statut_incident: StatutIncident
    date_signalement: datetime
    date_resolution: datetime | None

    model_config = {"from_attributes": True}
