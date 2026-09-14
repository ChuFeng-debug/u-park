from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Zone(Base):
    __tablename__ = "zone"

    id_zone: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_parking: Mapped[int] = mapped_column(ForeignKey("parking.id_parking"), nullable=False)
    nom_zone: Mapped[str] = mapped_column(String(80), nullable=False)
    capacite_theorique: Mapped[int] = mapped_column(Integer, nullable=False)
    heure_ouverture: Mapped[time] = mapped_column(Time, nullable=False)
    heure_fermeture: Mapped[time] = mapped_column(Time, nullable=False)
    zone_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
