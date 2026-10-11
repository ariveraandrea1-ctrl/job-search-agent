"""crea la tabla conversation_state

Guarda en qué paso de la conversación va cada usuario de Telegram
(por ejemplo "esperando_respuesta_entrevista"). n8n la lee y escribe
directamente con el nodo Postgres. Una fila por usuario.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_state",
        sa.Column("telegram_user_id", sa.BigInteger(), primary_key=True),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("conversation_state")
