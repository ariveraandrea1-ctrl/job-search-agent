"""crea la tabla profiles

profiles: el perfil que la IA arma a partir del CV (el JSON que devuelve
el workflow ai-model-router). Se guarda el JSON completo en una columna
JSONB, junto con quién es el usuario, de qué CV salió, qué proveedor de
IA respondió y con qué versión del prompt. Cada vez que el usuario manda
un CV se agrega una fila nueva (no se sobrescribe): así queda historial
y se pueden comparar versiones del prompt.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=True,
        ),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_profiles_telegram_user_id",
        "profiles",
        ["telegram_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_profiles_telegram_user_id", table_name="profiles")
    op.drop_table("profiles")
