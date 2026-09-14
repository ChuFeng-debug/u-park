from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nom_utilisateur: Mapped[str] = mapped_column(String(80), nullable=False)
    prenom_utilisateur: Mapped[str] = mapped_column(String(80), nullable=False)
    statut_compte: Mapped[str] = mapped_column(String(20), nullable=False)
    besoin_pmr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_creation_compte: Mapped[datetime] = mapped_column(DateTime, nullable=False)
