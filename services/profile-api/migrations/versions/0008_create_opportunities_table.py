"""crea la tabla opportunities (radar de vacantes)

opportunities: cada vacante (empleo) o proyecto (freelance) que el radar
encuentra en alguna fuente (alertas de correo, Greenhouse/Lever, URL
manual). "dedup_key" es la huella de la vacante (link normalizado o
fuente:id); es única por usuario, así la misma vacante nunca se guarda dos
veces aunque llegue repetida o n8n reintente.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        # "empleo" o "freelance"
        sa.Column("tipo", sa.String(length=20), nullable=False),
        # linkedin, indeed, computrabajo, workana, greenhouse, lever, manual...
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Datos originales tal como llegaron (por si hay que re-procesar).
        sa.Column("raw", postgresql.JSONB(), nullable=True),
        # nueva, guardada, descartada
        sa.Column("status", sa.String(length=20), nullable=False, server_default="nueva"),
        # Puntaje de 0 a 100 (se llena en la Semana 6).
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("dedup_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "telegram_user_id", "dedup_key", name="uq_opportunities_user_dedup"
        ),
    )
    op.create_index(
        "ix_opportunities_user_status",
        "opportunities",
        ["telegram_user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_user_status", table_name="opportunities")
    op.drop_table("opportunities")
