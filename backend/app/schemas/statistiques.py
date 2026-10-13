from datetime import date

from pydantic import BaseModel


class Indicateurs(BaseModel):
    reservations: int
    honorees: int
    annulees: int
    no_show: int
    # Ratios entre 0 et 1.
    taux_annulation: float
    taux_no_show: float
    taux_occupation: float


class StatJour(Indicateurs):
    jour: date


class StatZone(Indicateurs):
    id_zone: int
    nom_zone: str
    id_parking: int
    nom_parking: str
    nombre_places: int


class Statistiques(BaseModel):
    du: date
    au: date
    totaux: Indicateurs
    par_jour: list[StatJour]
    par_zone: list[StatZone]
