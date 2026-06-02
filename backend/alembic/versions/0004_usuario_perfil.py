"""usuario perfil (RBAC ligero)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-02

"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "perfil",
            sa.String(length=20),
            nullable=False,
            server_default="RECEPCION",
        ),
    )
    # Los usuarios admin existentes pasan a perfil ADMIN (coherencia con is_admin).
    op.execute("UPDATE usuarios SET perfil = 'ADMIN' WHERE is_admin = 1")


def downgrade() -> None:
    op.drop_column("usuarios", "perfil")
