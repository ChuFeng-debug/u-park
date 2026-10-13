"""passage et no-show

Revision ID: c6928a8fb982
Revises: bef2b70c53ee
Create Date: 2026-10-13 14:29:38.335054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6928a8fb982'
down_revision: Union[str, Sequence[str], None] = 'bef2b70c53ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Passage à l'entrée (scan simulé), base du statut no_show."""
    op.add_column("reservation", sa.Column("date_passage", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("reservation", "date_passage")
