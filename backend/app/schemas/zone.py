from datetime import time

from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    nom_zone: str
    capacite_theorique: int = Field(gt=0)
    heure_ouverture: time
    heure_fermeture: time
    zone_active: bool = True


class ZoneCreate(ZoneBase):
    id_parking: int


class ZoneUpdate(BaseModel):
    nom_zone: str | None = None
    capacite_theorique: int | None = Field(default=None, gt=0)
    heure_ouverture: time | None = None
    heure_fermeture: time | None = None
    zone_active: bool | None = None


class ZoneOut(ZoneBase):
    id_zone: int
    id_parking: int

    model_config = {"from_attributes": True}


class ZoneWithDisponibilite(ZoneOut):
    nombre_places: int
    nombre_places_libres: int
