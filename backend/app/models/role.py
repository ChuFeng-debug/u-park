from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(Base):
    __tablename__ = "role"

    code_role: Mapped[str] = mapped_column(String(20), primary_key=True)
    libelle_role: Mapped[str] = mapped_column(String(50), nullable=False)
    description_role: Mapped[str | None] = mapped_column(String(255))


class AttributionRole(Base):
    __tablename__ = "attribution_role"

    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id_utilisateur"), primary_key=True
    )
    code_role: Mapped[str] = mapped_column(ForeignKey("role.code_role"), primary_key=True)
    date_attribution: Mapped[date] = mapped_column(Date, nullable=False)
