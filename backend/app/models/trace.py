from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trace(Base):
    __tablename__ = "trace"

    id_trace: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    horodatage: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    type_action: Mapped[str] = mapped_column(String(50), nullable=False)
    entite_cible: Mapped[str] = mapped_column(String(50), nullable=False)
    identifiant_cible: Mapped[int] = mapped_column(Integer, nullable=False)
    detail_action: Mapped[str | None] = mapped_column(String(255))
