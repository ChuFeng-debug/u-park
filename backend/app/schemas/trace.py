from datetime import datetime

from pydantic import BaseModel


class TraceOut(BaseModel):
    id_trace: int
    id_utilisateur: int
    horodatage: datetime
    type_action: str
    entite_cible: str
    identifiant_cible: int
    detail_action: str | None

    model_config = {"from_attributes": True}
