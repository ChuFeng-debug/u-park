"""contrainte anti chevauchement reservation

Revision ID: 5d5d04aa650e
Revises: 40e3f13bb64c
Create Date: 2026-10-12 15:10:27.871377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d5d04aa650e'
down_revision: Union[str, Sequence[str], None] = '40e3f13bb64c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Interdit en base deux réservations confirmées qui se chevauchent sur une même place."""
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE reservation
        ADD CONSTRAINT excl_reservation_place_creneau
        EXCLUDE USING gist (id_place WITH =, tsrange(date_debut, date_fin) WITH &&)
        WHERE (statut_reservation = 'confirmee')
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE reservation DROP CONSTRAINT excl_reservation_place_creneau")
