
from pydantic import BaseModel

from app.schemas.types import UtcDatetime


class TraceOut(BaseModel):
    id_trace: int
    id_utilisateur: int
    horodatage: UtcDatetime
    type_action: str
    entite_cible: str
    identifiant_cible: int
    detail_action: str | None

    model_config = {"from_attributes": True}
