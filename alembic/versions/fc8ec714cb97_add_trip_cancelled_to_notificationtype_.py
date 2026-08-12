"""add trip_cancelled to notificationtype enum

Revision ID: <gardez celui généré>
Revises: fce766455a00
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '<gardez celui généré>'
down_revision: Union[str, None] = 'fce766455a00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'TRIP_CANCELLED'")


def downgrade() -> None:
    # PostgreSQL ne permet pas de retirer une valeur d'un enum facilement.
    # Downgrade non supporté pour cette migration.
    pass