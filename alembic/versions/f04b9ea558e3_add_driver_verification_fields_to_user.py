"""add driver verification fields to user

Revision ID: f04b9ea558e3
Revises: <gardez celui généré>
Create Date: 2026-08-08 11:29:52.241173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f04b9ea558e3'
down_revision: Union[str, None] = '<gardez celui généré>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


driver_verification_status_enum = postgresql.ENUM(
    'UNSUBMITTED', 'PENDING', 'APPROVED', 'REJECTED',
    name='driververificationstatus',
)
driver_document_type_enum = postgresql.ENUM(
    'DRIVING_LICENSE', 'NATIONAL_ID', 'STUDENT_CARD',
    name='driverdocumenttype',
)


def upgrade() -> None:
    bind = op.get_bind()
    driver_verification_status_enum.create(bind, checkfirst=True)
    driver_document_type_enum.create(bind, checkfirst=True)

    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('is_driver_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        'users',
        sa.Column(
            'driver_verification_status',
            driver_verification_status_enum,
            nullable=False,
            server_default='UNSUBMITTED',
        ),
    )
    op.add_column(
        'users',
        sa.Column('driver_document_type', driver_document_type_enum, nullable=True),
    )
    op.add_column('users', sa.Column('driver_document_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('driver_verification_rejection_reason', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'driver_verification_rejection_reason')
    op.drop_column('users', 'driver_document_url')
    op.drop_column('users', 'driver_document_type')
    op.drop_column('users', 'driver_verification_status')
    op.drop_column('users', 'is_driver_verified')
    op.drop_column('users', 'is_admin')

    bind = op.get_bind()
    driver_document_type_enum.drop(bind, checkfirst=True)
    driver_verification_status_enum.drop(bind, checkfirst=True)