from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parking(Base):
    __tablename__ = "parking"

    id_parking: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nom_parking: Mapped[str] = mapped_column(String(80), nullable=False)
    localisation_parking: Mapped[str] = mapped_column(String(150), nullable=False)
    description_parking: Mapped[str | None] = mapped_column(String(255))
