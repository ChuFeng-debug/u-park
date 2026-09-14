from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegleAcces(Base):
    __tablename__ = "regle_acces"

    id_regle: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_zone: Mapped[int] = mapped_column(ForeignKey("zone.id_zone"), nullable=False)
    libelle_regle: Mapped[str] = mapped_column(String(100), nullable=False)
    niveau_priorite: Mapped[int] = mapped_column(Integer, nullable=False)
    date_debut_validite: Mapped[date] = mapped_column(Date, nullable=False)
    date_fin_validite: Mapped[date | None] = mapped_column(Date)
    regle_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CibleRole(Base):
    __tablename__ = "cible_role"

    id_regle: Mapped[int] = mapped_column(ForeignKey("regle_acces.id_regle"), primary_key=True)
    code_role: Mapped[str] = mapped_column(ForeignKey("role.code_role"), primary_key=True)
