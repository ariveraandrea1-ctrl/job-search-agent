"""agrega "topic" a interview_answers

Guarda el tema de la pregunta respondida (salario, modalidad, ...), para
saber a qué dato del perfil corresponde cada respuesta. Las respuestas
viejas quedan con topic NULL (se guardaron antes de existir los temas).

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_answers",
        sa.Column("topic", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_answers", "topic")
