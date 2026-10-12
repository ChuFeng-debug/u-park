from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incident"

    id_incident: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_zone: Mapped[int] = mapped_column(ForeignKey("zone.id_zone"), nullable=False)
    id_utilisateur_signalement: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    id_utilisateur_traitant: Mapped[int | None] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur")
    )
    description_incident: Mapped[str] = mapped_column(String(500), nullable=False)
    priorite_incident: Mapped[str] = mapped_column(String(20), nullable=False)
    statut_incident: Mapped[str] = mapped_column(String(20), nullable=False)
    date_signalement: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_resolution: Mapped[datetime | None] = mapped_column(DateTime)
