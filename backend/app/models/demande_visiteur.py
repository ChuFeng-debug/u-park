from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DemandeVisiteur(Base):
    __tablename__ = "demande_visiteur"

    id_demande: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_demandeur: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    id_administrateur: Mapped[int | None] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur")
    )
    id_reservation: Mapped[int | None] = mapped_column(
        ForeignKey("reservation.id_reservation"), unique=True
    )
    date_demande: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_visite_souhaitee: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    motif_demande: Mapped[str] = mapped_column(String(255), nullable=False)
    statut_demande: Mapped[str] = mapped_column(String(20), nullable=False)
    date_traitement: Mapped[datetime | None] = mapped_column(DateTime)
    commentaire_traitement: Mapped[str | None] = mapped_column(String(255))
