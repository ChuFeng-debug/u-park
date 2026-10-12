from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Blocage(Base):
    __tablename__ = "blocage"

    id_blocage: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_zone: Mapped[int] = mapped_column(ForeignKey("zone.id_zone"), nullable=False)
    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    motif_blocage: Mapped[str] = mapped_column(String(255), nullable=False)
    date_debut_blocage: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_fin_blocage: Mapped[datetime] = mapped_column(DateTime, nullable=False)
