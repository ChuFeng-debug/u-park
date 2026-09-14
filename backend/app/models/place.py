from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Place(Base):
    __tablename__ = "place"

    id_place: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_zone: Mapped[int] = mapped_column(ForeignKey("zone.id_zone"), nullable=False)
    numero_place: Mapped[str] = mapped_column(String(10), nullable=False)
    type_place: Mapped[str] = mapped_column(String(20), nullable=False)
    etat_place: Mapped[str] = mapped_column(String(20), nullable=False)
