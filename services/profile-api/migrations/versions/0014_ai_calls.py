"""telemetría de IA: tabla ai_calls (una fila por cada uso de la IA)

tarea (cv | puntaje), proveedor (groq | gemini), modelo, prompt_version,
tokens de entrada y salida, latencia en ms, costo estimado (USD),
fallback (true si respondió Gemini porque Groq falló), ok (false si la
respuesta no sirvió: JSON inválido) y el error.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

TENANT_PRINCIPAL = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.create_table(
        "ai_calls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False,
                  server_default=sa.text(f"'{TENANT_PRINCIPAL}'::uuid")),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("tarea", sa.String(30), nullable=False),
        sa.Column("proveedor", sa.String(50), nullable=True),
        sa.Column("modelo", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("tokens_entrada", sa.Integer(), nullable=True),
        sa.Column("tokens_salida", sa.Integer(), nullable=True),
        sa.Column("latencia_ms", sa.Integer(), nullable=True),
        sa.Column("costo_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_calls_created_at", "ai_calls", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_calls_created_at", "ai_calls")
    op.drop_table("ai_calls")
