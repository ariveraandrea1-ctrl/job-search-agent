"""crea la tabla interview_questions y agrega question_position a conversation_state

interview_questions: la lista de preguntas de la entrevista, en orden.
Cada pregunta existe en un solo lugar; n8n la lee con el nodo Postgres.
Para agregar una pregunta basta con insertar una fila nueva.

conversation_state.question_position: en qué pregunta va cada usuario
(NULL si no está en entrevista).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    preguntas = op.create_table(
        "interview_questions",
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
    )
    op.bulk_insert(
        preguntas,
        [
            {"position": 1, "question": "¿Qué tipo de rol estás buscando?"},
            {
                "position": 2,
                "question": "¿Qué modalidad prefieres: remoto, híbrido o presencial?",
            },
            {"position": 3, "question": "¿En qué ciudad o país quieres trabajar?"},
        ],
    )
    op.add_column(
        "conversation_state",
        sa.Column("question_position", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_state", "question_position")
    op.drop_table("interview_questions")
