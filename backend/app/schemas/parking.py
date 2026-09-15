from pydantic import BaseModel


class ParkingBase(BaseModel):
    nom_parking: str
    localisation_parking: str
    description_parking: str | None = None


class ParkingCreate(ParkingBase):
    pass


class ParkingUpdate(BaseModel):
    nom_parking: str | None = None
    localisation_parking: str | None = None
    description_parking: str | None = None


class ParkingOut(ParkingBase):
    id_parking: int

    model_config = {"from_attributes": True}
