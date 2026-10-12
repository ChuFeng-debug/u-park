from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reservation(Base):
    __tablename__ = "reservation"

    id_reservation: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    id_place: Mapped[int] = mapped_column(ForeignKey("place.id_place"), nullable=False)
    date_debut: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_fin: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    statut_reservation: Mapped[str] = mapped_column(String(20), nullable=False)
    date_creation_resa: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_annulation: Mapped[datetime | None] = mapped_column(DateTime)
    motif_annulation: Mapped[str | None] = mapped_column(String(255))
