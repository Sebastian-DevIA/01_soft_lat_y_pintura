"""vehiculo soft-delete (columna activo)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-30

"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vehiculos",
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("vehiculos", "activo")
