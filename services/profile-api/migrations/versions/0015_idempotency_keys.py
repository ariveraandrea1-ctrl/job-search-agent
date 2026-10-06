"""idempotencia: tabla idempotency_keys (spec 7.2)

Una fila por cada cosa que debe pasar UNA sola vez. La clave es el
"idempotency_key":
  telegram-update:{update_id}   -> un mensaje de Telegram se atiende una vez
                                   (si Telegram lo reenvía, se ignora)
  resumen:{usuario}:{AAAA-MM-DD} -> un resumen diario por usuario y día
Si la clave ya existe, es un reintento y no se repite la acción.

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

TENANT_PRINCIPAL = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("clave", sa.Text(), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False,
                  server_default=sa.text(f"'{TENANT_PRINCIPAL}'::uuid")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
