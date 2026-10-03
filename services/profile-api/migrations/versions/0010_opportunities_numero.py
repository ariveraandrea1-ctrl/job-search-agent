"""agrega a opportunities un número corto (#12) para usar en Telegram

Con "numero" el usuario escribe /detalle 12 o /guardar 12 en vez del id
largo (uuid). Sale de una secuencia de Postgres: es único y nunca se
repite. Las filas que ya existían reciben su número al aplicar la
migración.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS opportunities_numero_seq")
    op.add_column(
        "opportunities",
        sa.Column(
            "numero",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("nextval('opportunities_numero_seq')"),
        ),
    )
    op.execute("ALTER SEQUENCE opportunities_numero_seq OWNED BY opportunities.numero")
    op.create_unique_constraint("uq_opportunities_numero", "opportunities", ["numero"])


def downgrade() -> None:
    op.drop_constraint("uq_opportunities_numero", "opportunities", type_="unique")
    op.drop_column("opportunities", "numero")
    op.execute("DROP SEQUENCE IF EXISTS opportunities_numero_seq")
