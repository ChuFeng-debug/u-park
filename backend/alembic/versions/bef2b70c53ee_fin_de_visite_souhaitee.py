"""fin de visite souhaitee

Revision ID: bef2b70c53ee
Revises: 5d5d04aa650e
Create Date: 2026-10-12 15:37:12.131767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bef2b70c53ee'
down_revision: Union[str, Sequence[str], None] = '5d5d04aa650e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Une demande visiteur porte un créneau complet (début et fin de visite)."""
    op.add_column(
        "demande_visiteur",
        sa.Column("date_fin_visite_souhaitee", sa.DateTime(), nullable=True),
    )
    # Demandes éventuelles antérieures : visite de 2 h par défaut.
    op.execute(
        "UPDATE demande_visiteur "
        "SET date_fin_visite_souhaitee = date_visite_souhaitee + interval '2 hours'"
    )
    op.alter_column("demande_visiteur", "date_fin_visite_souhaitee", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("demande_visiteur", "date_fin_visite_souhaitee")
