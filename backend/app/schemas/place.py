from typing import Literal

from pydantic import BaseModel

TypePlace = Literal["standard", "pmr", "electrique", "moto"]
EtatPlace = Literal["libre", "occupee", "hors_service"]


class PlaceBase(BaseModel):
    numero_place: str
    type_place: TypePlace
    etat_place: EtatPlace = "libre"


class PlaceCreate(PlaceBase):
    id_zone: int


class PlaceUpdate(BaseModel):
    numero_place: str | None = None
    type_place: TypePlace | None = None
    etat_place: EtatPlace | None = None


class PlaceOut(PlaceBase):
    id_place: int
    id_zone: int

    model_config = {"from_attributes": True}
