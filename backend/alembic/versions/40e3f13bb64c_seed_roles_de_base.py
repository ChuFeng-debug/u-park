"""seed roles de base

Revision ID: 40e3f13bb64c
Revises: 603caf0cfe62
Create Date: 2026-09-15 11:22:00.718778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40e3f13bb64c'
down_revision: Union[str, Sequence[str], None] = '603caf0cfe62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


role_table = sa.table(
    "role",
    sa.column("code_role", sa.String),
    sa.column("libelle_role", sa.String),
    sa.column("description_role", sa.String),
)

ROLES = [
    {
        "code_role": "etudiant",
        "libelle_role": "Étudiant",
        "description_role": "Étudiant motorisé de l'université",
    },
    {
        "code_role": "personnel",
        "libelle_role": "Personnel",
        "description_role": "Personnel universitaire, accès régulier ou prioritaire",
    },
    {
        "code_role": "visiteur",
        "libelle_role": "Visiteur",
        "description_role": "Visiteur ou intervenant extérieur, accès temporaire",
    },
    {
        "code_role": "administrateur",
        "libelle_role": "Administrateur",
        "description_role": "Administrateur de parking",
    },
]


def upgrade() -> None:
    op.bulk_insert(role_table, ROLES)


def downgrade() -> None:
    op.execute(
        role_table.delete().where(
            role_table.c.code_role.in_([r["code_role"] for r in ROLES])
        )
    )
