"""add driver verification notification types

Revision ID: 7ad84ef84cfd
Revises: f04b9ea558e3
Create Date: 2026-08-08

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7ad84ef84cfd'
down_revision: Union[str, None] = 'f04b9ea558e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'DRIVER_VERIFICATION_APPROVED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'DRIVER_VERIFICATION_REJECTED'")


def downgrade() -> None:
    # PostgreSQL ne permet pas de retirer facilement une valeur d'un enum.
    pass