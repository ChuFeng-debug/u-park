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
    """Interdit en base deux réservations confirmées qui se chevauchent sur une même place.

    La règle est déjà vérifiée par le service `reservations.py`, mais une
    vérification applicative ne suffit pas : entre le SELECT qui constate que
    la place est libre et l'INSERT qui la réserve, une autre requête peut
    s'intercaler. Deux clics simultanés produiraient alors deux réservations
    sur la même place.

    Cette contrainte ferme la fenêtre, car seule la base peut arbitrer des
    écritures concurrentes. C'est elle qui déclenche l'IntegrityError rattrapée
    dans `create_reservation`.
    """
    # Une contrainte EXCLUDE s'appuie sur un index GiST. Or GiST ne sait pas
    # indexer nativement l'égalité d'un entier : l'extension btree_gist ajoute
    # cette capacité, nécessaire pour combiner `id_place WITH =` et le test
    # de chevauchement dans un même index.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE reservation
        ADD CONSTRAINT excl_reservation_place_creneau
        EXCLUDE USING gist (id_place WITH =, tsrange(date_debut, date_fin) WITH &&)
        WHERE (statut_reservation = 'confirmee')
        """
    )
    # Lecture de la contrainte : deux lignes sont en conflit si elles portent
    # la MÊME place (`id_place WITH =`) ET si leurs intervalles de temps se
    # recoupent (`&&`, opérateur de chevauchement de plages PostgreSQL).
    #
    # `tsrange(date_debut, date_fin)` construit une plage semi-ouverte
    # [debut, fin[ — même convention que la classe Creneau côté Python, ce
    # qui autorise deux réservations adjacentes (10h–12h puis 12h–14h).
    #
    # La clause WHERE en fait une contrainte PARTIELLE : elle ne s'applique
    # qu'aux réservations confirmées. Les annulées et les no-show restent en
    # base pour l'historique sans jamais bloquer une nouvelle réservation.


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE reservation DROP CONSTRAINT excl_reservation_place_creneau")
